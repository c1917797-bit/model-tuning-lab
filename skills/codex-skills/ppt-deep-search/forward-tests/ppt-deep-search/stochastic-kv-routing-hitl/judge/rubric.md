# Judge Rubric: Stochastic KV Routing HITL Forward Test

Use this rubric after the candidate agent finishes. The judge may inspect the candidate's final review files, baselines, approval bundle, QA output, and interaction transcript.

## Scoring

Score each dimension from 0 to 3.

- HITL Workflow Discipline: asks for missing source scope, comparison targets, evidence gaps, and approval before writing final artifacts.
- Stakeholder Incorporation: uses the main agent's human answers to shape the source explanation and evidence boundaries without merely echoing them.
- Source Understanding: identifies the paper's core mechanism, depth-wise KV-sharing motivation, R-CLA training idea, cache-retention evidence, and deployment tradeoffs with concrete source locators.
- Source Understanding Review Artifact: produces `review/source_understanding_review.html`, exported screenshots, `review/visual-qa.md` with an independent checker verdict, and a saved source-understanding baseline before approval.
- Source Explanation Structure: organizes the paper into a clear source explanation rather than a section-by-section summary.
- Source Understanding Contract: `review/source_understanding_review.html` is present, source-grounded, readable, and contains no downstream PPT planning artifact.
- Evidence Boundary Discipline: avoids overstating deployment readiness and preserves uncertainty around training/fine-tuning cost, TTFT/throughput impact, model-family transfer, and serving-environment assumptions.
- QA Discipline: runs or clearly attempts `scripts/validate_source_understanding_html.py ... all ...`, records visual QA, and treats failures as blockers.

## Blocking Findings

Treat any of the following as a likely fail:

- The candidate skips human-in-the-loop approval and writes final files immediately despite missing source scope, comparison target, evidence gap, or approval decisions.
- The candidate skips the Source Understanding review artifact gate, or `review/source_understanding_review.html`, exported screenshots, `review/visual-qa.md`, the source-understanding baseline, or source-understanding render QA evidence is missing.
- `review/source_understanding_review.html` is missing, fails required structural validation, or contains author-facing audit/source-locator tables.
- The final review is a generic paper summary with no clear source explanation or evidence boundary.
- Claims about memory savings, quality preservation, throughput, TTFT, or deployability are not traceable to paper evidence or explicitly marked as inference.
- The candidate reads judge-only files or receives rubric-derived coaching.
- The candidate writes outputs outside the required run directory without reporting the actual final paths.

## Judgment Template

```markdown
# Forward Test Judgment

## Verdict

[Strong pass / Pass with issues / Needs rerun / Fail]

## Scores

- HITL Workflow Discipline: [0-3]
- Stakeholder Incorporation: [0-3]
- Source Understanding: [0-3]
- Source Understanding Review Artifact: [0-3]
- Source Explanation Structure: [0-3]
- Source Understanding Contract: [0-3]
- Evidence Boundary Discipline: [0-3]
- QA Discipline: [0-3]

## Blocking Findings

- [Finding or "None"]

## Notable Strengths

- [Strength]

## Improvement Targets

- [Target]

## Evidence Reviewed

- [Interaction transcript or summary]
- [Source Understanding HTML path]
- [Source Understanding screenshots path]
- [Visual QA record path]
- [Source Understanding baseline path]
- [Source Understanding review path]
- [Approval bundle or baseline path]
- [QA output path]
```




