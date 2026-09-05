# Qwen3.5 ShortGPT Paper-to-Ascend handoff

## State

- Workstream: `exp-20260905-qwen35-shortgpt`
- Maintainer branch: `work/exp-20260905-qwen35-shortgpt`
- Dependency: `exp-20260904-qwen35-query-rewrite-3x-e2e`
- Current phase: Block Influence collection/analysis host tools are ready. The fused-tail v9 activation gate rejected the candidate before benchmark traffic; one guarded v10 queue now waits for the protected `p0_r15` chain to finish and for physical NPU4-7 to become stably idle.
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

The source worktree is `/cache/cch/.worktrees/exp-20260905-qwen35-shortgpt-vllm`, branch `work/exp-20260905-qwen35-shortgpt`, local commit `54a6bb40ac83771538b3c859bcf9c55e2e51854a`. It adds default-off Block Influence recording and default-off layer skipping. Block Influence sampling covers both prompt head and tail, and rank-zero selection prefers the initialized distributed process group so TP duplicates do not bias the layer ranking. The exact vLLM-Ascend 0.23.0 image passes all 9 focused unit tests with `TORCH_DEVICE_BACKEND_AUTOLOAD=0`; a separate direct-module runtime smoke also validates head/tail selection, identity influence, JSONL emission, and distributed-rank precedence. These are CPU/no-device checks, so the fresh real-NPU BI run remains the integration gate. Push to `vllm-project/vllm-ascend` is blocked by GitHub 403 for the current account; do not retry unchanged. The local commit is therefore an explicit dependency until a writable fork or maintainer remote is supplied.

Host-side tools are `scripts/collect_qwen35_shortgpt_bi.py` and `scripts/analyze_qwen35_shortgpt_bi.py`. The collector sends one-token completions sequentially and writes only hashes, counts, status, and timing. The analyzer validates all 64 layers, computes token-weighted influence, ranks globally and by layer type, checks split-ranking Spearman stability, and emits the predeclared 8/16/20-layer planning sets only when the evidence is stable. `scripts/run_qwen35_shortgpt_bi_service.sh` launches the pinned eager TP4 diagnostic and fails closed on any NPU4-7 reservation/process or port conflict. `scripts/run_qwen35_shortgpt_bi_diagnostic.sh` waits for readiness, quarantines startup observations, collects 32 real prompts from dataset SHA256 `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`, stops only its exact container, analyzes the ranking, and hashes the artifacts.

`scripts/freeze_qwen35_shortgpt_layer_set.py` converts one stability-passing 8/16/20 planning point into an immutable JSON contract bound to the BI analysis hash, source commit, and model config hash. `scripts/run_qwen35_shortgpt_fused_service.sh` refuses any missing, edited, non-frozen, wrong-source, wrong-model, or out-of-range layer contract, then mounts the ShortGPT model hooks from source `54a6bb40ac83771538b3c859bcf9c55e2e51854a` and the compiler/fusion files from operator source `4424cc24ecfa355ce2b17ab48e04fb6fc4944e39` into the retained compiled stack. The two source identities are checked separately so a newer operator fix cannot be silently shadowed by the algorithm worktree. The generic candidate runner accepts `CANDIDATE_MODE=shortgpt-fused-tail` and requires the live fused topology before query traffic: for N removed layers it expects `64-N` normalized copies and `128-2N` fused tails on each of four TP ranks, while the large compile range remains inapplicable.

## Execution loop

