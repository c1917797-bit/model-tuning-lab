# Maintainer Handoff

## 0. Status

- Last updated: 2026-09-04.
- Repository: Model Tuning Lab, a Git-native Ascend NPU model-inference optimization workspace.
- Integrated maintainer model: `orient -> hypothesize -> baseline -> change -> verify -> measure -> decide` with pushed evidence and recovery checkpoints.
- Fresh clones route machine-bound work through
  `chicaihong01-host-maintenance`: resolve `chicaihong01/ma` through AWMCP,
  prove the direct target, then enter the canonical target-host repository.
- The repository-specific active worktree budget is eight.
- Active branch-local tuning workstreams (not integrated truth):
  - `work/exp-20260904-qwen35-dense-mtp-paper-to-ascend@07d723a`: dense-model Paper-to-Ascend, `planned / not-ready`, claims physical NPU0-3 and loopback port 8220.
  - `work/exp-20260904-qwen38-prefix-cache-general-eval-final@5d28f45`: fixed 2k40 Prefix Cache A/B, `started / not-ready`, claims physical NPU4-7 and loopback port 8210; Prefix Cache OFF baseline is complete and candidate is next.
- Superseded audit work: Dynamic MoE direct lowering is retained remotely at `work/exp-20260904-dynamic-moe-paper-to-ascend@55cc0a2`; its local worktree was reclaimed after the NPU lease was released. Do not merge that implementation into `main`.
- Runtime/process/device facts can change independently of Git; re-check all NPU, container, port, memory, and competing-process state before acting.
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

Maintain two isolated tracks without cross-contamination:

1. **Dense Paper-to-Ascend:** evaluate exact speculative decoding using the installed dense checkpoint's built-in Qwen3.5 MTP head. The primary variable is speculation OFF -> `qwen3_5_mtp` with three speculative tokens; baseline/candidate must run on physical NPU0-3 / port 8220 with exact-match correctness and repeated throughput/TPOT evidence.
2. **Prefix Cache A/B:** complete the frozen 2048-input/40-output protocol on physical NPU4-7 / port 8210. Prefix Cache OFF baseline is already recorded; next run is Prefix Cache ON followed by natural-prompt correctness and decision.

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
- Built a Paper-to-Ascend exemplar around Dynamic MoE and obtained a real negative result: the dynamic policy reduced token/expert pairs and accelerated expert GMM, but direct sort+cumsum+boolean compaction made whole-block latency much worse. The implementation was rejected, the paper/full-model conclusion remained inconclusive, and the workstream was superseded when the active installed target was confirmed to be dense.
- Selected a dense-compatible next paper direction: exact speculative decoding backed by the checkpoint's built-in MTP head, with immutable model/runtime identities and acceptance/abort thresholds recorded before baseline.

## 4. Current Action

Read both active branch-local handoffs before touching hardware. NPU0-3/8220 belongs to the Dense MTP experiment; NPU4-7/8210 belongs to the Prefix Cache experiment. Re-prove both leases and current processes before starting/stopping anything.

For the user's latest Paper-to-Ascend direction, continue the Dense MTP workstream from its `planned` checkpoint: live orientation, fresh baseline on NPU0-3, exact-match correctness gate, then candidate A/B. Do not mutate vLLM/vLLM-Ascend source unless profiling shows the built-in path is insufficient.

## 5. Next Actions

1. Dense MTP: read `.agents/workstreams/exp-20260904-qwen35-dense-mtp-paper-to-ascend/HANDOFF.md` and its experiment YAML, then re-prove NPU0-3/8220 isolation and run the declared fresh baseline before enabling speculation.
2. Dense MTP: compare speculation OFF vs `qwen3_5_mtp` with the exact frozen request protocol, three repetitions, greedy exact-match correctness, acceptance rate, throughput, TTFT/TPOT, and HBM evidence; checkpoint every stage.
3. Prefix Cache: read `.agents/workstreams/exp-20260904-qwen38-prefix-cache-general-eval-final/HANDOFF.md`; re-prove NPU4-7/8210 isolation, then run the three Prefix Cache ON repetitions against the already-recorded OFF baseline and perform natural-prompt correctness verification.
4. Keep the two tracks resource-isolated and never compare measurements across materially different model/runtime identities.
5. If either bounded method fails, preserve the negative result and profile the measured hot path before selecting another paper or changing low-level code.
6. Treat Qwen3-32B and HugeTLB release as separate future work: pass the Hugepage safety gate before any memory-pool change.
7. Reconcile global handoff/lessons only during serialized integration; branch-local progress remains branch-local truth until merged.

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
- Do not choose a paper by novelty alone. First prove that its required model mechanism exists in the installed checkpoint/runtime and that it addresses a measured bottleneck.
- Do not apply MoE-only optimizations to the current dense model just because the algorithm showed theoretical compute savings.
- Do not convert a rejected implementation into a rejected-paper claim; keep implementation, block-level, and full-model decision scopes explicit.
- Do not discard rejected, inconclusive, or failed experiments; recover active code in later checkpoints while preserving evidence.
- Do not merge failed active code into main.
- Do not release the 1 GiB HugeTLB pool merely because many pages look free; identify OVS/DPDK/VNF consumers and define rollback first.
- Do not assume a container is ready because it exists; prove listener and NPU workers in the same session.
- Do not disable TLS verification to repair Git.
- Do not commit credentials, SSH material, shell history, private certificates, datasets, model weights, checkpoints, or large generated profiler outputs.
- Do not commit or print the AWMCP verification value; obtain it through the
  approved runtime channel and pass it only in the connector `verify` field.
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

Active worktrees at this handoff:

```text
/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-dense-mtp-paper-to-ascend
/opt/host/vnf/austinov/worktrees/exp-20260904-qwen38-prefix-cache-general-eval-final
```

Dynamic MoE is audit-only on its retained remote branch; recreate a worktree from that remote branch only if a future MoE target justifies reopening it.
