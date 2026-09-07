# Qwen3.5-27B performance optimization lessons and handoff

Updated: 2026-09-06

## Authoritative state

- Goal: improve both TTFT and TPOT by 2x without quantization, using cumulative parameter, algorithm and operator treatments.
- Immutable comparison: frozen BF16 TP4/DP1 MTP-off baseline on physical NPU0-3 and the first 32 records of `/cache/cch/query_rewrite.jsonl`; its service log proves `speculative_config=None`.
- Baseline evidence: `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp4dp1-npu03-ref-v1`.
- Baseline summary SHA256: `cef6713367f387fd67c15c2cc0bdf071c33f58846b8ef9a041a489186aa0d9d4`.
- Primary acceptance metric is now P95: both TTFT P95 and TPOT P95 must
  improve by 2x at c1/c5/c8/c16. P50 is secondary and P99 is a risk guard.
- Current resources: GDN projection-fusion service
  `qwen35_gdn_proj_fusion_npu03_v1` owns physical NPU0-3 and port 10012;
  the external NPU4-7 workload remains running and untouched.
- Current decision: projection fusion is `iterate-performance / not
  promoted`. Three repetitions completed 384/384 requests with zero errors
  and natural stops. Median-of-three P95 speedups at c1/c5/c8/c16 are TTFT
  2.206x/1.938x/1.930x/1.910x and TPOT
  1.381x/1.651x/1.753x/1.980x, so the required all-cell 2x gate fails.
  Semantic quality also remains unproven.
- Retained fallback remains non-speculative Qwen3.5 dense gate/up prefetch
  0.1 with `mlp.down=0.0`; down-projection prefetch stays rejected.
- Speculative decoding is prohibited. All MTP, draft-model, suffix, ngram and local-argmax results are history only and cannot be retained or used as completion evidence.

## What succeeded

P95, not P50, is the governing performance statistic. The projection-fusion
candidate improved TTFT P50 beyond 2x in every cell, yet failed TTFT P95 in
c5/c8/c16 and failed TPOT P95 in every cell. This is the concrete reason
median gains cannot promote a treatment for this objective.

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
3. Verify the frozen TP4/NPU0-3 MTP-off baseline summary hash before computing any ratio.
4. Recheck NPU0-3 are idle before use and never stop, restart, or otherwise modify the external NPU4-7 workload.
5. Resume from the retained gate/up-only prefetch stack with `mlp.down=0.0`; prove Ascend activation and correctness for one BF16-compatible MMAR/dense-matmul treatment before running c1/c5/c8/c16.
6. Only if the screen passes the predeclared latency and tail gates, run three repetitions plus a meaningful paired semantic-quality gate and candidate profiling.

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
- Rollback is the frozen non-speculative TP4/NPU0-3 baseline. Never modify the external NPU4-7 workload.

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

## Non-speculative Qwen3.5 GDN prefetch result

- The user now prohibits speculative decoding. This overrides earlier notes
  that retained MTP: require `speculative_config=None` for every future
  candidate and for final validation.
- Completing the Qwen3.5 prefetch lifecycle matters. Extending gate/up prefetch
  across the 48 linear-attention/GDN layers raised TTFT P50 above 2x in all
  c1/c5/c8/c16 screen cells while preserving BF16 numerical equality.
- The same treatment did not solve decode: TPOT P50 speedup was only
  1.224x-1.432x. Treat prefetch as a TTFT ingredient, not a complete stack.
- c1 TTFT P95/P99 regressed even while P50 improved. A warm/cold or graph-state
  hypothesis must be tested with preserved repeated evidence; never delete the
  cold observation or promote from the median alone.
- Operator provenance requires both a pinned source commit and file hashes in
  the launcher, followed by container mount inspection and evidence checksums.
- Focus the next profile on non-speculative c16 decode, MMAR and dense-FFN
  execution. Do not spend further runs tuning draft depth or acceptance.

## Ascend-native evidence boundary and current bottleneck

- This is an Ascend 910B4 optimization loop. CUDA-only implementations,
  CUDA/GPU measurements, and cross-platform extrapolations are discovery
  inputs at most; they are never acceptance evidence.
- Retained evidence must prove the exact vLLM-Ascend 0.23.0/CANN runtime,
  physical NPU assignment, BF16, `quantization=None`, and
  `speculative_config=None`.
- Dynamic CANN profiling after the GDN gate/up prefetch change still attributes
  64.9357% of summed kernel duration to collectives and 24.4934% to matmul.
  `MatmulAllReduceMc2AicpuKernel` alone contributes 48.1818%.
- Summed kernel duration is not E2E wall time because streams overlap. Use it
  to select the next hypothesis, then require real query_rewrite A/B evidence.
