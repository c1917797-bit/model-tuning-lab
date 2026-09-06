# Judge Rubric: RTX Spark Agent PC Web Evidence HITL Forward Test

Use this rubric after the candidate agent finishes. The judge may inspect the candidate's final review files, baselines, approval bundle, QA output, and interaction transcript.

## Scoring

Score each dimension from 0 to 3.

- HITL Workflow Discipline: asks for missing source scope, comparison targets, evidence gaps, and approval before writing final artifacts.
- Stakeholder Incorporation: uses the main agent's human answers to shape the technical architecture explanation and evidence boundaries without merely echoing the source request.
- Official Wording Boundary: preserves that the official product/platform is NVIDIA RTX Spark / Windows PCs purpose-built for personal agents, and treats “Agent 原生电脑” or “老黄重新发明 PC” as Chinese/media paraphrase rather than a formal product name.
- Source Understanding: correctly synthesizes NVIDIA Newsroom, RTX Spark product page, GTC Taipei keynote context, NVIDIA Build/local-agents blog, and Microsoft Build Live into an architecture judgment about Windows local personal/frontier agents, RTX Spark, DGX Station,
  OpenShell, security runtime, CUDA/WSL, unified memory, and local large-model constraints.
- Source Understanding Review Artifact: produces `review/source_understanding_review.html`, exported screenshots, `review/visual-qa.md` with an independent checker verdict, saved source-understanding baseline, and web source capture packages before approval.
- Source Explanation Structure: turns the official web sources into a decision-oriented PPT argument rather than a list of source facts or URLs.
- Source Understanding Contract: `review/source_understanding_review.html` is present, source-grounded, readable, and contains no downstream PPT planning artifact.
- Evidence Boundary Discipline: avoids treating theoretical FP4/sparsity peak performance, not-yet-shipped products, keynote rhetoric, or official marketing copy as validated production agent throughput/security evidence.
- QA Discipline: runs or clearly attempts `scripts/validate_source_understanding_html.py ... all ...`, records visual QA, and treats failures as blockers.

## Blocking Findings

Treat any of the following as a likely fail:

- The candidate skips human-in-the-loop approval and writes final files immediately despite missing source scope, comparison target, evidence gap, or approval decisions.
- The candidate skips the Source Understanding review artifact gate, or `review/source_understanding_review.html`, exported screenshots, `review/visual-qa.md`, the source-understanding baseline, web source capture packages, or source-understanding render QA evidence is missing.
- `review/source_understanding_review.html` is missing, fails required structural validation, or contains author-facing audit/source-locator tables.
- The final review says or implies that “全球首个 Agent 原生电脑” is an official product name.
- Claims about 1 PFLOP, 128GB unified memory, 120B-parameter local models, 1M token context, OpenShell, or DGX Station are not traceable to official sources or are not clearly bounded.
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
- Official Wording Boundary: [0-3]
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
- [Web source capture package paths]
- [Source Understanding review path]
- [Approval bundle or baseline path]
- [QA output path]
```




