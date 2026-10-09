# AGENTS.md

You are operating as a repository maintainer agent for this Python service.

This repository uses a Maintainer Skill Tree.

Canonical sources:

- Skill registry: `.agents/skills.registry.yaml`
- Maintainer skills: `.agents/skills/**/SKILL.md`

Before changing code:

1. Identify the task type and target path.
2. Select the smallest relevant maintainer skills.
3. Follow the selected skills.
4. Run `./scripts/validate-mst.sh` and relevant product tests.
5. Report changed files, checks, and residual risk.

Runtime product skills live under `runtime-skills/**`; never treat them as
repository-maintainer instructions.

Tool-specific files are adapters, not the source of truth.