- The built-in sequence-parallel compiler pass is not automatically a win:
  default dense activation starts at 1000 tokens and its pattern expects an
  all-reduce plus AddRMSNormBias graph. Prove Qwen3.5 graph matching, MMAR
  interaction, numerical equality, and runtime activation before benchmarking.
- NPU0-3 are the experiment cards; do not disturb the external workload on
  NPU4-7.

## Sequence-parallel activation failure on the retained Ascend stack

- A configured compiler pass is not an activated optimization. Require
  compiled-graph or runtime-kernel evidence before launching an A/B matrix.
- With `VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1`, Qwen3.5 row-parallel layers
  compile to the opaque Ascend `npu_mm_all_reduce_base` path. The tested
  sequence-parallel pass did not materialize `reduce_scatter` or
  `all_gather`.
- Enabling sequence parallelism under TP4 removed non-multiple-of-four graph
  capture sizes, including c1. Even if a high-token prefill pattern later
  matches, this side effect must be weighed against TTFT and tail risk.
- Fail fast at the activation gate. One real private query is sufficient to
  prove graph shape and runtime constraints; it is not sufficient for a
  performance claim.
- Do not repeat `enable_sp=true` with MMAR unchanged. The next candidate must
  be Ascend-native, preserve BF16/no-quantization/no-speculation semantics, and
  prove its CANN/MMAR/HCCL activation before the c1/c5/c8/c16 matrix.

## Fused GDN prefill precision rejection

- A callable Ascend operator is not sufficient evidence for a lossless
  optimization. `torch_npu.npu_chunk_gated_delta_rule` executed successfully
  on physical 910B4 NPU0 with the Qwen3.5 TP4-local head geometry
  `Nk=4, Nv=12, Dk=Dv=128`, but correctness still had to pass its own golden.
- Use the operator repository's reference when an isolated vLLM wrapper cannot
  reproduce the installed runtime registration cleanly. The authoritative
  check here is
  `/cache/cch/ops-transformer/attention/chunk_gated_delta_rule/tests/pytest/chunk_gated_delta_rule_golden.py`,
  not a CUDA comparison or a source-only assertion.
- The supplied BF16 golden at `B=1, T=64` returned `FAILED` for both output
  and recurrent state. Output maximum absolute error was about `0.002604`
  and state maximum absolute error about `0.000928`; the golden's normalized
  maximum-relative-error ratios were `19.977` vs a `5` limit and `60.381`
  vs a `5` limit respectively.
- Reject before E2E when the semantic gate fails. This candidate also addresses
  only GDN prefill, which the retained profile attributes to about `0.5666%`
  of summed kernel duration, so it cannot plausibly close the missing TPOT
  P50 gap even if its precision is later repaired.
- Do not integrate or benchmark the current fused-GDN patch unchanged. A retry
  requires a CANN/operator precision fix or a predeclared, quality-justified
  tolerance change; neither is authorized by the current “精读无损” goal.

## BF16 dense FFN fusion applicability

- CANN `npu_ffn` is available on Atlas A2/910B4 and supports BF16 for
  non-gated activations, but availability alone does not make it compatible
  with Qwen3.5.
- The operator contract restricts `swiglu/geglu/reglu` to the no-expert FP16
  high-performance path. Qwen3.5-27B requires BF16 SwiGLU with
  `N1 = 2 * K2`; the supported BF16 `silu` path instead requires
  `N1 = K2`.
- Reject at the static applicability gate when an operator would require a
  dtype or activation change. Do not spend NPU time benchmarking a candidate
  that already violates the frozen BF16 and “精读无损” contracts.
- Retry only after the target CANN/torch_npu runtime explicitly supports BF16
  gated FFN fusion; a CUDA implementation or an FP16 result is not evidence.

## Down-projection prefetch does not close decode

- Adding `mlp.down=0.1` on top of the retained Qwen3.5 gate/up prefetch
  completed a real Ascend 910B4 c1/c5/c8/c16 screen with 128/128 requests,
  zero errors, natural EOS, BF16, `quantization=None`, and
  `speculative_config=None`.
- TPOT P50 speedup versus the frozen baseline remained only 1.224x, 1.363x,
  1.393x and 1.339x. Relative to gate/up-only prefetch, c8 and c16 TPOT P50
  regressed to about 0.973x and 0.948x.
- c16 TTFT P50 improved strongly in this single run, but one median cannot
  override TPOT regressions, c16 TPOT P99 at 0.568x, or the required
  three-repeat promotion gate.
- Prefetch each projection independently. Retain gate/up 0.1, restore down
  to 0.0, and do not retry the same down-prefetch ratio without a new
  Ascend profile mechanism explaining why decode economics should change.
