# How Sherlock works

Sherlock is a set of research instructions for Claude Code, accompanied by local Python helpers. Claude Code chooses and reads sources, develops studies, audits the argument, and writes the dossier using the session's available tools. The helpers handle specific file operations. Understanding that boundary is essential to interpreting the result.

## Three different kinds of assurance

| Layer | What it does | What it cannot establish |
|---|---|---|
| Skill instructions | Ask the model to refine objectives, investigate, preserve work, challenge claims, and deliver within scope | That a future run will comply with every instruction |
| Mechanical checks | Inspect inventories, file identity, supported links, data-provenance records, and supported render outputs | That a source is true, an extraction is faithful, or an answer is sufficient |
| Analytical judgment | Assess evidence, counterarguments, units, implications, confidence, and usefulness | A deterministic guarantee of accuracy or independent verification |

The default audit is self-review. Additional review or delegation depends on the host and mandate. Sherlock does not guarantee a panel, multiple model families, or independent judgment.

## 1. Make the question researchable

Before substantive collection, the skill asks the researcher to refine the primary question, offer secondary objectives, obtain confirmation, and show a strategy. A useful strategy explains which questions matter, what evidence could answer them, and what a sufficient result would enable. Suggested secondary objectives help expose adjacent fronts the user may not have named; they become part of the mandate only when the user accepts them.

The user can explicitly skip all or part of this briefing. Existing answers and confirmations should carry forward. Suggested objectives are not accepted objectives; silence is not approval. A clearer brief should reduce avoidable investigation, while preserving the user's actual interests.

Known access, cost, or scope dependencies are resolved before the work that depends on them. Once a cycle is approved, routine source substitutions and relevant checks proceed within that mandate. The strategy can divide the approved question into research fronts by theme, evidence type, or competing explanation; this does not guarantee parallel agents or authorize new objectives. A material expansion is proposed after delivery. An inaccessible source may leave a partial answer; it must not become evidence that something does not exist.

## 2. Keep the evidence and the explanation

Each substantive study should explain its question, answer, evidence, counterevidence, implication, confidence, limits, and revision conditions. It develops the reasoning while the investigation is happening. A folder of captured pages alone does not supply that analysis.

The workspace keeps three records distinct:

- **External evidence:** the page, attachment, excerpt, or tool return actually obtained, with origin, dates, and access level.
- **Original researcher output:** accessible handoffs and reviews as received, before editing or synthesis.
- **Edited analysis:** studies, the integrated report, executive, and final conclusion.

These have different evidentiary roles. A source summary is not a full capture. A revised study cannot retrospectively replace a lost original handoff. A hash can show that bytes match a record; it cannot show that the record is complete or correct.

Current studies live in `02-studies/`. Sources live in `03-sources/`. Derived data lives in `04-data/`, with source captures and a method recorded in `PROVENANCE.json`. The checker verifies that required provenance records and paths exist; it does not establish that the method really reproduces a table.

See the [workspace architecture](WORKSPACE-ARCHITECTURE.md) and [synthetic example](../examples/README.md).

## 3. Challenge the conclusion at its weakest premise

The skill asks the model to reopen original evidence for the claims carrying the recommendation. It must distinguish a vendor's declaration from demonstrated use, align populations and units in comparisons, and preserve qualifications when summarizing.

The useful audit question is: *If this premise fails, what else must change?* A failed premise should lead to correction, narrowing, conditioning, or withdrawal across dependent studies, tables, and reports. Adding a caution beside an unchanged invalid recommendation does not repair it.

A [claim-check record](../skill/assets/claim-check.md) connects each decisive statement to the evidence inspected and its disposition. The model is responsible for this judgment. File verification cannot certify it.

Central insights and the main recommendation receive a confidence score from 0 to 100 in steps of ten, when assessable. Each score needs a brief evidence basis and the decisive limitation that could change it. If the evidence does not permit an assessment, the answer explains why instead of supplying a number. A score is the model's judgment about support for a specific conclusion. It is not a calibrated probability, an impact rating, or a grade for the research. An invalid recommendation must be corrected or withdrawn; a confidence score cannot rescue it.

Keep three questions separate:

| Question | What to look for |
|---|---|
| Did the work cover the approved objectives? | Coverage of primary and secondary questions, including partial or unresolved ones |
| How well does the evidence support this conclusion? | Confidence score, its basis, and its decisive limitation for each central insight and the main recommendation |
| What should happen next? | A proposal tied to a finding or gap, with decision value and effort; no invented priority score |

