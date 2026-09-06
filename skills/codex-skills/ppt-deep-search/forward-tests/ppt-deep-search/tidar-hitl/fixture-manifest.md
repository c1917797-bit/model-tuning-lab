---
date: 2026-06-03
fixture: tidar-hitl
source_package: paper source request
---

# TiDAR HITL Forward Test

This fixture preserves a paper source request for `TiDAR: Think in Diffusion, Talk in Autoregression`.

## Goal

Validate whether `ppt-deep-search` can run its normal human-in-the-loop workflow and produce the required Source Understanding review artifacts:

- `review/source_understanding_review.html`, screenshots, visual QA, and baseline approval for the source-understanding gate.

The test is not a one-shot paper summary. The child agent should ask the human stakeholder for missing source scope, comparison targets, evidence gaps, and approval according to `SKILL.md`. The main agent answers those questions as the human.

## Candidate-Facing Assets

Pass only this directory to the candidate agent:

- `candidate/prompt.md`
- `candidate/input/source-request.md`

The candidate may also read the repository Skill and normal references/scripts required by `SKILL.md`.

## Judge-Facing Assets

Use after the candidate finishes:

- `judge/rubric.md`

Do not pass `judge/` to the candidate agent.

## Contamination Rules

- Do not pass `fixture-manifest.md`, `judge/`, or this case's `main-agent-prompt.md` to the child agent.
- Do not tell the child agent the desired scores, judge rubric, or expected findings.
- Do not summarize a complete source explanation to the child agent before it asks for human decisions.
- The main agent may answer child-agent questions with stakeholder preferences and approvals.

## Expected Candidate Output Shape

The candidate should write final artifacts under a run-specific workspace such as:

```text
.tmp/forward-tests/tidar-hitl/<run-id>/
```

Expected artifacts:

- `review/source_understanding_review.html`;
- `review/source-understanding-images/` with exported slide PNGs;
- `review/visual-qa.md` recording an independent checker verdict;
- saved source-understanding baseline under `baselines/`;
- saved approval bundle or baselines when produced by the Skill;
- validation output showing `scripts/validate_source_understanding_html.py ... all ...` passed for the review HTML, or a clear blocker note explaining why it could not;





