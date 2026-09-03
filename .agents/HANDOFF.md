# Maintainer Handoff

## 0. Status

- Last updated: 2026-09-03.
- Repository: Model Tuning Lab, a Python workspace for model fine-tuning,
  inference optimization, and evaluation experiments.
- Current active track: establish the repository-owned maintainer framework.
- Expected git state after completed work: clean worktree, validated checkpoint according to .agents/git-policy.yaml.

## 1. North Star

This repository uses skillsgit as a Git-native maintainer loop framework:

```text
AGENTS.md -> .agents/HANDOFF.md -> .agents/skills -> validation -> Git history
```

## 2. Current Focus

Bootstrap a minimal maintainer skill tree before model- or hardware-specific
implementation begins. Keep experimental claims reproducible and keep large or
sensitive artifacts outside Git.

## 3. Recent Progress

- Applied skillsgit `repository-transformation-v0.1` with the minimal profile.
- Added repository-specific maintenance, reproducibility, and artifact rules.
- Selected a maintainer-confirmed clean-main push policy for this bootstrap.

## 4. Current Action

Validate, commit, and push the maintainer bootstrap.

## 5. Next Actions

1. Define the first concrete model, framework, hardware, and dataset scope.
2. Add executable training, inference, and evaluation entry points.
3. Add focused tests and benchmark protocols alongside implementation.
4. Add repository-specific skills only after repeated maintenance behavior
   justifies them.

## 6. Validation Commands

```text
./scripts/validate-mst.sh
python -m pytest
git diff --check
```

## 7. Do Not Do

```text
- Do not use chat history as the only handoff state.
- Do not make AGENTS.md a giant prompt.
- Do not mix runtime product skills with maintainer skills.
- Do not commit secrets, datasets, weights, checkpoints, or generated outputs.
- Do not claim a performance improvement without an apples-to-apples protocol
  and captured environment details.
```

## 8. Recovery / Resume Commands

```text
git status --short --branch
sed -n '1,220p' .agents/HANDOFF.md
./scripts/validate-mst.sh
python -m pytest
```
