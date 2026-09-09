# Qwen3.5 Experience Ingestion

## 0. Status

- Execution: in-progress; integration: not-ready.
- Branch: work/qwen35-experience-ingestion-20260909.
- Base: origin/main at 31c43a4c249c9d4c597372f47d989a7c10b2c9c4.
- Resume checkpoint: 88dc4f3e8568892de2d80f7ec503b61a0b14620c;
  its existing six-file lesson update was validated and pushed in this turn.

## 1. North Star

Turn verified Qwen3.5 Ascend optimization experience into reusable maintainer
rules without copying experiment-specific claims into generic skills.

## 2. Current Focus

Ingest four durable lessons: exact worker/rank activation proof for runtime
patches, overlap-safe profiler accounting, multi-rank collective lifecycle and
buffer-ownership gates, and quality-claim boundaries for datasets without
reference answers.

## 3. Recent Progress

- Created an isolated workstream from synchronized origin/main.
- Froze the maintainer contracts and declared exclusive knowledge claims.

## 4. Current Action

Audit historical claims against artifacts; add a compact takeover packet,
structured lesson/evidence ledgers, warmup-generalization safeguards and
executable verification. Preserve all dirty performance-workstream material.
No NPU service mutation is part of this documentation task.

## 5. Next Actions

1. Apply the experience updates without changing experiment-specific thresholds.
2. Validate the full skill tree, JSON, and whitespace.
3. Commit and push the implementation checkpoint.
4. Mark the workstream ready with exact source evidence.

## 6. Validation Commands

Run scripts/validate-mst.sh, JSON parsing, and git diff --check.

## 7. Do Not Do

- Do not claim the Qwen3.5 40%/20% target is achieved.
- Do not embed dataset contents, raw profiles, model paths, credentials, or peer IDs.
- Do not turn failed IPC collective bytes into a recommended implementation.

## 8. Recovery / Resume Commands

Run git status --short --branch, git log -8 --decorate --oneline, and inspect
this handoff.
