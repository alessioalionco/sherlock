# Studies, report depth, and first delivery

## Plan for an answer, not a page count

Define what the user should understand or decide, and map primary and secondary objectives to themes and researchable questions. Explain why source types matter: official pages establish declared scope, operational documentation explains mechanisms, customer discussion may expose conditions, independent analysis can test an interpretation. An announced research route is not a source already consulted.

For complete research, plan an executive of N pages (1–7) and a full report of at least 7N analytical pages. Record the intended studies and feasible effort within the mandate. N is a proposed planning choice, not another mandatory user gate. If access or budget cannot support this contract, resolve the known mismatch before dependent work. The ratio does not authorize unlimited research.

Investigate and write studies first; integrate the full report; derive the executive last. Do not inflate a short finished report into a supposedly deep one. There is no arbitrary 130-page truncation ceiling: useful content may span volumes without duplication.

## Study contract

A substantive study includes stable ID, descriptive title, question and purpose, primary/secondary objective relationship, entities/aliases, coverage status, source-verification date, analysis date, version and producer when known. Its body provides a direct answer, developed evidence and explanation, alternatives, implications, confidence, limits and observable revision conditions. No empty schema is required where prose is clearer.

A study earns a deep-dive link by adding understanding beyond the executive. Label short notes, partial analyses and uninvestigated topics accurately. Sources are not studies. Shared evidence can serve several themes without being duplicated or counted as independent. Integrate contradictions across studies; do not merely concatenate unrelated manuscripts.

Keep factual claims separate from analytical reconstructions or proposed tests. A diagram of how a journey might work is not an observed customer implementation. Every material conclusion in the executive that has a completed study links to that study near the claim. A source link opens original evidence; a study link opens the researcher's analysis. Never substitute one for the other without labeling it.

## Confidence and coverage

For central conclusions, score in steps of ten: 0–39 low, 40–69 moderate, 70–89 high, 90–100 very high. Give the evidence basis and the gap or counterevidence that could change it. Confidence is not a statistical probability, product quality score, impact estimate or average of unlike claims. A score cannot rescue an invalid recommendation.

Coverage is answered, partial or unanswered by objective. Proposed expansions are **not investigated**, not unanswered research or negative findings. User usefulness is established by feedback, not by an auditor's score or silence. Keep these dimensions separate.

## Measure consistently

Default comparison profile: A4, 17 mm top/side margins and 19 mm bottom, body 10 pt at 1.36 line height, tables 9 pt. Use `delivery.py render ROOT DOC.md [DOC.md …]` as the default local renderer; its JSON reports pages, H1/H2 locations, dependency versions and the profile. If it refuses because a named table lost text, fix the presentation, not the check: split, transpose or narrow that table in text you authored, or, when the table belongs to a preserved original embedded in a compiled report, replace the embedded copy with a short narrowed version marked as such plus a link to the original file. Never edit the original. Render again until it passes, or deliver an explicit partial. Record any authorized alternative and use comparable density in both documents. N is the actual total executive PDF pages. The full report counts substantive analysis, reconstructed cases, explained calculations, analytical tables and counterarguments.

Exclude covers, table of contents, standalone bibliography, empty pages, transcribed originals and raw appendices. A mixed page counts only when analysis is its principal content. Record page intervals and actual renderer/profile. No rendering means **pagination unverified**. Actual N changes the required minimum; do not shrink it opportunistically to pass a shallow result.

Verify depth separately from length. Each section should contribute evidence, a relevant distinction, explanation, reconstruction, calculation or counterargument. Repeated disclaimers or copied chapters do not constitute depth. If viable authorized work still cannot meet the requirement, deliver **partial — depth/7N not achieved**, with actual size, reason and remaining gap; do not call it complete. A factual limitation on one topic does not automatically invalidate a sufficient overall report.

Simple questions, explicitly requested summaries and delta-only updates retain their scope. A full-research exemption comes from the user's request or explicit waiver, not from the agent wanting to pass an inadequate report.

## Delivery order

Use the first-delivery asset as a structural guide, in the user's language:

