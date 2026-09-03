# Maintainer Handoff

## 0. Status

- Last updated: 2026-09-04.
- Repository: Model Tuning Lab, a Git-native Ascend NPU model-inference optimization workspace.
- Integrated maintainer model: `orient -> hypothesize -> baseline -> change -> verify -> measure -> decide` with pushed evidence and recovery checkpoints.
- Current active tuning workstream: `work/exp-20260903-qwen38-prefix-cache-general-eval` at recorded tip `a497c49`; it is branch-local `started / not-ready`, not integrated truth.
- Current handoff-readiness workstream is being integrated from fetched remote `origin/work/handoff-readiness-20260904@8619fd49aa10d8996f39889cce90db0d2bdc681c`.
- Live snapshot on 2026-09-04: `qwen38_eval_baseline` listened on `127.0.0.1:8200`; physical NPU4-7 hosted its four TP workers; `qwen38_eval_client_run1` was running; NPU0-3 had no NPU processes; port 8100 was not listening; ordinary `MemAvailable` was about 64 GiB while `Hugetlb` remained about 1.9 TiB. Re-check all runtime facts before acting.
- Durable takeover guidance: `docs/LESSONS_LEARNED.md` and `docs/RUNBOOK.md`.
- Handoff/docs integration validation: Maintainer Skill Tree PASS (17 skills), full merge diff check PASS, workstream JSON parse checks PASS. `python -m pytest` was attempted but could not run because the host Python environment does not have the `pytest` module installed; no test PASS is claimed.

## 1. North Star

Make every Ascend inference optimization claim reproducible, auditable, rollback-safe, and resumable from Git alone. Preserve successful, rejected, inconclusive, and failed experiments while keeping failed active code out of the final safe tree.

```text
orient -> hypothesize -> baseline -> change -> verify -> measure -> decide
   ^                                                           |
   +---------------- Git evidence and next loop <---------------+
```

## 2. Current Focus

Finish the isolated Qwen3.8-27B prefix-cache experiment without contaminating its baseline. The workstream intentionally stopped using the historical NPU0-3/8100 service after an unrelated ablation runner changed it. Baseline and candidate are to run serially on the same physical NPU4-7 environment, with MMLU, GSM8K, and HumanEval correctness/workload snapshots frozen by hash.

Keep the distinction between three kinds of knowledge explicit:

1. integrated repository truth;
2. branch-local active experiment state;
3. live host state that must be re-proven each session.

## 3. Recent Progress

- Integrated the Ascend maintainer skills, experiment schema, workstream policy, and commit-implies-push tuning flywheel.
- Diagnosed the host's low ordinary memory as a ~1.9 TiB 1 GiB HugeTLB reservation rather than ordinary process consumption; no risky hugepage release was performed.
- Migrated the personal repository to `/opt/host/vnf/austinov/model-tuning-lab` with integrity checks and rollback backup; the old `/cache/austinov/model-tuning-lab` path remains a compatibility symlink.
- Repaired Git HTTPS runtime/CA handling without disabling TLS verification.
- Prepared source workspaces for `vllm-ascend`, CANN `ops-transformer`, `cannbot-skills`, and `cann-recipes-infer` under `/home/mtuser/cch`.
- Verified the vLLM-Ascend container provides `torch_npu.profiler`, `msprof`, and `asys`, and that the vLLM-Ascend profiler source uses Level1 + PipeUtilization.
- In the active prefix-cache workstream, added the general-eval harness, froze model/eval-data identity, established an isolated 8200/NPU4-7 baseline, and proved the target worker processes on those physical devices.
- Added durable success/failure history and maintainer takeover procedures in `docs/LESSONS_LEARNED.md` and `docs/RUNBOOK.md`.

## 4. Current Action

Resume the active prefix-cache workstream from its branch-local handoff. At the latest live snapshot, the isolated baseline service and an evaluation client were running on NPU4-7. Do not start another workload on NPU4-7 or stop that service until the active experiment state is re-checked.

The experiment hypothesis is that enabling vLLM prefix caching improves repeated-prefix TTFT and aggregate completion/throughput without quality regression. The experiment record requires three repeated measurements and serial baseline/candidate isolation on the same physical devices.

## 5. Next Actions

1. Read `.agents/workstreams/exp-20260903-qwen38-prefix-cache-general-eval/HANDOFF.md` and `.agents/experiments/exp-20260903-qwen38-prefix-cache-general-eval.yaml` in its worktree.
2. Re-run live orientation: container identity, 8200 readiness, NPU4-7 worker proof, NPU health/HBM, host ordinary memory, and competing processes. Do not rely on the snapshot above.
3. Complete and record the required repeated baseline measurements; checkpoint and push the baseline stage before changing prefix caching.
4. Stop the baseline cleanly, run the prefix-cache candidate serially on the same physical NPU4-7 environment, verify correctness, measure the same protocol, and decide accepted/rejected/inconclusive/failed.
5. If performance remains unexplained after the bounded hypothesis, capture a clean steady-state Decode profile and rank timeline/kernel/HCCL bottlenecks before changing `vllm-ascend` or `ops-transformer` code.
6. Treat Qwen3-32B and HugeTLB release as separate future work: re-prove free devices and pass the Hugepage safety gate in `docs/RUNBOOK.md` before any memory-pool change.
7. Update the relevant branch-local handoff at every non-trivial stop; reconcile this global handoff only during serialized integration.

## 6. Validation Commands

```text
./scripts/validate-mst.sh
python -m pytest
git diff --check
```

For tuning evidence, also run the exact benchmark/profiling commands declared in the experiment record and verify the intended NPU processes.

## 7. Do Not Do

```text
- Do not use chat history as the only handoff state.
- Do not overwrite global HANDOFF just to announce unmerged branch progress.
- Do not ignore workstream claims or resource leases; NPU4-7 currently belongs to the active prefix-cache experiment until live state proves otherwise.
- Do not claim an improvement without an apples-to-apples repeated protocol and correctness evidence.
- Do not discard rejected, inconclusive, or failed experiments; recover active code in later checkpoints while preserving evidence.
- Do not merge failed active code into main.
- Do not release the 1 GiB HugeTLB pool merely because many pages look free; identify OVS/DPDK/VNF consumers and define rollback first.
- Do not assume a container is ready because it exists; prove listener and NPU workers in the same session.
- Do not disable TLS verification to repair Git.
- Do not commit credentials, SSH material, shell history, private certificates, datasets, model weights, checkpoints, or large generated profiler outputs.
```

## 8. Recovery / Resume Commands

```text
git status --short --branch
git log -8 --decorate --oneline
git worktree list --porcelain
sed -n '1,260p' .agents/HANDOFF.md
sed -n '1,280p' docs/RUNBOOK.md
sed -n '1,320p' docs/LESSONS_LEARNED.md
./scripts/validate-mst.sh
python -m pytest
git diff --check
```

If a `work/*` branch is active, read its `.agents/workstreams/<task-id>/task.json` and branch-local `HANDOFF.md` before touching files or hardware resources.
