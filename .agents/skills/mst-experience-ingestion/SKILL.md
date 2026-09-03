---
name: mst-experience-ingestion
description: Use after a real repository transformation or maintenance session to turn practice experience into structured Maintainer Skill Tree updates instead of unstructured notes.
---

# Experience Ingestion

## Purpose

Turn real practice experience into structured maintainer skills.

The rule is:

```text
Experience enters the repository only when it is structured as skills, registry metadata, evals, examples, or verification rules.
```

## When to use

Use after:

- transforming a real repository,
- validating this skill library on a demo repository,
- discovering a missing transformation step,
- hitting a tool or environment constraint,
- confirming a maintainer workflow preference,
- or seeing a repeated pattern that should guide future agents.

## Inputs

Collect:

- source repository or session name,
- task goal,
- selected skills,
- what worked,
- what failed or caused friction,
- commands that validated the result,
- files changed,
- commit or checkpoint reference when available,
- whether the lesson is general, repository-specific, or tool-specific.

## Classification

Classify each lesson into one of these destinations:

1. Existing skill update
2. New narrow skill
3. Registry metadata
4. Example repository pattern
5. Eval or verification case
6. Tool adapter note
7. Runtime/product boundary rule
8. Git checkpoint policy
9. Audit-correction: an audit finding that was verified to be a false
   positive. The lesson is "an audit can be wrong; verify before fixing"
   and the destination is the originating practice-iteration yaml that
   disproved the finding. This is an ingestable lesson, not a no-op.
10. Do not ingest because it is one-off or not reusable

## Workflow

1. Summarize the practice session in 3 to 7 facts.
2. Extract reusable lessons only.
3. For each lesson, choose the smallest durable destination.
4. Prefer updating an existing skill before adding a new skill.
5. Add a new skill only when the lesson has a distinct trigger and repeatable workflow.
6. Update `.agents/skills.registry.yaml` for new or changed skills.
7. Add or update an eval/example when the lesson can be tested.
8. Run `mst-transformation-verification`.
9. If the repository has a confirmed git checkpoint policy, commit and push after validation.

## Ingestion quality gate

A lesson is ready to ingest only if it answers:

- What future task should trigger this knowledge?
- What should the agent do differently next time?
- Where should this knowledge live?
- How can we verify it did not break the skill tree?

## Verification

- Each ingested lesson answers all 4 ingestion quality gate questions: trigger, different action, destination, and verification method.
- The chosen destination for every lesson matches one of the 10 classification items (1–10) listed in the Classification section.
- `./scripts/validate-mst.sh` still passes after all ingestion changes are applied.

## Anti-patterns

Do not:

- paste long retrospectives into README,
- create broad skills from one isolated event,
- store raw chat transcripts as rules,
- duplicate the same lesson across many skills,
- hide tool-specific behavior inside canonical skills,
- or add experience that cannot guide future action.

## Required output

Report:

- practice source,
- lessons ingested,
- destination for each lesson,
- files changed,
- validation result,
- and commit/push status if applicable.
