"""Package boundary and failure behavior, without models or network access."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import re
from urllib.parse import urlsplit, unquote
import tempfile
import unittest
from unittest import mock
import zipfile

MODULE = Path(__file__).resolve().parents[1] / 'scripts/package_public.py'
spec = importlib.util.spec_from_file_location('package_public', MODULE)
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)
DELIVERY = MODULE.parents[1] / 'skill/scripts/delivery.py'
delivery_spec = importlib.util.spec_from_file_location('sherlock_delivery', DELIVERY)
delivery = importlib.util.module_from_spec(delivery_spec)
delivery_spec.loader.exec_module(delivery)
SAMPLE = 'examples/sample-dossier/'
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
INLINE_LINK = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>\n]*>|[^\s)]+)(?:\s+(?:"[^"\n]*"|\'[^\'\n]*\'|\([^)\n]*\)))?\s*\)')
REFERENCE_DEFINITION = re.compile(r'^ {0,3}\[[^\]\n]+\]:\s*(<[^>\n]*>|\S+)')


def prose_lines(text):
    """Lines a reader sees as Markdown prose: fenced code blocks are skipped."""
    fence = None
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) \
                    and not match.group(2).strip():
                fence = None
            continue
        if match:
            fence = match.group(1)
            continue
        yield line


def link_targets(text):
    """Inline (with optional title) and reference-definition destinations outside code."""
    targets = []
    for line in prose_lines(text):
        line = re.sub(r'`[^`\n]*`', '', line)
        definition = REFERENCE_DEFINITION.match(line)
        if definition:
            targets.append(definition.group(1).strip('<>'))
            continue
        targets.extend(target.strip('<>') for target in INLINE_LINK.findall(line))
    return targets


def markdown_anchors(text):
    """Heading anchors as GitHub's slugger makes them: fenced code ignored, collisions suffixed."""
    occurrences = {}
    for line in prose_lines(text):
        heading = re.match(r'^ {0,3}#{1,6}[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$', line)
        if not heading:
            continue
        title = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', heading.group(1))
        original = slug = re.sub(r'[^\w -]', '', title.lower()).replace(' ', '-')
        while slug in occurrences:
            occurrences[original] += 1
            slug = f'{original}-{occurrences[original]}'
        occurrences[slug] = 0
    return set(occurrences)


def broken_links(content):
    """Local links and fragments in packaged Markdown that would not resolve after extraction."""
    problems = []
    package_root = Path('/package-root')
    for name, data in content.items():
        if not name.endswith('.md') or name.startswith('skill/assets/'):
            continue  # Assets deliberately contain template variables.
        for target in link_targets(data.decode()):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not (parsed.path or parsed.fragment):
                continue
            normalized = name
            if parsed.path.startswith('/'):
                problems.append(f'{name} -> {target}: absolute path')
                continue
            if parsed.path:
                resolved = os.path.normpath(str((package_root / name).parent / unquote(parsed.path)))
                if not resolved.startswith(str(package_root) + os.sep):
                    problems.append(f'{name} -> {target}: outside package')
                    continue
                normalized = Path(resolved).relative_to(package_root).as_posix()
                if normalized not in content:
                    problems.append(f'{name} -> {target}: missing file')
                    continue
            if parsed.fragment and normalized.endswith('.md') \
                    and unquote(parsed.fragment) not in markdown_anchors(content[normalized].decode()):
                problems.append(f'{name} -> {target}: missing anchor')
    return problems


def checkout_sample_files(sample):
    """Sample files a reader authored; macOS/iCloud metadata is recognized by name and content."""
    return {p.relative_to(sample).as_posix(): p for p in sample.rglob('*')
            if p.is_file() and p.name != 'INVENTORY.json' and not delivery.os_metadata(p)}


