---
name: mst-skill-tree-design
description: Use to design the first .agents/skills tree and skills.registry.yaml for a target repository without overfitting or overproducing skills.
---

# Skill Tree Design

## Purpose

Design a small, useful Maintainer Skill Tree for a target repository.

## Skill design rule

Create a skill only when it captures reusable maintenance behavior.

A good skill has:

- a clear trigger,
- a narrow purpose,
- a repeatable workflow,
- concrete inputs and outputs,
- verification expectations,
- and a governance hook.

## Workflow

1. Identify the repository type (single package, monorepo, library, application, platform).
2. Start with the default first tree (see below).
3. Write each skill using the frontmatter rule and skill design rule.
4. Create `skills.registry.yaml` with schema, authority, selection strategy, and skill entries.
5. Add path-specific skills only when justified by repeated maintenance patterns.
6. Run `mst-transformation-verification` to validate the result.

## Default first tree

For a normal repository, start with:

```text
.agents/
  skills.registry.yaml
  skills/
    mst-repo-onboarding/
      SKILL.md
    mst-repo-transformation/
      SKILL.md
    mst-agentsmd-authoring/
      SKILL.md
    mst-skill-tree-design/
      SKILL.md
    mst-transformation-verification/
      SKILL.md
    mst-skill-governor/
      SKILL.md
```

## Add path-specific skills when

- a monorepo package has different build/test commands,
- a service has unique deployment or security rules,
- a subsystem has repeated review comments,
- or an area needs a dedicated maintainer workflow.

## Registry requirements

`skills.registry.yaml` should include:

- schema version,
- authority file,
- default selection strategy,
- conflict resolution rule,
- skill IDs,
- paths,
- status,
- purpose,
- triggers,
- scope.

## Frontmatter rule

Keep `SKILL.md` frontmatter minimal and broadly compatible:

```yaml
---
name: mst-example
description: Use when ... Do not use when ...
---
```

Put complex metadata in the registry, not frontmatter.

## Verification

- Every skill has a trigger, purpose, and workflow section.
- Registry entry lists match skills present on disk.
- No skill `SKILL.md` exceeds 120 lines.
- `scripts/validate-mst.sh` passes on the designed tree.
- Frontmatter in every skill contains `name` and `description`.

## Anti-patterns

Do not:

- create a skill per tiny preference,
- create a skill for one failed task without evidence it will repeat,
- hide security policy inside a general coding skill,
- put runtime product skills under `.agents/skills`,
- or make tool-specific adapter rules canonical.

## Multi-crate / monorepo skill trees

When the target repository is a Cargo workspace, Go monorepo, or similar multi-component layout:

- Create a root `.agents/skills.registry.yaml` with workspace-level coordination skills (build verification, crate boundary rules, cross-crate API design, agent delegation).
- Each crate or service that has distinct maintenance behavior gets its own `.agents/skills.registry.yaml` under `<component>/.agents/`.
- Per-crate skills should be written after the crate's code and boundaries are stable — writing them during a split is premature because the split itself changes ownership.
- Shared constants used by multiple crates belong in the shared types crate, not in any single consumer.
- Add a dependency boundary verification script (e.g., `validate-crate-boundaries.sh`) that checks actual `Cargo.toml` content against declared hierarchy rules. Documentation claims are not sufficient.
