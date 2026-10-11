---
name: sherlock
description: Deep research for Claude Code with a refined brief, explicit primary and secondary objectives, autonomous investigation, evidence-based conclusions, and a preserved, updateable research workspace. Use for deep research or updating an existing dossier; keep simple factual questions and requested summaries proportionate.
---

# Sherlock

Sherlock is a deep research skill for Claude Code. Improve the question, investigate openly, audit the conclusion, and deliver a workspace the user can browse or hand to another researcher. Conduct the research with Claude Code's available tools and permissions. Bundled Python helpers support file preservation and delivery checks; the skill uses the existing Claude Code setup without a separate research engine, model API, company memory service, or scheduler.

The reusable instructions, code, identifiers, templates, and directory names are English. Dossier file and directory names also stay English when report prose uses another language. Conversation and report prose follow the user's requested language; default to English otherwise. Preserve source material in its original language. Never silently translate an original in place.

## 1. Establish the research mandate

Read the request and already-confirmed context before asking anything. Explain that the user can skip all or part of briefing. Complete or record an explicit user skip for each step:

1. Refine the question and primary objectives: what does the user need to understand or decide? Clarify definitions, units, population, timing and material assumptions only when they change the investigation.
2. Ask about secondary objectives, offering relevant suggestions and allowing the user's own interests or none. Suggestions are not approved objectives.
3. Show primary and secondary objectives separately and obtain confirmation. Reuse confirmations already present; do not repeat them. Silence is not confirmation or skip.
4. Show a short research strategy: themes, subquestions, likely source types, what they can establish, and the criterion for a sufficient answer. Distinguish optional expansions from the approved scope.

These steps may share a message but none disappears silently. Record each as pending, completed, or explicitly skipped in the research journal. A user correction updates dependent work and does not erase earlier objectives. Resolve known access, cost and scope decisions before the dependent research begins. A skip does not authorize new spending, tools or publication.

For an underspecified request, usually start with 3–5 consequential questions, combining related choices. This is a useful default, not a quota: an already clear brief needs fewer. Offer a short selection of secondary objectives instead of a long questionnaire. After answers materially change the brief, show the **actual revised strategy in conversation before collection**; a plan saved in a file or printed in tool code does not provide user awareness. Reuse existing approval and continue without adding another gate.

For complete research, plan executive length N (1–7 pages), full-report minimum 7N, and studies that need their own investigation. Prioritize questions, not equal page allocations. Read [studies and delivery](references/studies-and-delivery.md). Keep simple questions, explicit summaries and delta-only updates within their requested scope.

## 2. Establish the workspace

Read [workspace and updates](references/workspace-and-updates.md) before creating or resuming research. Respect an explicit destination; if it lies inside a git repository, say so and write there only after the user explicitly confirms. Otherwise use the user's Sherlock library, in a project subfolder when a project is identified; never default into a repository. The [delivery helper](references/delivery-checks.md#sherlock-library)'s `library` command shows it; if it is unset, propose `~/Documents/Sherlock/` visibly and persist the user's choice with `library --set PATH`. Use the research name and creation date; propose a visible default if the user has not supplied a name, without another mandatory approval gate.

Create only directories with a clear purpose. Save the brief before collecting, evidence after receiving it, and the journal at useful checkpoints. Keep current reports in `01-reports/` and actual study files in `02-studies/`. External evidence belongs in `03-sources/`; original agent handoffs belong in `05-research-log/<cycle>/original-agent-outputs/`. They are different kinds of original. Every file in `04-data/` (except its top-level `README.md` and OS metadata) needs an entry in `04-data/PROVENANCE.json` naming its source captures (at least one in `03-sources/`) and its method: the extraction script, kept in the dossier, or a description of manual work. The delivery check fails without it.

If delegation is permitted by the host and mandate, use the [agent handoff instructions](assets/agent-handoff.md). Give the user's own product a dedicated research front or an explicit share of a front when the task compares it with another product. On hosts that block subagent file writes, the researcher returns the complete handoff as its final message and the integrator preserves it with `delivery.py handoff` before editing or synthesizing. Preserve every accessible substantive handoff and review. Do not claim a transcript or original draft exists unless it was actually saved. Report capture failures and limits explicitly.

## 3. Investigate within the approved cycle

An approved cycle runs through delivery without waiting for intermediate user input. Follow relevant leads, reconcile contradictions, look for counterevidence, and change sources autonomously within the mandate. A blocked page is an operational issue, not a reason to pause for direction. Use authorized alternatives or finish with a precise partial answer.

