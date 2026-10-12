"""Local dossier checks and lossless capture. No network, model calls or in-place edits."""
from pathlib import Path, PurePosixPath, PureWindowsPath
from html.parser import HTMLParser
from html import escape, unescape
from urllib.parse import urlsplit, unquote, urlunsplit
import argparse
from collections import Counter
import hashlib
import json
import ntpath
import os
import posixpath
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone


class Unverified(Exception):
    pass


def module(name):
    try:
        return __import__(name)
    except ImportError as exc:
        raise Unverified(f'{name} is not installed; affected checks are unverified') from exc


def contained(root, path):
    """Require a lexical and resolved in-root path without symlink components."""
    path = Path(os.path.abspath(path))
    parts = path.relative_to(root).parts
    current = root
    for part in parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f'Symlink is not allowed: {current.relative_to(root)}')
    path.resolve().relative_to(root)
    return path


def relative_name(root, path):
    """A dossier-relative JSON path has the same spelling on every OS."""
    return path.relative_to(root).as_posix()


def relative_file_link(owner, target):
    """Literal cross-file destinations use forward slashes on every host."""
    if isinstance(owner, PureWindowsPath):
        # Windows semantics first (drive letters compare case-insensitively), then separators.
        return ntpath.relpath(str(target), str(owner.parent)).replace('\\', '/')
    return posixpath.relpath(str(target), str(owner.parent))


def nonportable_name(name):
    """True for an inventory key that would not name the same file on every OS."""
    return (not isinstance(name, str) or not name or '\\' in name
            or bool(PureWindowsPath(name).drive) or name != PurePosixPath(name).as_posix()
            or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts)


def regular(path):
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f'Not a regular file: {path}')


