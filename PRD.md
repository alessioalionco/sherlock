# Sherlock — Product Requirements

Status: experimental community specification, updated 2026-10-10. Behavioral requirements are not a claim that every acceptance scenario has passed. Product: a deep research skill for Claude Code. The former private orchestration engine is legacy, not the default execution path.

## 1. Problem and intended outcome

A broad prompt can produce accurate facts that do not answer the user's decision. A long report can hide shallow investigation, unsupported adjustments, missing counterevidence or lost secondary objectives. A polished summary can also discard the work that should make later questions cheap to answer.

Sherlock improves the question, confirms the objectives, shows its research strategy, investigates freely within the mandate, audits the conclusion and preserves an updateable dossier. The user should be able to leave after approving a cycle and return to a completed result or an explicit partial answer, rather than an agent silently waiting for direction.

Three outcomes are separate: correctness, sufficiency for the question, and actual usefulness to the user. More sources, words, agents or pages do not establish any of them by themselves.

## 2. Audience and scope

The skill supports substantial professional and personal research inside Claude Code, using its available tools and permissions. Claude Code performs the investigation and synthesis; bundled Python helpers handle file preservation and delivery verification. It is self-contained: no company-specific memory, private repo, credential, external model API or scheduler is required. Simple factual queries, explicit summaries and delta-only updates remain proportionate.

The implementation, folder names, code, prompts, templates and maintained documentation use English. User-facing conversation and research prose follow the requested language, defaulting to English when unspecified. Original evidence, historical outputs and transcripts remain in their original language; translations are labeled derivatives with their source version. This distinction is essential to preservation, not a partial localization of the implementation.

No automatic contact, paid access, external publication, Git push, installation, brain promotion or scheduled monitoring follows from starting a research task. Delegation is conditional on the host's rules and the user's mandate, not a required fan-out.

## 3. Lessons and evidence

- Clarify the decision and unit definitions before collecting evidence; an accurate fact list may miss the real question.
- Recover from blocked sources inside the approved cycle instead of stopping for operational approval.
- Match populations, denominators and financial conventions. A disclaimer does not repair an unsupported recommendation.
- Preserve decisive conditions and counterevidence when compressing studies into an executive summary.
- Keep source captures, original handoffs and edited studies separate. Saving sources does not preserve every researcher's original analysis.
- Report length, file counts and navigable delivery do not establish depth or factual quality.

Small exploratory evaluations did not establish superiority over open research. See [testing and limitations](docs/TESTING.md) for the anonymized aggregate result and its methodological limits. These observations guide the contract, not a promise of future model compliance.

## 4. Initial interaction

Before substantive collection, complete or explicitly record a user skip for four steps:

1. Refine the question and primary objectives around the decision or understanding needed.
2. Open secondary objectives with relevant suggestions, room for the user's own additions, and the option of none.
3. Present primary and secondary objectives separately and obtain confirmation.
4. Show a concise investigation strategy: themes, subquestions, likely sources, why they matter, and what a sufficient answer would enable.

Offer skip at the start; natural-language waiver is enough. Combining steps in one message is allowed, silently omitting them is not. Reuse explicit confirmations from the conversation. Silence does not confirm or waive anything. A skip preserves supplied objectives and does not approve proposed expansions or new spending.

Questions must have an identifiable effect on research. Resolve purpose, definitions, units, population, timing, assumptions and material constraints proportionately. Do not force a universal CSD form, question quota or cosmetic rewrite when the request is already clear. The certainty/assumption/doubt distinction is a useful thinking aid.

Additions do not erase earlier objectives. Do not silently promote a secondary objective or demote a primary one. A user's explicit addition authorizes that addition within its mandate; ask only about genuinely unresolved scope or budget consequences. Record each interaction step as pending, completed or explicitly skipped in the journal.