For each decisive question, follow broad discovery into the concrete evidence that can answer it: a worked technical example, an individual observation or an actual implementation. Read the surrounding conditions as well as the matching passage. Prioritize unresolved questions that could change the answer over adding more themes or repeating overview sources. Keep useful findings in the studies as they emerge; these operational choices need no new user gate.

Material new objectives or cost expansions discovered during research go into the next-cycle proposal after delivery. Do not silently execute them. User-initiated scope changes carry the authority of that request; preserve existing work and clarify only a genuinely unresolved dependency. Respect explicit pause or cancellation.

Separate facts, vendor claims, user assumptions, calculations and inference. Archive accessible outputs with source, retrieval date, event date when known, access level and stable identity. An excerpt is not a full document. Repeated coverage of one announcement is not independent corroboration. Search for a capability before claiming it is absent; failed access is not negative evidence.

Write substantive studies while investigating. Each has a question, answer, evidence, explanation, counterevidence, implications, confidence, limits and revision conditions. A folder full of source captures is not a library of studies. Do not create one study per URL or fabricate intermediate analyses retrospectively.

## 4. Audit and close

Read [conclusion audit](references/conclusion-audit.md). Reconcile important numbers, units, samples, dates, claims and implications. Verify that the explanation answers the brief and survives synthesis. Correct or withdraw unsupported conclusions; adding a disclaimer does not repair an invalid recommendation.

Reserve effort to reopen original sources for the claims carrying the recommendation. Record their evidence, verification and actual disposition using the [claim-check template](assets/claim-check.md). Checking a generated extraction against its own summary is not original-source verification. When a decisive premise fails, repair or withdraw the dependent claim across studies, tables and conclusions before assigning confidence.

For central insights and the main recommendation, use a confidence score in steps of ten with a short basis and decisive limitation: 0–39 low, 40–69 moderate, 70–89 high, 90–100 very high. This is evidence-based judgment, not a probability, impact rating or product score. If not assessable, say why rather than invent a number. Keep objective coverage, confidence and actual user feedback separate.

Reconcile files with the inventory, preserve original handoffs, validate links and versions, integrate the full report, then derive the executive and final conclusion. Verify N/7N after rendering at a comparable density; use `delivery.py render` as the default local renderer and inspect its page/heading report. Missing evidence or insufficient depth produces an explicit partial delivery; do not pad pages, reduce N opportunistically or exceed authorized cost. Without a renderer, label pagination unverified.

For local artifacts, use the [delivery helper](references/delivery-checks.md) to preserve final host handoffs, capture supplied exports, render Markdown, freeze an inventory, check hashes and destinations, and repair PDFs made by other renderers when needed. Missing parsers or failed checks mean unverified/partial export, not technical approval. Inspect the report's factual argument separately; a successful script cannot approve it.

Deliver in this order, using [the first-delivery template](assets/first-delivery.md):

1. A direct, verified link to the **research folder**, before report links. Include `README.md` as a fallback if directories cannot open in the host.
2. Executive, full report and study-library links, with measured lengths when available.
3. The central conclusion, confidence, practical implication and decisive limitation.
4. A concise thematic explanation preserving primary and secondary objectives and partial coverage.
5. A linked index of analytical documents, with **Final conclusion as the last analytical file**. Link the full inventory for every source, data file and execution record; do not dump hundreds of raw files into chat.
6. Suggested deeper investigations, automatically included using the [next-cycle proposal guidance](references/studies-and-delivery.md#next-cycle-proposals). Tie each to a linked finding or gap, a question, decision value, incremental scope and effort/access limits. Recommend a small priority set; use no fixed quota or numerical ranking. If no strong opportunity remains, say so briefly. Proposals are not executed research or approved scope.
7. Optional conversational exploration or other formats. The completed cycle does not wait for a menu response; new investigations require user selection within an authorized mandate.

The final-conclusion file is a dated synthesis of the studies: answer, recommendation, confidence, limitations and what would change the assessment. It adds no unsupported claims and is not another independent study counted toward depth.

For “update this research,” resolve the existing workspace, reuse its confirmed brief, create a new cycle and revisit sources and assessments. Do not create a duplicate project or imply every topic was reverified. Preserve historical versions and use a consistent latest-delivery pointer only after the new packet is checked.

Saving does not authorize publishing, pushing, contacting people, buying access, installing services or sharing private material. Report observable cost and preservation limits honestly.
