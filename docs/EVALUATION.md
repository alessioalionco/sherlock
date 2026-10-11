# Evaluation and limits

**Sherlock is experimental. Its published evaluation does not establish a consistent advantage over open research.** Better preservation and easier inspection do not, by themselves, make a conclusion more accurate or useful.

This page restates the aggregate findings authorized for distribution in [Testing and limitations](TESTING.md). The two-case comparison below is a **previously disclosed comparison**. It is not presented as the latest evaluation or as proof of the current version's effect. Private case identities and underlying research material are excluded.

## Previously disclosed research comparison

Each condition began with the same original user request. Spontaneous clarification questions were answered under a prewritten disclosure policy.

| Metric | Sherlock | Open chat |
|---|---:|---:|
| Mean qualitative score, 0–10 | 6.68 | 6.57 |
| Relative reported research usage | 2.89× | 1× |

The mean difference was **+0.11**, below the predeclared **+0.5** improvement threshold. Correctness was lower for Sherlock in both cases. A central conclusion failed verification; a decisive conclusion in the other case was not cleared. Purpose discovery, original-source capture, and auditability showed benefits, but those benefits did not establish a reliable advantage in the final answer.

## What the score measures

Correctness, evidence depth, and question fit each received double weight. Counterevidence, calibration, auditability, actionability, and efficiency each received single weight. The weighted sum was divided by eleven.

A central error cannot be averaged away by good presentation. The result should therefore be read with the correctness failures visible, rather than interpreted from the mean score alone.

Reported research usage excludes unmeasured coordination and assessment effort. It is neither a full accounting of effort nor an invoice guarantee.

## What the comparison cannot establish

The exercise used only two known tasks, one current session per condition, scripted replies, recognizable formats, qualitative native graders, and live sources that could vary. It does not establish statistical significance, measure natural user satisfaction, or isolate the causal effect of a skill revision.

The public summary is a limitation disclosure. It is not an independently reproducible benchmark dataset: case identities, local costs, and the full source corpus are intentionally excluded.

## Technical checks answer a different question

Local tests cover supporting behavior including package allowlists, file identity, missing or changed files, supplied export capture, supported navigation, rendering, and recorded data provenance. They are useful for checking whether an artifact was assembled and preserved as expected.

They do not establish factual accuracy, analytical depth, usefulness, complete access to host exports, or compliance with every behavioral instruction. A passed check is not a research-quality certificate.

To reproduce the local suite from the package root:

```bash
python3 -m unittest discover -s tests -v
```

Use Python 3.9 or newer. Core checks use the standard library and temporary synthetic files. Optional Markdown and PyMuPDF enable additional checks; missing dependencies appear as skips, not verified passes. Runtime validation covers macOS; path-semantics tests do not establish native Windows or Linux support. Consult [TESTING.md](TESTING.md) for the tested versions and coverage details.

## Behavioral coverage still open

The [acceptance criteria](ACCEPTANCE-CRITERIA.md) describe intended behavior. Open coverage includes cold resume, longitudinal and concurrent updates, real first-use host discovery, resistance to hostile source instructions during live browsing, and reliably complete default N/7N delivery. Mechanical tests do not clear those behaviors.

Stronger claims need new evaluations with predefined tasks, actual models and tools, effort limits, interaction and stopping rules, and a judging rubric. They should distinguish execution after a shared brief from the complete experience of eliciting that brief. Decisive conclusions need original-source checks. Confidence, objective coverage, and actual user feedback must remain separate.

For now, the justified claim is narrow: Sherlock supplies a structured research method and supporting preservation tools. Its research results still need substantive review.
