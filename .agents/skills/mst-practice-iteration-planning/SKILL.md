---
name: mst-practice-iteration-planning
description: Use when planning a validation stage for a target repository, decomposing a goal into verifiable sub-tasks, or deciding what to validate next in a practice session. Do not use for routine coding tasks.
---

# Practice Iteration Planning

## Purpose

Turn a stage goal into a concrete, verifiable iteration plan with machine-checkable pass criteria, then feed reusable lessons back into the skillsgit library.

## Definitions

- **Stage goal**: a single coherent transformation or validation objective (e.g., "split monolith into 3 crates", "add per-crate skill registries").
- **Iteration**: one commit-worthy unit of work within a stage, with its own pass criteria.
- **Skills library**: this skillsgit repository, which receives lessons from practice.

## Workflow

1. **State the stage goal** in one sentence.
2. **Inventory the current state** — what exists, what is missing, what changed since last iteration.
3. **Decompose into iterations** — each iteration must be:
   - Small enough to validate in one pass (typically 1-3 file changes or 1 structural change).
   - Large enough to be a coherent unit (not "rename one variable").
   - Independently verifiable with explicit pass criteria.
4. **Write the iteration plan** as a YAML file (see Output Format).
5. **Execute each iteration**, running validation after each.
6. **Record lessons** in the iteration YAML under `lessons_ingested`.
7. **Feed back to skillsgit** — classify each lesson using `mst-experience-ingestion` and update the library.

## Output format

Each iteration is recorded in `.agents/evals/practice-iterations/<id>.yaml`:

```yaml
schema: mst-practice-iteration/v1
id: <descriptive-slug>
repository: <target-repo-name>
status: done | in_progress | blocked
date: YYYY-MM-DD
validated_commit: <last validated Git checkpoint for this iteration>

stage_goal: <one sentence>

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

For `in_progress`, `validated_commit` names the last validated input
checkpoint, not an anticipated future result. For `done`, advance it to the
commit whose changes passed the listed validation. This field and the
`mst-practice-iteration/v1` schema are required by `scripts/validate-mst.sh`.

## Sizing guide

A well-sized iteration:

- Produces 1-3 files changed, or 1 structural change (e.g., splitting a crate).
- Has at least 1 machine-checkable pass criterion.
- Can be described in a single commit message.
- Does not require "and then we'll also..." to be coherent.

If an iteration requires more than 5 file changes or 2 structural changes, split it.

## Verification

- Every iteration has at least one `validation_commands` entry.
- Every `lessons_ingested` entry has a `destination` and `severity`.
- The `stage_goal` is a single sentence.
- The iteration YAML parses without errors.
- `validated_commit` resolves to the checkpoint it claims; do not label an
  unrun or uncommitted future change as validated.

## Anti-patterns

Do not:

- plan 10 iterations ahead (plan 2-3, then replan),
- skip the validation repo and update skillsgit directly,
- record lessons without classifying their destination,
- create iterations without machine-checkable pass criteria,
- or treat the plan as immutable (replan after each iteration based on findings).