def packaged_inventory_issues(archive):
    """The inventory must describe the bytes actually shipped at each sample destination."""
    issues = []
    inventory = json.loads(archive.read(SAMPLE + 'INVENTORY.json'))
    shipped = {n[len(SAMPLE):] for n in archive.namelist()
               if n.startswith(SAMPLE) and n != SAMPLE + 'INVENTORY.json'}
    if shipped != set(inventory['files']):
        issues.append(f'packaged {sorted(shipped ^ set(inventory["files"]))} differ from inventory')
    for name in sorted(shipped & set(inventory['files'])):
        data = archive.read(SAMPLE + name)
        if inventory['files'][name] != {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}:
            issues.append(f'{name}: packaged bytes differ from inventory')
    return issues


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()
        for source in set(package.PUBLIC_FILES.values()):
            path = self.root / source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'Fixture for {source}\n')
        (self.root / 'VERSION').write_text('0.1.0-test\n', encoding='utf-8')
        (self.root / 'LICENSE').write_text(package.MIT_TEMPLATE.replace('<copyright>', 'Copyright (c) 2026 Fixture Owner'), encoding='utf-8')
        (self.root / 'skill/LICENSE').write_bytes((self.root / 'LICENSE').read_bytes())
        self.output = Path(self.temp.name) / 'public.zip'

    def test_only_allowlisted_files_and_matching_hashes(self):
        for name in ['research/private.txt', 'archive/token.txt', 'skill/secret.txt', '.env']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('PRIVATE_MARKER')
        package.build_package(self.root, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(set(archive.namelist()), set(package.PUBLIC_FILES) | {'PACKAGE-MANIFEST.json'})
            self.assertNotIn(b'PRIVATE_MARKER', b''.join(archive.read(n) for n in archive.namelist()))
            for row in json.loads(archive.read('PACKAGE-MANIFEST.json'))['files']:
                self.assertEqual(hashlib.sha256(archive.read(row['path'])).hexdigest(), row['sha256'])

    def test_release_identity_and_license_survive_extraction(self):
        result = package.build_package(self.root, self.output)
        with zipfile.ZipFile(self.output) as archive:
            manifest = json.loads(archive.read('PACKAGE-MANIFEST.json'))
            self.assertEqual(manifest['version'], '0.1.0-test')
            self.assertEqual(manifest['license'], 'MIT')
            self.assertEqual(archive.read('LICENSE'), archive.read('skill/LICENSE'))
            self.assertEqual(result['version'], manifest['version'])

    # Value: protects=the manifest version is a whole semantic release id, not a string that merely contains one;
    # fails_when=fullmatch is loosened to match/search or the patch/pre-release grammar is dropped;
    # why_new='not a release' contains no digits, so it could not tell fullmatch from search; seam=none
    def test_invalid_identity_or_mismatched_license_creates_no_package(self):
        for bad in ('not a release', 'v0.1.0', '0.1', '0.1.0 beta', '0.1.0-'):
            with self.subTest(version=bad):
                (self.root / 'VERSION').write_text(bad)
                with self.assertRaisesRegex(ValueError, 'VERSION'):
                    package.build_package(self.root, self.output)
                self.assertFalse(self.output.exists())
        (self.root / 'VERSION').write_text('0.1.0-test')
        (self.root / 'skill/LICENSE').write_text('different notice')
        with self.assertRaises(ValueError):
            package.build_package(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_non_mit_license_is_not_declared_mit(self):
        for name in ('LICENSE', 'skill/LICENSE'):
            (self.root / name).write_text('Apache License\nVersion 2.0\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'MIT'):
            package.build_package(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_mit_heading_with_other_terms_is_not_declared_mit(self):
        notice = (self.root / 'LICENSE').read_text(encoding='utf-8') + 'Redistribution prohibited.\n'
        for name in ('LICENSE', 'skill/LICENSE'):
            (self.root / name).write_text(notice, encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'MIT'):
            package.build_package(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_extra_terms_between_notice_paragraphs_are_rejected(self):
        notice = (self.root / 'LICENSE').read_text(encoding='utf-8').replace(
            '\n\nPermission is hereby', '\n\nNo commercial use.\n\nPermission is hereby')
        self.assertFalse(package.is_mit_notice(notice))
        self.assertFalse(package.is_mit_notice('MIT License\n'))
        reworded = (self.root / 'LICENSE').read_text(encoding='utf-8').replace('free of charge', 'for a fee')
        self.assertFalse(package.is_mit_notice(reworded))
        notice = (self.root / 'LICENSE').read_text(encoding='utf-8')
        no_grant = notice.replace('Copyright (c) 2026 Fixture Owner', 'All rights reserved. No license is granted.')
        self.assertFalse(package.is_mit_notice(no_grant))

    # Value: protects=a genuine MIT notice still packages from a Windows (CRLF) checkout and with multi-year copyright;
    # fails_when=the rstrip normalization (which also removes CRLF) or the year-list part of the copyright regex is removed,
    # or the holder requirement is dropped; why_new=only rejections and the single-year LF notice were tested; seam=none
    def test_mit_notice_accepts_crlf_checkout_and_year_lists_but_needs_a_holder(self):
        base = (self.root / 'LICENSE').read_text(encoding='utf-8')
        for line in ('Copyright (c) 2025-2026 Fixture Owner', 'Copyright (c) 2024, 2026 Fixture Owner'):
            with self.subTest(copyright=line):
                self.assertTrue(package.is_mit_notice(base.replace('Copyright (c) 2026 Fixture Owner', line)))
        crlf = base.replace('\n', '  \r\n').encode('utf-8')
        for name in ('LICENSE', 'skill/LICENSE'):
            (self.root / name).write_bytes(crlf)
        self.assertEqual(package.build_package(self.root, self.output)['license'], 'MIT')
        self.assertFalse(package.is_mit_notice(base.replace('Copyright (c) 2026 Fixture Owner', 'Copyright (c) 2026')))

    def test_real_license_is_the_mit_notice(self):
        real = Path(__file__).resolve().parents[1] / 'LICENSE'
        self.assertTrue(package.is_mit_notice(real.read_text(encoding='utf-8')))

    def test_cli_unicode_destination_succeeds_on_ascii_console(self):
        target = Path(self.temp.name) / 'packagé.zip'
        result = subprocess.run([sys.executable, str(MODULE), str(target)],
                                capture_output=True,
                                env=dict(os.environ, PYTHONIOENCODING='ascii'))
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(target) as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn('PACKAGE-MANIFEST.json', archive.namelist())

    def test_existing_destination_is_unchanged(self):
        self.output.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):
            package.build_package(self.root, self.output)
        self.assertEqual(self.output.read_bytes(), b'existing')

    def test_missing_input_creates_no_partial_zip(self):
        (self.root / 'PRD.md').unlink()
        with self.assertRaises(FileNotFoundError):
            package.build_package(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_symlink_file_rejected(self):
        path = self.root / 'PRD.md'
        path.unlink()
        path.symlink_to(self.root / 'skill/SKILL.md')
        with self.assertRaises(ValueError):
            package.build_package(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_symlink_parent_rejected(self):
        path = self.root / 'skill/assets'
        path.rename(self.root / 'real-assets')
        path.symlink_to(self.root / 'real-assets', target_is_directory=True)
        with self.assertRaises(ValueError):
            package.build_package(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_destination_symlink_does_not_change_target(self):
        target = Path(self.temp.name) / 'target'
        target.write_bytes(b'keep')
        self.output.symlink_to(target)
        with self.assertRaises(FileExistsError):
            package.build_package(self.root, self.output)
        self.assertEqual(target.read_bytes(), b'keep')

    def test_write_failure_removes_partial_zip(self):
        with mock.patch.object(zipfile.ZipFile, 'writestr', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                package.build_package(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_real_package_can_rebuild_after_extraction(self):
        package.build_package(MODULE.parents[1], self.output)
        extracted = Path(self.temp.name) / 'extracted'
        with zipfile.ZipFile(self.output) as archive:
            archive.extractall(extracted)
        rebuilt = Path(self.temp.name) / 'rebuilt.zip'
        package.build_package(extracted, rebuilt)
        self.assertEqual(self.output.read_bytes(), rebuilt.read_bytes())

    def test_checked_in_package_manifest_matches_current_files(self):
        root = MODULE.parents[1]
        expected = package.build_package(root, self.output)
        actual = json.loads((root / 'PACKAGE-MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(actual, expected)

    def test_sample_inventory_is_exact_and_every_sample_file_is_packaged(self):
        root = MODULE.parents[1]
        sample = root / SAMPLE
        inventory = json.loads((sample / 'INVENTORY.json').read_text(encoding='utf-8'))
        paths = checkout_sample_files(sample)
        self.assertEqual(set(inventory['files']), set(paths))
        for name, path in paths.items():
            data = path.read_bytes()
            self.assertEqual(inventory['files'][name], {
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            self.assertEqual(package.PUBLIC_FILES.get(SAMPLE + name), SAMPLE + name)
        self.assertEqual(package.PUBLIC_FILES.get(SAMPLE + 'INVENTORY.json'), SAMPLE + 'INVENTORY.json')
        package.build_package(root, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(packaged_inventory_issues(archive), [])

    # Value: protects=the inventory describes the shipped bytes, not only the checkout;
    # fails_when=a sample destination is remapped to another source file;
    # why_new=the checkout comparison and allowlist key both still pass under a remap; seam=PUBLIC_FILES
    def test_remapped_sample_destination_is_reported(self):
        root = MODULE.parents[1]
        with mock.patch.dict(package.PUBLIC_FILES, {SAMPLE + 'README.md': 'README.md'}):
            package.build_package(root, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(packaged_inventory_issues(archive), ['README.md: packaged bytes differ from inventory'])

    # Value: protects=Finder/iCloud metadata cannot fail the inventory test on one machine,
    # while a data file using such a name is still counted;
    # fails_when=rglob counts .DS_Store/._ files, or metadata is skipped by name alone; seam=delivery.os_metadata
    def test_os_metadata_is_ignored_only_when_its_content_matches(self):
        sample = Path(self.temp.name) / 'sample'
        sample.mkdir()
        (sample / 'README.md').write_text('# Sample\n')
        (sample / '.DS_Store').write_bytes(b'\x00\x00\x00\x01Bud1' + b'\x00' * 8)
        (sample / '._README.md').write_bytes(b'\x00\x05\x16\x07' + b'\x00' * 8)
        (sample / 'Icon\r').write_bytes(b'')
        self.assertEqual(set(checkout_sample_files(sample)), {'README.md'})
        (sample / '.DS_Store').write_text('metric,value\n')
        self.assertEqual(set(checkout_sample_files(sample)), {'README.md', '.DS_Store'})

    def test_public_document_links_resolve_inside_package(self):
        self.assertEqual(broken_links(package.collect_files(MODULE.parents[1])), [])

    # Value: protects=every packaged fragment link, including same-file ones, lands on a real heading;
    # fails_when=fragments are checked only for sample targets, '#x' links are skipped,
    # fenced '# comments' count as headings, or a repeated heading's -1 suffix is unknown; seam=none
    def test_link_check_reports_fragment_errors_the_reader_would_hit(self):
        content = {
            'README.md': (
                '# Guide\n\n## Steps\n\n## Steps\n\n```bash\n# not-a-heading\n```\n\n'
                '[ok](#steps) [repeat](#steps-1) [same file](#missing) [fenced](#not-a-heading)\n'
                '[doc](docs/A.md#intro) [bad doc](docs/A.md#nowhere) [skill](skill/x.md#y)\n'
                '[outside](../elsewhere.md) [web](https://example.com/#z)\n'
                '[titled](docs/gone.md "Title") [ref][r] [abs](/package-root/README.md)\n'
                '`[code](inline-missing.md)`\n\n```\n[example](fenced-missing.md)\n```\n\n'
                '[r]: docs/ref-gone.md\n').encode(),
            'docs/A.md': b'# Intro\n\n~~~\n## Hidden\n~~~\n[hidden](#hidden)\n',
        }
        self.assertEqual(broken_links(content), [
            'README.md -> #missing: missing anchor',
            'README.md -> #not-a-heading: missing anchor',
            'README.md -> docs/A.md#nowhere: missing anchor',
            'README.md -> skill/x.md#y: missing file',
            'README.md -> ../elsewhere.md: outside package',
            'README.md -> docs/gone.md: missing file',
            'README.md -> /package-root/README.md: absolute path',
            'README.md -> docs/ref-gone.md: missing file',
            'docs/A.md -> #hidden: missing anchor',
        ])
        self.assertEqual(markdown_anchors('# A [link](x.md) title\n## A link title\n'),
                         {'a-link-title', 'a-link-title-1'})
        self.assertEqual(markdown_anchors('# A\n# A\n# A-1\n'), {'a', 'a-1', 'a-1-1'})

    def test_real_implementation_and_local_install_match(self):
        root = MODULE.parents[1]
        content = package.collect_files(root)
        self.assertGreater(len(content['skill/SKILL.md']), 1000)
        installed = root.parent.parent / '.claude/skills/sherlock'
        if installed.is_dir():
            for name in content:
                if name.startswith('skill/'):
                    self.assertEqual(content[name], (installed / name.removeprefix('skill/')).read_bytes())


if __name__ == '__main__':
    unittest.main()
