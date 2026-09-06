# Qwen3.5-27B performance optimization lessons and handoff

Updated: 2026-09-06

## Authoritative state

- Goal: improve both TTFT and TPOT by 2x without quantization, using cumulative parameter, algorithm and operator treatments.
- Immutable comparison: BF16 TP8/DP1 baseline v5 on physical NPU0-7 and the first 32 records of `/cache/cch/query_rewrite.jsonl`, repeated three times at c1/c5/c8/c16.
- Baseline evidence: `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp8-user-baseline-v5-20260905T184600Z`.
- Baseline summary SHA256: `e3e03a5f1a5ce8d3e2d5f35ccf6a410d5d96555ad9012ba5881fd9227246639d`.
- Current resources after suffix-k15 c1 fail-fast: the exact candidate container exited 0, matching task processes are absent, and NPU0-3 have no running processes. NPU4-7 remain outside this run's scope even when an instantaneous process snapshot is idle.
- Current decision: reject suffix decoding on the current vLLM-Ascend 0.23.0 integration; retain the frozen non-speculative denominator and return to graph-compatible MMAR/matmul work.
- Latest TP4/NPU0-3 tail-aware screen `tp4-npu03-mmar-prefetch0p1-hccl1024-static-kernel-v1` completed 128/128 requests with zero errors and natural EOS. It is rejected from promotion: TTFT p50 reaches 2x only at c1/c5, TPOT p50 is only 1.30x-1.42x, and p99 TPOT regresses at c5/c8/c16. Tail-aware decision SHA256: `54c0b690ca3e2c53794457711fa2585d20797365133b17f13e3eb0e955f4fa0a`.
- The independent local Qwen3.5-4B BF16 draft route is exhausted for vLLM-Ascend 0.23.0. Suffix Decoding was then rejected by a complete c1 P50/P95/P99 fail-fast: synchronous scheduling plus uncaptured speculative batches overwhelmed its 30.18% token acceptance.

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
| MTP local-argmax TP8 k3 screen | Valid first repetition, 128/128 requests, 66.39% token acceptance; c16 TTFT/TPOT speedups collapsed to 0.153x/0.321x | Reject at fail-fast screen; deeper speculation overloads high concurrency |
| Independent Qwen3.5-4B draft v1 | vLLM applied the MTP config override despite explicit `method=draft_model`; loading 2560-hidden draft weights into 5120-hidden MTP tensors failed before traffic | Startup-contract failure, not performance evidence. Preserve v1 and retry only with the pinned explicit-draft architecture fix |
| Independent Qwen3.5-4B draft v2 | Config repair worked, then generic DraftModelProposer rejected M-RoPE; the extra-slot expansion kernel is one-dimensional | Exhaust for vLLM-Ascend 0.23.0. Do not bypass the assertion without a tested three-axis position/slot implementation |
| Suffix Decoding v1 with async scheduling | vLLM 0.23.0 rejected this proposer/scheduler combination before worker startup | Retry only with explicit synchronous scheduling and charge that compatibility change to the candidate's E2E result |
| Suffix Decoding v2 with 16 drafts | Ascend fused TND attention counts the current token too, producing threshold 17 above its limit of 16 | Bound suffix drafts at 15 so the effective threshold is 16; preserve the assertion |
| Suffix Decoding v3 with 15 drafts | c1 completed 32/32 with no errors, but TPOT P50/P95/P99 speedups were only 0.255x/0.247x/0.368x and TTFT P95/P99 only 0.162x/0.156x | Reject at c1 fail-fast. Do not retune depth until suffix can retain async scheduling and captured decode graphs |
| Legacy exact TP4/DP2 FULL_AND_PIECEWISE launcher | Model-inspection subprocess could not obtain the Ascend device/arch and exited before model load | Preserve failure; retry only through the proven device-mapping launcher |
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
4. Obtain explicit approval before stopping p0_r19; do not bypass the guard while it owns NPU4-7.
5. Start RUNTIME_ROLE=tp4-dp2-fullpiece-user through scripts/run_qwen35_tp8_user_baseline_service.sh, then run one complete c1/c5/c8/c16 screen.
6. Only if the screen passes predeclared latency/non-regression gates, run the remaining repetitions and full correctness, profiling and decision gates.