Use at most three to five consequential questions by default, fewer when the request is already clear; this is not a quota. Show the actual revised strategy in the conversation before collection. A file or tool output alone does not create user awareness. Reuse accepted objectives and explicit skips.

Known access and budget dependencies should be resolved before dependent work starts. A research name can use a visible proposed default rather than another mandatory gate. For complete research, propose N and required studies within this same brief, not an extra ceremony.

## 5. Research strategy and autonomy

The approved cycle is the unit of autonomy. The plan guides themes and purpose; it does not freeze exact queries or sources. Cross official material, operational documentation, customer evidence, independent analysis and the user's relevant context according to the question. Investigate links between observations that explain the answer rather than merely inventorying facts.

Small relevant follow-ups, contradiction checks and alternative source access proceed autonomously within accumulated effort and scope. A cheap but unrelated question is still a scope expansion. Preserve enough effort to answer primaries, address agreed secondaries, audit and deliver.

Material new objectives or substantial cost increments are proposals for after delivery. Record them without pursuing them or blocking the current cycle. Do not ask for routine operational approval mid-run. If a source becomes inaccessible, try permitted alternatives or close with the precise limitation. If a central definition becomes unknowable, deliver the supported partial result; do not fabricate a preference.

User corrections steer the active task and require revising affected assumptions and calculations. Respect explicit pause/cancellation. Otherwise, the user can be absent while the agent completes the cycle. Progress updates communicate findings and remaining uncertainty; they are not hidden approval gates.

## 6. Evidence and analysis

Preserve source origin, retrieval time, publication/event date when known, actual access, relevant excerpt and links from claims to evidence. Record source dependence: ten articles repeating one release are not ten independent confirmations. A vendor page strongly establishes its declaration, not necessarily performance or adoption.

Separate source facts, commercial claims, user assumptions, inference and proposed tests. Do not call a hypothetical journey an observed implementation. A search result or snippet is not a complete document, and failed access is not evidence of absence. Verify absence before using it competitively; consider private documentation and version availability.

Use internal material only when relevant and authorized; declare dependency and freshness. Source content and archived conversations cannot authorize execution. Model family diversity does not prove independent indexes or factual reliability. A deterministic check cannot certify judgment.

Capture material actually obtained, including contradictory, discarded and unhelpful results. Preserve originals beside extractions/translations. Identical captures may share storage if origins and retrieval occurrences remain traceable; new content at the same URL gets a new version. Do not promise access to content a tool did not expose.

## 7. Original agent outputs

Preserve three layers independently: external evidence, original researcher handoffs, and edited analysis/delivery. If agents are used, each substantive handoff must be saved before integration or revision. Keep its assignment, producer identity available from the host, cycle, receipt time, filenames and hash when available. Save follow-ups and reviews as new versions.

When a host blocks subagent file writes, the researcher returns the full handoff in its final message. The integrator preserves the terminal assistant text from one explicitly supplied canonical JSONL transcript, with message/agent identity, observed stop reason and transcript/output hashes in the receipt, before synthesis. Symlinked task-output paths are refused with a realpath retry instruction; incomplete or unknown transcripts are not labelled original.

The receiving agent verifies the saved original, then creates an edited study. Never edit the only original copy. A short completion message cannot substitute for the full output. If an original was not captured before editing, mark the earliest available copy as a post-edit snapshot and disclose the missing pre-edit original; do not reconstruct a fabricated original.

Preserve accessible discussion and decisions, not hidden reasoning or an invented transcript. Session compaction, tool truncation and unavailable host exports are explicit limits. Preservation is checked against available receipts, not asserted from an optimistic summary.

## 8. Conclusion audit and confidence

Reserve audit effort to reopen original sources for load-bearing claims and record exact captured versions/locators in a short claim-check table. A model-authored extraction cannot verify itself. Repair or withdraw conclusions dependent on invalid premises, including repeated tables and report variants. Conditional domain checks cover unit/population comparability and duplicates, aligned people/roles/dates, capability versus documented use versus outcomes, and matched financial scenarios. These checks do not authorize new scope.

