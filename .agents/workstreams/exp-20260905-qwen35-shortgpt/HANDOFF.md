# Qwen3.5 ShortGPT Paper-to-Ascend handoff

## State

- Workstream: `exp-20260905-qwen35-shortgpt`
- Maintainer branch: `work/exp-20260905-qwen35-shortgpt`
- Dependency: `exp-20260904-qwen35-query-rewrite-3x-e2e`
- Current phase: Block Influence collection/analysis host tools are ready; wait for the guarded fused-tail v9 queue and for physical NPU4-7 to become idle.
- Goal remains open: every concurrency cell must reach at least 2x TTFT and 2x TPOT versus the immutable original baseline.

## Scope and resource boundary

- Model: dense hybrid Qwen3.5-27B at the current-host path `/cache/austinov/Qwen3.8-27B`. The directory name is historical; `config.json` identifies `qwen3_5`, 64 layers, hidden size 5120, SHA256 `191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`. The previously supplied `/softwarePlatform/c00879303/Qwen3-5/Qwen3.5-27B/` path is absent on this host.
- Runtime: vLLM/vLLM-Ascend 0.23.0, BF16, TP4/DP1, no quantization.
- Workload: real `/cache/cch/query_rewrite.jsonl`; the former `/home/mtuser/cch` location is obsolete.
- Frozen concurrency matrix: 1, 5, 8, 16.
- Only physical NPU4-7 are in scope, mapped to logical 0-3 inside the task container.
- Physical NPU0-3 are prohibited. Existing workloads on NPU4-7 are also protected: check Docker device reservations first and `npu-smi` second; wait on any conflict and never stop an unowned container or process.

## Immutable reference and retained stack

Original p50 reference:

| Concurrency | TTFT ms | TPOT ms |
| ---: | ---: | ---: |
| 1 | 928.328810 | 38.471822 |
| 5 | 1092.265540 | 53.831043 |
| 8 | 1082.311615 | 67.616824 |
| 16 | 2075.070625 | 80.811616 |

Retained stack is BF16 TP4/DP1, MatMulAllReduce on, dense gate/up prefetch ratio 0.1, NZ1, FlashComm1/2 off, async scheduling, FULL_DECODE_ONLY, HCCL_BUFFSIZE=512, max model length 133000. It already passes the TTFT target, with TTFT speedups 2.190x/2.227x/2.198x/2.316x and TPOT speedups 1.334x/1.417x/1.532x/1.556x.

## Selected paper method

ShortGPT is the next inference-time algorithm candidate because it removes low-influence decoder blocks without retraining. Qwen3.5 has 64 hybrid layers, repeating three linear-attention/GDN layers and one full-attention layer, so no layer list is copied from Llama results. Measure Block Influence on the real query_rewrite distribution first, then freeze a Qwen3.5-specific removal ladder.

The source worktree is `/cache/cch/.worktrees/exp-20260905-qwen35-shortgpt-vllm`, branch `work/exp-20260905-qwen35-shortgpt`, local commit `18c4d061529d226dd0d699d9e3e1df16dadf29d7`. It adds default-off Block Influence recording and default-off layer skipping. Static validation passed. Push to `vllm-project/vllm-ascend` is blocked by GitHub 403 for the current account; do not retry unchanged. The local commit is therefore an explicit dependency until a writable fork or maintainer remote is supplied.

Host-side tools are `scripts/collect_qwen35_shortgpt_bi.py` and `scripts/analyze_qwen35_shortgpt_bi.py`. The collector sends one-token completions sequentially and writes only hashes, counts, status, and timing. The analyzer validates all 64 layers, computes token-weighted influence, ranks globally and by layer type, checks split-ranking Spearman stability, and emits the predeclared 8/16/20-layer planning sets only when the evidence is stable. `scripts/run_qwen35_shortgpt_bi_service.sh` launches the pinned eager TP4 diagnostic and fails closed on any NPU4-7 reservation/process or port conflict. `scripts/run_qwen35_shortgpt_bi_diagnostic.sh` waits for readiness, quarantines startup observations, collects 32 real prompts from dataset SHA256 `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`, stops only its exact container, analyzes the ranking, and hashes the artifacts.