## Recovery and rollback

- TP8 baseline launcher/config:
  - `configs/qwen35-query-rewrite-tp8-user-baseline.yaml`
  - `scripts/run_qwen35_tp8_user_baseline_service.sh`
  - `scripts/run_qwen35_tp8_baseline_matrix.py`
  - `scripts/run_qwen35_tp8_user_baseline.sh`
- MTP v2 failure evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp8-mtp-local-argmax-k1-20260905T192433Z`.
- MTP source checkpoint: `/cache/cch/.worktrees/exp-20260905-qwen35-mtp-local-argmax`, commit `37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd`.
- MTP k3 screen evidence: /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp8-mtp-local-argmax-k3-v2-20260905T215000Z; screen-decision SHA256 6c8698f8a52c1db91f5062f781e085b85101d5372ea7bbf283c544ea9f25ec95.
- User TP4/DP2 candidate integration: commit a625b2b, config configs/qwen35-query-rewrite-tp4-dp2-fullpiece-user.yaml.
- Legacy-launcher failure evidence: /cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp4-dp2-fullpiece-user-20260905T220500Z.
- Rollback is the non-speculative TP8 baseline. Do not restart paused external workloads unless the user requests it.

## Parameter provenance and attribution

- A user-reported configuration is valuable hypothesis evidence, but it must
  remain a candidate until reproduced on the frozen workload.
- TP4/DP2 changes both per-request execution and aggregate capacity; always
  report latency and throughput separately against TP8/DP1.
- Do not credit environment variables that are already active in the baseline
  or have no installed-source reader. Require actual runtime activation.
- Never edit a shell script while an existing shell process may still be
  reading it. Create a versioned successor or wait for the process to finish.

## TP4 MTP k3 local-argmax lessons

- Repaired target-verified MTP k3 is the first TP4 candidate in this loop to
  exceed 2x TPOT P50 at c1, c5 and c8; retain it as a stack component.
- A 66.16% token acceptance rate is not sufficient to guarantee high-load
  benefit: c16 TPOT P50 reached only 1.489x and TPOT P99 regressed to 0.979x.
- Always inspect TTFT and TPOT P95/P99. P50-only reporting would have hidden
  TTFT tail regressions at c1, c8 and c16.
- The first c1 screen after graph capture can include cold tail behavior.
  Preserve it as E2E evidence; use repeated warmed runs only as an explicitly
  separate attribution experiment, never by deleting the cold observation.
- An analyzer's frozen hashes are baseline-specific. Route an explicitly
  selected TP4/NPU0-3 baseline to its matching hash-verifying analyzer.
- Greedy response hashes vary across the existing baseline repetitions, so
  hashes are diagnostics, not proof of semantic equivalence. 精读无损 still
  requires a meaningful paired reference or calibrated judge.

## BT40960 tail-aware result and baseline policy

- The authoritative iteration denominator is now the frozen TP4/NPU0-3
  MTP-off baseline. Its engine log proves `speculative_config=None`.
- Compare candidates only with that MTP-off denominator while tuning. Measure
  a same-protocol MTP-on baseline only after the 2x performance and semantic
  gates pass, so final attribution separates ordinary MTP benefit from the
  cumulative optimized stack.
- Raising `max_num_batched_tokens` from 32,768 to 40,960 is not sufficient.
  Across three repetitions it reaches 2x only for TPOT P50 at c1/c5/c8 and
  TPOT P95 at c1; no TTFT percentile reaches 2x.
- c16 TPOT P99 speedup is only 0.431x even though c16 TTFT P95/P99 improve to
  about 1.514x. Scheduler budget tuning can move prefill tails without solving
  decode-tail instability.
- Three repetitions materially changed the conclusion relative to a one-pass
  screen. Do not promote a candidate from a single repetition, especially at
  c16.
- A TPOT outlier on very short completions can dominate P99 because the
  denominator contains few inter-token intervals. Preserve the user-visible
  aggregate P95/P99, and add output-length-stratified diagnostics during
  profiling instead of deleting or silently filtering those requests.
- Retain MTP k3 local argmax as an algorithm component, revert the batched-token
  budget hypothesis to unaccepted, and profile c16 draft/verify scheduling plus
  short-completion tails before selecting the next operator change.
