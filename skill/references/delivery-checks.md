# Local delivery checks

This helper supports the Sherlock deep research skill for Claude Code. Use [delivery.py](../scripts/delivery.py) for filesystem evidence, not research judgment. It performs no network requests, model calls, installation or publication. Run it with Python 3.9 or newer; filesystem/inventory/capture and HTML checks use the standard library. Markdown checks require the optional `Markdown` package; PDF inspection/export requires optional `PyMuPDF`. Use an already available environment, or follow the host's installation rules. Missing libraries produce an explicit **partial** result (exit 2), never a silent pass. Invalid files, paths, hashes or destinations return **fail** (exit 1). Exit 0 means only the requested mechanical operation succeeded.

## Sherlock library

The library is one persisted location per machine for dossiers without an explicit destination:

```bash
python3 SCRIPT library                       # prints it, or status "unset" (exit 2) with a suggestion
python3 SCRIPT library --set ~/Documents/Sherlock
python3 SCRIPT library --set /new/path --replace
```

The setting lives in `~/.config/sherlock/config.json` (`SHERLOCK_CONFIG` overrides the file location; `~` expands, relative overrides fail). `--set` resolves symlinks first and stores the real path, then refuses a relative path, a path inside a git working tree (any ancestor holding `.git`, including a worktree file; a symlink into a repository is caught after resolution) and a silent change of an existing value without `--replace`. A cross-process lock serializes config updates; unique staging files and read-back catch interrupted or conflicting writes. `--replace` without `--set` fails. It creates the directory, also when the same path is set again after the folder was deleted. Reading the library re-checks the stored path, so a repository created above it later makes `library` fail instead of returning it. Only an ancestor `.git` is detected; a work tree defined elsewhere through `GIT_DIR`/`core.worktree` is not. A malformed config fails rather than being trusted or overwritten; the error says to move it aside or point `SHERLOCK_CONFIG` at another file before `--set`.

## Freeze and verify

Finish reports, sources, log records and the root index first. Link the intended inventory filename in the root index before creating it. Paths after `ROOT` are relative to the dossier, except an explicitly supplied capture source. `SCRIPT` means this skill's `scripts/delivery.py`; `ROOT` means the selected dossier, not the skill folder.

```bash
python3 SCRIPT inventory ROOT inventory-v1.json
python3 SCRIPT check ROOT --manifest inventory-v1.json
```

