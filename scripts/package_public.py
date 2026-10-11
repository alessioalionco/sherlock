"""Build an implementation-only ZIP. Never traverse a user's research corpus."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

# The manifest declares MIT, so the notice must be the MIT text with only the copyright line varying.
MIT_TEMPLATE = """MIT License

<copyright>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def is_mit_notice(text):
    """Exactly the MIT notice, line by line; only the copyright line may vary."""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    template = MIT_TEMPLATE.strip().splitlines()
    if len(lines) != len(template):
        return False
    for got, want in zip(lines, template):
        if want == '<copyright>':
            if not re.fullmatch(r'Copyright \(c\) [0-9]{4}(?:[-, ]+[0-9]{4})* \S.*', got):
                return False
        elif got != want:
            return False
    return True


# Destination names are fixed: adding a file to the project cannot publish it implicitly.
PUBLIC_FILES = {
    'README.md': 'README.md',
    'VERSION': 'VERSION',
    'LICENSE': 'LICENSE',
    'skill/LICENSE': 'skill/LICENSE',
    'PRD.md': 'PRD.md',
    'docs/WORKSPACE-ARCHITECTURE.md': 'docs/WORKSPACE-ARCHITECTURE.md',
    'docs/ACCEPTANCE-CRITERIA.md': 'docs/ACCEPTANCE-CRITERIA.md',
    'docs/TESTING.md': 'docs/TESTING.md',
    'docs/EVALUATION.md': 'docs/EVALUATION.md',
    'docs/HOW-IT-WORKS.md': 'docs/HOW-IT-WORKS.md',
    'examples/README.md': 'examples/README.md',
    'examples/sample-dossier/README.md': 'examples/sample-dossier/README.md',
    'examples/sample-dossier/01-reports/executive.md': 'examples/sample-dossier/01-reports/executive.md',
    'examples/sample-dossier/01-reports/final-conclusion.md': 'examples/sample-dossier/01-reports/final-conclusion.md',
    'examples/sample-dossier/02-studies/01-attachment-portability.md': 'examples/sample-dossier/02-studies/01-attachment-portability.md',
    'examples/sample-dossier/02-studies/02-customer-identity.md': 'examples/sample-dossier/02-studies/02-customer-identity.md',
    'examples/sample-dossier/03-sources/fictional-export-guide.md': 'examples/sample-dossier/03-sources/fictional-export-guide.md',
    'examples/sample-dossier/05-research-log/2026-10-08-demo/brief.md': 'examples/sample-dossier/05-research-log/2026-10-08-demo/brief.md',
    'examples/sample-dossier/05-research-log/2026-10-08-demo/reviews/claim-check.md': 'examples/sample-dossier/05-research-log/2026-10-08-demo/reviews/claim-check.md',
    'skill/SKILL.md': 'skill/SKILL.md',
    'skill/references/workspace-and-updates.md': 'skill/references/workspace-and-updates.md',
    'skill/references/studies-and-delivery.md': 'skill/references/studies-and-delivery.md',
    'skill/references/conclusion-audit.md': 'skill/references/conclusion-audit.md',
    'skill/references/delivery-checks.md': 'skill/references/delivery-checks.md',
    'skill/assets/claim-check.md': 'skill/assets/claim-check.md',
    'skill/scripts/delivery.py': 'skill/scripts/delivery.py',
    'tests/test_delivery.py': 'tests/test_delivery.py',
    'skill/assets/agent-handoff.md': 'skill/assets/agent-handoff.md',
    'skill/assets/first-delivery.md': 'skill/assets/first-delivery.md',
    'scripts/package_public.py': 'scripts/package_public.py',
    'tests/test_package_public.py': 'tests/test_package_public.py',
}


def collect_files(root):
    """Read and validate all inputs before creating any destination."""
    root = Path(root).resolve(strict=True)
    content = {}
    for destination, source in PUBLIC_FILES.items():
        path = root / source
        # Reject symlink components even if they resolve within the repository.
        current = path
        while current != root:
            if current.is_symlink():
                raise ValueError(f'Symlink is not an allowed package input: {source}')
            current = current.parent
        path.resolve(strict=True).relative_to(root)
        if not path.is_file():
            raise ValueError(f'Package input is not a file: {source}')
        content[destination] = path.read_bytes()
    return content


def build_package(root, destination):
    content = collect_files(root)
    destination = Path(destination)
    version = content['VERSION'].decode('utf-8').strip()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?', version):
        raise ValueError('VERSION must contain a semantic release identifier')
    if content['LICENSE'] != content['skill/LICENSE']:
        raise ValueError('Root and installable skill license notices must match')
    if not is_mit_notice(content['LICENSE'].decode('utf-8')):
        raise ValueError('LICENSE must be the MIT notice declared in the package manifest')
    manifest = {
        'version': version,
        'license': 'MIT',
        'kind': 'implementation_only',
        'path_base': 'zip_root',
        'excluded': ['research', 'archive', 'evaluations', 'internal_review_artifacts', 'docs/internal',
                     'dist', 'host_configuration', 'private_evidence'],
        'files': [{'path': name, 'bytes': len(data),
                   'sha256': hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(content.items())],
    }
    content['PACKAGE-MANIFEST.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    # Exclusive creation: never truncate an existing package or follow a destination symlink.
    created = False
    try:
        with destination.open('xb') as output:
            created = True
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as package:
                for name, data in sorted(content.items()):
                    info = zipfile.ZipInfo(name, (2026, 9, 27, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    package.writestr(info, data)
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    result = build_package(Path(__file__).resolve().parents[1], args.destination)
    print(f"Created {str(args.destination)!a}: {len(result['files'])} implementation files; no publication.")
