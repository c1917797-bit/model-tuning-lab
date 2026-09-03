# AGENTS.md

You are operating as the repository maintainer for Model Tuning Lab.

This Python repository builds a repeatable optimization flywheel for model
inference on Ascend NPUs. It uses a Maintainer Skill Tree.

Canonical sources:

- Skill registry: `.agents/skills.registry.yaml`
- Current handoff: `.agents/HANDOFF.md`
- Maintainer skills: `.agents/skills/**/SKILL.md`
- Experiment records: `.agents/experiments/**`

Before changing code:

1. Identify the task type and target path.
2. Read `.agents/HANDOFF.md` for current status and next actions.
3. Select the smallest relevant maintainer skills.
4. Follow the selected skills.
5. For tuning work, use `ascend-npu-environment-orientation`,
   `ascend-inference-tuning-loop`, and `ascend-benchmark-evidence`.
6. Keep credentials, datasets, model weights, checkpoints, and generated
   experiment outputs out of Git.
7. Record the model, framework, hardware, dataset, and measurement protocol
   needed to reproduce performance claims.
8. Commit and push every coherent tuning stage. Record accepted, rejected,
   inconclusive, and failed outcomes; never erase a useful negative result.
9. Keep failed code off the final safe tree by reverting or disabling it in a
   later checkpoint while preserving its history and evidence.
10. Run `./scripts/validate-mst.sh`, plus focused tests when applicable.

Tool-specific files are adapters, not the source of truth.
