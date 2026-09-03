---
name: mst-transformation-verification
description: Use after adding or changing AGENTS.md and .agents/skills in a target repository to verify the maintainer skill system is coherent, minimal, and safe.
---

# Transformation Verification

## Purpose

Verify that a transformed repository has a usable and safe `AGENTS.md + Maintainer Skill Tree` system.

## Checks

### Bootstrap

- `AGENTS.md` exists at repository root.
- It declares the maintainer role.
- It points to `.agents/skills.registry.yaml`.
- It points to `.agents/skills/**/SKILL.md`.
- It stays short and does not duplicate all skill content.

### Registry

- `.agents/skills.registry.yaml` exists.
- Every registry path exists.
- Every skill directory has `SKILL.md`.
- Skill IDs are unique.
- Status is one of stable, experimental, deprecated, retired.
- Trigger text is specific enough for selection.

### Skills

- Every `SKILL.md` has `name` and `description` frontmatter.
- Every skill has a clear purpose and workflow.
- Skills are not overly broad.
- Verification expectations are included where relevant.

### Multi-level registries (monorepo / multi-crate)

When a repository has sub-components (crates, packages, services) with their own `.agents/` directories:

- Each sub-component may have its own `skills.registry.yaml` under `<component>/.agents/`.
- The workspace root registry must declare a selection precedence that includes `crate_scoped` before `workspace_scoped`.
- Verification must walk all sub-component registries, not just the root.
- Per-crate skill directories must follow the same frontmatter and structure rules as root skills.

### Boundaries

- Tool adapters do not duplicate canonical rules.
- Runtime/product skills are outside `.agents/skills/**`.
- Maintainer skills are not exposed as runtime assets.
- Runtime skills do not override maintainer instructions.

## Suggested shell checks

```sh
test -f AGENTS.md
test -f .agents/skills.registry.yaml
find .agents/skills -name SKILL.md -type f
```

For multi-crate or monorepo layouts, also check:

```sh
for dir in crates/*/; do
  test -f "${dir}.agents/skills.registry.yaml" && \
    find "${dir}.agents/skills" -name SKILL.md -type f
done
```

For dependency boundary verification in multi-crate workspaces, verify that declared hierarchy rules match actual `Cargo.toml` content — do not trust documentation claims alone.

For deeper validation, add repository-specific schema or script checks.

## Output

Report:

- pass/fail summary,
- files checked,
- missing files,
- boundary risks,
- recommended fixes.

### Experience ingestion

When a transformation was performed as a validation run, check that reusable practice experience was recorded structurally. Acceptable destinations include:

- `.agents/evals/transformation-cases/*.yaml`,
- `examples/**`,
- a new or updated `SKILL.md`,
- registry metadata,
- or a verification script change.

Do not treat loose notes alone as durable ingestion.

## Verification

See the Checks section above. After running all checks, confirm `scripts/validate-mst.sh` passes.

## Anti-patterns

Do not:

- skip verification because "the skills look right",
- verify only the root registry and ignore per-crate/per-service sub-registries,
- trust documentation claims about hierarchy without checking actual dependency files,
- accept a transformation where `validate-mst.sh` fails,
- or treat a passing validation as proof that the skills are correct (structure is necessary but not sufficient).
