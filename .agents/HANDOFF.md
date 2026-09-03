# Maintainer Handoff

## 0. Status

- Last updated: 2026-09-03.
- Repository: Model Tuning Lab, an Ascend NPU model-inference optimization
  workspace.
- Current active track: establish a Git-recorded tuning flywheel.
- Expected git state after completed work: clean worktree, validated checkpoint according to .agents/git-policy.yaml.

## 1. North Star

This repository uses skillsgit as a Git-native Ascend tuning loop:

```text
orient -> hypothesize -> baseline -> change -> verify -> measure -> decide
   ^                                                           |
   +---------------- Git evidence and next loop <---------------+
```

## 2. Current Focus

Make every tuning stage resumable and auditable. Preserve successful, failed,
rejected, and inconclusive attempts in pushed Git history while keeping the
final integrated tree safe.

## 3. Recent Progress

- Applied skillsgit `repository-transformation-v0.1` with the minimal profile.
- Added Ascend environment, tuning-loop, and benchmark-evidence skills.
- Added a versioned experiment-record template.
- Confirmed staged commit-implies-push policy for tuning workstreams.

## 4. Current Action

Validate and integrate the Ascend NPU tuning flywheel.

## 5. Next Actions

1. Create the first `.agents/experiments/exp-*.yaml` from the template.
2. Capture exact Ascend hardware, CANN, driver, framework, and model identity.
3. Record and push a repeated baseline before changing optimization variables.
4. Run one bounded hypothesis through the full decision and recovery loop.

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
- Do not discard failed or negative experiments; record their evidence and
  decision, then recover the active tree in a later commit.
- Do not merge failed active code into `main`.
```

## 8. Recovery / Resume Commands

```text
git status --short --branch
sed -n '1,220p' .agents/HANDOFF.md
./scripts/validate-mst.sh
python -m pytest
```
