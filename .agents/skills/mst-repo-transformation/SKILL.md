---
name: mst-repo-transformation
description: Use to inspect an ordinary repository and plan or implement its conversion into an AGENTS.md + .agents/skills driven maintainer system.
---

# Repository Transformation

## Purpose

Transform a normal code repository into a repository that a coding agent can maintain through a clear `AGENTS.md + Maintainer Skill Tree` structure.

## When to use

Use when the user asks to:

- add `AGENTS.md`,
- add `.agents/skills`,
- migrate from `CLAUDE.md`, `.cursorrules`, ad-hoc prompts, or tool-specific rules,
- make a repository agent-friendly,
- or introduce a reusable repository maintainer skill system.

## Inputs

Collect or infer:

- repository type and primary languages,
- build/test/package commands,
- monorepo layout,
- existing agent instruction files,
- CI workflows,
- security/release/deployment sensitivity,
- whether the product contains runtime skills or end-user agents.

## Workflow

1. Inventory the repository.
2. Identify existing instruction files:
   - `AGENTS.md`
   - `CLAUDE.md`
   - `.opencode/**`
   - `.codex/**`
   - `.cursor/**`
   - `.cursorrules`
   - README contributor sections
   - CI workflows
3. Classify repository needs:
   - minimal single-package repo,
   - monorepo,
   - library,
   - application,
   - infrastructure repo,
   - hosted agent/runtime platform.
4. Create or update a minimal `AGENTS.md` bootstrap.
5. Create `.agents/skills.registry.yaml`.
6. Add only the first useful skills.
7. Keep tool-specific files as adapters, not canonical sources.
8. If runtime/product skills exist, physically separate them from maintainer skills.
9. Run transformation verification.
10. If the transformation is a validation run, record it as an eval or practice case.
11. Use `mst-experience-ingestion` to feed reusable lessons back into the skills library.

## First skill set for most repositories

Start with the core skills from the `repository-transformation-v0.1` pack:

- `mst-repo-onboarding`
- `mst-repo-transformation`
- `mst-agentsmd-authoring`
- `mst-skill-tree-design`
- `mst-transformation-verification`
- `mst-skill-governor`

Add more only when justified by repeated maintenance patterns:

- `mst-git-checkpoint-policy` — when the repository needs a commit/push policy
- `mst-experience-ingestion` — when the repository is a validation target
- `mst-practice-iteration-planning` — when planning structured iterations
- `mst-tool-adapter-boundary` — when multiple tool adapters coexist
- `mst-runtime-skill-boundary` — when the product has runtime/end-user skills
- path-specific skills for monorepos or multi-crate workspaces.

## Output

Provide:

- transformation summary,
- files created/changed,
- selected skill set,
- commands discovered,
- open questions,
- verification result,
- residual risk.

## Verification

- `AGENTS.md` exists at the repository root and is at most 60 lines.
- Every path referenced in `.agents/skills.registry.yaml` resolves to an existing directory with a `SKILL.md`.
- No directory under `.agents/skills/` contains a runtime/product skill (only maintainer skills).
- `./scripts/validate-mst.sh` passes with exit code 0.

## Anti-patterns

Do not:

- dump a huge prompt into `AGENTS.md`,
- duplicate full instructions across tools,
- make tool adapter files canonical,
- mix runtime skills with maintainer skills,
- create many skills before the repository has real maintenance patterns,
- let an agent self-authorize dangerous workflows.

## Empty repository validation

When the target repository is empty and is being used as a validation case, create both:

- a minimal product scaffold that matches the repository positioning, and
- a maintainer scaffold with `AGENTS.md`, registry, skills, validation scripts, and git checkpoint policy.

This proves that the transformation skills work on a real repository instead of only producing abstract guidance.
