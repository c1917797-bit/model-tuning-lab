# drror_vllm_ascend project manifest

This directory contains the opt-in DRRQR plugin, tests, tools, and compact
experiment evidence for Qwen3.8-27B on vLLM-Ascend.

## Provenance

- Source repository:
  `https://github.com/c1917797-bit/drror_vllm_ascend.git`
- Imported branch: `research/qwen38-drrqr-correctness-20260908`
- Imported commit: `7eec54c9caacad3f37f80a493e01171ec8f62003`
- Imported tree: `9fcefa3b84e1c79b5ac283eb39dd8cbb75362555`
- History policy: the source commit is a parent of the import commit, so all
  25 committed source revisions remain reachable. The import is not squashed.

Inspect the original path history with:

```sh
git log --oneline 7eec54c9caacad3f37f80a493e01171ec8f62003
git show 7eec54c9caacad3f37f80a493e01171ec8f62003:README.md
```

The source working tree's uncommitted goal-alignment rule was split by scope:
the reusable three-level review is maintained in the root
`mst-practice-iteration-planning` skill, while DRRQR-specific acceptance and
candidate-selection constraints remain in this project's `AGENTS.md`.

The untracked `native/`, `tests/test_native_build_gate.py`, and
`tests/test_native_codegen_gate.py` were not imported. They were outside the
named source commit and had not passed the project's validation gates.

## Maintenance

Use the root `.agents/skills.registry.yaml` for maintenance workflows and
this directory's `AGENTS.md` for DRRQR-specific constraints. Project-local
`skills/model-infer-profiling` is an audited experiment skill, not a second
Maintainer Skill Tree.

Large runtime artifacts, models, datasets, CANN builds, and profiler traces
remain outside Git.
