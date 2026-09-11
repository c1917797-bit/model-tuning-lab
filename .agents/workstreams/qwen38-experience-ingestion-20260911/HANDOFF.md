# Qwen3.8 Experience Ingestion

## 0. Status

- Execution: started; integration: not-ready.
- Branch: `work/qwen38-experience-ingestion-20260911`.
- Base: `origin/main` at `31c43a4c249c9d4c597372f47d989a7c10b2c9c4`.
- Live Qwen3.8 quality evaluation is out of scope and must not be stopped or modified.

## 1. North Star

Turn verified Qwen3.8 TP8 inference practice into reusable maintainer rules without converting experiment-specific numbers into universal recommendations.

## 2. Current Focus

Ingest model-identity proof, measurement-interference isolation, long-matrix evidence integrity, and lifecycle/cold-warm comparability lessons into the narrowest existing Ascend skills and an executable regression case.

## 3. Recent Progress

- Created this isolated workstream from synchronized `origin/main`.
- Declared knowledge claims for the three narrow Ascend skills and lessons ledger.

## 4. Current Action

Audit the reusable lessons against existing skill text, apply minimal additions, add a regression/eval case, then validate.

## 5. Next Actions

1. Update only existing narrow skills unless a distinct new trigger is proven.
2. Add concise repository-specific lessons and an executable validation case.
3. Run MST, JSON, focused regression, and whitespace checks.
4. Commit and push each coherent checkpoint.

## 6. Validation Commands

Run `./scripts/validate-mst.sh`, focused experience-ingestion checks, JSON parsing, and `git diff --check`.

## 7. Do Not Do

- Do not stop, restart, or mutate the live Qwen3.8 quality evaluation.
- Do not encode model-specific latency values as generic skill thresholds.
- Do not claim service alias, architecture class, or directory name alone proves model identity.
- Do not treat a benchmark overlapped by large-file hashing or compilation as clean evidence.

## 8. Recovery / Resume Commands

Run `git status --short --branch`, `git log -8 --decorate --oneline`, inspect this handoff and task manifest, then continue from Current Action.
