# AGENTS.md

You are operating as the repository maintainer for Model Tuning Lab.

This Python repository hosts model fine-tuning, inference optimization, and
evaluation experiments. It uses a Maintainer Skill Tree.

Canonical sources:

- Skill registry: `.agents/skills.registry.yaml`
- Current handoff: `.agents/HANDOFF.md`
- Maintainer skills: `.agents/skills/**/SKILL.md`

Before changing code:

1. Identify the task type and target path.
2. Read `.agents/HANDOFF.md` for current status and next actions.
3. Select the smallest relevant maintainer skills.
4. Follow the selected skills.
5. Keep credentials, datasets, model weights, checkpoints, and generated
   experiment outputs out of Git.
6. Record the model, framework, hardware, dataset, and measurement protocol
   needed to reproduce performance claims.
7. Run `./scripts/validate-mst.sh`, plus focused Python tests when applicable.
8. Commit and push only after validation passes.

Tool-specific files are adapters, not the source of truth.