- The remaining gap is the profiled collective/matmul path. Candidate
  selection must stay within vLLM-Ascend/CANN/910B4 and pass BF16 correctness
  before E2E; CUDA kernels remain discovery input only.

## GDN input-projection fusion: operator win, P95 result still open

- Merge the separate Qwen3.5 linear-attention `qkvz` and `ba`
  projections. A real 910B4 BF16 microbench measured 3.046x-3.085x at
  TP4-local M=1/5/8/16 with max absolute error `2.44140625e-4`.
- Never translate that operator result into an E2E claim. Screen r1 primary
  TTFT P95 speedups are 0.153x/1.906x/1.930x/1.910x and TPOT P95 speedups
  are 1.379x/1.264x/1.753x/2.032x. Most P95 gates fail.
- A vLLM model-attribute refactor is incomplete on Ascend until the
  vLLM-Ascend wrapper contract is updated. The first service failed because
  the wrapper expected `in_proj_qkvz`; the adapter must consume
  `in_proj_qkvzba` and reconstruct qkvz/ba for the existing AscendC path.
- New shapes can trigger first-use dynamic compilation. Preserve cold r1,
  then use r2/r3 to characterize hot P95; do not hide cold cost or substitute
  a favorable P50 for the user-selected P95 gate.
- Isolation includes restart supervisors. `watch03.sh` reappeared with
  PPID 1 while NPU0-3 still contained only the intended TP workers. Verify
  exact cmdline, stop only that supervisor, guard every cell, and invalidate
  measurements if a second device process appears.
- Provenance: vLLM `685fdf22098fb3a0aa8d582dda57063773606a02`;
  Ascend adapter `d98e37ebb72acd71b5a35222fd7ab7f8049d41cb`;
  integration `f58e3e964141747d4b62ef749dc25cea270c2ee4`.
- The sparse/weak `answer` field cannot prove `精读无损`. Promotion
  requires deterministic paired baseline/candidate semantic equivalence;
  stochastic aggregate reference metrics remain diagnostic only.

## MMAR x3 residual fusion rejection

- For `npu_mm_all_reduce_base`, `x3` is part of the reduced value rather
  than a post-reduction local residual. A TP-replicated residual is therefore
  multiplied by world size when passed unchanged.
- The only direct semantics-preserving TP4 form tested here divides the
  residual by four on every rank before MMAR. Include that division in the
  timed candidate; precomputing it outside the measured path would hide a
  real per-layer cost.
- Real BF16 910B4 NPU0-3 results passed numerical correctness after scaling,
  but `MMAR(x3=residual/4) + RMSNorm` achieved only 0.655224x geometric
  mean speed versus `MMAR + AddRMSNorm`, with a 0.635134x worst cell.
- Reject before E2E. API availability and apparent operator-count reduction
  do not justify integration when cross-rank semantics require an extra
  elementwise transform and the viable sequence is slower.
- Evidence report SHA256:
  `92b42c33c4449ee5f788b93e8337f8bd9becbe6a44e993140acabf8d2b673224`.
  Do not retry this route unchanged.

## MMAR layout and production logging screens

- A transpose view is not automatically an MMAR bottleneck on 910B4. Making
  the TP-local weight physically contiguous in `[K,N]` produced only
  `1.009789x` geometric-mean speedup and included a `0.994723x` regression.
  Require both the aggregate gate and every-cell non-regression before paying
  integration or checkpoint-conversion cost.
- Lowering vLLM logging from DEBUG to INFO looked attractive because the old
  service log was debug-heavy, but the real c16 median-of-three regressed from
  `6796.297/69.560 ms` to `10352.929/104.020 ms` for TTFT/TPOT P95. Reject the
  setting as a performance ingredient on this frozen stack.
- Prefix caching makes run order observable. A cache-salted diagnostic run is
  useful for exposing uncached behavior but is not comparable with the frozen
  unsalted denominator. Label it diagnostic and never mix it into promotion
  arithmetic.
- The query_rewrite generation config is stochastic and completion-token counts
  vary across repeats. Keep the median-of-three rule and report all per-run P95
  values; do not select a favorable repeat.

## Quality evidence when references are empty

- Audit the reference field before trusting aggregate quality metrics. Here,
  all 357 `answer` values were empty, so reference similarity could not prove
  `精读无损`.
- Use a deterministic paired baseline/candidate capture with identical prompt
  indices, temperature 0, fixed seed, natural EOS, and hashed raw outputs.
- Exact match is a useful first gate but not the semantic decision. Five of 16
  samples differed byte-for-byte; manual inspection showed all final task
  outputs were equivalent, with only whitespace, compact reason wording,
  punctuation, or word order changes.
