---
name: mst-agentsmd-authoring
description: Use when creating or updating AGENTS.md in a target repository. Do not use for editing AGENTS.md in this skillsgit library itself (that follows mst-repo-onboarding).
---

# AGENTS.md Authoring

## Purpose

Write minimal, effective AGENTS.md bootstrap files for target repositories being transformed.

## Principles

- AGENTS.md is the entry point, not the encyclopedia.
- It declares the maintainer role and points to the registry and skills.
- It stays short: under 60 lines for a typical repository.
- It does not duplicate skill content.

## Workflow

### Creating a new AGENTS.md

1. Ask the maintainer: what is this repository's primary purpose?
2. Determine if the repository needs a simple or multi-role bootstrap.
3. Write AGENTS.md using the minimal template below.
4. Create the compatibility shims (CLAUDE.md, etc.) if requested.
5. Run `mst-transformation-verification` to check the result.

### Updating an existing AGENTS.md

1. Read the current AGENTS.md and inventory all sections.
2. Identify stale, duplicated, or misplaced content.
3. Remove content that belongs in skills (move it to a SKILL.md first).
4. Remove tool-specific configuration (move it to adapter files).
5. Ensure the four required elements are present (see Template).
6. Run `mst-transformation-verification`.

## Minimal template

```markdown
# AGENTS.md

You are operating as a repository maintainer agent.

This repository uses a Maintainer Skill Tree.

Canonical sources:

- Skill registry: `.agents/skills.registry.yaml`
- Maintainer skills: `.agents/skills/**/SKILL.md`

Before changing code:

1. Identify the task type and target path.
2. Select the smallest relevant maintainer skills.
3. Follow the selected skills.
4. Run the required validation.
5. Report changed files, checks, and residual risk.

Tool-specific files are adapters, not the source of truth.
```

## Compatibility shims

For tool-specific adapters, create thin shims that point to AGENTS.md:

- `CLAUDE.md`: single line `@AGENTS.md`
- `.opencode/` or `.codex/`: reference AGENTS.md path

These shims must not duplicate governance rules.

## Verification

- AGENTS.md exists and is under 60 lines.
- It declares the maintainer role.
- It points to `.agents/skills.registry.yaml`.
- It points to `.agents/skills/**/SKILL.md`.
- It does not contain skill-level workflow details.
- Tool adapters do not duplicate its content.

## Anti-patterns

Do not:

- write a 200-line AGENTS.md that duplicates all skill content,
- embed tool-specific profiles or prompts in AGENTS.md,
- make AGENTS.md the only source of maintenance knowledge (skills are the canonical source),
- update AGENTS.md without also updating affected skills,
- or remove the pointer to the registry.
