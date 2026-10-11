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

    def test_public_document_links_resolve_inside_package(self):
        content = package.collect_files(MODULE.parents[1])
        for name, data in content.items():
            if not name.endswith('.md') or name.startswith('skill/assets/'):
                continue  # Assets deliberately contain template variables.
            for target in re.findall(r'!?\[[^\]\n]*\]\(([^\s)]+)\)', data.decode()):
                parsed = urlsplit(target)
                if parsed.scheme or not parsed.path:
                    continue
                package_root = Path(self.temp.name).resolve() / 'package'
                resolved = (package_root / name).parent / unquote(parsed.path)
                normalized = resolved.resolve().relative_to(package_root).as_posix()
                self.assertIn(normalized, content, f'{name} -> {target}')

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