`scripts/freeze_qwen35_shortgpt_layer_set.py` converts one stability-passing 8/16/20 planning point into an immutable JSON contract bound to the BI analysis hash, source commit, and model config hash. `scripts/run_qwen35_shortgpt_fused_service.sh` refuses any missing, edited, non-frozen, wrong-source, wrong-model, or out-of-range layer contract, then mounts both the ShortGPT source and the pinned fused-tail operator into the retained compiled stack. The generic candidate runner accepts `CANDIDATE_MODE=shortgpt-fused-tail` and requires the live fused topology before query traffic: for N removed layers it expects `64-N` normalized copies and `128-2N` fused tails on each of four TP ranks, while the large compile range remains inapplicable.

## Execution loop

1. Let the already queued fused-tail v9 candidate finish. Require 64 normalized plus 128 fused patterns per TP rank in decode range 1-16 and the large range to remain inapplicable.
2. If v9 meets every final threshold, close the umbrella goal and retain ShortGPT only as prepared follow-up work.
3. Otherwise, once NPU4-7 are idle, run the unpruned retained model with Block Influence recording on privacy-safe samples from the real workload. Instrumentation is the only primary variable in this diagnostic phase.
4. Aggregate influence by layer and layer type. Record sample count, prompt-length coverage, and ranking stability. Freeze the layer sets before any pruning benchmark.
5. Evaluate a conservative cumulative removal ladder (initial planning points: 8, 16, and at most 20 layers), each as a separate attempted stage. Stop escalation at the first correctness failure.
6. For every viable set, run a same-runtime unpruned control for semantic attribution, then the frozen c1/c5/c8/c16 matrix against the immutable original. Promote only a set that passes correctness, improves TPOT versus the retained stack in every cell, and reaches both final 2x goals in every cell.
7. Stack the accepted algorithm with the accepted fused-tail operator, profile the resulting E2E service, finalize hashes and the decision, commit and push the maintainer evidence, and update the canonical handoff only at integration.

## Correctness and abort gates

- Default behavior must be unchanged when both ShortGPT environment variables are absent.
- Require service readiness, 32/32 completed requests, zero request errors, and natural stops in every measured cell.
- Exact historical output hashes are diagnostic only because no-op controls previously changed them. Compare candidate with a same-runtime unpruned control using the established privacy-safe semantic review and require no material business-quality regression.
- Abort on startup/capture failure, non-finite output, missing layer samples, unstable layer ranking, any resource conflict, or any attempt to use quantization.

## Prepared rollback

Unset `VLLM_ASCEND_QWEN35_SKIP_LAYERS` and `VLLM_ASCEND_QWEN35_BI_DIR`, remove the ShortGPT source overlay, and relaunch the retained pinned stack. Both features are default off.

## Known external state

- The only guarded fused-tail v9 queue is corrected operation `exec-0000000000000060`, host PID `579462`; it is waiting without NPU allocation and must not be duplicated. The superseded operation `exec-0000000000000004` was terminated after its Docker reservation probe was found to use invalid CLI argument ordering.
- External NPU4-7 chains may still be running. Their containers, scripts, logs, and processes are out of scope and must not be changed.
- Maintainer commit `c033270ec6d0646da57418488196362ee58ed3f8` contains the frozen ShortGPT plus fused-tail E2E harness and is locally clean. This branch is three commits ahead of `origin/work/exp-20260905-qwen35-shortgpt@d1ec5b06fcef562b00c1c947c3cc901bff253978`; a bounded 25-second push attempt timed out with no output, so remote publication remains pending.
- The umbrella workstream is likewise three local commits ahead of its upstream checkpoint because the same Git transport is hanging. Do not claim either branch is pushed until local HEAD and upstream are verified equal.
- The global `.agents/HANDOFF.md` is integrated truth; keep branch-local progress here until integration.
