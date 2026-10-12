# Sherlock

**A sharper question. A traceable answer. The next investigation.**

Sherlock is a deep research skill for Claude Code. It helps turn a broad request into an agreed research brief: the main question, primary and secondary objectives, and a strategy for finding a sufficient answer. After the approved investigation, it delivers the analysis, rates its confidence in central conclusions with reasons and limits, and, when worthwhile, proposes next questions grounded in the findings and gaps it uncovered.

A long report can still answer the wrong question. An interesting lead can quietly become an unapproved objective. A promising conclusion can lose the counterevidence that limits it. Sherlock makes those choices visible: you confirm the scope, Claude Code follows relevant leads within it, and the answer states what is supported, partial, or still unresolved. The dossier keeps the studies and available evidence linked so you can inspect the reasoning and return to it later.

Claude Code does the research using the tools and permissions in your session. Local Python helpers preserve supplied files, render reports, and check parts of the delivery. The research method is written instructions for the model; those helpers cannot certify the answer.

**Experimental beta.** The previously disclosed two-case comparison did not establish a consistent advantage over open research. Correctness was lower for Sherlock in both cases. Use the dossier to inspect the work, and review consequential conclusions yourself. See [evaluation and limits](docs/EVALUATION.md).

## What Sherlock adds to a research cycle

- **A clearer mandate.** Sherlock asks what you need to understand or decide, clarifies consequential definitions, and shows a research strategy before collecting. You can explicitly skip part or all of the briefing.
- **Primary and secondary objectives kept distinct.** It suggests useful adjacent questions before the run; you decide which become objectives. It tracks their coverage separately, so an attractive side topic does not displace the main question.
- **Relevant fronts pursued within the approved scope.** Claude Code follows leads, changes sources when a page is blocked, reconciles contradictions, and develops substantive studies while investigating. Delegation depends on your host and mandate; Sherlock does not promise a fixed agent fan-out.
- **A conclusion challenged against its evidence.** The method asks for decisive claims to be reopened in original sources, with counterevidence, limits, and corrections reflected in the answer. An unsupported conclusion should become a narrower or partial answer.
- **Confidence you can question.** Central insights and the main recommendation receive a confidence score from 0 to 100 in steps of ten, when assessable. Each score comes with the evidence behind it and the decisive limitation that could change the judgment. It is an assessment of support, not a calibrated probability or a grade for the entire report.
- **Next investigations grounded in this cycle.** When strong opportunities remain, delivery suggests a small set of deep dives, each tied to a finding or gap, the decision it could change, what it adds, and its likely effort or access needs. They are proposals; you choose whether to start another cycle.
- **A dossier you can inspect and update.** Reports, studies, source captures, available original handoffs, and dated revisions remain linked. An update distinguishes changed topics from topics that were not reverified.

These are instructions and delivery requirements, not a guarantee that every run will fulfill them. A run may fall short and must identify its partial coverage. File counts, report length, and successful checks do not prove that the investigation was good.

## See the shape of an answer

Suppose the question is: *Can we move our support history to a new help desk without losing attachments?* The brief separates that primary objective from customer identity mapping, an agreed secondary objective. It also records what evidence would make the attachment answer sufficient.

In the [synthetic sample dossier](examples/sample-dossier/README.md), a fictional export guide supports a narrower conclusion: the export lists attachment links, but does not establish that the files themselves will transfer. The sample records the correction, leaves customer identity explicitly not reverified in the update, and proposes a separate next investigation into access after the old account closes. That proposal is linked to a source condition and is not treated as executed research.

Follow the chain: [executive answer](examples/sample-dossier/01-reports/executive.md) → [study](examples/sample-dossier/02-studies/01-attachment-portability.md) → [source text](examples/sample-dossier/03-sources/fictional-export-guide.md) → [review](examples/sample-dossier/05-research-log/2026-10-08-demo/reviews/claim-check.md).

Every part of that example is fictional. It demonstrates navigation and editorial form, not research quality, a real run, or a complete dossier. It deliberately assigns no confidence score to invented evidence; a real conclusion gets a reasoned score only when there is a basis to assess one.

## Is this useful for your question?

Sherlock fits an ambiguous, consequential question that benefits from a defined scope, several research fronts, an auditable synthesis, or a follow-on cycle: a vendor comparison, a technical investigation, a market question, or a personal decision. It asks you to define what an adequate answer would let you understand or decide.

A quick factual question or an explicitly requested summary should stay small. The skill instructs Claude Code to keep those requests proportionate. Substantial research costs more attention and model usage; choose it when the question, analysis, and possible next steps warrant that effort.

## Install

Requirements: **Claude Code and Python 3.9+**. Research access depends on your session's browsing, download, and other available tools. Sherlock requires no separate research engine, database, or additional model API key.

From the Sherlock repository or extracted package, copy the **entire** `skill/` folder into your Claude Code project's `.claude/skills/sherlock/` directory. Include its references, assets, scripts, and license. Preserve any existing customization before replacing an installation.

For a first installation, run this from the destination project, replacing the source path with your extracted Sherlock folder:

```bash
mkdir -p .claude/skills
cp -R /path/to/sherlock/skill .claude/skills/sherlock
```

Then invoke `/sherlock` in Claude Code. The other package files are documentation, tests, and contributor tooling. There is no plugin marketplace installation in this flow.

Core helper checks use Python's standard library. Optional **Markdown** and **PyMuPDF** dependencies enable specific navigation checks and rendering; missing dependencies leave those checks or exports partial. Runtime validation currently covers macOS. Native Windows, Linux, and other skill hosts are not cleared. Details are in [testing](docs/TESTING.md).

