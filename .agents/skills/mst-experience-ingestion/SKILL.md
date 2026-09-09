---
name: mst-experience-ingestion
description: Use after a real repository transformation or maintenance session to turn practice experience into structured Maintainer Skill Tree updates instead of unstructured notes.
---

# Experience Ingestion

## Purpose

Turn real practice experience into structured maintainer skills.

Skills are durable procedural memory, not a dump of run-specific state.
Reusable triggers, guards, and decision rules belong in skills; the current
candidate and resume action belong in `.agents/HANDOFF.md`; bounded decisions
belong in practice-iteration YAML; measurements and immutable identities belong
in experiment/evidence records. Together these Git-tracked layers, rather than
chat history, form the maintainer's recoverable long-term memory.

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
- outcome class: accepted, rejected, failed, invalid, or inconclusive,
- evidence level and the highest claim it can support,
- the actual execution path or identity evidence when behavior depends on it,
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

## Outcome and claim discipline

Do not flatten all outcomes into "worked" and "failed":

- An accepted result contributes only the rule justified by its evidence
  layer; a local pass is not a product-level success.
- A rejected result contributes a bounded exclusion such as "this tested
  configuration missed the gate", not "the whole approach cannot work".
- A failed result contributes a correctness, implementation, or safety guard
  and a recovery rule.
- An invalid result contributes a path-identity, comparability, or measurement
  guard; it contributes no algorithm trend.
- An inconclusive result contributes a disambiguation rule only when another
  bounded check can change the decision.

Preserve corrections by marking old conclusions superseded and linking the
new evidence. Do not erase the historical conclusion, silently keep using it,
or turn a corrected error into a permanent constraint.

## Workflow

1. Summarize the practice session in 3 to 7 facts.
2. Classify every outcome and state its evidence level, claim ceiling, and
   tested scope before extracting a lesson.
3. Extract reusable lessons only; separate domain-specific rules from generic
   loop, evidence, Git, and tool behavior.
4. For each lesson, choose the smallest durable destination.
5. Prefer updating an existing skill before adding a new skill.
6. Add a new skill only when the lesson has a distinct trigger and repeatable workflow.
7. Update .agents/skills.registry.yaml for new or changed skills.
8. Add or update an eval/example when the lesson can be tested.
9. Run mst-transformation-verification.
10. Reconcile the active iteration and `.agents/HANDOFF.md` with the new
    evidence so the next session cannot resume an obsolete candidate.
11. If the repository has a confirmed git checkpoint policy, commit and push after validation.

## Ingestion quality gate

A lesson is ready to ingest only if it answers:

- What future task should trigger this knowledge?
- What should the agent do differently next time?
- What is the tested scope, evidence level, and claim ceiling?
- Where should this knowledge live?
- How can we verify it did not break the skill tree?

## Verification

- Each ingested lesson answers the ingestion quality gate questions: trigger,
  different action, tested scope, evidence level, claim ceiling, destination,
  and verification method.
- The chosen destination for every lesson matches one of the 10 classification items (1–10) listed in the Classification section.
- `./scripts/validate-mst.sh` still passes after all ingestion changes are applied.

## Anti-patterns

Do not:

- paste long retrospectives into README,
- create broad skills from one isolated event,
- store raw chat transcripts as rules,
- duplicate the same lesson across many skills,
- leave the active iteration or handoff pointing at a superseded decision,
- depend on an uncommitted chat conclusion for the next resume action,
- hide tool-specific behavior inside canonical skills,
- convert an invalid run into evidence that an algorithm improved or regressed,
- promote a single screen or local check into a general success rule,
- generalize a rejected configuration to an untested technique family,
- overwrite a historical error instead of linking a superseding correction,
- or add experience that cannot guide future action.

## Required output

Report:

- practice source,
- lessons ingested,
- destination for each lesson,
- files changed,
- validation result,
- and commit/push status if applicable.
