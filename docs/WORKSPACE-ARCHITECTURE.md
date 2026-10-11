# Research workspace architecture

Sherlock is a deep research skill for Claude Code. This architecture describes the research files it produces; Claude Code executes the workflow, with Python helpers for preservation and delivery checks.

The canonical operating instructions are [workspace and updates](../skill/references/workspace-and-updates.md) and [studies and delivery](../skill/references/studies-and-delivery.md). This document explains the decisions behind them.

## Six directories, three kinds of content

| Directory | Purpose | What it must not be confused with |
|---|---|---|
| `01-reports/` | Current executive, integrated full report, final conclusion, rendered formats | The only retained research |
| `02-studies/` | Actual current analytical studies, directly accessible by subject | An index that hides every file inside execution folders |
| `03-sources/` | External evidence, source inventory, original captures and labeled extractions | Research written by an agent |
| `04-data/` | Tables, datasets and reproducible calculations, plus `PROVENANCE.json` naming each file's sources and method (an extraction script may sit next to its table) | Rendering or orchestration code; a table without a provenance entry |
| `05-research-log/<cycle>/` | Brief, journal, original agent outputs, reviews and verification | A substitute for the readable study library |
| `06-history/` | Immutable published snapshots and migration originals | Current conclusions or automatically revalidated facts |

A root `README.md` identifies the research, objectives, current published cycle, any cycle in progress, navigation, gaps and update instructions. A file inventory accounts for the entire dossier. Current reports and studies are visible without knowing a cycle ID. Cycle IDs preserve lineage and prevent concurrent sessions from overwriting each other.

## Preserve before interpreting

External source bytes, original agent handoffs and edited studies are three different records. Capture a substantive handoff before editing it, with assignment, producer, receipt time and hashes where available. Follow-up corrections are additional versions. Store reviews as received, then separately record their disposition. A source download or final edited study cannot retrospectively stand in for a lost original draft.

The host may not expose all conversation or agent state. Save complete accessible transcripts and tool returns when available, plus checkpoints that allow another researcher to resume. Declare inaccessible material and preservation failures. Do not promise access to hidden reasoning, reconstruct missing drafts, or label a post-edit copy as an original.

## Identity and links

The research name and creation date remain stable. Use descriptive English slugs; ask about ambiguous identities before research. Each study has a stable ID, descriptive title, aliases, objective, coverage, version, verification date and a concrete path. Current navigation resolves to current files. A published historical report resolves to the study versions it actually used.

Use relative paths in portable files. Link an executive claim to its completed study near the claim; keep source links distinguishable from analytical links. PDFs require tested destinations and readable fallback references; HTML may serve as a fallback where viewers block cross-file links. Copy the dossier to another directory to verify portability.

JSON indexes are part of navigation too. Record the base for paths, validate dependencies and recalculate hashes for edited derivatives. Preserve original manifests; issue a new derived manifest with migration provenance instead of quietly changing historical receipts.

## Updating a dossier

Resolve explicit path, active dossier, the identified project's folder in the persisted library, a legacy project `research/` folder, then the library root. Load the confirmed brief and current conclusions; do not ask answered questions again. Known identity, access or budget dependencies are resolved before collection. An old spending limit is not a fresh allowance.

A new cycle preserves captures and revisions, compares central assessments, and reports maintained, strengthened, weakened, replaced/withdrawn and not-revalidated conclusions. Distinguish event date, capture date and analytical revision. No-change checks do not automatically strengthen confidence. A partial update does not refresh every topic's verification date.

Freeze the previous publication before changing the current projection. Mark work in progress separately and advance the published pointer only after the new packet is coherent. A failed export or correction that invalidates an assessment stays explicit. Save conflicts separately rather than overwriting another session.

## Report depth and delivery

For complete research: executive N pages, N at most seven; full report at least 7N analytical pages using comparable density. Raw corpus, covers, isolated bibliography and duplicated material do not count. There is no arbitrary upper page cap. Record actual page ranges and renderer profile. Missing rendering means unverified pagination; insufficient substance means partial delivery, never filler.

The first response links the folder, reports and study library, states the central conclusion/confidence/limit, then explains themes and links all analytical files. The final-conclusion document is last in that analytical index. Link the full inventory separately instead of dumping raw filenames into chat.

## Public distribution

Reusable docs, code, templates, prompts, field names and directory names are English. Research prose follows the user's language. Original captures and historical work retain their bytes and language. The public package contains only explicitly approved implementation files; local dossiers, private company evidence and historical exports are excluded. Saving, packaging and publication are separate actions.

## Local verification boundary

Use the [delivery helper](../skill/references/delivery-checks.md) to inspect the configured library, preserve a subagent's final text from an explicitly supplied canonical transcript, copy raw exports, render Markdown to HTML/PDF, freeze a versioned SHA-256 inventory and check authored navigation plus `04-data` provenance after relocating a dossier. A source summary, host-side evaluation harness or hash receipt is not a full original capture. Label preservation as complete, partial or unavailable according to what the host actually exposes.

Keep check output outside a frozen dossier or create a new inventory version after adding it. The inventory cannot hash itself. Never overwrite old manifests or original PDFs to make checks pass: create a named derivative and declare unsupported or historical failures. The helper only inspects documented link formats; custom JSON indexes and other renderer actions still need their own validation.

A separate claim-check record in the cycle's reviews connects decisive statements to original captured evidence and their keep/condition/correct/withdraw/not-verified disposition. This factual audit remains the model's responsibility and is not certified by file checks.