Actual user feedback is separate from all three. A high score does not establish that the user found the answer useful.

## 4. Deliver enough work to answer the brief

The intended delivery starts with the folder, then links the reports and study library, states the conclusion and limitations, explains thematic coverage, and ends the analytical index with the final-conclusion file. A separate inventory accounts for preserved files. Proposed deeper investigations follow the completed cycle; proposals are not executed studies.

Complete research has a planned executive length N, from one to seven pages, and a full-report minimum of 7N analytical pages at comparable density. Raw captures, repeated material, and standalone bibliographies do not supply analytical depth. The full report is integrated before the executive is derived from it.

Pagination must be measured after rendering. Without rendering it remains unverified. Insufficient substance is a partial delivery, even when every link works. The researcher should not pad pages, lower the planned scope to pass, or exceed the mandate. Explicit summaries, simple questions, and delta-only requests stay within their requested scope.

## 5. Let the findings define the next investigation

Each completed cycle ends with proposed deeper investigations derived from its actual findings, contradictions, mechanisms, and gaps. A useful suggestion links to the exact study or recorded limit that triggered it. It states the question, which decision or understanding it could change, what it adds beyond completed work, and the likely effort and access needs. The skill recommends only strong opportunities, with no fixed quota or invented priority score. If none is worthwhile, it should say so.

These proposals are different from agreed work left unfinished. A central source check or correction owed under the current mandate must be completed if feasible or disclosed as outstanding in a partial answer. It cannot be reframed as an optional next cycle. New investigations wait for your selection and any new authorization they require. Silence does not start them.

The [synthetic dossier](../examples/sample-dossier/README.md#next-cycle-proposal) shows the distinction: a transfer test and customer-identity question remain outstanding under the fictional brief; a later decision about retiring the old account is proposed separately because the source says attachment links need an active account.

## 6. Update without making everything look new

An update starts from the existing dossier, confirmed brief, and current conclusions. The name and creation date remain stable; a new cycle records the new work. Prior spending authorization does not renew automatically.

Before replacing the current files, the method requires preservation of the previous published packet. Historical reports should link to the study and source versions they actually used. Current indexes can advance once the new packet is coherent; interrupted work and conflicts remain separate.

Each affected assessment gets a disposition: maintained, strengthened, weakened, replaced/withdrawn, or not revalidated. The update distinguishes an actual event from a newly discovered old fact or a correction of the analyst's earlier error. Finding no change does not automatically increase confidence.

Topic dates matter. An attachment study revisited today does not refresh yesterday's identity-mapping analysis. The [example review](../examples/sample-dossier/05-research-log/2026-10-08-demo/reviews/claim-check.md) illustrates this distinction with fictional content.

These are prescribed behaviors. Cold resume, longitudinal and concurrent updates, and reliably complete default delivery still have open behavioral coverage in [testing](TESTING.md).

## What the Python helper does

The [helper reference](../skill/references/delivery-checks.md) documents commands for the configured library, explicit raw-export capture, preservation of a final handoff from a supplied canonical JSONL transcript, Markdown rendering, inventory freezing, delivery checking, and relative-link PDF derivatives.

The helper does not conduct web research, find hidden host transcripts, judge factual support, or enforce a research budget. Missing optional parsers and unsupported checks must remain explicit partial results. A successful check applies only to the checks performed.

## Preservation has a boundary

The host may expose only part of a conversation, a truncated tool response, or no export. Preserve what is accessible, record the gap, and avoid claiming missing originals were saved. Hidden reasoning is outside the preservation contract. Earlier material already edited can be labeled a post-edit snapshot; it must not be passed off as an original.

Relative links help move a dossier between folders, but supported navigation still needs checking after relocation. A PDF viewer may restrict cross-file links. Custom indexes and unsupported actions require their own validation. The [technical coverage](TESTING.md) describes these limits.

## What leaves your machine

Sherlock uses the model and tools available in your Claude Code session. The brief, queries, source content, and material shared with authorized subagents may be sent to the providers behind those tools. Sherlock adds no separate research provider or outbound content filter. Review the session's tools and the material you supply before researching sensitive subjects.

The dossier is written to the destination you choose; that location may itself be synchronized by your operating system or storage service. The skill does not schedule a refresh, publish the dossier, or authorize sharing. Saving a file does not make earlier model or tool calls local. It also creates no independent backup.

The current beta should be evaluated on the actual research it delivers, with [public evidence and limitations](EVALUATION.md) in view.
