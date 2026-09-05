# Qwen3.5-27B performance optimization lessons and handoff

Updated: 2026-09-05

## Authoritative state

- Goal: improve both TTFT and TPOT by 2x without quantization, using cumulative parameter, algorithm and operator treatments.
- Immutable comparison: BF16 TP8/DP1 baseline v5 on physical NPU0-7 and the first 32 records of `/cache/cch/query_rewrite.jsonl`, repeated three times at c1/c5/c8/c16.
- Baseline evidence: `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp8-user-baseline-v5-20260905T184600Z`.
- Baseline summary SHA256: `e3e03a5f1a5ce8d3e2d5f35ccf6a410d5d96555ad9012ba5881fd9227246639d`.
- Current resources: NPU0-7 idle. Previously paused p0/qwen36 schedulers were not restarted.
- Current decision: retain the non-speculative TP8 baseline as denominator. No TP8 optimization is promoted yet.

## What succeeded

| Treatment or practice | Evidence-backed lesson | Disposition |
|---|---|---|
| Reconstructed TP8 baseline | 12/12 cells, 384/384 requests, zero errors, natural stop, exact runtime/config proof | Frozen denominator |
| Ascend MatMulAllReduce | Repeatedly produced large TTFT improvements in TP4 development runs; TPOT gains were smaller | Useful ingredient, already present in TP8 baseline; never credit it from cross-topology comparisons |
| Dense gate/up prefetch ratio 0.1 | Smaller bounded prefetch was better behaved than the rejected 18 MB attempt | Retained only in the historical TP4 stack; must be revalidated on TP8 before promotion |
| Selective NZ mode | Demonstrated that layout changes can help dense FFN, but compatibility must be scoped per linear path | Reuse the selective approach, not blanket NZ |
| Exact-container and device guards | Prevented competing workloads and made cleanup/recovery auditable | Mandatory for every run |
| Three-repeat aggregation | Exposed cold-start/high-concurrency variance, especially c16 TTFT | Mandatory; never promote from one cell or one repetition |
| TP8 MTP local-argmax repair | Avoided the full-logits startup OOM, completed 384/384 requests, and proved speculative activation | Use this source base for bounded depth tuning |
| Profiling before implementation | Identified collective and matmul as dominant categories and prevented blind operator work | Continue profile-guided selection |

## What failed and why

| Attempt | Failure class | Reusable conclusion |
|---|---|---|
| FlashComm1 initial integration | Qwen3.5 GDN symbolic sequence-parallel shape mismatch before readiness | Do not relaunch unchanged; activation must be proven through graph capture |
| FlashComm1 repaired v3 | Correctness/activation passed, but TPOT regressed in all cells and TTFT regressed in c1/c5/c8 | Reject from retained stack |
| Blanket BF16 NZ + MMAR | `aclnnMatmulAllReduce` required ND input and rejected FRACTAL_NZ | Layout optimization must respect communication-op contracts |
| NZ recovery with MMAR off | Some latency gains, but c16 regressed and output hashes/quality gate did not pass | Do not promote; topology-wide E2E gates override microbench wins |
| HCCL AIV | No acceptable end-to-end improvement/compatibility result | Do not retry without a new mechanism or profile hypothesis |
| TP2/PP2 and TP2/DP2 | Capacity/startup or c1 fail-fast failures | Topology is not a free speedup; prove memory headroom and c1 first |
| Static decode kernel | High-concurrency regression | Decode improvements must pass all four concurrency cells |
| `TASK_QUEUE_ENABLE=2` | Graph-capture startup failure | Keep baseline setting unless runtime support changes |
| Prompt Lookup Decoding | Real inference result did not satisfy the target | Workload repetition was insufficient to offset overhead |
| ShortGPT/remove-layer | Semantic correctness failure | Training-free layer removal is excluded for this goal |
| Fused MMAR+Add+RMS tail v1-v17 | Multiple matcher, dispatcher, graph contract and partial-coverage failures; final cumulative E2E did not justify promotion | Do not resume old variants unchanged; require whole-model economics before more fusion work |
| MTP local-argmax v1 | Externally interrupted before readiness, zero requests | Invalid experiment, not algorithm evidence |
| MTP local-argmax TP8 v2 | Full-logits dummy-run memory pressure; exit 137, `OOMKilled=false`, zero requests; all cards released | Startup-resource failure, not performance evidence. Next design must avoid materializing full draft logits or reduce dummy-run memory |
| MTP local-argmax TP8 k1 v3 | Valid 12-cell run; logged acceptance 85.32%, but TTFT speedup was 0.868x-0.934x and TPOT 0.965x-1.054x | Reject k1 performance; test depth 3 as a new primary variable |
| Edited launcher while it was executing | Matrix and shutdown completed, then changed script bytes caused a postprocessing parse error | Wait for terminal state or create a versioned successor; never edit an executing script |

## Rules learned

1. Compare only against TP8 baseline v5 with the same dataset hash, prompt path, generation policy, concurrency and three-repeat aggregation.
2. Change one primary treatment per attribution run, then stack only accepted treatments.
3. Microbench and profiling results select candidates; they never prove E2E improvement.
4. Correctness and activation gates precede performance. A request-free startup failure cannot be scored as a slowdown.
5. Require all c1/c5/c8/c16 cells to pass. A gain at c16 cannot compensate for regressions elsewhere.
6. Keep quantization prohibited.
7. Preserve exact logs, config, container inspection, NPU snapshots, result marker and SHA256SUMS under a unique evidence root.
8. Never reuse an output directory, bypass the device-idle guard, kill by broad process pattern, or compete with an existing workload.
9. Cross-run response hashes are diagnostics, not a calibrated semantic gate; retain aggregate reference-quality checks and privacy-safe hashes.
10. Historical TP4 results guide hypotheses only. They are not part of the current TP8 goal denominator.

## Resume entry point

1. Read this file, then the latest section of `HANDOFF.md`, the experiment YAML, and `task.json`.
2. Recheck `git status`, exact branch/HEAD, containers, host processes and the NPU0-7 process table. Recorded idle state is never sufficient.
3. Verify the TP8 baseline summary hash before computing any ratio.
4. Highest-value bounded next step: validate source commit `37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd`, which mounts both the Qwen3.5 MTP model patch and the Ascend proposer patch so dummy run cannot bypass local argmax; then prove startup, local-argmax activation and speculative acceptance before benchmark traffic.
5. If that repair changes more than the draft-token selection path, start a new experiment attempt and state the expanded primary variable explicitly.
6. Run the complete repeated matrix, correctness, profiling and decision gates. Promote only an additive treatment that improves both TTFT and TPOT across the frozen cells.

## Recovery and rollback

- TP8 baseline launcher/config:
  - `configs/qwen35-query-rewrite-tp8-user-baseline.yaml`
  - `scripts/run_qwen35_tp8_user_baseline_service.sh`
  - `scripts/run_qwen35_tp8_baseline_matrix.py`
  - `scripts/run_qwen35_tp8_user_baseline.sh`
- MTP v2 failure evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp8-mtp-local-argmax-k1-20260905T192433Z`.
- MTP source checkpoint: `/cache/cch/.worktrees/exp-20260905-qwen35-mtp-local-argmax`, commit `37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd`.
- Rollback is the non-speculative TP8 baseline. Do not restart paused external workloads unless the user requests it.
