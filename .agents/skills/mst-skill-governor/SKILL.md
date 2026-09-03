---
name: mst-skill-governor
description: Use when updating, adding, deprecating, or restructuring skills in this repository or a transformed repository's Maintainer Skill Tree.
---

# Skill Governor

## Purpose

Govern changes to maintainer skills so the skill system improves without becoming noisy, unsafe, or tool-specific.

## When to update a skill

Update or add a skill only when there is evidence of reusable value:

- repeated agent or maintainer failure,
- CI or review caught a missing required step,
- repository structure changed,
- a tool adapter conflict appeared,
- runtime/maintainer boundary became unclear,
- an example or eval requires a new behavior.

## Workflow

1. Identify the problem.
2. Decide whether it belongs in:
   - `AGENTS.md`,
   - an existing skill,
   - a new skill,
   - registry metadata,
   - a tool adapter,
   - documentation,
   - or runtime product skill policy.
3. Prefer editing an existing narrow skill over adding a new broad one.
4. Keep `SKILL.md` frontmatter minimal.
5. Update `.agents/skills.registry.yaml` when adding, moving, renaming, deprecating, or retiring a skill.
6. Add or update an example/eval if the behavior should be testable.
7. Report why the change is reusable.

## Deprecation rule

Deprecate a skill when:

- its trigger is no longer valid,
- another skill fully replaces it,
- it causes repeated mis-selection,
- or it encodes stale repository structure.

Mark it `deprecated` in the registry before removing it, unless it is unsafe.

## Where do lessons go?

When a lesson is being ingested, the **10 classification destinations** are defined in `mst-experience-ingestion/SKILL.md` under the "Classification" section. This skill does not duplicate the list; it references it:

```text
See: mst-experience-ingestion/SKILL.md -> "Classification"
```

When this governor changes the skill tree, the destination of the change is recorded as one of those 10 classification destinations.

## Verification

- Registry has no duplicate skill IDs (`grep -c` on id fields).
- All registry paths resolve to existing `SKILL.md` files.
- New or changed skill has valid frontmatter (`name` and `description`).
- `scripts/validate-mst.sh` passes after the change.
- A reason for the change is recorded (repeated failure, missing step, etc.).

## Anti-patterns

Do not:

- make one large universal skill,
- encode personal preferences as governance,
- copy external tool docs wholesale,
- let runtime skills govern repository maintenance,
- or change governance rules without explaining the reason.

## Relationship to experience ingestion

Use `mst-experience-ingestion` before changing skills based on practice. That skill decides whether a lesson deserves to enter the repository and where it belongs. Use this governor skill after that decision to make the actual skill, registry, eval, or example change safely.
