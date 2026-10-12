"""Offline regressions for dossier integrity, preservation and portable navigation."""
from pathlib import Path, PurePosixPath, PureWindowsPath
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

MODULE = Path(__file__).resolve().parents[1] / 'skill/scripts/delivery.py'
spec = importlib.util.spec_from_file_location('delivery', MODULE)
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)
HAS_MARKDOWN = importlib.util.find_spec('markdown') is not None
HAS_PDF = importlib.util.find_spec('pymupdf') is not None


class DossierFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = (Path(self.temp.name) / 'dossier').resolve()
        self.root.mkdir()
        self.write('README.html', '<h1 id="intro">Research</h1>')
        self.manifest = self.root / 'inventory.json'

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def freeze(self):
        delivery.inventory(self.root, self.manifest)

    def check(self, **kwargs):
        return delivery.check(self.root, self.manifest, **kwargs)


class DeliveryTests(DossierFixture):
    def test_frozen_inventory_passes_after_relocation(self):
        self.write('README.html', '<a href="02-studies/topic.html#answer">Answer</a>')
        self.write('02-studies/topic.html', '<h1 id="answer">Answer</h1>')
        self.freeze()
        moved = self.root.parent / 'shared dossier'
        shutil.copytree(self.root, moved)
        result = delivery.check(moved, moved / 'inventory.json')
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['checks']['local_links'], 1)

    def test_portable_names_match_across_windows_and_posix(self):
        expected = '02-studies/café.html'
        for root in (PureWindowsPath('C:/dossier'), PurePosixPath('/dossier')):
            with self.subTest(root=root):
                self.assertEqual(delivery.relative_name(root, root / expected), expected)

    def test_relative_pdf_file_links_use_posix_spelling_on_every_host(self):
        for root in (PureWindowsPath('C:/dossier'), PurePosixPath('/dossier')):
            with self.subTest(root=root):
                owner = root / '01-reports/pdf/executive.pdf'
                target = root / '02-studies/café 100%#one.html'
                self.assertEqual(delivery.relative_file_link(owner, target),
                                 '../../02-studies/café 100%#one.html')

    def test_relative_pdf_file_links_ignore_windows_drive_letter_case(self):
        owner = PureWindowsPath('c:/dossier/01-reports/portable.pdf')
        target = PureWindowsPath('C:/dossier/02-studies/topic.html')
        self.assertEqual(delivery.relative_file_link(owner, target), '../02-studies/topic.html')

    def test_network_path_references_are_rejected_in_local_dossiers(self):
        # Opened from disk, //host/x resolves to file://host/x (a UNC fetch on Windows) and
        # ///abs or //localhost/abs to an absolute local file outside the dossier.
        for target in ('//example.invalid/study', '///etc/passwd', '//localhost/etc/passwd',
                       '////host/share', '//server\\share\\file.html'):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, 'Network-path reference|Nonportable'):
                    delivery.local_target(self.root, self.root / 'README.html', target)
        self.assertIsNone(delivery.local_target(self.root, self.root / 'README.html',
                                                'https://example.invalid/study'))
        self.write('README.html', '<a href="///etc/passwd">Local file</a>')
        self.freeze()
        result = self.check()
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(any('Network-path reference' in e['reason'] for e in result['errors']))

    # Value: protects=links a browser resolves to //host are refused on every Python version;
    # fails_when=the WHATWG trim/tab removal is dropped or runs after the // check;
    # why_new=the test above covers clean // targets only; seam=none
    def test_whatwg_preprocessing_cannot_hide_a_network_path(self):
        # Browsers strip leading/trailing C0 controls and spaces, then drop every tab/LF/CR.
        # Python 3.9.6 urlsplit keeps a leading space, so " //host/x" plus a bait file at
        # "<dir>/ /host/x" used to pass as a verified local link.
        bait = self.write(' /example.invalid/x', 'bait')
        self.assertTrue(bait.exists())
        for target in (' //example.invalid/x', '\x01//example.invalid/x', '/\t/example.invalid/x',
                       '/\n/example.invalid/x', ' \t/\r/example.invalid/x'):
            with self.subTest(target=repr(target)):
                with self.assertRaisesRegex(ValueError, 'Network-path reference'):
                    delivery.local_target(self.root, self.root / 'README.html', target)
        for target in (' ', '\t\n', '\x1f'):
            with self.subTest(target=repr(target)):
                with self.assertRaisesRegex(ValueError, 'Invalid empty link target'):
                    delivery.local_target(self.root, self.root / 'README.html', target)
        # A legitimate link survives the same preprocessing, fragment included.
        self.write('02-studies/topic.html', '<h1 id="answer">Answer</h1>')
        path, fragment = delivery.local_target(self.root, self.root / 'README.html',
                                               ' 02-studies/topic.html#answer\n')
        self.assertEqual((path.name, fragment), ('topic.html', 'answer'))
        # A literal PDF filename is not a URL: its leading space is part of the name.
        literal = self.write(' lead.pdf', 'pdf')
        self.assertEqual(delivery.local_target(self.root, self.root / 'README.html', ' lead.pdf',
                                               literal_file=True)[0], literal)
        # End to end: the bait no longer turns the network path into a passing local link.
        self.write('README.html', '<a href=" //example.invalid/x">x</a>')
        self.freeze()
        result = self.check()
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(any('Network-path reference' in e['reason'] for e in result['errors']))

    def test_duplicate_link_attributes_are_all_checked(self):
        # Browsers use the first duplicate attribute; checking only the last let //host pass.
        for html in ('<img src="//example.invalid/share" src="https://example.invalid/pixel">',
                     '<img src="https://example.invalid/pixel" src="//example.invalid/share">'):
            with self.subTest(html=html):
                self.write('README.html', html)
                self.manifest.unlink(missing_ok=True)
                self.freeze()
                result = self.check()
                self.assertEqual(result['status'], 'fail', result)
                self.assertTrue(any('Network-path reference' in e['reason'] for e in result['errors']))

    # Value: protects=fragment anchors follow browser rules (first duplicate wins; name only on <a>; id and name are independent);
    # fails_when=handle_starttag treats name on any tag as an anchor or lets the first id suppress a distinct name;
    # why_new=the rewritten loop's (key == 'id' or tag == 'a') and per-key `seen` branches had no case; seam=none
    def test_only_the_first_duplicate_id_or_name_is_an_anchor(self):
        # Browsers keep the first duplicate attribute, so a link to a later one is broken.
        cases = (('<h1 id="real" id="ghost">x</h1><a href="#ghost">go</a>', 'fail'),
                 ('<h1 id="real" id="ghost">x</h1><a href="#real">go</a>', 'pass'),
                 ('<a name="real" name="ghost">x</a><a href="#ghost">go</a>', 'fail'),
                 ('<div name="real">x</div><a href="#real">go</a>', 'fail'),
                 ('<a id="one" name="two">x</a><a href="#one">1</a><a href="#two">2</a>', 'pass'))
        for html, status in cases:
            with self.subTest(html=html):
                self.write('README.html', html)
                self.manifest.unlink(missing_ok=True)
                self.freeze()
                self.assertEqual(self.check()['status'], status)

    def test_literal_unc_pdf_file_is_rejected_as_windows_path(self):
        for target in ('//server/share/file.pdf', r'\\server\share\file.pdf'):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, 'Nonportable Windows path'):
                    delivery.local_target(self.root, self.root / 'README.html', target,
                                          literal_file=True)

    def test_inventory_refuses_names_its_own_check_would_reject(self):
        for name in ('03-sources/foo\\bar.txt', 'C:export.txt'):
            with self.subTest(name=name):
                bad = self.write(name, 'x')
                with self.assertRaisesRegex(ValueError, 'Invalid inventory path'):
                    self.freeze()
                self.assertFalse(self.manifest.exists())
                bad.unlink()

    def test_unicode_inventory_survives_legacy_locale_and_relocation(self):
        self.write('02-studies/café.html', '<p>Evidence</p>')
        self.freeze()
        moved = self.root.parent / 'copied dossier'
        shutil.copytree(self.root, moved)
        read_text = Path.read_text
        def legacy_default(path, *args, **kwargs):
            if not args and 'encoding' not in kwargs:
                kwargs['encoding'] = 'cp1252'
            return read_text(path, *args, **kwargs)
        with mock.patch.object(Path, 'read_text', legacy_default):
            result = delivery.check(moved, moved / 'inventory.json')
        self.assertEqual(result['status'], 'pass', result)
        manifest = json.loads((moved / 'inventory.json').read_text(encoding='utf-8'))
        self.assertIn('02-studies/café.html', manifest['files'])

    def test_inventory_rejects_nonportable_keys_on_any_host(self):
        self.freeze()
        original = json.loads(self.manifest.read_text(encoding='utf-8'))
        for key in ('02-studies\\study.html', 'C:/study.html', './README.html', '/README.html',
                    '02-studies//study.html', '../study.html'):
            with self.subTest(key=key):
                invalid = dict(original, files={key: original['files']['README.html']})
                self.manifest.write_text(json.dumps(invalid), encoding='utf-8')
                result = self.check()
                self.assertEqual(result['status'], 'fail', result)
                self.assertTrue(any('Invalid inventory path' in e['reason'] for e in result['errors']))

    def test_cli_json_supports_ascii_console_with_unicode_paths(self):
        result = subprocess.run(
            [sys.executable, str(MODULE), 'inventory', str(self.root), 'inventário.json'],
            capture_output=True, env=dict(os.environ, PYTHONIOENCODING='ascii'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['path'], 'inventário.json')

    def test_inventory_detects_changed_missing_and_extra_files(self):
        self.write('03-sources/original.bin', 'source')
        self.freeze()
        self.write('README.html', 'changed')
        (self.root / '03-sources/original.bin').unlink()
        self.write('new.txt', 'extra')
        result = self.check()
        self.assertEqual(result['status'], 'fail')
        self.assertEqual({e['reason'] for e in result['errors']},
                         {'Inventory byte/hash mismatch', 'Missing inventoried file', 'File missing from inventory'})

    def test_inventory_is_exclusive(self):
        self.freeze()
        original = self.manifest.read_bytes()
        with self.assertRaises(FileExistsError):
            self.freeze()
        self.assertEqual(original, self.manifest.read_bytes())

    def test_malformed_manifests_return_failure(self):
        for content in ['[]', '{"schema":1,"schema":1}', '{"schema":true,"path_base":"dossier_root","files":{}}',
                        '{"schema":1,"path_base":"dossier_root","files":{"../escape":{}}}']:
            with self.subTest(content=content):
                self.manifest.write_text(content)
                self.assertEqual(self.check()['status'], 'fail')

    def test_symlink_directory_rejected(self):
        (self.root / 'linked').symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.freeze()
        self.assertFalse(self.manifest.exists())
        self.assertEqual(self.check()['status'], 'fail')

    def test_path_escape_and_destination_symlink_refused(self):
        outside = self.root.parent / 'outside.json'
        outside.write_text('keep')
        with self.assertRaises(ValueError):
            delivery.inventory(self.root, outside)
        self.manifest.symlink_to(outside)
        with self.assertRaises(ValueError):
            self.freeze()
        self.assertEqual(outside.read_text(), 'keep')

    def test_capture_preserves_exact_bytes_and_records_provenance(self):
        source = self.root.parent / 'transcript.jsonl'
        source.write_bytes(b'{"text":"original"}\n\x00\xff')
        target = self.root / '05-research-log/cycle/transcript.jsonl'
        target.parent.mkdir(parents=True)
        result = delivery.capture(self.root, source, target, 'explicit host export')
        self.assertEqual(target.read_bytes(), source.read_bytes())
        receipt = json.loads((self.root / result['receipt']).read_text())
        self.assertEqual(receipt['sha256'], delivery.digest(source)['sha256'])
        self.assertEqual(receipt['origin'], 'explicit host export')
        with self.assertRaises(FileExistsError):
            delivery.capture(self.root, source, target, 'repeat')

    def test_capture_existing_receipt_prevents_write(self):
        source = self.write('input', 'original')
        self.write('copy.receipt.json', 'keep')
        with self.assertRaises(FileExistsError):
            delivery.capture(self.root, source, self.root / 'copy', 'source')
        self.assertFalse((self.root / 'copy').exists())
        self.assertEqual((self.root / 'copy.receipt.json').read_text(), 'keep')

    def test_capture_changed_source_and_receipt_failure_remove_only_new_copy(self):
        source = self.write('input', 'original')
        target = self.root / 'copy'
        original_copy = shutil.copyfileobj
        def mutate(src, dst):
            original_copy(src, dst)
            source.write_text('mutated')
        with mock.patch.object(shutil, 'copyfileobj', side_effect=mutate):
            with self.assertRaises(ValueError):
                delivery.capture(self.root, source, target, 'export')
        self.assertFalse(target.exists())
        with mock.patch.object(delivery, 'new_bytes', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                delivery.capture(self.root, source, target, 'export')
        self.assertFalse(target.exists())
        self.assertFalse(Path(str(target) + '.receipt.json').exists())
        self.assertEqual(source.read_text(), 'mutated')

    def test_missing_fragment_missing_file_absolute_and_external_links(self):
        self.write('README.html', '<a href="#missing">Bad</a><img src="missing.png">'
                   '<a href="/tmp/host-secret">Local</a><a href="https://example.invalid">External</a>')
        self.freeze()
        result = self.check()
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(len(result['errors']), 3)

    def test_missing_library_and_html_base_are_partial(self):
        self.write('README.md', '# Research')
        self.write('README.html', '<base href="https://example.invalid/">')
        self.freeze()
        with mock.patch.object(delivery, 'module', side_effect=delivery.Unverified('missing library')):
            result = self.check()
        self.assertEqual(result['status'], 'partial', result)
        self.assertEqual(len(result['unverified']), 2)

    def test_evidence_not_navigation_but_still_in_inventory(self):
        self.write('03-sources/raw.html', '<a href="/publisher/path">Original</a>')
        self.freeze()
        self.assertEqual(self.check()['status'], 'pass')
        self.write('03-sources/raw.html', 'changed')
        self.assertEqual(self.check()['status'], 'fail')

    def test_cli_fail_and_partial_exit_codes(self):
        result = subprocess.run([sys.executable, str(MODULE), 'check', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'partial')
        result = subprocess.run([sys.executable, str(MODULE), 'inventory', str(self.root), '../escape.json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['status'], 'fail')

    # Generated by /ship test-coverage audit (Sherlock 0.1.0-beta.4).
    # Value: protects=the CLI refuses a symlinked, non-directory or missing dossier root before any write;
    # fails_when=the root guards are lost when main() delegates to dossier_command;
    # why_new=no test drove the CLI with a bad root, before or after the refactor; seam=none
    def test_cli_refuses_symlinked_missing_or_non_directory_root(self):
        alias = self.root.parent / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        for root, reason in ((alias, 'cannot be a symlink'), (self.root / 'README.html', 'must be a directory'),
                             (self.root.parent / 'missing', 'missing')):
            with self.subTest(root=root):
                result = subprocess.run([sys.executable, str(MODULE), 'inventory', str(root), 'inventory.json'],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                out = json.loads(result.stdout)
                self.assertEqual(out['status'], 'fail')
                self.assertRegex(out['errors'][0], reason)
                self.assertFalse(self.manifest.exists())

    @unittest.skipUnless(HAS_MARKDOWN, 'Optional Markdown dependency not installed')
    def test_markdown_reference_unicode_fragment_and_image(self):
        self.write('README.md', '[Study][s]\n\n[s]: 02-studies/study.md#conclusão\n\n![image](asset.svg)')
        self.write('02-studies/study.md', '# Conclusão\n\nAn answer.')
        self.write('asset.svg', '<svg/>')
        self.freeze()
        self.assertEqual(self.check()['status'], 'pass')
        self.write('02-studies/study.md', '# Different')
        self.manifest.unlink()
        self.freeze()
        self.assertTrue(any('Missing fragment' in e['reason'] for e in self.check()['errors']))

    # Value: protects=the original final handoff, including every block and a null stop reason;
    # fails_when=only the last text event is saved or U+2028 is treated as a JSONL boundary;
    # why_new=capture never parses host transcripts; seam=none
    def test_handoff_preserves_terminal_multiblock_text_and_receipt(self):
        source = self.root.parent / 'agent-real.jsonl'
        records = [
            {'type': 'assistant', 'agentId': 'a-1', 'message': {'id': 'earlier', 'content': [{'type': 'tool_use', 'id': 'tool'}], 'stop_reason': 'tool_use'}},
            {'type': 'assistant', 'agentId': 'a-1', 'message': {'id': 'final', 'content': [{'type': 'text', 'text': 'Part\u2028one\n'}], 'stop_reason': None}},
            {'type': 'assistant', 'agentId': 'a-1', 'message': {'id': 'final', 'content': [{'type': 'text', 'text': 'Part two'}], 'stop_reason': None}},
        ]
        source.write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in records) + '\n', encoding='utf-8')
        target = self.root / '03-sources' / 'cycle' / 'front-1.md'
        target.parent.mkdir(parents=True)
        result = delivery.handoff(self.root, source, target, 'F1')
        self.assertEqual(target.read_bytes(), 'Part\u2028one\nPart two'.encode('utf-8'))
        receipt = json.loads((self.root / result['receipt']).read_text(encoding='utf-8'))
        self.assertEqual((receipt['agentId'], receipt['message_id'], receipt['stop_reason']), ('a-1', 'final', None))
        self.assertEqual(receipt['transcript']['sha256'], delivery.digest(source)['sha256'])
        self.assertEqual(receipt['sha256'], delivery.digest(target)['sha256'])
        with self.assertRaises(FileExistsError):
            delivery.handoff(self.root, source, target, 'again')

    # Value: protects=no incomplete or symlinked transcript is labelled original;
    # fails_when=the terminal-entry or source-path guard is weakened;
    # why_new=handoff is new; seam=none
    def test_handoff_refuses_symlink_trailing_and_malformed_records(self):
        source = self.root.parent / 'agent-real.jsonl'
        target = self.root / 'original.md'
        alias = self.root.parent / 'task.output'
        source.write_text(json.dumps({'type': 'assistant', 'message': {'id': 'x', 'content': [{'type': 'text', 'text': 'full'}]}}) + '\n')
        alias.symlink_to(source)
        with self.assertRaisesRegex(ValueError, str(source)):
            delivery.handoff(self.root, alias, target, 'F1')
        for content in (source.read_text() + '{"type":"progress"}\n', '{bad json}\n',
                        json.dumps({'type': 'assistant', 'message': {'id': 'x', 'content': [{'type': 'tool_use'}]}}) + '\n',
                        json.dumps({'type': 'assistant', 'message': {'id': 'x', 'stop_reason': 'tool_use',
                            'content': [{'type': 'text', 'text': 'Still working'}, {'type': 'tool_use', 'id': 'call'}]}}) + '\n',
                        json.dumps({'type': 'assistant', 'message': {'id': 'x', 'stop_reason': 'tool_use',
                            'content': [{'type': 'tool_use', 'id': 'call'}]}}) + '\n' +
                        json.dumps({'type': 'assistant', 'message': {'id': 'x', 'stop_reason': None,
                            'content': [{'type': 'text', 'text': 'Still working'}]}}) + '\n'):
            source.write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError):
                delivery.handoff(self.root, source, target, 'F1')
            self.assertFalse(target.exists())
            self.assertFalse(Path(str(target) + '.receipt.json').exists())

    # Value: protects=check of an existing dossier from render-only list strictness;
    # fails_when=check uses the render list repair/refusal before validating links;
    # why_new=beta.4 accepted two-space lists and render intentionally rejects them; seam=none
    @unittest.skipUnless(HAS_MARKDOWN, 'Optional Markdown dependency not installed')
    def test_check_accepts_existing_two_space_nested_list(self):
        self.write('notes.md', '# Notes\n\n- parent\n  - child\n')
        self.freeze()
        self.assertEqual(self.check()['status'], 'pass')

    def test_handoff_cli_writes_original_and_receipt(self):
        source = self.root.parent / 'agent-real.jsonl'
        source.write_text(json.dumps({'type': 'assistant', 'agentId': 'a', 'message': {
            'id': 'm', 'content': [{'type': 'text', 'text': 'original'}], 'stop_reason': 'end_turn'}}) + '\n')
        run = subprocess.run([sys.executable, str(MODULE), 'handoff', str(self.root), str(source),
                              'original.md', '--origin', 'front'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertEqual((self.root / 'original.md').read_text(), 'original')

    # Value: protects=handoff never leaves an unreceipted original after receipt failure;
    # fails_when=receipt creation fails after writing output and rollback misses that output;
    # why_new=existing handoff tests cover transcript refusal but not the write boundary; seam=none
    def test_handoff_receipt_failure_rolls_back_only_new_output(self):
        source = self.root.parent / 'agent-real.jsonl'
        source.write_text(json.dumps({'type': 'assistant', 'message': {
            'id': 'final', 'content': [{'type': 'text', 'text': 'Original'}],
            'stop_reason': None}}) + '\n')
        target = self.root / 'original.md'
        receipt = Path(str(target) + '.receipt.json')
        real_new_bytes = delivery.new_bytes

        def fail_receipt(path, content):
            if path == receipt:
                raise OSError('receipt disk full')
            return real_new_bytes(path, content)

        with mock.patch.object(delivery, 'new_bytes', side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError, 'receipt disk full'):
                delivery.handoff(self.root, source, target, 'F1')
        self.assertFalse(target.exists())
        self.assertFalse(receipt.exists())
        receipt.write_bytes(b'older receipt')
        with self.assertRaises(FileExistsError):
            delivery.handoff(self.root, source, target, 'F1')
        self.assertEqual(receipt.read_bytes(), b'older receipt')
        self.assertFalse(target.exists())

    def test_capture_cli_keeps_exact_bytes(self):
        source = self.root.parent / 'export.bin'
        source.write_bytes(b'raw\x00\xff')
        run = subprocess.run([sys.executable, str(MODULE), 'capture', str(self.root), str(source),
                              'captured.bin', '--origin', 'explicit export'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertEqual((self.root / 'captured.bin').read_bytes(), source.read_bytes())


@unittest.skipUnless(HAS_MARKDOWN and HAS_PDF, 'Optional Markdown and PyMuPDF dependencies not installed')
class RenderTests(DossierFixture):
    # Value: protects=ordinary inline formatting from a false PDF text-loss refusal;
    # fails_when=HTML text nodes are separated inside one rendered word;
    # why_new=the tall-table guard must distinguish true clipping from inline tags; seam=none
    def test_inline_formatting_keeps_complete_pdf(self):
        import pymupdf
        doc = self.write('inline.md', '# Notes\n\nThis is **un**believable.\n\n'
                         '| A | B |\n|---|---|\n| one | two |\n')
        self.assertEqual(delivery.render(self.root, [doc])['status'], 'created')
        with pymupdf.open(doc.with_suffix('.pdf')) as pdf:
            self.assertIn('unbelievable', ''.join(page.get_text() for page in pdf))

    # Value: protects=long table-cell evidence from a PDF that silently clips it;
    # fails_when=render returns created despite missing the tail of a tall cell;
    # why_new=small table tests cannot trigger a row taller than one page; seam=none
    def test_tall_table_cell_cannot_claim_complete_pdf(self):
        doc = self.write('tall.md', '| Description |\n|---|\n| ' +
                         'Long explanation ' * 800 + 'END_OF_CELL |\n')
        with self.assertRaisesRegex(delivery.Unverified, 'PDF text is missing'):
            delivery.render(self.root, [doc])
        self.assertFalse(doc.with_suffix('.html').exists())
        self.assertFalse(doc.with_suffix('.pdf').exists())

    # Value: protects=links from a rendered peer when a partial replacement preserves no HTML;
    # fails_when=requested input alone causes a link to nonexistent HTML;
    # why_new=existing link test renders both targets successfully; seam=none
    def test_partial_batch_does_not_link_to_unwritten_html(self):
        first = self.write('first.md', '[Study](second.md#new)')
        second = self.write('second.md', '![remote](https://example.invalid/chart.png)')
        second.with_suffix('.pdf').write_bytes(b'old pdf')
        result = delivery.render(self.root, [first, second], replace=True)
        self.assertEqual(result['status'], 'partial')
        self.assertIn('second.md#new', first.with_suffix('.html').read_text(encoding='utf-8'))
        self.assertFalse(second.with_suffix('.html').exists())
        self.assertEqual(second.with_suffix('.pdf').read_bytes(), b'old pdf')

    # Value: protects=all documents in one render call from partial mutation on a later failure;
    # fails_when=validation or promotion of the second document leaves the first updated;
    # why_new=single-document rollback cannot catch cross-document inconsistency; seam=none
    def test_multiple_documents_validate_and_replace_as_one_batch(self):
        first = self.write('first.md', '# First\n\n[Next](second.md)')
        second = self.write('second.md', '- parent\n  - child\n')
        outputs = [first.with_suffix('.html'), first.with_suffix('.pdf'),
                   second.with_suffix('.html'), second.with_suffix('.pdf')]
        for output in outputs:
            output.write_bytes(('old ' + output.name).encode())
        before = {output: output.read_bytes() for output in outputs}
        with self.assertRaisesRegex(ValueError, 'Ambiguous nested-list'):
            delivery.render(self.root, [first, second], replace=True)
        self.assertEqual({output: output.read_bytes() for output in outputs}, before)

        second.write_text('# Second\n', encoding='utf-8')
        real_replace = os.replace
        def fail_last_pdf(source, destination):
            if Path(destination) == outputs[-1] and str(source).endswith('.new'):
                raise OSError('second promotion failed')
            return real_replace(source, destination)
        with mock.patch.object(delivery.os, 'replace', side_effect=fail_last_pdf):
            with self.assertRaisesRegex(OSError, 'second promotion failed'):
                delivery.render(self.root, [first, second], replace=True)
        self.assertEqual({output: output.read_bytes() for output in outputs}, before)

    # Value: protects=check and render interpret one Markdown document with the same IDs and blocks;
    # fails_when=their extension profiles diverge for headings, tables or fenced code;
    # why_new=separate render and check tests do not prove agreement on one source; seam=none
    def test_render_and_check_share_markdown_profile(self):
        source = self.write('study.md', '# Café Notes\n\n[Jump](#café-notes)\n\n'
                            '| A | B |\n|---|---|\n| x | y |\n\n'
                            '```text\n- literal, not a list\n```\n')
        delivery.render(self.root, [source])
        html = source.with_suffix('.html').read_text(encoding='utf-8')
        self.assertIn('id="café-notes"', html)
        self.assertIn('<table>', html)
        self.assertIn('<pre><code class="language-text">- literal, not a list', html)
        self.freeze()
        result = self.check()
        self.assertEqual(result['status'], 'pass', result)
        self.assertGreaterEqual(result['checks']['local_links'], 1)

    def test_linked_image_report_relocates_and_check_agrees(self):
        import pymupdf
        chart = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 30, 30), False)
        chart.clear_with(0x2255aa)
        chart.save(self.root / 'chart.png')
        source = self.write('01-reports/executive.md',
                            '# Executive\n\nEvidence\n- one\n- two\n\n![Chart](../chart.png)\n\n'
                            '[Study](../02-studies/study.md#conclusão)\n\n<!-- pagebreak -->\n\n## Next\n')
        self.write('02-studies/study.md', '# Conclusão\n\nA table:\n\n| A | B |\n|---|---|\n| x | y |\n')
        before = source.read_bytes()
        out = delivery.render(self.root, [source, self.root / '02-studies/study.md'])
        self.assertEqual(out['status'], 'created')
        self.assertEqual(out['documents'][0]['pages'], 2)
        self.assertEqual(out['documents'][0]['headings'][-1]['page'], 2)
        self.assertEqual(source.read_bytes(), before)
        self.assertIn('study.html#conclusão', source.with_suffix('.html').read_text())
        self.assertIn('<li>one</li>', source.with_suffix('.html').read_text())
        with pymupdf.open(source.with_suffix('.pdf')) as pdf:
            self.assertGreaterEqual(sum(len(p.get_image_info()) for p in pdf), 1)
            self.assertTrue(any(delivery.pdf_link_info(pdf, link)[1] == '../02-studies/study.html#conclusão'
                                for page in pdf for link in page.get_links()))
        self.freeze()
        moved = self.root.parent / 'relocated'
        shutil.copytree(self.root, moved)
        result = delivery.check(moved, moved / 'inventory.json')
        self.assertEqual(result['status'], 'pass', result)

    # Value: protects=argument hierarchy and code examples from silent list rewriting;
    # fails_when=0/2/4 nesting is flattened or a code fence is treated as a list;
    # why_new=outside Codex found this semantic counterexample; seam=none
    def test_ambiguous_nested_list_is_refused_but_fenced_marker_is_safe(self):
        bad = self.write('bad.md', '- parent\n  - child\n    - grandchild\n')
        with self.assertRaisesRegex(ValueError, 'line 2.*4/8-space'):
            delivery.render(self.root, [bad])
        self.assertFalse(bad.with_suffix('.html').exists())
        good = self.write('good.md', 'Example\n\n```text\n  - literal\n```\n\n- parent\n    - child\n        - grandchild\n')
        self.assertEqual(delivery.render(self.root, [good])['status'], 'created')
        # A fence-looking line with trailing text is code, not a closing fence.
        import markdown
        for tricky in ('```text\n``` example\n  - literal\n```\n',
                       '```text\n````\n  - literal\n```\n',
                       '```text\n ```\n  - literal\n```\n',
                       '```text\n```\t\n  - literal\n```\n'):
            with self.subTest(tricky=tricky):
                self.assertEqual(delivery.markdown_html(tricky),
                                 markdown.markdown(tricky, extensions=['tables', 'fenced_code', 'toc']))

    def test_pdf_geometry_matches_the_documented_profile(self):
        import pymupdf
        geometry = []
        class Probe:
            def __init__(self, *args, **kwargs):
                pass
            def write_with_links(self, rectfn, positionfn=None):
                geometry.append(rectfn(0, None))
                raise RuntimeError('stop after geometry')
        with mock.patch.object(pymupdf, 'Story', Probe):
            with self.assertRaisesRegex(RuntimeError, 'stop after geometry'):
                delivery.render_pdf(pymupdf, '<p>body</p>', {})
        page, rect, _ = geometry[0]
        self.assertAlmostEqual(rect.y0, 17 * 72 / 25.4, places=2)
        self.assertAlmostEqual(page.height - rect.y1, 19 * 72 / 25.4, places=2)

    # Value: protects=an existing HTML/PDF pair from mixed Markdown generations;
    # fails_when=partial --replace updates only HTML or a failed promotion loses the old PDF;
    # why_new=outside Codex found check cannot detect stale-PDF provenance; seam=module dependency injection
    def test_partial_replace_preserves_pair_and_full_failure_rolls_back(self):
        doc = self.write('report.md', '# New')
        html, pdf = doc.with_suffix('.html'), doc.with_suffix('.pdf')
        html.write_bytes(b'old html')
        pdf.write_bytes(b'old pdf')
        real_module = delivery.module
        def without_pdf(name):
            if name == 'pymupdf':
                raise delivery.Unverified('pymupdf missing')
            return real_module(name)
        with mock.patch.object(delivery, 'module', side_effect=without_pdf):
            result = delivery.render(self.root, [doc], replace=True)
        self.assertEqual(result['status'], 'partial')
        self.assertEqual((html.read_bytes(), pdf.read_bytes()), (b'old html', b'old pdf'))
        real_replace = os.replace
        once = [False]
        def fail_pdf_stage(source, destination):
            if Path(destination) == pdf and str(source).endswith('.new') and not once[0]:
                once[0] = True
                raise OSError('injected promotion failure')
            return real_replace(source, destination)
        with mock.patch.object(delivery.os, 'replace', side_effect=fail_pdf_stage):
            with self.assertRaisesRegex(OSError, 'injected promotion failure'):
                delivery.render(self.root, [doc], replace=True)
        self.assertEqual((html.read_bytes(), pdf.read_bytes()), (b'old html', b'old pdf'))
        self.assertEqual(delivery.render(self.root, [doc], replace=True)['status'], 'created')

    def test_local_image_escape_and_remote_image_are_not_complete(self):
        bad = self.write('bad.md', '![escape](../outside.png)')
        with self.assertRaises(ValueError):
            delivery.render(self.root, [bad])
        missing = self.write('missing.md', '![missing](chart.png)')
        with self.assertRaisesRegex(ValueError, 'Missing local target'):
            delivery.render(self.root, [missing])
        outside = self.root.parent / 'chart.png'
        outside.write_bytes(b'outside')
        (self.root / 'chart.png').symlink_to(outside)
        linked = self.write('linked.md', '![linked](chart.png)')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            delivery.render(self.root, [linked])
        remote = self.write('remote.md', '![remote](https://example.invalid/chart.png)')
        result = delivery.render(self.root, [remote])
        self.assertEqual(result['status'], 'partial')
        self.assertTrue(remote.with_suffix('.html').exists())
        self.assertFalse(remote.with_suffix('.pdf').exists())

        embedded = self.write('embedded.md', '![embedded](data:image/png;base64,aA==)')
        result = delivery.render(self.root, [embedded])
        self.assertEqual(result['status'], 'partial')
        self.assertTrue(embedded.with_suffix('.html').exists())
        self.assertFalse(embedded.with_suffix('.pdf').exists())

    # Value: protects=missing Markdown cannot create derivatives or claim a complete render;
    # fails_when=render writes output before dependency validation or CLI reports success;
    # why_new=existing dependency test hides only PyMuPDF; seam=none
    def test_missing_markdown_dependency_returns_partial_without_output(self):
        import contextlib
        import io
        doc = self.write('first.md', '# First')
        with mock.patch.object(delivery, 'module', side_effect=delivery.Unverified('markdown missing')):
            with mock.patch.object(sys, 'argv', ['delivery.py', 'render', str(self.root), 'first.md']):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = delivery.main()
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())['status'], 'partial')
        self.assertFalse(doc.with_suffix('.html').exists())
        self.assertFalse(doc.with_suffix('.pdf').exists())

    # Value: protects=unrendered Markdown links stay unchanged and derivatives are exclusive;
    # fails_when=render rewrites a link to missing HTML or overwrites a previous derivative;
    # why_new=existing link test only renders its target and replace test explicitly opts in; seam=none
    def test_unrendered_link_and_existing_derivative(self):
        doc = self.write('report.md', '[Study](study.md#answer)')
        self.write('study.md', '# Answer')
        delivery.render(self.root, [doc])
        html = doc.with_suffix('.html')
        self.assertIn('study.md#answer', html.read_text(encoding='utf-8'))
        before = html.read_bytes()
        with self.assertRaises(FileExistsError):
            delivery.render(self.root, [doc])
        self.assertEqual(html.read_bytes(), before)

    def test_missing_pdf_dependency_allows_only_first_html_partial(self):
        doc = self.write('first.md', '# First')
        real_module = delivery.module
        def without_pdf(name):
            if name == 'pymupdf':
                raise delivery.Unverified('pymupdf missing')
            return real_module(name)
        with mock.patch.object(delivery, 'module', side_effect=without_pdf):
            result = delivery.render(self.root, [doc])
        self.assertEqual(result['status'], 'partial')
        self.assertTrue(doc.with_suffix('.html').exists())
        self.assertFalse(doc.with_suffix('.pdf').exists())

    def test_encoded_local_pdf_uri_keeps_fragment_and_checks(self):
        import pymupdf
        doc = self.write('report.md', '[Café notes](caf%C3%A9%20notes.html#notes)')
        self.write('café notes.html', '<h1 id="notes">Notes</h1>')
        delivery.render(self.root, [doc])
        with pymupdf.open(doc.with_suffix('.pdf')) as pdf:
            link = pdf[0].get_links()[0]
            self.assertEqual(delivery.pdf_link_info(pdf, link),
                             (pymupdf.LINK_URI, 'caf%C3%A9%20notes.html#notes', False))
        self.freeze()
        self.assertEqual(self.check()['status'], 'pass')


class ProvenanceTests(DossierFixture):
    """Every file in 04-data names its source captures and its method (script or description)."""

    def setUp(self):
        super().setUp()
        self.write('03-sources/c01/page.html', '<p>R$ 17.448/m²</p>')
        self.write('04-data/prices.csv', 'bairro,preco\nBatel,17448\n')
        self.write('04-data/extract_prices.py', 'print("extract")\n')

    def provenance(self, files):
        self.write('04-data/PROVENANCE.json', json.dumps({'schema': 1, 'files': files}))

    def reasons(self):
        result = delivery.check(self.root)
        return result['status'], {e['reason'] for e in result['errors']}

    GOOD = {'prices.csv': {'sources': ['03-sources/c01/page.html'],
                           'method': {'script': '04-data/extract_prices.py'}}}

    # Value: protects=portable citations on filesystems that preserve decomposed Unicode;
    # fails_when=the citation is matched only by literal spelling or two normalized twins are guessed;
    # why_new=existing NFC tests cover table keys but not source/script citations; seam=none
    def test_nfc_equal_source_and_script_citations_resolve_uniquely(self):
        import unicodedata
        self.write('03-sources/c01/café.html', 'capture')
        self.write('04-data/café.py', 'print(1)')
        (self.root / '04-data/extract_prices.py').unlink()
        self.provenance({'prices.csv': {'sources': ['03-sources/c01/' + unicodedata.normalize('NFD', 'café.html')],
                                        'method': {'script': '04-data/' + unicodedata.normalize('NFD', 'café.py')}}})
        self.assertEqual(self.reasons(), ('partial', set()))
        # U+212B, U+00C5 and A+ring have one NFC form; the third spelling
        # makes a genuinely ambiguous reference on a normalization-preserving FS.
        first = self.write('03-sources/c01/Å.html', 'one')
        second = self.write('03-sources/c01/A\u030a.html', 'two')
        if first.exists() and second.exists() and not os.path.samefile(first, second):
            self.provenance({'prices.csv': {'sources': ['03-sources/c01/\u212b.html'],
                                            'method': {'script': '04-data/café.py'}}})
            self.assertIn('Ambiguous Unicode-normalized provenance path', self.reasons()[1])

    def test_invisible_description_is_not_a_method(self):
        (self.root / '04-data/extract_prices.py').unlink()
        for value in ('\u00a0', '\u200b', '\u200d\u00a0'):
            with self.subTest(value=repr(value)):
                self.provenance({'prices.csv': {'sources': ['03-sources/c01/page.html'],
                                                'method': {'description': value}}})
                self.assertIn('Provenance method needs exactly one of script or a non-empty description',
                              self.reasons()[1])

    # Value: protects=existing dossiers without 04-data keep their check result;
    # fails_when=the provenance rule fires when 04-data is absent; why_new=new rule could leak; seam=none
    def test_dossier_without_data_is_unaffected(self):
        shutil.rmtree(self.root / '04-data')
        self.assertEqual(self.reasons(), ('partial', set()))  # partial only: no inventory supplied

    # Value: protects=a table cannot ship without provenance; fails_when=a missing PROVENANCE.json
    # passes; why_new=no provenance check existed; seam=none
    def test_data_without_provenance_file_fails(self):
        status, reasons = self.reasons()
        self.assertEqual(status, 'fail')
        self.assertIn('Data files without 04-data/PROVENANCE.json', reasons)

    # Value: protects=R3, a script cited as method needs no entry of its own, a stray one does;
    # fails_when=the exemption is dropped or widened to every script; why_new=R3 contract; seam=none
    def test_cited_script_is_exempt_and_uncited_file_is_not(self):
        self.provenance(self.GOOD)
        self.assertEqual(self.reasons(), ('partial', set()))
        self.write('04-data/stray.py', 'print("unexplained")\n')
        self.assertEqual(self.reasons(), ('fail', {'Data file without provenance entry'}))

    # Value: protects=a table cannot escape its own provenance by being cited as another entry's script;
    # fails_when=any existing 04-data file cited as a script is exempted regardless of type;
    # why_new=TODOS P2 item 5, confirmed open after beta.5; seam=none
    def test_table_cited_as_script_is_not_exempt(self):
        self.write('04-data/other.csv', 'x,y\n1,2\n')
        self.provenance({'prices.csv': {'sources': ['03-sources/c01/page.html'],
                                        'method': {'script': '04-data/other.csv'}}})
        result = delivery.check(self.root)
        found = {(e['path'], e['reason']) for e in result['errors']}
        self.assertIn(('04-data/prices.csv', 'Provenance script must be a code file'), found)
        self.assertIn(('04-data/other.csv', 'Data file without provenance entry'), found)

    # Value: protects=common analysis languages remain valid methods, matched case-insensitively;
    # fails_when=the code-file rule rejects a legitimate script; why_new=the rule is new; seam=none
    def test_common_script_types_are_accepted(self):
        (self.root / '04-data/extract_prices.py').unlink()
        for name in ('extract.py', 'model.R', 'query.sql', 'notebook.ipynb', 'clean.sh', 'calc.jl', 'Fit.PY'):
            with self.subTest(name=name):
                for old in (self.root / '04-data').glob('*'):
                    if old.name not in ('prices.csv', 'PROVENANCE.json'):
                        old.unlink()
                self.write(f'04-data/{name}', 'code\n')
                self.provenance({'prices.csv': {'sources': ['03-sources/c01/page.html'],
                                                'method': {'script': f'04-data/{name}'}}})
                self.assertEqual(self.reasons(), ('partial', set()))

    # Value: protects=a citation whose letter case differs from the real file fails closed and says why,
    # on case-insensitive APFS as on Linux; fails_when=the reason is a bare "Missing" or the twin counts;
    # why_new=TODOS P2 item 4 (beta.5 already fails closed, with a misleading reason); seam=none
    def test_letter_case_variant_citation_fails_and_names_the_file(self):
        self.provenance({'prices.csv': {'sources': ['03-sources/c01/PAGE.html'],
                                        'method': {'script': '04-data/Extract_Prices.py'}}})
        result = delivery.check(self.root)
        errors = {(e['reason'], e.get('source') or e.get('script'), e.get('actual')) for e in result['errors']}
        self.assertEqual(result['status'], 'fail')
        self.assertIn(('Provenance path differs only by letter case from a dossier file',
                       '03-sources/c01/PAGE.html', '03-sources/c01/page.html'), errors)
        self.assertIn(('Provenance path differs only by letter case from a dossier file',
                       '04-data/Extract_Prices.py', '04-data/extract_prices.py'), errors)

    # Value: protects=scripts outside 04-data keep any file type, since they cannot hide a table there;
    # fails_when=the code-file rule is applied to every cited script; why_new=review found false failures; seam=none
    def test_script_type_rule_applies_only_inside_data(self):
        (self.root / '04-data/extract_prices.py').unlink()
        self.write('scripts/build.Makefile-task', 'all:\n')
        self.provenance({'prices.csv': {'sources': ['03-sources/c01/page.html'],
                                        'method': {'script': 'scripts/build.Makefile-task'}}})
        self.assertEqual(self.reasons(), ('partial', set()))

    # Value: protects=a mis-cased directory, several case twins and a spelling variant each get the right reason;
    # fails_when=the prefix rule fires first, twins collapse to "missing", or casefold maps ß to ss; seam=none
    def test_letter_case_reasons_cover_directories_twins_and_spelling(self):
        self.provenance({'prices.csv': {'sources': ['03-Sources/c01/page.html'],
                                        'method': {'script': '04-data/extract_prices.py'}}})
        errors = delivery.check(self.root)['errors']
        self.assertIn(('Provenance path differs only by letter case from a dossier file', '03-sources/c01/page.html'),
                      {(e['reason'], e.get('actual')) for e in errors})
        self.write('03-sources/c01/strasse.html', 'capture')
        self.provenance({'prices.csv': {'sources': ['03-sources/c01/straße.html'],
                                        'method': {'script': '04-data/extract_prices.py'}}})
        self.assertIn('Missing provenance source', self.reasons()[1])
        lower = self.write('03-sources/c01/twin.html', 'one')
        upper = self.write('03-sources/c01/TWIN.html', 'two')
        if lower.exists() and upper.exists() and not os.path.samefile(lower, upper):  # case-sensitive FS only
            self.provenance({'prices.csv': {'sources': ['03-sources/c01/Twin.html'],
                                            'method': {'script': '04-data/extract_prices.py'}}})
            errors = delivery.check(self.root)['errors']
            self.assertIn(('Provenance path differs only by letter case from several dossier files',
                           ('03-sources/c01/TWIN.html', '03-sources/c01/twin.html')),
                          {(e['reason'], tuple(e.get('candidates', ()))) for e in errors})

    def test_description_method_is_accepted(self):
        (self.root / '04-data/extract_prices.py').unlink()
        self.provenance({'prices.csv': {'sources': ['03-sources/c01/page.html'],
                                        'method': {'description': 'Transcribed by hand from the PDF table'}}})
        self.assertEqual(self.reasons(), ('partial', set()))

    # Value: protects=every entry rule fails closed; fails_when=any single rule is loosened;
    # why_new=new file format; seam=none
    def test_invalid_entries_fail(self):
        src, script = '03-sources/c01/page.html', '04-data/extract_prices.py'
        cases = {
            'missing data file': ({**self.GOOD, 'gone.csv': self.GOOD['prices.csv']},
                                  'Provenance entry for missing data file'),
            'empty sources': ({'prices.csv': {'sources': [], 'method': {'script': script}}},
                              'Provenance sources must be a non-empty list of dossier paths'),
            'missing source': ({'prices.csv': {'sources': ['03-sources/c01/nope.html'], 'method': {'script': script}}},
                               'Missing provenance source'),
            'self source': ({'prices.csv': {'sources': ['04-data/prices.csv'], 'method': {'script': script}}},
                            'Provenance source is the data file itself'),
            'escaping source': ({'prices.csv': {'sources': ['../outside.html'], 'method': {'script': script}}},
                                'Invalid provenance source path'),
            # A trace must reach a capture: no cycles through other tables, no record as a source.
            'no capture': ({'prices.csv': {'sources': ['04-data/extract_prices.py'], 'method': {'description': 'x'}}},
                           'Provenance sources must include a 03-sources capture'),
            'record as source': ({'prices.csv': {'sources': [src, '04-data/PROVENANCE.json'],
                                                 'method': {'script': script}}},
                                 'Provenance source cannot be the provenance record'),
            'self script': ({'prices.csv': {'sources': [src], 'method': {'script': '04-data/prices.csv'}}},
                            'Provenance script is the data file itself'),
            'record as script': ({'prices.csv': {'sources': [src], 'method': {'script': '04-data/PROVENANCE.json'}}},
                                 'Provenance script cannot be the provenance record'),
            'missing script': ({'prices.csv': {'sources': [src], 'method': {'script': '04-data/nope.py'}}},
                               'Missing provenance script'),
            'two methods': ({'prices.csv': {'sources': [src], 'method': {'script': script, 'description': 'x'}}},
                            'Provenance method needs exactly one of script or a non-empty description'),
            'blank description': ({'prices.csv': {'sources': [src], 'method': {'description': '  '}}},
                                  'Provenance method needs exactly one of script or a non-empty description'),
            'unknown key': ({'prices.csv': {'sources': [src], 'method': {'script': script}, 'note': 'x'}},
                            'Invalid provenance entry'),
            # Generated by /ship test-coverage audit (Sherlock 0.1.0-beta.4).
            # Value: protects=a script outside the dossier or not a string is an invalid entry, not a crash;
            # fails_when=the dossier_file(script) guard is dropped (None.is_file escapes check());
            # why_new=no case named a nonportable script; seam=none
            'escaping script': ({'prices.csv': {'sources': [src], 'method': {'script': '../outside.py'}}},
                                'Invalid provenance script path'),
            'non-string script': ({'prices.csv': {'sources': [src], 'method': {'script': 5}}},
                                  'Invalid provenance script path'),
        }
        for name, (files, reason) in cases.items():
            with self.subTest(case=name):
                self.provenance(files)
                status, reasons = self.reasons()
                self.assertEqual(status, 'fail')
                self.assertIn(reason, reasons)

    # Value: protects=real Finder/iCloud metadata and the top-level README.md need no provenance;
    # fails_when=the exemption is dropped or widened (by name only, any dotfile, nested README);
    # why_new=Finder .DS_Store broke a valid dossier, and a table could hide behind those names; seam=none
    def test_os_metadata_and_readme_are_exempt_only_when_they_really_are(self):
        self.provenance(self.GOOD)
        for name, content in (('.DS_Store', b'\x00\x00\x00\x01Bud1\x00'), ('._prices.csv', b'\x00\x05\x16\x07\x00'),
                              ('.prices.csv.icloud', b'bplist00\xd1'), ('Icon\r', b''), ('README.md', b'# Data')):
            (self.root / '04-data' / name).write_bytes(content)
        self.assertEqual(self.reasons(), ('partial', set()))
        for name in ('prices 2.csv', '.hidden.csv', '._sales.csv', '.q3.csv.icloud', 'sub/README.md'):
            with self.subTest(name=name):
                self.write(f'04-data/{name}', 'bairro,preco\n')  # real data under a tempting name
                self.assertEqual(self.reasons(), ('fail', {'Data file without provenance entry'}))
                (self.root / '04-data' / name).unlink()

    # Value: protects=an entry for an existing README.md is harmless, not reported as a missing file;
    # fails_when=exempt files are compared only against data; why_new=agents following SKILL.md write it; seam=none
    def test_entry_for_an_existing_exempt_file_is_accepted(self):
        self.write('04-data/README.md', '# Columns')
        self.provenance({**self.GOOD, 'README.md': {'sources': ['03-sources/c01/page.html'],
                                                    'method': {'description': 'Column notes'}}})
        self.assertEqual(self.reasons(), ('partial', set()))

    # Value: protects=a trace reaches a real capture, not an index, receipt or OS metadata in 03-sources;
    # fails_when=the prefix alone satisfies the rule; why_new=03-sources/README.md passed as a capture; seam=none
    def test_capture_must_be_real_evidence(self):
        self.write('03-sources/README.md', '| S1 | ... |')
        self.write('03-sources/c01/page.html.receipt.json', '{}')
        (self.root / '03-sources/.DS_Store').write_bytes(b'\x00\x00\x00\x01Bud1')
        for source in ('03-sources/README.md', '03-sources/c01/page.html.receipt.json', '03-sources/.DS_Store'):
            with self.subTest(source=source):
                self.provenance({'prices.csv': {'sources': [source], 'method': {'script': '04-data/extract_prices.py'}}})
                self.assertEqual(self.reasons(), ('fail', {'Provenance sources must include a 03-sources capture'}))

    # Value: protects=an entry with an extra key still exempts its script and names the keys;
    # fails_when=script registration moves after the shape check; why_new=extra keys double-reported the script; seam=none
    def test_malformed_entry_keeps_its_script_exempt_and_names_the_keys(self):
        self.provenance({'prices.csv': {'sources': ['03-sources/c01/page.html'],
                                        'method': {'script': '04-data/extract_prices.py'}, 'rows': 1}})
        result = delivery.check(self.root)
        self.assertEqual([(e['path'], e['reason']) for e in result['errors']],
                         [('04-data/prices.csv', 'Invalid provenance entry')])
        self.assertEqual(result['errors'][0]['found'], ['method', 'rows', 'sources'])

    # Value: protects=names match regardless of Unicode normalization (macOS stores NFD);
    # fails_when=keys are compared byte for byte; why_new=an NFD file got two contradictory errors; seam=none
    def test_unicode_normalization_does_not_split_a_file_from_its_entry(self):
        import unicodedata
        nfd = unicodedata.normalize('NFD', 'preços.csv')
        self.write(f'04-data/{nfd}', 'bairro,preco\n')
        self.provenance({**self.GOOD, 'preços.csv': {'sources': ['03-sources/c01/page.html'],
                                                     'method': {'description': 'Copied by hand'}}})
        self.assertEqual(self.reasons(), ('partial', set()))

    # Value: protects=only the 03-sources index is excluded; a captured README elsewhere is evidence;
    # fails_when=every README.md under 03-sources is refused; why_new=a captured upstream README failed; seam=none
    def test_a_captured_readme_is_evidence_but_the_sources_index_is_not(self):
        self.write('03-sources/c04/README.md', '# upstream project: version 3.2 supports X')
        self.provenance({'prices.csv': {'sources': ['03-sources/c04/README.md'],
                                        'method': {'script': '04-data/extract_prices.py'}}})
        self.assertEqual(self.reasons(), ('partial', set()))

    # Value: protects=names that differ only by Unicode normalization never merge silently;
    # fails_when=data or entries are keyed by NFC without a collision check; why_new=Linux keeps both forms; seam=none
    def test_unicode_twins_and_duplicate_entries_are_reported(self):
        import unicodedata
        nfc_name, nfd_name = 'preços.csv', unicodedata.normalize('NFD', 'preços.csv')
        self.write(f'04-data/{nfc_name}', 'x')
        files = delivery.file_list(self.root) + [self.root / '04-data' / nfd_name]  # a second file on Linux
        twin = {**self.GOOD, nfc_name: {'sources': ['03-sources/c01/page.html'], 'method': {'description': 'x'}}}
        self.provenance(twin)
        issues = delivery.provenance_issues(self.root, files)
        self.assertTrue(any(i['reason'] == 'Data file names differ only by Unicode normalization'
                            and i['path'].startswith('04-data/') for i in issues))
        record = json.dumps({'schema': 1, 'files': twin})[:-2] + ', "' + nfd_name + '": ' + json.dumps(twin[nfc_name]) + '}}'
        self.write('04-data/PROVENANCE.json', record)
        self.assertIn('Duplicate provenance entry after Unicode normalization', self.reasons()[1])

    # Value: protects=an invalid entry name and a non-object entry get accurate reasons;
    # fails_when=they share the key-mismatch message and found field; why_new=found contradicted itself; seam=none
    def test_invalid_entry_names_and_shapes_have_their_own_reasons(self):
        self.provenance({**self.GOOD, 'sub//x.csv': self.GOOD['prices.csv'], 'other.csv': [1]})
        errors = {e['path']: e for e in delivery.check(self.root)['errors']}
        self.assertEqual(errors['04-data/sub//x.csv']['reason'], 'Invalid provenance entry name')
        self.assertEqual(errors['04-data/other.csv']['reason'], 'Invalid provenance entry')
        self.assertNotIn('found', errors['04-data/other.csv'])

    # Value: protects=a case variant of 04-data or PROVENANCE.json cannot skip or confuse the check;
    # fails_when=the exact-spelling checks are removed; why_new=04-Data bypassed provenance; seam=none
    def test_case_variants_of_the_data_directory_and_record_fail(self):
        shutil.rmtree(self.root / '04-data')
        self.write('04-Data/prices.csv', 'x')
        self.assertIn('Data directory must be spelled exactly 04-data', self.reasons()[1])
        shutil.rmtree(self.root / '04-Data')
        self.write('04-data/prices.csv', 'x')
        self.write('04-data/provenance.json', json.dumps({'schema': 1, 'files': {}}))
        status, reasons = self.reasons()
        self.assertEqual(status, 'fail')
        self.assertIn('Provenance record must be spelled exactly 04-data/PROVENANCE.json', reasons)

    # Value: protects=the record is read only as a regular in-root file (no symlink escape, no FIFO hang);
    # fails_when=the record is read before file_list validates it; why_new=a symlinked record was followed; seam=none
    def test_symlinked_or_fifo_record_is_never_read(self):
        outside = self.root.parent / 'outside.json'
        outside.write_text('{"not": "a provenance record"}', encoding='utf-8')
        (self.root / '04-data/PROVENANCE.json').symlink_to(outside)
        result = delivery.check(self.root)
        self.assertEqual(result['status'], 'fail')
        self.assertFalse(any('provenance schema' in e['reason'] for e in result['errors']), result)
        (self.root / '04-data/PROVENANCE.json').unlink()
        os.mkfifo(self.root / '04-data/PROVENANCE.json')
        run = subprocess.run([sys.executable, str(MODULE), 'check', str(self.root)],
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 1, run.stderr)

    # Value: protects=each problem is reported once: an invalid entry still exempts the script it cites;
    # fails_when=scripts are registered only for valid entries; why_new=the script got a second, false issue; seam=none
    def test_invalid_entry_still_exempts_its_script(self):
        self.provenance({'prices.csv': {'sources': [], 'method': {'script': '04-data/extract_prices.py'}}})
        self.assertEqual(self.reasons(), ('fail', {'Provenance sources must be a non-empty list of dossier paths'}))

    def test_malformed_provenance_file_fails(self):
        for content in ('[]', '{"schema":1,"schema":1,"files":{}}', '{"schema":2,"files":{}}',
                        '{"schema":1,"files":{},"extra":1}', 'not json'):
            with self.subTest(content=content):
                self.write('04-data/PROVENANCE.json', content)
                result = delivery.check(self.root)
                self.assertEqual(result['status'], 'fail', result)
                self.assertTrue(any(e['path'] == '04-data/PROVENANCE.json' for e in result['errors']))


class LibraryTests(unittest.TestCase):
    """The Sherlock library: one persisted location per machine, never inside a repository."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.config = self.base / 'config' / 'sherlock.json'

    def run_cli(self, *args):
        result = subprocess.run([sys.executable, str(MODULE), 'library', *args], capture_output=True,
                                text=True, env=dict(os.environ, SHERLOCK_CONFIG=str(self.config)))
        return result.returncode, json.loads(result.stdout)

    # Value: protects=one honest winner when two processes configure an unset library;
    # fails_when=both setters report success for different persisted locations;
    # why_new=the prior fixed staging filename raced across processes; seam=SHERLOCK_CONFIG
    def test_concurrent_setters_have_one_winner(self):
        env = dict(os.environ, SHERLOCK_CONFIG=str(self.config))
        calls = [subprocess.Popen([sys.executable, str(MODULE), 'library', '--set', str(self.base / name)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
                 for name in ('one', 'two')]
        results = []
        for call in calls:
            stdout, stderr = call.communicate(timeout=10)
            results.append((call.returncode, json.loads(stdout), stderr))
        winners = [value for code, value, _ in results if code == 0]
        losers = [value for code, value, _ in results if code == 1]
        self.assertEqual((len(winners), len(losers)), (1, 1), results)
        self.assertEqual(delivery.read_library(self.config), winners[0]['library'])

    def test_config_override_and_orphan_replace_are_rejected(self):
        with mock.patch.dict(os.environ, {'SHERLOCK_CONFIG': 'relative/config.json'}):
            with self.assertRaisesRegex(ValueError, 'absolute'):
                delivery.config_path()
        home = self.base / 'home'
        home.mkdir()
        with mock.patch.dict(os.environ, {'HOME': str(home), 'SHERLOCK_CONFIG': '~/private.json'}):
            self.assertEqual(delivery.config_path(), home / 'private.json')
        with self.assertRaisesRegex(ValueError, 'requires --set'):
            delivery.library(replace=True, config=self.config)
        self.config.parent.mkdir(parents=True)
        self.config.write_text('{"schema":1,"library":42}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unsupported Sherlock config'):
            delivery.library(config=self.config)
        code, output = self.run_cli('--replace')
        self.assertEqual((code, output['status']), (1, 'fail'))
        self.assertIn('requires --set', output['errors'][0])

    # Value: protects=the configured library persists and is read back by a later process;
    # fails_when=set does not write, unset is reported as set, or a repeat set is not idempotent;
    # why_new=no library command existed; seam=SHERLOCK_CONFIG (also the documented user override)
    def test_unset_then_set_persists_across_processes(self):
        code, out = self.run_cli()
        self.assertEqual((code, out['status']), (2, 'unset'))
        self.assertEqual(out['suggested'], '~/Documents/Sherlock')
        self.assertFalse(self.config.exists())
        library = self.base / 'Documents' / 'Sherlock'
        code, out = self.run_cli('--set', str(library))
        self.assertEqual((code, out['status'], out['library']), (0, 'configured', str(library)))
        self.assertTrue(library.is_dir())
        code, out = self.run_cli()
        self.assertEqual((code, out['status'], out['library']), (0, 'set', str(library)))
        self.assertEqual(self.run_cli('--set', str(library))[1]['status'], 'unchanged')

    # Value: protects=a different library is never overwritten silently;
    # fails_when=the --replace guard is dropped; why_new=new command; seam=none
    def test_changing_the_library_requires_replace(self):
        first, second = self.base / 'one', self.base / 'two'
        delivery.library(first, config=self.config)
        before = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'different library is already configured'):
            delivery.library(second, config=self.config)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(second.exists())
        self.assertEqual(delivery.library(second, replace=True, config=self.config)['library'], str(second))
        self.assertEqual(delivery.library(config=self.config)['library'], str(second))

    # Value: protects=dossiers never default into a git repository (the 1.3 GB incident);
    # fails_when=the ancestor walk misses a .git dir/file or a not-yet-existing subpath;
    # why_new=new command; seam=none
    def test_library_inside_a_git_working_tree_is_refused(self):
        repo = self.base / 'repo'
        (repo / '.git').mkdir(parents=True)
        worktree = self.base / 'worktree'
        worktree.mkdir()
        (worktree / '.git').write_text('gitdir: ../repo/.git/worktrees/w\n')
        for target in (repo, repo / 'research' / 'not-yet-created', worktree / 'out'):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, 'inside the git working tree'):
                    delivery.library(target, config=self.config)
                self.assertFalse(self.config.exists())
        self.assertFalse((repo / 'research').exists())
        self.assertFalse((worktree / 'out').exists())

    # Value: protects=the stored path is unambiguous and not redirected;
    # fails_when=relative paths or symlinked ancestors are accepted; why_new=new command; seam=none
    # Value: protects=relative paths are refused and symlinks are resolved before the repository check;
    # fails_when=realpath is dropped (a symlink into a repo passes, or a symlinked /home is unusable);
    # why_new=new resolution contract replaces the blanket symlink refusal; seam=none
    def test_relative_refused_and_symlinks_resolved_before_the_repository_check(self):
        with self.assertRaisesRegex(ValueError, 'absolute'):
            delivery.library(Path('Sherlock'), config=self.config)
        real = self.base / 'real'
        real.mkdir()
        (self.base / 'alias').symlink_to(real, target_is_directory=True)
        out = delivery.library(self.base / 'alias' / 'Sherlock', config=self.config)
        self.assertEqual((out['status'], out['library']), ('configured', str(real / 'Sherlock')))
        self.assertTrue((real / 'Sherlock').is_dir())
        repo = self.base / 'repo'
        (repo / '.git').mkdir(parents=True)
        (self.base / 'into-repo').symlink_to(repo, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'inside the git working tree'):
            delivery.library(self.base / 'into-repo' / 'out', replace=True, config=self.config)
        self.assertEqual(delivery.read_library(self.config), str(real / 'Sherlock'))

    # Value: protects=a repository created above the library after configuration is caught on read;
    # fails_when=show mode stops re-validating the stored path; why_new=only --set validated; seam=none
    def test_reading_a_library_that_is_now_inside_a_repository_fails(self):
        library = self.base / 'work' / 'Sherlock'
        delivery.library(library, config=self.config)
        (self.base / 'work' / '.git').mkdir()
        with self.assertRaisesRegex(ValueError, 'no longer acceptable'):
            delivery.library(config=self.config)

    # Value: protects=--set on the configured path recreates a deleted library directory, as documented;
    # fails_when=the unchanged branch returns before mkdir; why_new=no test deleted the directory; seam=none
    def test_setting_the_same_library_recreates_a_deleted_directory(self):
        library = self.base / 'Sherlock'
        delivery.library(library, config=self.config)
        library.rmdir()
        self.assertEqual(delivery.library(library, config=self.config)['status'], 'unchanged')
        self.assertTrue(library.is_dir())

    # Value: protects=a corrupted or foreign config fails loudly instead of being trusted or replaced;
    # fails_when=the schema check is loosened; why_new=new file format; seam=none
    def test_malformed_config_fails(self):
        self.config.parent.mkdir(parents=True)
        for content in ('not json', '[]', '{"schema":1,"schema":1,"library":"/x"}',
                        '{"schema":2,"library":"/x"}', '{"schema":1,"library":"relative"}',
                        '{"schema":1,"library":"/x","extra":true}', '{"schema":true,"library":"/x"}'):
            with self.subTest(content=content):
                self.config.write_text(content, encoding='utf-8')
                # The error itself says how to recover: the command cannot repair an unreadable file.
                with self.assertRaisesRegex(ValueError, 'SHERLOCK_CONFIG'):
                    delivery.library(config=self.config)
                with self.assertRaisesRegex(ValueError, 'SHERLOCK_CONFIG'):
                    delivery.library(self.base / 'new', replace=True, config=self.config)
                self.assertEqual(self.config.read_text(encoding='utf-8'), content)
                code, out = self.run_cli()
                self.assertEqual((code, out['status']), (1, 'fail'))

    # Generated by /ship test-coverage audit (Sherlock 0.1.0-beta.4).
    # Value: protects=the documented default config location ~/.config/sherlock/config.json and its override;
    # fails_when=the default path changes, so configured machines silently read as unset;
    # why_new=every other test sets SHERLOCK_CONFIG; seam=none
    def test_default_config_lives_in_the_user_home(self):
        home = self.base / 'home'
        env = {k: v for k, v in os.environ.items() if k != 'SHERLOCK_CONFIG'}
        env.update(HOME=str(home), USERPROFILE=str(home))
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(delivery.config_path(), home / '.config' / 'sherlock' / 'config.json')
        with mock.patch.dict(os.environ, {'SHERLOCK_CONFIG': str(self.config)}):
            self.assertEqual(delivery.config_path(), self.config)

    # Generated by /ship test-coverage audit (Sherlock 0.1.0-beta.4).
    # Value: protects=the suggested ~/Documents/Sherlock is accepted verbatim and stored expanded;
    # fails_when=expanduser is dropped, so the suggestion is refused as relative;
    # why_new=tests pass only already-absolute paths; seam=none
    def test_suggested_tilde_path_is_expanded_and_stored_absolute(self):
        home = self.base / 'home'
        home.mkdir()
        with mock.patch.dict(os.environ, {'HOME': str(home), 'USERPROFILE': str(home)}):
            out = delivery.library(Path(delivery.SUGGESTED_LIBRARY), config=self.config)
        expected = home / 'Documents' / 'Sherlock'
        self.assertEqual((out['status'], out['library']), ('configured', str(expected)))
        self.assertTrue(expected.is_dir())
        self.assertEqual(delivery.read_library(self.config), str(expected))

    # Generated by /ship test-coverage audit (Sherlock 0.1.0-beta.4).
    # Value: protects=a staged config left by an interrupted --set never blocks the next one;
    # fails_when=the stale .new cleanup is removed (exclusive create then fails);
    # why_new=no test pre-seeded the staging file; seam=none
    def test_stale_staged_config_does_not_block_a_set(self):
        self.config.parent.mkdir(parents=True)
        stale = self.config.with_name(self.config.name + '.new')
        stale.write_text('{"schema": 1, "libr', encoding='utf-8')
        target = self.base / 'Sherlock'
        self.assertEqual(delivery.library(target, config=self.config)['status'], 'configured')
        self.assertFalse(stale.exists())
        self.assertEqual(json.loads(self.config.read_text(encoding='utf-8')),
                         {'schema': 1, 'library': str(target)})


@unittest.skipUnless(HAS_PDF, 'Optional PyMuPDF dependency not installed')
class PdfTests(DossierFixture):
    def make_pdf(self, path, links=()):
        import pymupdf
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((50, 50), 'Preserved analytical text')
            for i, link in enumerate(links):
                page.insert_link({'from': pymupdf.Rect(40, 80 + i * 25, 300, 100 + i * 25), **link})
            pdf.save(path)
        return path

    def test_absolute_pdf_links_fail_then_relative_derivative_survives_move(self):
        import pymupdf
        target = self.write('02-studies/topic 100%#one.html', '<h1>Study</h1>')
        source = self.make_pdf(self.root / 'original.pdf', [
            {'kind': pymupdf.LINK_LAUNCH, 'file': str(target)},
            {'kind': pymupdf.LINK_URI, 'uri': target.as_uri()},
            {'kind': pymupdf.LINK_URI, 'uri': 'https://example.invalid/public'},
        ])
        before = source.read_bytes()
        self.freeze()
        self.assertEqual(self.check(documents=[source])['status'], 'fail')
        output = self.root / 'portable.pdf'
        delivery.portable_pdf(self.root, source, output)
        self.assertEqual(source.read_bytes(), before)
        with pymupdf.open(source) as old, pymupdf.open(output) as new:
            self.assertEqual(old[0].get_text(), new[0].get_text())
            self.assertEqual(len(old), len(new))
            self.assertTrue(any(link.get('uri') == 'https://example.invalid/public' for link in new[0].get_links()))
        self.manifest.unlink()
        self.freeze()
        moved = self.root.parent / 'moved'
        shutil.copytree(self.root, moved)
        result = delivery.check(moved, moved / 'inventory.json', [moved / 'portable.pdf'])
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(delivery.check(moved, moved / 'inventory.json')['status'], 'fail')  # Original stays honestly broken.

    def test_portable_pdf_cli_creates_relative_derivative(self):
        import pymupdf
        target = self.write('topic.html', '<h1>Topic</h1>')
        self.make_pdf(self.root / 'original.pdf', [{'kind': pymupdf.LINK_LAUNCH, 'file': str(target)}])
        run = subprocess.run([sys.executable, str(MODULE), 'portable-pdf', str(self.root),
                              'original.pdf', 'portable.pdf'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout)
        with pymupdf.open(self.root / 'portable.pdf') as pdf:
            self.assertEqual(pdf[0].get_links()[0]['file'], 'topic.html')

    def test_pdf_refuses_outside_target_and_preserves_existing_output(self):
        import pymupdf
        outside = self.root.parent / 'private.txt'
        outside.write_text('private')
        source = self.make_pdf(self.root / 'original.pdf', [{'kind': pymupdf.LINK_LAUNCH, 'file': str(outside)}])
        output = self.root / 'portable.pdf'
        with self.assertRaises(ValueError):
            delivery.portable_pdf(self.root, source, output)
        self.assertFalse(output.exists())
        output.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            delivery.portable_pdf(self.root, source, output)
        self.assertEqual(output.read_bytes(), b'keep')

    def test_remote_pdf_page_bounds_checked(self):
        import pymupdf
        target = self.make_pdf(self.root / 'study.pdf')
        source = self.make_pdf(self.root / 'report.pdf', [{'kind': pymupdf.LINK_GOTOR, 'file': target.name, 'page': 4, 'to': pymupdf.Point(0, 0)}])
        self.freeze()
        self.assertEqual(self.check()['status'], 'fail')
        with self.assertRaises(ValueError):
            delivery.portable_pdf(self.root, source, self.root / 'fixed.pdf')
        self.assertFalse((self.root / 'fixed.pdf').exists())

    def test_omitted_pdf_actions_cannot_pass_or_be_exported(self):
        import pymupdf
        actions = ['<< /S /GoTo /D [99 /Fit] >>', '<< /S /JavaScript /JS () >>']
        for i, action in enumerate(actions):
            with self.subTest(action=action):
                source = self.make_pdf(self.root / f'input-{i}.pdf', [
                    {'kind': pymupdf.LINK_URI, 'uri': 'https://example.invalid'}])
                with pymupdf.open(source) as pdf:
                    xref = pdf[0].get_links()[0]['xref']
                    pdf.xref_set_key(xref, 'A', action)
                    data = pdf.tobytes()
                source.write_bytes(data)
                self.manifest.unlink(missing_ok=True)
                self.freeze()
                result = self.check(documents=[source])
                self.assertEqual(result['status'], 'partial', result)
                self.assertTrue(any('omitted or unresolved' in e['reason'] for e in result['unverified']))
                output = self.root / f'output-{i}.pdf'
                with self.assertRaises(delivery.Unverified):
                    delivery.portable_pdf(self.root, source, output)
                self.assertFalse(output.exists())
                self.assertEqual(source.read_bytes(), data)

    def test_chained_actions_and_uri_base_are_not_passed(self):
        import pymupdf
        for i, change in enumerate(('next', 'base')):
            with self.subTest(change=change):
                source = self.make_pdf(self.root / f'chain-{i}.pdf', [
                    {'kind': pymupdf.LINK_URI, 'uri': 'https://example.invalid'}])
                with pymupdf.open(source) as pdf:
                    if change == 'next':
                        xref = pdf[0].get_links()[0]['xref']
                        pdf.xref_set_key(xref, 'A/Next', '<< /S /Launch /F (//example.invalid/share) >>')
                    else:
                        pdf.xref_set_key(pdf.pdf_catalog(), 'URI', '<< /Base (https://example.invalid/r/) >>')
                    data = pdf.tobytes()
                source.write_bytes(data)
                self.manifest.unlink(missing_ok=True)
                self.freeze()
                result = self.check(documents=[source])
                self.assertEqual(result['status'], 'partial', result)
                output = self.root / f'chain-out-{i}.pdf'
                with self.assertRaises(delivery.Unverified):
                    delivery.portable_pdf(self.root, source, output)
                self.assertFalse(output.exists())

    def test_pdf_fragment_page_bounds_checked(self):
        self.make_pdf(self.root / 'study.pdf')
        self.write('README.html', '<a href="study.pdf#page=2">Nonexistent page</a>')
        self.freeze()
        self.assertEqual(self.check()['status'], 'fail')


if __name__ == '__main__':
    unittest.main()