1. Research-folder link first, verified to exist; provide README fallback for hosts that cannot open directories.
2. Executive, full report and study-library links with measured lengths or honest missing-format labels.
3. Central conclusion, practical implication, confidence and decisive limit.
4. Concise thematic map with findings, primary/secondary objectives, coverage and links.
5. Linked index of all analytical documents, ending with the **Final conclusion** file. Include a path to the full file inventory for raw sources, data, original handoffs and reviews.
6. Automatically show suggested deeper investigations, following the next-cycle guidance below. Present the suggestions in chat, not only behind a file link.
7. Optional discussion or derived format. Do not hold the results for a menu response.

The final-conclusion file answers the main question and consolidates the recommendation, basis, confidence, counterargument, unresolved limits and events that would change the assessment. It is dated and linked to the studies it synthesizes. It introduces no new unsupported research and is not another independent study to multiply page counts.

## Next-cycle proposals

Include this block in the first delivery of each research cycle, after the analytical index. Derive candidates from the completed corpus: an observed mechanism needing explanation, a consequential hypothesis needing a test, a finding whose decision implications remain unclear, or a signal/contradiction warranting further investigation. These are reasoning aids, not mandatory categories. Do not start fresh collection merely to generate suggestions.

Filter candidates by the user's confirmed objectives, the decision or understanding they could change, what they add beyond existing studies, and the feasibility of obtaining a useful answer. Merge overlapping questions. Prioritize decision impact, relevant uncertainty and answerability relative to effort; use plain-language judgments, not a numerical score implying calibration. Offer only strong opportunities, with no fixed count. If none survives, say so briefly rather than manufacture a list. Keep explicit short-answer or derivative requests proportionate.

For each suggestion, show a concise title and:

- **Trigger:** the finding, contradiction or gap that prompted it, with a link to the exact study/section or recorded limitation.
- **Question and value:** what to discover and which user decision or understanding it could change.
- **Increment:** what the new investigation adds beyond what is already known.
- **Feasibility and effort:** likely evidence route, small/medium/large relative effort with a reason, and material access dependencies. State when public research alone is unlikely to answer; do not imply interviews, paid access or hands-on testing are available or approved.

Use compact numbered entries, as in a research handoff, rather than a generic topic menu. End with a small recommended subset and its rationale when prioritization is useful. Keep unresolved hypotheses explicit; a proposal is not a finding or an already executed study. Proposal priority is distinct from conclusion confidence.

Corrections, routine verification and missing work already owed under the current mandate are not optional expansions. Repair them within the mandate or identify them separately as outstanding current-cycle work in a partial delivery. Do not conceal them in this list or require approval merely to fix an error. Material new scope or cost remains a proposal for a subsequent cycle; finish the approved delivery without waiting and execute only after user selection within an authorized mandate. Silence does not authorize continuation.

Preserve the delivered proposals and their linked rationale in the current cycle's journal, with a pointer from the dossier README. Record subsequent selection, deferral or rejection without erasing the original proposal. This reuses the existing workspace; it does not require a new scheduler, scoring engine or folder type.

## Export and navigation

Keep Markdown/HTML links relative within a portable dossier. Freeze report-to-study references to the versions used. Keep readable study ID/title/page in PDFs; use working internal or relative cross-file destinations when supported, and offer the HTML library when a PDF viewer blocks them. Check targets after moving the package, not only on the author's machine.

Run the [delivery checks](delivery-checks.md) on the frozen packet and a relocated copy. Sherlock's renderer writes relative PDF file destinations and embeds validated local images; still inspect the actual PDF and its page intervals. Other renderers may turn relative HTML links into absolute machine paths inside the PDF; a successful Markdown check cannot certify those links. Produce a new portable derivative when the helper supports the link type, retaining the original. Missing dependencies, unsupported destinations or failed export remain explicit limitations. Link the usable Markdown/HTML version and deliver a partial export without waiting for another user response.

In conversation, resolve links from the host's actual working directory or use verified absolute local links. A file-relative link that works in a report may fail when pasted into chat. In the portable files themselves, keep relative targets.

Do not alter the source capture to make a link work. Preserve the old publication and create a new export or migration derivative. Any shared-copy omissions are explicit. A selected format does not authorize external publication.

## Post-delivery requests

Conversational explanation and reformatting reuse the existing corpus. Clarify only missing audience, depth, format or destination necessary for a requested derivative. New formatting does not refresh evidence. A question requiring new evidence is either a correction still owed or a new authorized cycle; do not confuse it with an already executed study.