- Record the evidence boundary. Passing 16 length-quantile samples supports the
  retained stack but does not prove equivalence over every dataset row or
  arbitrary production traffic.
- Keep the quality control separate from the performance denominator. The TP4
  cumulative control isolates algorithm/operator semantics; the immutable TP8
  MTP-off baseline remains the performance denominator.

## HCCL-buffer and MMAR-off sequence-parallel screens

- A communication tuning parameter must pass every important real shape, not
  only a geometric mean. `HCCL_BUFFSIZE` 64/128/256 each failed the
  predefined 1.02x all-shape gate against 512 on the two exact BF16 decode
  MMAR shapes, so none justified an E2E run.
- Exposing ordinary all-reduce nodes is still not sequence-parallel
  activation. With MMAR disabled, the compiled graph had 832 `all_reduce`
  occurrences but no `reduce_scatter` or `all_gather`.
- Stop at the activation gate and preserve the graph plus hashes. Do not turn
  an absent graph rewrite into a performance claim.
- Repository product tables are eligibility evidence, not performance
  evidence. For this dense model, A3-only expert-routing and disaggregated
  worker operators are contract-mismatched; the only direct dense analogue,
  `FFN`, still needs a new A2 BF16 gated-SwiGLU contract.

## MMAR-off real E2E result

- Graph activation alone is not a win. Disabling MMAR produced the intended
  ordinary graph (0 MMAR, 832 all-reduce occurrences), but the real c1
  32-request screen regressed TTFT P95 by 0.527248% and TPOT P95 by
  0.220490% versus the retained stack.
- This closes the simple `MMAR off` branch: do not retry it unchanged or
  infer that the large profiled AICPU share means ordinary matmul plus
  all-reduce must be faster.
- The evidence sharpens the P0 task. Improve the existing A2/910B4 MMAR
  implementation for the exact M=1 BF16 shapes, or create a materially
  different fusion that removes launch/memory overhead while preserving
  MMAR; do not merely decompose it.
- Evidence manifest SHA256:
  `21deab1aa598edb04bfd38f6c88bd30118c3a6b1f04ed244e68cc403d12f964f`.

## Selective MMAR shape-family isolation

- An all-off result can hide opposing family effects, so add a source-level
  prefix control and prove activation from the compiled graph before drawing
  shape-specific conclusions.
- For this stack, disabling MMAR only for attention/GDN `o_proj/out_proj`
  was decisively worse: c1 TTFT P95 +1.168625% and TPOT P95 +14.224519%.
  The graph retained 384 MMAR occurrences, so this was not an accidental
  global disable.
- Preserve MMAR for the smaller attention/GDN output projection shape. The
  complementary MLP down-projection screen also failed: c1 TTFT P95
  regressed 0.199734% and TPOT P95 regressed 0.077779%, despite an activated
  graph with 320 MMAR and 768 ordinary all-reduce occurrences.
- Selective decomposition is now closed for both real projection families.
  Do not retry prefix variants unchanged. The next operator experiment must
  improve the A2 MMAR kernel/tiling itself, preserve BF16 semantics, and pass
  exact-shape microbench correctness before E2E.
- MLP-down screen manifest SHA256:
  `78e15989e9fcb9580428c702fc83fed65535b93db22455953ca3f8ac8d6886d8`.

## M=1 MMAR core-count and launch-participation lesson

- On arch22, every launched block participates in `Mc2SyncAll` and HCCL
  post-processing. Reducing `blockDim` together with matmul cores is not a
  performance tuning shortcut; it produced grossly corrupted outputs on real
  910B4 hardware.
- Preserve the full platform launch width. If matmul tiling uses fewer cores,
  keep launch participation separate from `usedCoreNum` and prove complete
  fused-output correctness against the frozen default.
- A broad real scan of 8/12/16/18/20/22 matmul cores found no candidate that
  was both correct and at least 1.02x faster on the two profiled M=1 shapes.
  The only isolated gain, 1.036689x for 12 cores at K=1536, came with a
  0.898306x result at K=4352 and is unusable for the shared Qwen path.
- Do not repeat core-count or physical launch-width tuning unchanged. The
  dominant opportunity is fixed per-call HCCL orchestration
  (AllReduce/Commit/Wait/Finalize), or a materially different fusion that
  amortizes it while preserving BF16 semantics and full synchronization.
- Evidence roots are the v2 and v3 full-sync scans recorded in HANDOFF.md;
  package SHA256 is
  `420275e89e83d2e42b82152fc52db87f470b2a5372c7a8d7746200b31569c640`.