## Start a dossier

```text
/sherlock Research whether our current help desk can export everything we need
for a migration. Focus on ticket history, attachments, and customer identity.
Separate documented capabilities from anything we would need to test.
```

The skill asks Claude Code to refine the primary question, offer secondary objectives, confirm both lists, and show a research strategy with a sufficiency criterion. You can explicitly skip all or part of the briefing. Earlier answers and confirmations should be reused; suggested secondary objectives are not automatically approved.

Once the cycle is approved and known dependencies are resolved, the instruction is to investigate through delivery within that mandate. Relevant new leads can change the source route without another approval wait. Blocked pages should lead to authorized alternatives or a precise partial answer. Material new objectives belong in a proposal after delivery.

On first use, Sherlock proposes `~/Documents/Sherlock/` as your library and saves your chosen location. You can inspect or configure it with the installed helper:

```bash
python3 .claude/skills/sherlock/scripts/delivery.py library
python3 .claude/skills/sherlock/scripts/delivery.py library --set ~/Documents/Sherlock
```

The configuration normally lives at `~/.config/sherlock/config.json`; `SHERLOCK_CONFIG` can override that location. A library inside a git working tree is refused. An explicit research destination takes precedence; using one inside a repository requires explicit confirmation. Nothing schedules updates or publishes research automatically.

To revisit existing work:

```text
/sherlock Update the research at ~/Documents/Sherlock/help-desk-migration-2026-10-01.
Recheck attachment portability. Keep the other topics marked as not reverified.
```

The same dossier keeps its identity. A new cycle records changes and preserves historical versions. An old budget is not renewed by asking to resume.

## How a research cycle works

```text
Question → primary + secondary objectives → strategy you see
         → investigation across relevant fronts → studies + claim audit
         → answer + confidence and limits + dossier + next-cycle proposals
         → your selection → another cycle in the same dossier
```

Within the approved cycle, Claude Code follows relevant leads, develops studies, and checks counterevidence. Before delivery, the skill asks it to reopen original sources for the claims carrying the conclusion and to correct or withdraw unsupported claims. Any suggested deep dive cites the exact finding or gap that motivates it and includes decision value and likely effort. Another cycle begins only when you choose it.

## How the method holds the work together

The key connection is **question → study → evidence → conclusion → revision**. Studies explain the answer, counterevidence, limits, and what would change the assessment. A conclusion audit asks the model to reopen original evidence for decisive claims and repair dependent recommendations when a premise fails.

```text
research-name-YYYY-MM-DD/
  README.md
  01-reports/
  02-studies/
  03-sources/
  04-data/
  05-research-log/<cycle>/
  06-history/
```

Only useful directories are created. Derived data files require source captures and a recorded method in `04-data/PROVENANCE.json`. Historical reports should retain links to the versions they used. A partial update must not make untouched subjects look fresh.

For complete research, the delivery contract specifies an executive of N pages, with N from one to seven, and at least 7N analytical pages in the full report. This is a scope requirement, not a quality score. Insufficient substance means a partial delivery; missing rendering means unverified pagination. Simple questions, explicit summaries, and requested delta updates remain proportionate.

Read [how it works](docs/HOW-IT-WORKS.md) for the distinction between instructions, executable checks, and analytical judgment.

## Cost, privacy, and preservation

Sherlock uses your existing Claude Code setup. Model usage, searches, downloads, and any authorized delegation can carry cost. The skill asks the researcher to respect the mandate and report observable usage; it does **not** implement a spending cap. Unknown cost must remain unknown.

The dossier is saved locally, but the research may send prompts, queries, excerpts, or documents to external model and tool providers through your host. Local storage does not mean local processing. Choose sources and session tools accordingly. Saving does not authorize sharing, paid access, contacting people, or publication.

Preservation is limited to material the host exposes. A snippet is not a full document; an edited study is not an original agent handoff. Missing exports, truncated returns, and unavailable originals must be disclosed. Files on disk are not a backup unless you separately provide one.

## What has been evaluated

The local suite checks supporting behavior such as packaging, file inventories, hashes, paths, links, and data provenance. It cannot verify whether evidence supports a conclusion or whether the research answers your question.

The previously disclosed two-case comparison fell below its predefined improvement threshold, and Sherlock's correctness was lower in both cases. The small, qualitative design and incomplete effort accounting limit interpretation. It is not evidence of a reliable accuracy advantage. The figures and method are in the [public evaluation](docs/EVALUATION.md); the [technical coverage](docs/TESTING.md) describes what the supporting tests establish.

## Explore or contribute

- [Example guide](examples/README.md)
- [How it works](docs/HOW-IT-WORKS.md)
- [Skill instructions](skill/SKILL.md)
- [Workspace architecture](docs/WORKSPACE-ARCHITECTURE.md)
- [Acceptance criteria](docs/ACCEPTANCE-CRITERIA.md), which describe intended behavior
- [Product requirements](PRD.md)
- [Helper reference](skill/references/delivery-checks.md)

From the package root, run local tests with `python3 -m unittest discover -s tests -v`. Optional-dependency skips are not verified successes. Build a new local package with `python3 scripts/package_public.py /path/to/new-package.zip`; the allowlist controls its contents and existing destinations are refused. Building does not publish.

The current package identity is `0.1.0-beta.8`, recorded in [VERSION](VERSION). The implementation and documentation are licensed under [MIT](LICENSE). That license does not grant rights to third-party evidence collected in a dossier.