def digest(path):
    regular(path)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return {'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def file_list(root):
    result = []
    def walk_error(error):
        raise error
    for parent, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        for name in dirs + names:
            path = contained(root, Path(parent) / name)
            if name in names:
                regular(path)
                result.append(path)
    return sorted(result)


def new_bytes(path, content):
    """Exclusive creation and cleanup only for the file created by this call."""
    created = False
    try:
        with path.open('xb') as output:
            created = True
            output.write(content)
    except BaseException:
        if created:
            path.unlink(missing_ok=True)
        raise


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def inventory(root, output):
    output = contained(root, output)
    files = file_list(root)
    if output.exists():
        raise FileExistsError(output)
    names = {relative_name(root, p): p for p in files if p != output}
    for name in names:
        if nonportable_name(name):
            raise ValueError(f'Invalid inventory path: {name}')
    result = {'schema': 1, 'path_base': 'dossier_root',
              'files': {name: digest(p) for name, p in names.items()}}
    new_bytes(output, json_bytes(result))
    return {'status': 'created', 'files': len(result['files']), 'path': relative_name(root, output)}


def capture(root, source, destination, origin):
    """Copy one explicitly supplied export, never discover a host's session store."""
    source = Path(os.path.abspath(source))
    if any(p.is_symlink() for p in (source, *source.parents)):
        raise ValueError('Capture source cannot contain symlinks')
    regular(source)
    destination = contained(root, destination)
    receipt = contained(root, Path(str(destination) + '.receipt.json'))
    if destination.exists() or receipt.exists():
        raise FileExistsError('Capture destination or receipt already exists')
    before = digest(source)
    created = False
    try:
        with source.open('rb') as src, destination.open('xb') as dst:
            created = True
            shutil.copyfileobj(src, dst)
        copied = digest(destination)
        if copied != before or digest(source) != before:
            raise ValueError('Source changed during capture; no stable copy established')
        new_bytes(receipt, json_bytes({'schema': 1, 'origin': origin,
            'captured_at': datetime.now(timezone.utc).isoformat(),
            'path': relative_name(root, destination), **copied,
            'scope': 'Bytes in the supplied export only; completeness of host export not certified'}))
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise
    return {'status': 'captured', 'path': relative_name(root, destination),
            'receipt': relative_name(root, receipt), **copied}


def handoff(root, transcript, destination, origin):
    """Preserve the complete final assistant text from one explicit Claude JSONL export."""
    transcript = Path(os.path.abspath(transcript))
    if any(part.is_symlink() for part in (transcript, *transcript.parents)):
        raise ValueError(f'Handoff transcript cannot contain symlinks; retry with real path: {transcript.resolve()}')
    regular(transcript)
    destination = contained(root, destination)
    receipt = contained(root, Path(str(destination) + '.receipt.json'))
    if destination.exists() or receipt.exists():
        raise FileExistsError('Handoff destination or receipt already exists')
    identity = None
    blocks = []
    tool_in_message = False
    final = None
    count = 0
    before = digest(transcript)
    with transcript.open('rb') as stream:
        for raw in stream:  # literal LF records; str.splitlines() splits valid U+2028 JSON strings
            count += 1
            try:
                entry = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
            except (UnicodeError, ValueError) as exc:
                raise ValueError(f'Invalid transcript JSONL at line {count}: {exc}') from exc
            if not isinstance(entry, dict):
                raise ValueError(f'Invalid transcript entry at line {count}')
            final = entry
            if entry.get('type') != 'assistant':
                continue
            message = entry.get('message')
            if not isinstance(message, dict) or not isinstance(message.get('id'), str):
                raise ValueError(f'Unknown assistant message shape at line {count}')
            content = message.get('content')
            if not isinstance(content, list):
                raise ValueError(f'Unknown assistant content shape at line {count}')
            if identity != message['id']:
                identity, blocks = message['id'], []
                tool_in_message = False
            if message.get('stop_reason') == 'tool_use':
                tool_in_message = True
            for block in content:
                if not isinstance(block, dict) or not isinstance(block.get('type'), str):
                    raise ValueError(f'Unknown assistant block shape at line {count}')
                if block['type'] == 'text':
                    if not isinstance(block.get('text'), str):
                        raise ValueError(f'Unknown text block shape at line {count}')
                    blocks.append(block['text'])
                elif block['type'] == 'tool_use':
                    tool_in_message = True
    if count == 0 or not isinstance(final, dict) or final.get('type') != 'assistant':
        raise ValueError('Final assistant message must be the last transcript entry')
    message = final.get('message')
    if not isinstance(message, dict) or message.get('id') != identity or not ''.join(blocks).strip():
        raise ValueError('Final assistant message has no complete nonempty text')
    if tool_in_message:
        raise ValueError('Final assistant message still requests a tool; handoff is unfinished')
    if digest(transcript) != before:
        raise ValueError('Transcript changed during extraction')
    content = ''.join(blocks).encode('utf-8')
    created = False
    try:
        new_bytes(destination, content)
        created = True
        result = digest(destination)
        record = {'schema': 1, 'origin': origin,
                  'captured_at': datetime.now(timezone.utc).isoformat(),
                  'path': relative_name(root, destination), **result,
                  'transcript': {'supplied_path': str(transcript), 'realpath': str(transcript.resolve()),
                                 **before},
                  'agentId': final.get('agentId'), 'message_id': identity,
                  'stop_reason': message.get('stop_reason'),
                  'extraction': 'all text blocks of the final assistant message.id, in JSONL order'}
        new_bytes(receipt, json_bytes(record))
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise
    return {'status': 'captured', 'path': relative_name(root, destination),
            'receipt': relative_name(root, receipt), **result}


SUGGESTED_LIBRARY = '~/Documents/Sherlock'


def config_path():
    """Per-machine library setting; SHERLOCK_CONFIG overrides the location."""
    override = os.environ.get('SHERLOCK_CONFIG')
    if override:
        path = Path(os.path.expanduser(override))
        if not path.is_absolute():
            raise ValueError('SHERLOCK_CONFIG must be an absolute path (or start with ~)')
        return path
    return Path.home() / '.config' / 'sherlock' / 'config.json'


@contextmanager
def config_lock(config):
    """Serialize config read/validate/write across processes on POSIX hosts."""
    import fcntl
    config.parent.mkdir(parents=True, exist_ok=True)
    lock = config.with_name(config.name + '.lock')
    flags = os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(lock, flags, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def read_library(config):
    if not config.exists():
        return None
    recovery = ('move it aside, or point SHERLOCK_CONFIG at another file, '
                'then run library --set PATH')
    try:
        obj = json.loads(config.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    except ValueError as exc:
        raise ValueError(f'Unreadable Sherlock config {config} ({exc}); {recovery}') from exc
    if (not isinstance(obj, dict) or set(obj) != {'schema', 'library'} or type(obj['schema']) is not int
            or obj['schema'] != 1 or not isinstance(obj['library'], str)
            or not Path(obj['library']).is_absolute()):
        raise ValueError(f'Unsupported Sherlock config {config}; {recovery}')
    return obj['library']


def git_working_tree(path):
    """The nearest ancestor holding .git (directory or worktree file), existing or not yet."""
    for parent in (path, *path.parents):
        if (parent / '.git').exists():
            return parent
    return None


def library_problem(path):
    """Why a resolved library location is unacceptable, or None."""
    repository = git_working_tree(path)
    if repository is not None:
        return (f'Library would be inside the git working tree at {repository}; '
                'choose a location outside any repository')
    return None


def library(path=None, replace=False, config=None):
    """Show or persist the user's Sherlock library. Never inside a git working tree."""
    config = config or config_path()
    config = Path(os.path.expanduser(str(config)))
    if not config.is_absolute():
        raise ValueError('Sherlock config path must be absolute')
    if path is None and replace:
        raise ValueError('--replace requires --set PATH')
    current = read_library(config) if path is None else None
    if path is None:
        if current is None:
            return {'status': 'unset', 'config': str(config), 'suggested': SUGGESTED_LIBRARY,
                    'next': 'Propose the suggestion visibly, then persist the choice with library --set PATH'}
        # A repository can appear above the library after it was configured.
        problem = library_problem(Path(os.path.realpath(current)))
        if problem:
            raise ValueError(f'Configured library is no longer acceptable: {problem}; '
                             'set another with library --set PATH --replace')
        return {'status': 'set', 'library': current, 'config': str(config)}
    path = Path(os.path.expanduser(str(path)))
    if not path.is_absolute():
        raise ValueError(f'Library path must be absolute: {path}')
    # Resolve symlinks so the repository check sees the real location; a symlinked
    # /home or /var stays usable, and a symlink into a repository is still refused.
    path = Path(os.path.realpath(path))
    problem = library_problem(path)
    if problem:
        raise ValueError(problem)
    with config_lock(config):
        current = read_library(config)
        if current == str(path):
            path.mkdir(parents=True, exist_ok=True)
            return {'status': 'unchanged', 'library': current, 'config': str(config)}
        if current is not None and not replace:
            raise ValueError(f'A different library is already configured: {current}; pass --replace to change it')
        path.mkdir(parents=True, exist_ok=True)
        # Retire a pre-lock beta.4 staging artifact; new writes use unique names.
        config.with_name(config.name + '.new').unlink(missing_ok=True)
        fd, name = tempfile.mkstemp(prefix=config.name + '.', suffix='.new', dir=config.parent)
        staged = Path(name)
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(json_bytes({'schema': 1, 'library': str(path)}))
                output.flush()
                os.fsync(output.fileno())
            os.replace(staged, config)
        finally:
            staged.unlink(missing_ok=True)
        if read_library(config) != str(path):
            raise ValueError('Sherlock config changed during write; check the configured library')
        return {'status': 'configured', 'library': str(path), 'config': str(config)}


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []
        self.anchors = set()
        self.has_base = False

    def handle_starttag(self, tag, attrs):
        if tag == 'base':
            self.has_base = True
        # Browsers use the first duplicate attribute: every href/src is checked (fail closed),
        # but only the first id/name can be an anchor.
        seen = set()
        for key, value in attrs:
            if key in ('href', 'src') and value is not None:
                self.targets.append(value)
            elif key in ('id', 'name') and key not in seen:
                seen.add(key)
                if value and (key == 'id' or tag == 'a'):
                    self.anchors.add(value)


def document(path):
    text = path.read_text(encoding='utf-8')
    if path.suffix.lower() == '.md':
        text = markdown_html(text)
    parser = Links()
    parser.feed(text)
    if parser.has_base:
        raise Unverified('HTML <base> changes target resolution; remove it or verify with the renderer')
    return parser


LIST_MARKER = re.compile(r'^( *)(?:[-+*]|\d+[.)])\s')


def markdown_input(text):
    """Repair paragraph/list separation; refuse indentation with ambiguous hierarchy."""
    # Reuse the active extension's fence recognition so a longer/indented/unfinished
    # delimiter never makes us mutate or reject content the parser sees as code.
    from markdown.extensions.fenced_code import FencedBlockPreprocessor
    protected = set()
    for match in FencedBlockPreprocessor.FENCED_BLOCK_RE.finditer(text):
        first = text.count('\n', 0, match.start()) + 1
        protected.update(range(first, first + match.group(0).count('\n') + 1))
    result, list_active = [], False
    for number, line in enumerate(text.split('\n'), 1):
        if number in protected:
            result.append(line)
            continue
        item = LIST_MARKER.match(line)
        if item and len(item.group(1)) in (2, 3) and list_active:
            raise ValueError(f'Ambiguous nested-list indentation at line {number}; use explicit 4/8-space levels')
        if item and len(item.group(1)) == 0 and result:
            previous = result[-1]
            if (previous.strip() and not LIST_MARKER.match(previous)
                    and not re.match(r'^\s*(?:#{1,6}\s|>|<|\|)', previous)):
                result.append('')
        if item:
            list_active = True
        elif line.strip() and not line.startswith(' '):
            list_active = False
        result.append(line)
    return '\n'.join(result)


def markdown_html(text, repair_lists=False):
    """One Markdown profile for check and render, including Unicode heading IDs."""
    md = module('markdown')
    def slugify(value, separator):
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'\s', separator, value).strip(separator)
    return md.markdown(markdown_input(text) if repair_lists else text,
                       extensions=['tables', 'fenced_code', 'toc'],
                       extension_configs={'toc': {'slugify': slugify}})


RENDER_CSS = ('body { font-family: sans-serif; font-size: 10pt; line-height: 1.36; } '
              'table { border-collapse: collapse; font-size: 9pt; } '
              'td, th { border: 1px solid #aaa; padding: 4pt; } '
              'img { max-width: 100%; height: auto; } '
              'pre { white-space: pre-wrap; }')


class Images(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            values = [value for key, value in attrs if key == 'src']
            if len(values) != 1 or not values[0]:
                raise ValueError('Each rendered image needs exactly one nonempty src')
            self.sources.append(values[0])


class VisibleText(HTMLParser):
    """Collect text the PDF should expose; skip non-rendered source elements."""
    BLOCK_TAGS = {'p', 'div', 'br', 'hr', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th',
                  'pre', 'blockquote', 'section', 'article', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skipped = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'svg'):
            self.skipped += 1
        elif not self.skipped and tag in self.BLOCK_TAGS:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'svg') and self.skipped:
            self.skipped -= 1
        elif not self.skipped and tag in self.BLOCK_TAGS:
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.skipped:
            self.parts.append(data)


def text_tokens(value):
    return Counter(re.findall(r'\w+', unicodedata.normalize('NFKD', value).casefold()))


HTML_ATTR = re.compile(r'(?P<start><(?P<tag>a|img)\b[^>]*?\s(?P<attr>href|src)\s*=\s*)(?P<quote>["\'])(?P<value>.*?)(?P=quote)', re.I | re.S)


def render_links(root, source, html_body, requested, pdf=False, image_names=None):
    """Rewrite only proven local targets; keep original HTML references otherwise."""
    image_names = image_names or {}
    def replace(match):
        tag, attr = match.group('tag').lower(), match.group('attr').lower()
        value = unescape(match.group('value'))
        if tag == 'img' and attr == 'src' and pdf:
            if value not in image_names:
                raise Unverified(f'Image resource could not be staged: {value}')
            value = image_names[value]
        elif tag == 'a' and attr == 'href':
            parsed = urlsplit(value)
            if not parsed.scheme and not parsed.netloc and parsed.path.lower().endswith('.md'):
                target = local_target(root, source, value)
                if target is not None:
                    candidate = target[0].with_suffix('.html')
                    if candidate.exists() or candidate in requested:
                        value = urlunsplit(('', '', parsed.path[:-3] + '.html', parsed.query, parsed.fragment))
            # Story writes local hrefs as URI actions. Keep URL escapes and fragments;
            # pdf_link_info/check decode and validate the raw action, not get_links()['file'].
        return match.group('start') + match.group('quote') + escape(value, quote=True) + match.group('quote')
    return HTML_ATTR.sub(replace, html_body)


def render_pdf(pdfmod, html_body, images):
    archive = pdfmod.Archive()
    for name, content in images.items():
        archive.add(content, path=name)
    story = pdfmod.Story(html_body, user_css=RENDER_CSS, em=10, archive=archive)
    positions = []
    def rectangle(number, filled):
        page = pdfmod.paper_rect('a4')
        return page, pdfmod.Rect(48.19, 48.19, page.width - 48.19, page.height - 53.86), None
    def position(item):
        if item.heading in (1, 2) and item.open_close == 1:
            positions.append({'level': item.heading, 'id': item.id, 'text': item.text,
                              'page': item.page_num})
    with story.write_with_links(rectangle, positionfn=position) as pdf:
        if sum(len(page.get_image_info()) for page in pdf) < len(images):
            raise ValueError('PDF omitted one or more validated local images')
        visible = VisibleText()
        visible.feed(html_body)
        missing = text_tokens(''.join(visible.parts)) - text_tokens(
            ' '.join(page.get_text() for page in pdf))
        if missing:
            raise Unverified('PDF text is missing or not extractable; inspect long table cells before delivery')
        return pdf.tobytes(garbage=4, deflate=True), len(pdf), positions


def replace_pair(outputs):
    """Stage every byte, promote as a pair, restore originals on ordinary failure."""
    staged, backups, promoted = {}, {}, []
    restored = False
    try:
        for path, content in outputs.items():
            fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.new', dir=path.parent)
            stage = Path(name)
            staged[path] = stage
            with os.fdopen(fd, 'wb') as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
        for path in outputs:
            if path.exists():
                fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.bak', dir=path.parent)
                os.close(fd)
                backup = Path(name)
                try:
                    os.replace(path, backup)
                    backups[path] = backup
                except BaseException:
                    backup.unlink(missing_ok=True)
                    raise
            os.replace(staged[path], path)
            promoted.append(path)
    except BaseException:
        for path in promoted:
            path.unlink(missing_ok=True)
        for path, backup in backups.items():
            os.replace(backup, path)
        restored = True
        raise
    finally:
        for stage in staged.values():
            stage.unlink(missing_ok=True)
        # If restoration itself fails, keep the backup for manual recovery.
        if restored or len(promoted) == len(outputs):
            for backup in backups.values():
                backup.unlink(missing_ok=True)


def render(root, documents, replace=False):
    md = module('markdown')
    try:
        pdfmod = module('pymupdf')
    except Unverified:
        pdfmod = None
    docs = [contained(root, path) for path in documents]
    if (not docs or len(set(docs)) != len(docs)
            or len({path.with_suffix('.html') for path in docs}) != len(docs)):
        raise ValueError('Render requires distinct Markdown documents and output stems')
    for path in docs:
        if path.suffix.lower() != '.md':
            raise ValueError(f'Render input must be Markdown: {path}')
        regular(path)
        for output in (path.with_suffix('.html'), path.with_suffix('.pdf')):
            contained(root, output)
            if output.exists() and not replace:
                raise FileExistsError(output)
    prepared = []
    for path in docs:
        html_path, pdf_path = path.with_suffix('.html'), path.with_suffix('.pdf')
        source = path.read_text(encoding='utf-8')
        body = markdown_html(source, repair_lists=True).replace(
            '<!-- pagebreak -->', '<div style="page-break-before: always"></div>')
        images = Images()
        images.feed(body)
        image_names, resources, unsupported = {}, {}, []
        for number, value in enumerate(images.sources):
            target = local_target(root, path, value)
            if target is None:
                unsupported.append(value)
                continue
            image_path, fragment = target
            if fragment or image_path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.gif', '.svg'):
                raise ValueError(f'Unsupported local image resource: {value}')
            regular(image_path)
            name = f'sherlock-image-{number}{image_path.suffix.lower()}'
            image_names[value], resources[name] = name, image_path.read_bytes()
        partial = pdfmod is None or bool(unsupported)
        preserved = partial and replace and (html_path.exists() or pdf_path.exists())
        prepared.append((path, body, image_names, resources, unsupported, partial, preserved))
    requested = {path.with_suffix('.html') for path, _, _, _, _, _, preserved in prepared
                 if not preserved}
    results, all_outputs = [], {}
    for path, body, image_names, resources, unsupported, partial, preserved in prepared:
        html_path, pdf_path = path.with_suffix('.html'), path.with_suffix('.pdf')
        if preserved:
            results.append({'document': relative_name(root, path), 'status': 'partial',
                            'reason': 'PDF dependency or image support unavailable; existing derivatives preserved'})
            continue
        html_body = render_links(root, path, body, requested)
        html_bytes = ('<!doctype html><html><head><meta charset="utf-8"><style>' + RENDER_CSS +
                      '</style></head><body>' + html_body + '</body></html>\n').encode('utf-8')
        outputs = {html_path: html_bytes}
        item = {'document': relative_name(root, path), 'html': relative_name(root, html_path),
                'renderer': 'Python-Markdown', 'markdown_version': getattr(md, '__version__', 'unknown')}
        if not partial:
            pdf_body = render_links(root, path, body, requested, pdf=True, image_names=image_names)
            data, pages, headings = render_pdf(pdfmod, pdf_body, resources)
            outputs[pdf_path] = data
            item.update({'pdf': relative_name(root, pdf_path), 'pages': pages,
                         'headings': headings, 'pdf_renderer': 'PyMuPDF',
                         'pymupdf_version': getattr(pdfmod, 'VersionBind', 'unknown')})
        all_outputs.update(outputs)
        item['status'] = 'partial' if partial else 'created'
        if partial:
            item['unverified'] = ('PDF pagination unavailable (PyMuPDF not installed)' if pdfmod is None
                                  else f'Unsupported remote or embedded images: {unsupported}')
        results.append(item)
    # Validate every requested document before changing any derivative. One failed
    # document must not leave its peers updated or links aimed at absent HTML.
    if replace:
        if all_outputs:
            replace_pair(all_outputs)
    else:
        created = []
        try:
            for output, content in all_outputs.items():
                new_bytes(output, content)
                created.append(output)
        except BaseException:
            for output in created:
                output.unlink(missing_ok=True)
            raise
    return {'status': 'partial' if any(item['status'] == 'partial' for item in results) else 'created',
            'profile': {'markdown_extensions': ['tables', 'fenced_code', 'toc'],
                        'page': 'A4', 'margins_mm': [17, 17, 19]}, 'documents': results}


C0_CONTROL_OR_SPACE = ''.join(map(chr, range(0x21)))


def browser_url(target):
    """WHATWG URL preprocessing, independent of the Python version's urlsplit."""
    return re.sub('[\t\n\r]', '', target.strip(C0_CONTROL_OR_SPACE))


def local_target(root, owner, target, allow_absolute=False, literal_file=False):
    """Return (path, fragment) for local links. External URLs are not fetched."""
    if not isinstance(target, str) or not target or '\x00' in target:
        raise ValueError('Invalid empty link target')
    # A browser strips edge C0/space and drops tab/newline before parsing; older urlsplit
    # (3.9.6) does not, so " //host/x" could pass as a local path. PDF filenames are literal.
    if not literal_file:
        target = browser_url(target)
        if not target:
            raise ValueError('Invalid empty link target')
    # Opened from disk, //host/x resolves to file://host/x (a UNC fetch on Windows) and
    # ///abs or //localhost/abs to an absolute local file: never a portable external link.
    if not literal_file and target.startswith('//') and '\\' not in target:
        raise ValueError(f'Network-path reference is not portable; use an explicit https:// URL: {target}')
    if PureWindowsPath(target).drive or '\\' in target:
        raise ValueError(f'Nonportable Windows path: {target}')
    if literal_file:
        if Path(target).is_absolute() and not allow_absolute:
            raise ValueError(f'Absolute local destination: {target}')
        path = contained(root, owner.parent / target)
        if not path.exists():
            raise ValueError(f'Missing local target: {target}')
        return path, ''
    url = urlsplit(target)
    if url.scheme in ('https', 'http', 'mailto', 'tel', 'data'):
        return None
    if url.scheme not in ('', 'file'):
        raise Unverified(f'Unsupported link scheme: {url.scheme}')
    if url.netloc:
        raise ValueError(f'Nonlocal file URL: {target}')
    decoded = unquote(url.path)
    if '\\' in decoded or PureWindowsPath(decoded).drive:
        raise ValueError(f'Nonportable encoded path: {target}')
    if url.scheme == 'file' or Path(decoded).is_absolute():
        if not allow_absolute:
            raise ValueError(f'Absolute local destination: {target}')
    path = owner if not decoded else owner.parent / decoded
    path = contained(root, path)
    if not path.exists():
        raise ValueError(f'Missing local target: {target}')
    if url.query:
        raise Unverified(f'Local query resolution not verified: {target}')
    return path, unquote(url.fragment)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f'Duplicate JSON key: {key}')
        obj[key] = value
    return obj


PROVENANCE = '04-data/PROVENANCE.json'
# A script inside 04-data that is cited as a method needs no entry of its own. Only code-file names
# qualify there, so a table cannot escape its own provenance by being cited as another entry's script.
# The test is by name: a table deliberately renamed with a code suffix is not detected.
SCRIPT_SUFFIXES = frozenset({
    '.py', '.ipynb', '.r', '.rmd', '.qmd', '.sql', '.sh', '.bash', '.zsh', '.ps1', '.js', '.mjs', '.cjs',
    '.jsx', '.ts', '.tsx', '.jl', '.m', '.do', '.ado', '.sas', '.sps', '.pl', '.rb', '.awk', '.go', '.rs',
    '.c', '.cpp', '.java', '.kt', '.scala', '.php', '.lua'})


def code_file(name):
    return Path(name).suffix.lower() in SCRIPT_SUFFIXES


def in_data_dir(name):
    return nfc(name).startswith('04-data/')


# Files macOS and iCloud write on their own, recognized by name AND content, so a data
# table cannot hide behind one of these names.
OS_METADATA = (
    (lambda base: base == '.DS_Store', lambda head, size: head.startswith(b'\x00\x00\x00\x01Bud1')),
    (lambda base: base.startswith('._'), lambda head, size: head.startswith(b'\x00\x05\x16\x07')),
    (lambda base: base.startswith('.') and base.endswith('.icloud'), lambda head, size: head.startswith(b'bplist00')),
    (lambda base: base == 'Icon\r', lambda head, size: size == 0),
)


def os_metadata(path):
    for name_matches, content_matches in OS_METADATA:
        if name_matches(path.name):
            with path.open('rb') as stream:
                return content_matches(stream.read(8), path.stat().st_size)
    return False


def nfc(text):
    """Compare dossier names the way a reader sees them (macOS often stores NFD)."""
    return unicodedata.normalize('NFC', text)


def visible_text(text):
    """Whitespace and Unicode formatting controls are not a method description."""
    return any(unicodedata.category(char)[0] not in ('C', 'Z') for char in text)


def provenance_issues(root, files):
    """Every 04-data file names a source capture and a method; a cited script is the method."""
    issues, scripts = [], set()

    def problem(where, reason, **detail):
        issues.append({'path': where, 'reason': reason, **detail})

    record = root / PROVENANCE
    for top in sorted({p.relative_to(root).parts[0] for p in files}):
        if top != '04-data' and top.casefold() == '04-data':
            problem(top, 'Data directory must be spelled exactly 04-data')
    for p in files:
        if p.parent == root / '04-data' and p != record and p.name.casefold() == 'provenance.json':
            problem(relative_name(root, p), 'Provenance record must be spelled exactly 04-data/PROVENANCE.json')

    def exempt(path):
        # Top-level 04-data/README.md documents the folder; OS/iCloud metadata is checked by content.
        return relative_name(root, path) == '04-data/README.md' or os_metadata(path)

    data = {relative_name(root / '04-data', p): p for p in files
            if p.relative_to(root).parts[0] == '04-data' and p != record and not exempt(p)}
    by_nfc = {}
    for name in data:
        by_nfc.setdefault(nfc(name), []).append(name)
    for names in by_nfc.values():
        if len(names) > 1:  # distinct files on Linux, one visible name for a reader
            problem(f'04-data/{min(names)}', 'Data file names differ only by Unicode normalization',
                    names=sorted(names))
    # Read the record only when file_list accepted it as a regular in-root file (no symlink or FIFO).
    if record not in files:
        if data:
            problem('04-data', 'Data files without 04-data/PROVENANCE.json')
        return issues
    obj = json.loads(record.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    if (not isinstance(obj, dict) or set(obj) != {'schema', 'files'} or type(obj['schema']) is not int
            or obj['schema'] != 1 or not isinstance(obj['files'], dict)):
        raise ValueError('Unsupported provenance schema')

    def dossier_file(name):
        if not isinstance(name, str) or nonportable_name(name):
            return None
        exact = contained(root, root / name)
        if exact in files:
            return exact
        matches = [p for p in files if nfc(relative_name(root, p)) == nfc(name)]
        if len(matches) > 1:
            raise ValueError(f'Ambiguous Unicode-normalized provenance path: {name}')
        return matches[0] if matches else exact

    def case_twins(name):
        # A citation that matches dossier files only when letter case is ignored fails closed on
        # case-insensitive APFS and on Linux alike; name the real file(s) instead of "missing".
        # lower() rather than casefold(): 'straße' and 'strasse' differ in spelling, not case.
        if not isinstance(name, str) or nonportable_name(name):
            return []
        key = nfc(name).lower()
        return sorted(relative_name(root, p) for p in files
                      if nfc(relative_name(root, p)).lower() == key and nfc(relative_name(root, p)) != nfc(name))

    def case_problem(where, field, cited):
        twins = case_twins(cited)
        if len(twins) == 1:
            problem(where, 'Provenance path differs only by letter case from a dossier file',
                    **{field: cited, 'actual': twins[0]})
        elif twins:
            problem(where, 'Provenance path differs only by letter case from several dossier files',
                    **{field: cited, 'candidates': twins})
        return bool(twins)

    def capture(source, path):
        # A capture is evidence in 03-sources, not its index, a receipt or OS metadata.
        return (source.startswith('03-sources/') and path.is_file() and nfc(source) != '03-sources/README.md'
                and not source.endswith('.receipt.json') and not os_metadata(path))

    entries = set()
    for name, entry in obj['files'].items():
        where = f'04-data/{name}'
        if nfc(name) in entries:
            problem(where, 'Duplicate provenance entry after Unicode normalization')
        entries.add(nfc(name))
        method = entry.get('method') if isinstance(entry, dict) else None
        script = method.get('script') if isinstance(method, dict) else None
        if dossier_file(script) in files and (code_file(script) or not in_data_dir(script)):
            scripts.add(nfc(script))  # the method stays exempt even when this entry has other faults
        if nonportable_name(name):
            problem(where, 'Invalid provenance entry name')
            continue
        if not isinstance(entry, dict):
            problem(where, 'Invalid provenance entry', expected=['method', 'sources'])
            continue
        if set(entry) != {'sources', 'method'}:
            problem(where, 'Invalid provenance entry', expected=['method', 'sources'], found=sorted(entry))
            continue
        sources, target = entry['sources'], dossier_file(where)
        only_script = isinstance(method, dict) and set(method) == {'script'}
        described = (isinstance(method, dict) and set(method) == {'description'}
                     and isinstance(method['description'], str) and visible_text(method['description']))
        if not (isinstance(sources, list) and sources and all(isinstance(x, str) for x in sources)):
            problem(where, 'Provenance sources must be a non-empty list of dossier paths')
        else:
            paths = [dossier_file(x) for x in sources]
            if None in paths:
                problem(where, 'Invalid provenance source path')
            elif any(path not in files and case_twins(x) for x, path in zip(sources, paths)):
                # Letter-case mismatches are reported before the prefix and capture rules.
                for source, path in zip(sources, paths):
                    if path not in files and not case_problem(where, 'source', source):
                        problem(where, 'Missing provenance source', source=source)
            elif nfc(where) in map(nfc, sources):
                problem(where, 'Provenance source is the data file itself')
            elif PROVENANCE in sources:
                problem(where, 'Provenance source cannot be the provenance record')
            elif not any(x.startswith('03-sources/') for x in sources):
                problem(where, 'Provenance sources must include a 03-sources capture')
            else:
                missing = [x for x, path in zip(sources, paths) if path not in files]
                for source in missing:
                    problem(where, 'Missing provenance source', source=source)
                if not missing and not any(capture(x, path) for x, path in zip(sources, paths)):
                    problem(where, 'Provenance sources must include a 03-sources capture')
        if not (only_script or described) or (only_script and not script):
            problem(where, 'Provenance method needs exactly one of script or a non-empty description')
        elif only_script:
            if dossier_file(script) is None:
                problem(where, 'Invalid provenance script path')
            elif nfc(script) == nfc(where):
                problem(where, 'Provenance script is the data file itself')
            elif script == PROVENANCE:
                problem(where, 'Provenance script cannot be the provenance record')
            elif dossier_file(script) not in files:
                if not case_problem(where, 'script', script):
                    problem(where, 'Missing provenance script', script=script)
            elif in_data_dir(script) and not code_file(script):
                problem(where, 'Provenance script must be a code file', script=script,
                        accepted=sorted(SCRIPT_SUFFIXES))
        # An entry for README.md or OS metadata that exists is harmless, not a missing file.
        if nfc(name) not in by_nfc and not (target is not None and target.is_file() and exempt(target)):
            problem(where, 'Provenance entry for missing data file')
    for name, path in sorted(data.items()):
        if nfc(name) not in entries and nfc(f'04-data/{name}') not in scripts:
            problem(f'04-data/{name}', 'Data file without provenance entry')
    return issues


def check(root, manifest=None, documents=None):
    issues, pending, counts = [], [], {'files': 0, 'documents': 0, 'local_links': 0, 'pdf_pages': {}}
    parsed = {}

    def attempt(where, action):
        try:
            return action()
        except Unverified as exc:
            pending.append({'path': where, 'reason': str(exc)})
        except (ValueError, OSError, TypeError, KeyError, RuntimeError) as exc:
            issues.append({'path': where, 'reason': str(exc)})

    files = attempt('.', lambda: file_list(root))
    if files is None:
        files = []
    counts['files'] = len(files)

    def verify_manifest():
        path = contained(root, manifest)
        obj = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
        if not isinstance(obj, dict) or type(obj.get('schema')) is not int or obj.get('schema') != 1 or obj.get('path_base') != 'dossier_root' or not isinstance(obj.get('files'), dict):
            raise ValueError('Unsupported inventory schema')
        expected = obj['files']
        actual = {relative_name(root, p): p for p in files if p != path}
        for name, record in expected.items():
            if nonportable_name(name):
                raise ValueError(f'Invalid inventory path: {name}')
            item = contained(root, root / name)
            if item == path:
                raise ValueError('Inventory cannot hash itself')
            if not isinstance(record, dict) or set(record) != {'bytes', 'sha256'} or type(record['bytes']) is not int or record['bytes'] < 0 or not isinstance(record['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', record['sha256']):
                raise ValueError(f'Invalid inventory entry: {name}')
            if name not in actual:
                issues.append({'path': name, 'reason': 'Missing inventoried file'})
            elif digest(item) != record:
                issues.append({'path': name, 'reason': 'Inventory byte/hash mismatch'})
        for extra in sorted(actual.keys() - expected.keys()):
            issues.append({'path': extra, 'reason': 'File missing from inventory'})

    if manifest is None:
        pending.append({'path': '.', 'reason': 'No inventory supplied; completeness and version hashes unverified'})
    else:
        attempt('inventory', verify_manifest)
    issues.extend(attempt(PROVENANCE, lambda: provenance_issues(root, files)) or [])

    def parsed_doc(path):
        if path not in parsed:
            parsed[path] = document(path)
        return parsed[path]

    def verify_target(owner, target, literal_file=False):
        local = local_target(root, owner, target, literal_file=literal_file)
        if local is None:
            return
        counts['local_links'] += 1
        path, fragment = local
        if not fragment:
            return
        if path.suffix.lower() in ('.md', '.html', '.htm'):
            if fragment not in parsed_doc(path).anchors:
                raise ValueError(f'Missing fragment: {target}')
        elif path.suffix.lower() == '.pdf' and re.fullmatch('page=[1-9][0-9]*', fragment):
            with module('pymupdf').open(path) as pdf:
                if int(fragment[5:]) > len(pdf):
                    raise ValueError(f'PDF page out of range: {target}')
        else:
            raise Unverified(f'Fragment type not verified: {target}')

    def verify_document(path):
        if path.suffix.lower() != '.pdf':
            for target in parsed_doc(path).targets:
                attempt(relative_name(root, path), lambda t=target: verify_target(path, t))
            return
        pdfmod = module('pymupdf')
        with pdfmod.open(path) as pdf:
            if pdf.needs_pass:
                raise ValueError('Encrypted PDF cannot be checked')
            counts['pdf_pages'][relative_name(root, path)] = len(pdf)
            for page in pdf:
                for link in page_links(pdf, page):
                    kind, target, literal = pdf_link_info(pdf, link)
                    if kind == pdfmod.LINK_GOTO:
                        if not 0 <= link.get('page', -1) < len(pdf):
                            raise ValueError('Invalid internal PDF page destination')
                    elif kind in (pdfmod.LINK_LAUNCH, pdfmod.LINK_GOTOR):
                        verify_target(path, target, literal_file=literal)
                        if kind == pdfmod.LINK_GOTOR:
                            destination = local_target(root, path, target, literal_file=literal)[0]
                            with pdfmod.open(destination) as other:
                                verify_remote_page(link, other)
                    elif kind == pdfmod.LINK_URI:
                        verify_target(path, target)
                    else:
                        raise Unverified('Unsupported PDF link action')

    if documents is None:
        # Captured evidence/log transcripts are originals, not authored navigation.
        documents = [p for p in files if p.suffix.lower() in ('.md', '.html', '.htm', '.pdf')
                     and p.relative_to(root).parts[0] not in ('03-sources', '04-data', '05-research-log')
                     and not any(part in ('03-sources', '05-research-log') for part in p.relative_to(root).parts)]
    for path in documents:
        def run(path=path):
            path = contained(root, path)
            regular(path)
            counts['documents'] += 1
            verify_document(path)
        attempt(str(path), run)
    if not counts['documents']:
        pending.append({'path': '.', 'reason': 'No delivery documents were inspected'})
    return {'status': 'fail' if issues else 'partial' if pending else 'pass',
            'checks': counts, 'errors': issues, 'unverified': pending,
            'limits': ['No factual, inference, freshness, analytic-page or reader-usability certification',
                       'External URLs are not fetched; Markdown uses the documented Python-Markdown profile',
                       'Custom index schemas, PDF outlines/actions outside page links, CSS resources and scripts are not inspected',
                       'Only HTML href/src are checked; srcset, poster, object data, SVG xlink:href and meta refresh URLs are not']}


def page_links(pdf, page):
    """Do not silently pass link annotations omitted by MuPDF's action parser."""
    links = page.get_links()
    annotations = {xref for xref, _kind, _name in page.annot_xrefs()
                   if pdf.xref_get_key(xref, 'Subtype')[1] == '/Link'}
    if annotations != {link['xref'] for link in links}:
        raise Unverified('PDF link annotations omitted or unresolved by the parser')
    return links


def pdf_link_info(pdf, link):
    # MuPDF can normalize Launch to GoToR and percent-encode literal filenames.
    # Read the original PDF action so filenames and URI fragments stay distinct.
    pdfmod = module('pymupdf')
    if pdf.xref_get_key(link['xref'], 'A/Next')[0] != 'null':
        raise Unverified('Chained PDF link actions (/Next) are not inspected')
    action = pdf.xref_get_key(link['xref'], 'A/S')[1]
    if action == '/URI':
        if pdf.xref_get_key(pdf.pdf_catalog(), 'URI/Base')[0] != 'null':
            raise Unverified('PDF /URI /Base changes relative link resolution')
        value_type, value = pdf.xref_get_key(link['xref'], 'A/URI')
        if value_type == 'string':
            return pdfmod.LINK_URI, value, False
    if action in ('/Launch', '/GoToR'):
        for key in ('A/F/UF', 'A/F/F', 'A/F'):
            value_type, value = pdf.xref_get_key(link['xref'], key)
            if value_type == 'string':
                kind = pdfmod.LINK_LAUNCH if action == '/Launch' else pdfmod.LINK_GOTOR
                return kind, value, True
        raise Unverified('Unsupported PDF file specification')
    if link['kind'] == pdfmod.LINK_GOTO:
        return pdfmod.LINK_GOTO, None, False
    raise Unverified('Unsupported PDF link action')


def verify_remote_page(link, pdf):
    if pdf.needs_pass:
        raise ValueError('Encrypted remote PDF cannot be checked')
    page = link.get('page', -1)
    if page == -1:
        raise Unverified('Remote named PDF destination not verified')
    if not 0 <= page < len(pdf):
        raise ValueError('Remote PDF page out of range')


def portable_pdf(root, source, output):
    """Preserve the input; write only a new relative-link PDF derivative."""
    source, output = contained(root, source), contained(root, output)
    if source.suffix.lower() != '.pdf' or output.suffix.lower() != '.pdf':
        raise ValueError('PDF input and output must use the .pdf extension')
    if output.exists():
        raise FileExistsError(output)
    pdfmod = module('pymupdf')
    changed = 0
    with pdfmod.open(source) as pdf:
        if pdf.needs_pass:
            raise ValueError('Encrypted PDF cannot be exported')
        for page in pdf:
            for link in page_links(pdf, page):
                kind, target, literal = pdf_link_info(pdf, link)
                link['kind'] = kind
                if kind == pdfmod.LINK_GOTO:
                    if not 0 <= link.get('page', -1) < len(pdf):
                        raise ValueError('Invalid internal PDF destination')
                    continue
                if kind not in (pdfmod.LINK_URI, pdfmod.LINK_LAUNCH, pdfmod.LINK_GOTOR):
                    raise ValueError('Unsupported PDF link action; original left intact')
                local = local_target(root, source, target, allow_absolute=True,
                                     literal_file=literal)
                if local is None:
                    continue
                path, fragment = local
                if fragment:
                    raise ValueError('Local PDF URL fragments require a renderer-specific export')
                if kind == pdfmod.LINK_GOTOR:
                    with pdfmod.open(path) as other:
                        verify_remote_page(link, other)
                # File links are literal PDF filenames, not percent-encoded URL strings.
                if kind == pdfmod.LINK_URI:
                    link['kind'] = pdfmod.LINK_LAUNCH
                    link.pop('uri', None)
                link['file'] = relative_file_link(output, path)
                page.update_link(link)
                changed += 1
        data = pdf.tobytes(garbage=4, deflate=True)
    new_bytes(output, data)
    return {'status': 'created', 'path': relative_name(root, output), 'links_rewritten': changed,
            'next': 'Check the new derivative and a relocated copy; retain HTML for viewer restrictions'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('inventory', 'check', 'capture', 'handoff', 'render', 'portable-pdf'):
        p = sub.add_parser(name)
        p.add_argument('root', type=Path)
        if name == 'check':
            p.add_argument('--manifest', type=Path)
            p.add_argument('--documents', nargs='+', type=Path)
        elif name in ('capture', 'handoff'):
            p.add_argument('source', type=Path)
            p.add_argument('destination', type=Path)
            p.add_argument('--origin', required=True)
        elif name == 'render':
            p.add_argument('documents', nargs='+', type=Path)
            p.add_argument('--replace', action='store_true')
        elif name == 'portable-pdf':
            p.add_argument('source', type=Path)
            p.add_argument('output', type=Path)
        else:
            p.add_argument('output', type=Path)
    p = sub.add_parser('library', help='show or persist the Sherlock library (outside any git repository)')
    p.add_argument('--set', dest='path', type=Path)
    p.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    try:
        result = library(args.path, args.replace) if args.command == 'library' else dossier_command(args)
    except Unverified as exc:
        result = {'status': 'partial', 'unverified': [str(exc)]}
    except (OSError, ValueError, RuntimeError) as exc:
        result = {'status': 'fail', 'errors': [str(exc)]}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    # An unset library is not an error, but nothing is configured yet: same exit as partial.
    return {'fail': 1, 'partial': 2, 'unset': 2}.get(result['status'], 0)


def dossier_command(args):
    if args.root.is_symlink():
        raise ValueError('Dossier root cannot be a symlink')
    root = args.root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Dossier root must be a directory')
    def inside(p):
        return p if p.is_absolute() else root / p
    if args.command == 'check':
        return check(root, inside(args.manifest) if args.manifest else None,
                     [inside(p) for p in args.documents] if args.documents else None)
    if args.command == 'inventory':
        return inventory(root, inside(args.output))
    if args.command == 'capture':
        return capture(root, args.source, inside(args.destination), args.origin)
    if args.command == 'handoff':
        return handoff(root, args.source, inside(args.destination), args.origin)
    if args.command == 'render':
        return render(root, [inside(path) for path in args.documents], args.replace)
    return portable_pdf(root, inside(args.source), inside(args.output))


if __name__ == '__main__':
    sys.exit(main())