1. Let the only guarded fused-tail v10 queue finish. It must wait for `/cache/austinov/p0/r15.log` to contain `R15_DONE`, then pass four stable idle checks before it may allocate NPU4-7. Require 64 normalized plus 128 fused patterns per TP rank in decode range 1-16 and the large range to remain inapplicable.
2. If v10 meets every final threshold, close the umbrella goal and retain ShortGPT only as prepared follow-up work.
3. Otherwise, after v10 is terminal and NPU4-7 are idle, run a fresh unpruned retained model with Block Influence recording on privacy-safe samples from the real workload. Instrumentation is the only primary variable in this diagnostic phase; never reuse the empty failed probe root `bi-20260905T125900Z`.
4. Aggregate influence by layer and layer type. Record sample count, prompt-length coverage, and ranking stability. Freeze the layer sets before any pruning benchmark.
5. Evaluate a conservative cumulative removal ladder (initial planning points: 8, 16, and at most 20 layers), each as a separate attempted stage. If v10 is accepted, use `CANDIDATE_MODE=shortgpt-fused-tail`; if the operator is rejected or slower, first use `CANDIDATE_MODE=shortgpt-retained` so the algorithm is not forced to carry a negative operator. Stop escalation at the first correctness failure.
6. If v10 completes its matrix, use that unpruned candidate as the same-runtime semantic control. If v10 fails activation or produces no candidate matrix, first run a fresh `CANDIDATE_MODE=shortgpt-retained-control` matrix and use it instead. That control loads the pinned ShortGPT hooks but deliberately omits all skip-layer variables and leaves the fused-tail pass disabled, so the documented fallback is executable and default-off. v9 is invalid as a control because it was rejected before traffic and produced no candidate directory. Then run the frozen c1/c5/c8/c16 matrix against the immutable original. The pruned ShortGPT runner requires `SEMANTIC_CONTROL_DIR` and compares privacy-safe aggregate answer similarity plus exact-match counts with strict default bounds (mean and p50 similarity drop at most 0.02; raw and normalized exact-match drop at most 1 of 32). Promote only a set that passes this gate, improves TPOT versus the retained stack in every cell, and reaches both final 2x goals in every cell.
7. Stack the accepted algorithm with the accepted fused-tail operator, profile the resulting E2E service, finalize hashes and the decision, commit and push the maintainer evidence, and update the canonical handoff only at integration.

## Correctness and abort gates

- Default behavior must be unchanged when both ShortGPT environment variables are absent.
- Require service readiness, 32/32 completed requests, zero request errors, and natural stops in every measured cell.
- Exact historical output hashes are diagnostic only because no-op controls previously changed them. Compare candidate with a same-runtime unpruned control using the established privacy-safe semantic review and require no material business-quality regression.
- Abort on startup/capture failure, non-finite output, missing layer samples, unstable layer ranking, any resource conflict, or any attempt to use quantization.

## Prepared rollback

Unset `VLLM_ASCEND_QWEN35_SKIP_LAYERS` and `VLLM_ASCEND_QWEN35_BI_DIR`, remove the ShortGPT source overlay, and relaunch the retained pinned stack. Both features are default off.

## Known external state

- Fused-tail v9 operation `exec-0000000000000060` terminated with exit 72 after all four TP ranks reported only 0 normalized full copies and 64 fused patterns in the decode range. Its gate expected 64/128 per rank, so it rejected the run before benchmark traffic and created no candidate cell or decision.
- The source-side symbolic full-slice fix is pinned at `4424cc24ecfa355ce2b17ab48e04fb6fc4944e39`. Static compile/diff checks passed; new source tests could not execute because every available no-NPU container import failed while loading the `torch_npu` backend, so target validation remains the live v10 activation gate.
- The first v10 launch, `exec-00000000000000e6`, hit a 30-second synchronous tool timeout without leaving a host waiter or allocating an NPU. The only active replacement waiter is asynchronous operation `exec-00000000000000f7`; do not duplicate it. It waits for the external `p0_r15` chain to emit `R15_DONE` and then for four stable idle checks before starting.
- The protected `p0_r15` chain currently owns NPU4-7 and may release them briefly between its sequential configurations. Its containers, scripts, logs, and processes are out of scope and must not be changed. Wait for terminal completion, not a transient idle window.
- The first ShortGPT BI attempt, operation `exec-00000000000000c8`, exited 48 before Docker creation because `p0_r15` held NPU4-7. Its empty output root `/cache/austinov/eval-runs/exp-20260905-qwen35-shortgpt/bi-20260905T125900Z` is not evidence and must never be reused.
- Maintainer implementation history through `7b1fdbaaf8d5411a5e5101150a276141328510c2` includes semantic-quality gating, operator attribution, incremental TPOT acceptance, retained-config preservation, and dirty-source rejection in addition to the original frozen harness. Subsequent local checkpoints `ef8c82c4e0333b6ae0f3d6c22cfdeae045a6a880` and `84d0bd470e11c9617efee4b16990d370d85b7482` pin the v10 operator source and make the retained semantic-control fallback executable. The branch remains ahead of the last verified upstream, `origin/work/exp-20260905-qwen35-shortgpt@d1ec5b06fcef562b00c1c947c3cc901bff253978`; a bounded 25-second push attempt timed out with no output, so remote publication remains pending.
- The umbrella workstream is also ahead of its upstream checkpoint because the same Git transport is hanging. Do not claim either branch is pushed until local HEAD and upstream are verified equal.
- The global `.agents/HANDOFF.md` is integrated truth; keep branch-local progress here until integration.
