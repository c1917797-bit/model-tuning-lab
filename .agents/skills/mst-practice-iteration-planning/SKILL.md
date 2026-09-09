---
name: mst-practice-iteration-planning
description: Use when planning or revising a validation stage, decomposing a long-term objective through a medium-term milestone into bounded short-term work, or deciding what evidence should change the next iteration. Do not use for routine coding tasks.
---

# Practice Iteration Planning

## Purpose

Turn a fixed long-term objective and its current acceptance gap into a
medium-term milestone and a concrete, verifiable short-term iteration. Use new
evidence to choose the next iteration without silently weakening the objective.

## Definitions

- **Stage goal**: a single coherent transformation or validation objective (e.g., "split monolith into 3 crates", "add per-crate skill registries").
- **Long-term objective**: the user-approved outcome and acceptance boundaries;
  it does not change merely because a local attempt fails.
- **Medium-term milestone**: a defensible capability, candidate, or decision
  that materially advances the long-term objective.
- **Iteration**: one commit-worthy unit of work within a stage, with its own pass criteria.
- **Deciding evidence**: an observation whose pass, failure, or inconclusive
  result changes the candidate or next implementation decision.

## Workflow

1. **State the goal chain** — long-term objective, current acceptance gap,
   medium-term milestone, and the short-term decision needed next.
2. **Inventory authoritative evidence** — what exists, what is missing, what
   changed since the last iteration, and which earlier assumptions were
   invalidated.
3. **Choose the next iteration from the gap** — each iteration must be:
   - Small enough to validate in one pass (typically 1-3 file changes or 1 structural change).
   - Large enough to be a coherent unit (not "rename one variable").
   - Independently verifiable with explicit pass criteria.
   - Bound to deciding evidence, a budget or stop rule, and explicit actions
     for pass, failure, and inconclusive outcomes.
4. **Write the iteration plan** as a YAML file (see Output Format).
5. **Execute each iteration**, running validation after each.
6. **Review the goal chain** at the deciding result or budget limit, before
   changing branch or substantially expanding cost, and at handoff. Record
   evidence, uncertainty, changed judgment, and the next decision.
7. **Replan from the review**, not merely from unfinished backlog items.
   Negative evidence counts when it eliminates or redirects a candidate.
8. **Ingest reusable lessons** with `mst-experience-ingestion`; keep
   project-specific constraints in the owning project.

## Output format

Each iteration is recorded in `.agents/evals/practice-iterations/<id>.yaml`:

```yaml
schema: mst-practice-iteration/v1
id: <descriptive-slug>
repository: <target-repo-name>
status: done | in_progress | blocked
date: YYYY-MM-DD
validated_commit: pending  # replace with the validated implementation/evidence commit when done

stage_goal: <one sentence>

goal_chain:
  long_term_objective: <fixed user-approved outcome and boundaries>
  current_gap: <unsatisfied acceptance condition>
  medium_term_milestone: <candidate capability or decision>
  short_term_decision: <decision this iteration can change>
  deciding_evidence: <measurement or check>
  budget_or_stop_rule: <bounded cost or stopping condition>
  on_pass: <next action>
  on_failure: <next action>
  on_inconclusive: <next action>

changes:
  - type: <workspace|skill-tree|agents|validation|docs>
    description: <what changed>
    files: [<changed files>]

validation_commands:
  - <command 1>
  - <command 2>

lessons_ingested:
  - lesson: <what was learned>
    destination: <skill or file to update>
    severity: high | medium | low
```

## Sizing guide

A well-sized iteration:

- Produces 1-3 files changed, or 1 structural change (e.g., splitting a crate).
- Has at least 1 machine-checkable pass criterion.
- Can be described in a single commit message.
- Does not require "and then we'll also..." to be coherent.

If an iteration requires more than 5 file changes or 2 structural changes, split it.

## Verification

- Every iteration has at least one `validation_commands` entry.
- `validated_commit` is `pending` only while work is in progress; completed
  iterations identify the immutable implementation or evidence commit actually
  covered by the recorded validation.
- Every iteration links its short-term decision to a current gap and
  medium-term milestone without weakening the long-term objective.
- Deciding evidence, budget, and pass/failure/inconclusive actions are explicit.
- Every `lessons_ingested` entry has a `destination` and `severity`.
- The `stage_goal` is a single sentence.
- The iteration YAML parses without errors.

## Anti-patterns

Do not:

- plan 10 iterations ahead (plan 2-3, then replan),
- select the next task only because it is unfinished,
- turn a diagnostic, report, commit, or local passing check into the long-term
  objective,
- lower acceptance criteria after a failed or inconclusive result,
- extend a diagnostic chain after its budget without a changed decision,
- skip the validation repo and update skillsgit directly,
- record lessons without classifying their destination,
- create iterations without machine-checkable pass criteria,
- or treat the plan as immutable (replan after each iteration based on findings).
