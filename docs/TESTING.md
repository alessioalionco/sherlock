# Testing and limitations

Sherlock runs as a deep research skill in Claude Code. The local tests below verify its supporting scripts and distribution; research behavior is evaluated separately.

## Reproduce the local checks

From the extracted package root, run `python3 -m unittest discover -s tests -v`. Use Python 3.9 or newer. Core checks use the standard library and temporary synthetic files; no model API, private repository, browser session or company data is required. Optional `Markdown` and `PyMuPDF` enable Markdown/PDF checks. Missing optional dependencies appear as test skips, not verified successes.

The tested baseline is macOS with Python 3.9.6 and 3.14.7. The complete optional suite uses Python 3.14.7, Markdown 3.11 and PyMuPDF 1.28.2. Use an isolated environment and the host's installation rules if those libraries are needed. Other library versions, Linux, native Windows and other skill hosts have not received runtime clearance. Windows path spelling and legacy locale behavior have dedicated platform-independent regressions; these do not substitute for a native Windows run. They test the path helpers directly: on macOS and Linux, a call site that bypassed a helper (for example `portable_pdf` reverting to `os.path.relpath`) would still pass, so only a native Windows run verifies that wiring.

## Deterministic coverage

The package suite verifies the explicit distribution allowlist, member hashes, missing inputs, symlink rejection, existing-output preservation, write-failure cleanup, extraction/rebuild and relative documentation links. A conditional local-install comparison is supplemented by explicit skill-file comparisons during release preparation. A fresh extracted package must rebuild without any private source directory.

Delivery checks cover missing/extra/changed files, malformed inventories, path escapes, exact export capture, failure cleanup, Markdown/HTML fragments, PDF page bounds and relative-link derivatives after relocation. JSON inventory keys are POSIX-style relative paths, read/written as UTF-8; tests include Windows path semantics, nested non-ASCII filenames and a legacy-default-encoding simulation. The checker preserves original PDFs and rejects unsupported or omitted page-link actions rather than silently passing them. Link targets get the browser's URL preprocessing first, with the leading-space network-path case proven red on Python 3.9.6 before the fix. The `library` command is covered for persistence across processes, the default and overridden config location, `~` expansion, symlink resolution, refusal inside a git working tree (also when it appears later), `--replace`, malformed configs and interrupted writes. `04-data` provenance is covered for every failure reason, the requirement of a real `03-sources` capture (not an index, receipt or metadata), the cited-script exemption (also for malformed entries), the top-level README and content-verified OS/iCloud metadata exemptions with tables under tempting names still failing, Unicode NFC matching, case variants and a symlinked or FIFO record that must never be read. Each of these behaviors has a mutant shown red.

Beta.5 tests also cover `handoff` extraction of a terminal multi-block assistant message, receipt hashes, symlink refusal, trailing entries and malformed JSONL. Renderer tests cover image validation, Markdown-to-HTML/PDF links after relocation, heading-page reporting, fenced-code versus nested-list parsing, clipped table text, links in partial batches, and rollback of an entire replacement batch. Config tests exercise stale staging files; provenance tests cover NFC-equal citations and invisible method descriptions.

See [helper usage](../skill/references/delivery-checks.md) for limits and exit codes. File checks do not establish factual accuracy, completeness of inaccessible host exports, analytical depth or user usefulness. An exact inventory also includes OS metadata if present; a new metadata file is a real inventory change, not something silently ignored.

## Public evaluation summary

Sherlock remains **experimental**. Small exploratory comparisons and an engineering loop did not establish a consistent advantage over open research. The previously disclosed two-case end-to-end comparison began each condition with the same original user request and answered spontaneous questions according to a prewritten disclosure policy.

| Metric | Sherlock | Open chat |
|---|---:|---:|
| Mean qualitative score, 0–10 | 6.68 | 6.57 |
| Relative reported research usage | 2.89× | 1× |

The mean advantage was +0.11, below the predeclared +0.5 threshold. Correctness was lower for Sherlock in both cases. One central conclusion failed verification; a decisive conclusion in the other case was not cleared. Purpose discovery, original-source capture and auditability showed benefits, but those did not establish a reliable final-answer advantage.

The scoring weighted correctness, evidence depth and question fit twice, and counterevidence, calibration, auditability, actionability and efficiency once (weighted sum divided by 11). A central error cannot be averaged away by presentation quality. Reported research usage excludes unmeasured coordination and assessment effort and is not an invoice guarantee.

Only two known tasks were used, with one current session per condition, scripted replies, recognizable formats, qualitative native graders and live-source variation. This is not statistical significance, natural user-satisfaction measurement or an isolated causal estimate of a skill revision. Private case identities, local costs and full source corpora are intentionally excluded from this distribution; the public summary is a limitation disclosure, not an independently reproducible benchmark dataset.

## Behavioral coverage still open

[Acceptance criteria](ACCEPTANCE-CRITERIA.md) specify intended behavior, not passed tests. Remaining coverage includes cold resume, longitudinal and concurrent updates, real first-use host discovery, live browsing resistance to hostile source instructions and a reliably complete default N/7N delivery. Mechanical navigation and preservation tests do not clear these behaviors. Do not market the skill as more accurate or safer than open research on the basis of this package.

Future evaluations should preregister the question being measured, tasks, actual model/tools, effort envelope, interaction/stopping policy and judging rubric. Distinguish execution after a shared brief from the full experience including elicitation. Check original sources for decisive claims; separate confidence, objective coverage and actual user feedback. For resumed sessions, verify whether cost/token fields are cumulative before aggregation; never sum cumulative snapshots as independent spend. Run new studies only under a valid bounded mandate.

## Public-content review

An allowlist limits which files ship; it cannot detect private facts embedded in approved prose. Inspect changed public files before creating a release. Include only synthetic/neutral examples and deliberately selected aggregate findings. Research folders, internal snapshots, raw evaluation artifacts, credentials and host configuration must remain outside the distribution. Publishing the implementation does not authorize publishing a user's dossier.
