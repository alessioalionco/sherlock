# Research assignment and original handoff

Use this instruction when delegation is authorized. Fill the assignment from the confirmed brief; do not invent a new objective, budget, provider or authority.

## Assignment

Record: cycle ID, subject, primary/secondary objectives served, specific questions, relevant existing evidence, allowed tools/access, effort limit if observable, required outputs, destination and known limitations. If comparing a third party with the user's own product, give that product a dedicated front or an explicit share of this front's effort and evidence. Avoid sharing unrelated private context. Do not allow nested delegation unless separately authorized.

## Researcher instructions

Investigate the assigned questions, including counterevidence. Distinguish facts, source claims, inference and proposed tests. Preserve every accessible source/tool return and its actual access level. Keep rejected material with its disposition.

If the host permits subagent file writes, write the complete substantive Markdown output under `05-research-log/<cycle>/original-agent-outputs/<subject>/`. Include a source index and limitations. This is the original handoff: do not replace it after review. Save follow-up corrections as new files with a sequence or version. On hosts that block subagent file writes, including Claude Code, return the complete handoff as your final message. State that you could not save it yourself so the integrator can preserve that exact final text before synthesis.

Return the file paths, scope actually covered, strongest findings, confidence with basis, unresolved questions, and what was not preserved. A short completion message does not replace the substantive file.

## Integrator instructions

On a host that blocks subagent writes, take the explicitly supplied canonical `agent-<id>.jsonl` transcript and run `python3 SCRIPT handoff ROOT TRANSCRIPT 05-research-log/<cycle>/original-agent-outputs/<subject>.md --origin "<assignment and producer>"` before reading it for synthesis. A `tasks/<id>.output` path may be a symlink: the command refuses it and reports the real path to pass explicitly on retry. It takes every text block of the terminal assistant message and records the observed stop reason, including null; a trailing transcript entry, missing final text or tool request within that message fails. Do not search the host session store. The optional raw transcript can be preserved separately with `capture` only when scoped and authorized.

Verify original files and receipts before editing. Keep the assignment, producer identity available from the host, receipt time, paths, versions and file hashes. Do not infer the model identity. Preserve accessible substantive follow-up messages and reviewer outputs separately.

Create the edited study under `02-studies/`, linking its lineage to the original handoff and sources. Integrate corrections there; do not overwrite the original. If only a post-edit copy exists, label it accordingly and record the missing pre-edit version. Never reconstruct a supposed original from the final report.