The inventory includes every regular file, except itself, with size and SHA-256. JSON is UTF-8; inventory and receipt paths use forward slashes on every OS. Never rewrite a historical manifest to normalize it; preserve it and create a new version if needed. It refuses overwrite and symlinks. Create a new version after changes; never rewrite a historical receipt to make mismatched bytes pass. Save check output **outside** the frozen dossier (for example in the parent project's review log), or freeze a later inventory after adding it. This avoids a self-changing manifest/report loop.

`check` verifies inventory coverage/hashes and authored Markdown/HTML/PDF navigation. By default it excludes raw source, data and log directories from document parsing while still inventorying their bytes. It includes historical report navigation. For a specific document set:

```bash
python3 SCRIPT check ROOT --manifest inventory-v1.json --documents README.md 01-reports/executive.pdf
```

A selected-document pass covers only those documents. External URLs are not fetched. In HTML `href`/`src` (every duplicate attribute counts) and Markdown links, a network-path reference such as `//host/x`, `///path` or `//localhost/path` fails: opened from disk it resolves to a local file or a network share, so write an explicit `https://` URL instead. Every link target first gets the browser's URL preprocessing (leading and trailing C0 controls and spaces stripped, every tab and newline removed), so `" //host/x"` is judged as `//host/x` on every Python version; literal PDF filenames are not preprocessed. `srcset`, `poster`, `<object data>`, SVG `xlink:href` and meta-refresh URLs are not inspected. Python's HTML parser does not follow every HTML5 recovery rule: on Python 3.9 a malformed comment such as `<!-->` can hide a following link from the check, so treat authored HTML with malformed comments as unverified. Inventory creation refuses names with backslashes, drive prefixes, absolute or parent segments; Windows reserved names (`CON`, `NUL.txt`), trailing dots or spaces, colons and case-only collisions are not checked. Supported links are HTML `href`/`src` and Python-Markdown inline/reference links with tables, fenced code and generated Unicode heading IDs. Check the parser's reported fragment failures against the actual renderer; different Markdown dialects may assign different duplicate-heading IDs. Explicit HTML anchor IDs avoid that ambiguity. Custom JSON index semantics, source truth, CSS/script resources and viewer behavior are outside the check. PDF inspection covers page links and page bounds, not every PDF action/outline; chained link actions (`/Next`) and a document `/URI /Base` return partial. An unverified check must be resolved or disclosed, not ignored.

Copy the complete frozen dossier to a different directory and run `check` there with its copied inventory. Do not follow old absolute destinations and count that as a relocation pass. File/hash checks prove current byte identity, not that every topic was re-researched or that a narrative version label is correct; compare the entry point, cycle, coverage and assessment dispositions separately.

## Data provenance

A table that cannot be traced back to its capture cannot be audited or re-derived. `check` therefore requires `04-data/PROVENANCE.json` whenever `04-data/` holds a file other than the exempt ones below:

```json
{"schema": 1, "files": {
  "prices.csv": {"sources": ["03-sources/fipezap-202608/report.pdf"],
                 "method": {"script": "04-data/extract_prices.py"}},
  "rent-sample.csv": {"sources": ["03-sources/listings/pages/p01.html"],
                      "method": {"description": "Copied by hand from the listing table; 218 rows"}}}}
```

Keys are paths relative to `04-data/`; `sources` and `script` are dossier-relative paths to existing files. Every entry cites at least one real capture under `03-sources/`: evidence itself, not the `03-sources/README.md` index, a `.receipt.json` or OS metadata (a README captured as evidence inside a capture folder counts). Other tables may be listed as intermediate sources, but each entry must cite a capture directly. `method` holds exactly one of `script` or a non-empty `description`; the script cannot be the table itself or the record. A file cited as some entry's `script` needs no entry of its own, even when the citing entry has other faults; every other file in `04-data/` does, except the top-level `04-data/README.md` and metadata the OS or iCloud create on their own (`.DS_Store`, `._*`, `Icon\r`, `.*.icloud`), which are recognized by name and content, so a table cannot hide behind those names. An entry for an exempt file that exists is accepted. An iCloud conflict copy such as `prices 2.csv` is real data and still needs an entry or removal. Names are compared after Unicode NFC normalization, because macOS often stores accented names decomposed; two files or two entries whose names differ only by normalization fail instead of merging. The directory and record must be spelled exactly `04-data/` and `PROVENANCE.json`; case variants fail. The record is read only when it is a regular file inside the dossier.

Each failure has its own reason: a data file without an entry, an entry for a missing file, an invalid entry name, an entry that is not an object or lacks exactly the keys `sources` and `method` (the `found` field lists the keys of an object), duplicate keys (also after Unicode normalization), data file names that differ only by normalization, sources that are not a non-empty list, an invalid or escaping path, a source equal to the file itself or to the record, no real `03-sources/` capture, a missing source or script, a script equal to the file itself or to the record, and a method that is not exactly one of the two.

Limits: only `04-data/` is checked, so keep every table there; navigation indexes and pagination files belong with the reports, not in `04-data/`. The check verifies that the cited files exist, not that the method actually produces the table: rerun the script when the number matters. It also cannot tell a real citation from an invented one; an entry must name the capture the table actually came from.

Source and script citations first use exact file paths, then a unique Unicode NFC-equal path from the inventoried files. An ambiguous normalized match fails. A description made only of invisible formatting characters or Unicode spacing counts as empty.

## Render Markdown

Use the same Markdown profile as `check` (`tables`, `fenced_code`, `toc` and Unicode heading IDs):

```bash
python3 SCRIPT render ROOT 01-reports/executive.md 01-reports/full.md 02-studies/topic.md
python3 SCRIPT render ROOT 01-reports/executive.md --replace
```

The helper leaves Markdown unchanged, inserts a missing blank line between prose and a following list in the rendered copy, and refuses ambiguous 2–3-space nested-list indentation with a source line and 4/8-space guidance. A `<!-- pagebreak -->` comment starts a new PDF page. It writes adjacent `.html` and `.pdf`, reports PDF page counts and H1/H2 pages, and rewrites `.md` links to `.html` only when that HTML already exists or is requested in the same call. PDF cross-file links use relative URI actions that retain URL escapes and fragments; `check` reads the raw action to validate their targets. Inspect both formats and run `check` after freezing an inventory.

Only validated local images inside the dossier are supplied to the PDF renderer. Missing, escaping, symlinked or unsupported local images fail; remote or embedded images produce HTML with `partial` status and no PDF. Without Markdown nothing is written; without PyMuPDF a first render can write HTML with `partial` status and unverified pagination. Existing derivatives are never overwritten without `--replace`. Every requested document is validated before any derivative is written; with both dependencies, all new derivatives are staged and ordinary write failures roll back the batch. If PyMuPDF is missing during `--replace`, existing HTML/PDF remain byte-for-byte intact. The renderer also refuses a PDF when text extraction shows missing source words, including clipped tall table cells. The status reports these boundaries; a partial result is not a measured N/7N claim.

## Portable PDF derivative

When a renderer emits absolute local links, create a **new** derivative:

```bash
python3 SCRIPT portable-pdf ROOT 01-reports/executive.pdf 01-reports/executive-portable.pdf
```

The helper rewrites supported in-root file destinations relative to the new PDF, keeping original pages/content and external links. It refuses outside-root targets, unsupported actions and an existing output. It does not map an old path to a guessed latest study. Regenerate from the correct source versions when the original targets are no longer available. Check the derivative, update the reader-facing links, freeze a new inventory and verify after relocation. Preserve the first PDF as an earlier export with its known limitation; do not advertise it as portable. Some viewers block local-file links even when valid: provide the HTML library and readable study names as fallbacks.

## Capture a host export or original handoff

After the host provides an explicit export file:

```bash
python3 SCRIPT capture ROOT /path/to/export.jsonl 05-research-log/CYCLE/host-export.jsonl --origin "Host-provided export for this research cycle"
```

Create the intended parent directory first. Symlink ancestors are rejected too. On macOS, `/tmp` and `/var/folders` may be aliases; obtain a canonical temporary directory with `python3 -c 'import os,tempfile; print(os.path.realpath(tempfile.gettempdir()))'` and pass a file below that real path. Do not disable path guards. The source is read-only; the destination and adjacent `.receipt.json` must not already exist. The helper copies exact bytes, verifies a stable source around the copy, records a hash/time/origin, and removes an incomplete newly created copy on failure. It does not discover sessions, infer completeness, remove secrets from an export or recover hidden context. Use only an authorized export scoped to the research; identify any host omissions. Add later exports under new names.

For a Claude Code subagent whose host blocks direct file writes, preserve the complete final text from an explicitly supplied canonical transcript instead:

```bash
python3 SCRIPT handoff ROOT /real/path/subagents/agent-ID.jsonl 05-research-log/CYCLE/original-agent-outputs/front.md --origin "front assignment and producer"
```

The command refuses `tasks/ID.output` symlinks and prints the real path for an explicit retry. It takes all text blocks of the final assistant message only when that message is the transcript's last entry and does not request a tool; a null `stop_reason` is accepted. The receipt includes transcript and output hashes, message ID, agent ID when present, origin and the observed `stop_reason` (which can be null). Unknown JSONL shapes fail; no output or receipt is created. Preserve a full raw transcript with `capture` only when its scope is authorized.

## Completion meaning

Record technical check status separately from the conclusion audit. A clean inventory/link report cannot certify factual correctness, temporal freshness, analytical 7N depth or user usefulness. A known bad historical export can remain preserved: report its failing status and identify the verified current formats, rather than editing the original or declaring the entire corpus clean.