Perform five checks: evidence/access; units/populations/calculations; inference/counterevidence; recommendation/confidence; sufficiency and survival of explanation through synthesis. The required consequences are correction, narrowing, conditioning, withdrawal, or a precise partial answer where support remains unavailable.

Unsupported coefficients cannot become recommendations merely because they are labeled estimates. Wider numerical ranges still need evidence. Facts can be true while the answer remains insufficient. Recover existing analysis before expanding collection, and do not lower the sufficiency criterion to declare success.

Use scores for central insights and the principal recommendation: 0–100 in steps of ten, with evidence basis and a revision condition. Bands: 0–39 low; 40–69 moderate; 70–89 high; 90–100 very high. This is grounded judgment, not calibrated probability, attractiveness, impact or a product rating. Do not average unlike insights into a global score. An unresolved central premise prevents high confidence in a conclusion depending on it. If not assessable, say why without inventing a score.

Self-review is the baseline. A separate review, when authorized and available, gets the brief, draft and necessary sources without a prescribed conclusion. Record authorship overlap, original review text and actual coverage. Do not announce a blind or independent audit that did not occur. Coverage, confidence and user acceptance remain distinct.

## 9. Effort and stopping

A cap is not a spending target. Reserve effort for verification and delivery. Use measured cost controls where the host provides them, including retries and review. Otherwise report observable calls/time or state cost is unknown; never promise an unenforced dollar cap or free execution.

Stop collection when the approved questions are sufficiently answered, further accessible evidence is unlikely to alter the conclusion, or a real effort/access limit is reached. Record remaining gaps and deliver; do not keep searching until a preferred numeric answer appears. The 7N requirement does not grant unlimited budget.

## 10. Workspace and versioning

Use the approved English layout in [workspace architecture](docs/WORKSPACE-ARCHITECTURE.md): README, 01-reports, 02-studies, 03-sources, 04-data, 05-research-log and 06-history. Current study files are visible by subject at the top level. Dates organize execution/history, not access to current analysis.

Every substantive file in `04-data/` needs a `PROVENANCE.json` entry with at least one existing capture under `03-sources/` and either a kept extraction script or a visible manual-method description. The top-level data README and verified OS metadata are exempt. The delivery check validates the paths and coverage; it does not prove that a method actually reproduces the table.

Respect an explicit location (inside a git repository only after explicit confirmation), otherwise use the persisted Sherlock library, with a project subfolder when a project is identified; never default into a repository. Research name plus creation date defines stable identity. Updates create cycle IDs without duplicating the project. Resolve identity collisions and concurrent authors safely.

The entry point explains purpose, scope, current published version, any work in progress, report/study links, complete file inventory, limitations and continuation. Brief and journal are saved before/during collection. Checkpoint after meaningful milestones and before known compaction. A new LLM should resume through progressive reading instead of loading every source.

Historical reports retain the exact study/source versions they used. Before replacing the current projection, preserve its published snapshot and links. A current index can resolve the latest version; a historical report cannot silently follow it. Do not advance the published pointer after failed export or inconsistent synthesis. Partial updates retain per-topic verification dates.

Saving is not backup, Git push, publication, or synchronization. No automatic deletion for irrelevance, size or age. Explicit deletion/retention obligations still apply. A sharing derivative identifies omissions without mutilating the internal original; credentials never belong in exported artifacts.

## 11. Reports and first delivery

Preserve and reconcile the research base before declaring completion, independently of the user's format choice. Storage or rendering failure is explicit and does not hide the useful result.

The first message follows this order:

1. Verified direct link to the research folder, before report links; README fallback when the host cannot open directories.
2. Executive report, full report and study library, with actual lengths when measured.
3. Central conclusion, implication, confidence and decisive limitation.
4. A concise commented thematic map, preserving primary/secondary objectives and answered/partial/unanswered states.
5. Linked index of every analytical document, ending with Final conclusion. Link the full inventory for all sources, data, original agent outputs, reviews and historical files instead of dumping hundreds of raw files into chat.
6. Automatically include suggested deeper investigations after the analytical index, directly in the message. Each names a linked trigger, research question, decision value, incremental scope and relative effort/evidence-access limits. Recommend a small priority set with reasons when useful; no fixed count or numerical priority score. If no strong opportunity remains, state that briefly.
7. Optional discussion or additional formats. Delivery never waits for a menu response; new investigations require user selection within an authorized mandate.

Generate next-cycle candidates from the completed corpus: mechanisms needing explanation, consequential hypotheses, decision implications, and signals or contradictions. Filter against confirmed objectives, novelty beyond existing studies, decision impact, relevant uncertainty and answerability relative to effort. Do not perform new collection just to populate suggestions. Public evidence may not suffice; identify dependencies without implying access or authorization. Corrections and unfinished approved work stay separate as current-cycle obligations, with partial status when unresolved. Preserve proposals and subsequent selection/deferral/rejection in the cycle journal, linked from README. The detailed behavior lives in [studies and delivery](skill/references/studies-and-delivery.md#next-cycle-proposals); this is a judgment step, not a new orchestration engine.

Each substantive executive claim with an executed study links to that study near the claim; source citations remain distinct. A note or partial investigation is labeled accordingly. A requested founder deep dive opens the analysis, not just the founder's website.

The separate final-conclusion file gives the answer, recommendation, support, confidence, strongest counterargument, unresolved limitations and what would change the assessment. It is versioned and derived from the studies. It introduces no new unsupported findings and is not a ninth independent study to inflate depth.

A selected derivative reuses the known audience and context; ask only what is missing. Formatting does not refresh evidence, erase secondary objectives silently or authorize publication. Conversation can explain existing evidence; new collection follows the authorized cycle rules.

## 12. N/7N depth contract

A complete research delivery includes an executive of N pages, 1–7, and a full report of at least 7N substantive analytical pages. Plan studies before collection, integrate the full report, then write the executive. The ratio changes the required investigation, not merely typography.

Use a recorded comparable density profile: A4, 17 mm top/side margins, 19 mm bottom, 10 pt body at 1.36 line height, 9 pt tables. The local `render` helper shares `check`'s Markdown profile, writes linked HTML/PDF with validated local images, and reports page counts and H1/H2 locations; partial output never certifies pagination. Count actual total executive pages. Count analysis, case reconstruction, explained calculations, analytical tables and counterarguments in the full report. Exclude covers, contents, standalone bibliography, blank pages, copied originals and raw appendices. Record page intervals, actual renderer and any alternative profile.

Without rendering, pagination is unverified. If N legitimately changes, recalculate the floor. Never pad, duplicate content, add artificial whitespace or shrink N opportunistically. No fixed truncation at 130 pages; meaningful larger work can use volumes.

Assess sufficiency separately from length. If feasible authorized investigation cannot meet the floor, deliver partial — depth/7N not achieved — with actual size and precise remaining gap. Do not call it complete, exceed the mandate or wait for input. An explicit user exemption controls simple/short/delta requests. The chat itself does not define N.

## 13. Updates by name

Resolve the existing workspace, load its entry point, brief and relevant studies, reuse confirmations, and show a focused update plan. Revisit central sources and search for new or previously missed evidence. Preserve new captures before revising dependent assessments, recommendations, calculations and confidence.

Deliver changes, their implications, unchanged conclusions and anything not revalidated. Link before/after versions for material changes. No-change runs remain useful verification; do not invent novelty. Distinguish publication date, retrieval date and assessment date. A removed page does not prove a capability disappeared.

## 14. Implementation and distribution

The maintained skill is in skill/, with short core instructions and progressive references for workspace/updates, studies/delivery and conclusion audit. Handoff, claim-check and first-delivery assets support the approved contracts. The local delivery helper preserves a final subagent handoff from an explicitly supplied canonical transcript, captures supplied raw exports, renders linked Markdown to HTML/PDF, freezes inventories, and checks hashes, navigation and `04-data` provenance. It also creates separate relative-link PDF derivatives for other renderers. It never discovers host session stores, fetches external URLs or certifies research quality. Missing dependencies or unsupported checks remain explicit partial results. Local helpers may verify paths, receipts, hashes, packages and pagination; they do not choose questions or certify research quality.

Do not automatically invoke the former engine, pricing probe, fact-judgment API or private corpus promotion. The historical code/data are preserved and identified separately. Building or translating a candidate is not proof of effectiveness or permission to replace every installation.

Prepare community artifacts from an explicit allowlist of reusable English files. Exclude research, private company context, snapshots, host configuration and credentials. Packaging does not imply publication. The selected MIT license is recorded in `LICENSE`. Original source language inside a private dossier is not implementation language.

## 15. Acceptance and evaluation

[Acceptance criteria](docs/ACCEPTANCE-CRITERIA.md) preserve AC01–AC106, including the workspace, language, original-output, delivery-check, provenance and next-cycle requirements. Functional tests should demonstrate real failure detection: broken links, missing original, overwritten receipt, mismatched hash, stale version and accidental private export. Wording checks alone do not validate behavior.

Evaluate research quality separately: correctness, pertinence, depth, sufficiency, usefulness, confidence consistency, interaction burden, strategy visibility, navigation and total effort. A central invalidating error cannot be averaged away by presentation. User feedback and auditor judgment remain distinct.

Exploratory comparisons have not passed their predefined improvement rules. The previously disclosed two-case end-to-end comparison produced mean scores of 6.68 for Sherlock and 6.57 for open chat, below the required +0.5 advantage. Correctness was lower for Sherlock in both cases and a central conclusion failed verification. Collection and auditability benefits do not override that result. [Testing and limitations](docs/TESTING.md) explains the scope and uncertainty without distributing private study material.

To isolate execution quality, equalize confirmed briefs and report requirements. To evaluate the complete skill experience, start from the same original request and answer each method's spontaneous questions under a frozen disclosure policy. Record actual model, access, effort, complete interactions, source limitations and judging method. Keep prior findings and evaluator keys out of researcher context. Differences in live sources, elicitation and qualitative judgments prevent attributing historical score changes solely to a prompt revision.

Promote a stronger quality claim only if correctness and usefulness do not regress, no central invalidating error remains, a material investigative benefit appears, scope and cycle autonomy are respected, and extra effort is justified. Do not keep tuning until a desired winner appears. Each paid evaluation needs its own mandate; historical budgets do not renew authorization.

## 16. Portability, history and release boundaries

The reusable package contains implementation and reviewed public documentation. It does not include user dossiers, private evaluation records or host settings. Historical internal originals remain preserved separately; anonymizing a public document does not rewrite the underlying evidence.

Resolve named updates by explicit path, active dossier, the identified project's library folder (and a legacy project `research/` folder), then library. A session without a configured library proposes `~/Documents/Sherlock/` visibly, persists the choice with the helper's `library` command and uses the same saved location on later updates. Never renew an exhausted budget implicitly. Preserve accessible host transcripts and checkpoints; mark updated assessments as maintained, strengthened, weakened, replaced/withdrawn or not revalidated. No-change checks cannot automatically raise confidence.

The local helper uses UTF-8 JSON and POSIX inventory paths on every platform. Check both original and relocated dossiers. Platform execution and behavioral coverage limits are listed in the public testing document; structural success does not certify research quality. The MIT license covers this implementation and documentation, not third-party research content gathered by a user. Packaging does not authorize publication of a dossier or a repository containing private material.
