# Qwen3.5-27B query_rewrite 2x E2E Optimization

## State

- Execution: `fixed-runtime-profile-next-after-control-calibration`;
  integration: `not-ready`.
- Branch: `work/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Worktree: `/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- The user assigned physical NPU4-7 to this task. The old
  `qwen38_gdn_fused_candidate` service was idle but used a
  non-comparable 41,984/16,384/no-prefix-cache protocol; it was retained for
  audit and stopped. Use NPU4-7 for current candidates.
- `scripts/run_qwen35_tp4_dev_service.sh` now refuses to start if
  `npu-smi` reports any process on NPU0-3 (exit 42), and profile mode refuses
  to reuse an existing output directory (exit 44). Mock-only tests prove both
  failures occur before `docker run`; never bypass these guards.
- The attempted workstream profile container
  `qwen35_query_rewrite_tp4_dev_profile` exited before serving when Triton
  Ascend `get_arch()` returned NULL during Qwen3.5 architecture inspection.
  The failed container is retained; its readiness observer was terminated and
  no workstream process remains on NPU0-3. This is a resource-ownership race,
  not valid profile evidence.
- Physical NPU0-3 are not required for the current loop.
- No baseline rerun is pending. The user designated the existing TP4
  `quick32-v3` artifacts as the immutable original denominator. Future
  runs use exclusive physical NPU4-7 for one candidate.
- FlashComm1 was really launched on physical NPU4-7 as run
  `flashcomm1-fixedorig-npu4-7-20260904T1816Z`. The v0.23.0 runtime proved
  both FlashComm1 and MatMulAllReduce active, then all four TP workers failed
  before readiness: the Qwen3.5 GDN graph attempted to place symbolic length
  `s59` into a sequence-parallel `ceil(s59/4)` buffer. No benchmark cell
  ran. Treat this as a runtime-compatibility failure, exclude FlashComm1 from
  the cumulative stack, and do not retry it unchanged.
- Immutable failure evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/flashcomm1-fixedorig-npu4-7-20260904T1816Z/service.log`
  (SHA256
  `35ef543dd9ab29d127ce01b2556b6abf8b0a46e9068320f7a97d4e69cf59e692`).
  The exact container was stopped; NPU4-7 remain the assigned candidate set.
- BF16 `weight_nz_mode=2` was then really launched alone on NPU4-7 as run
  `bf16-nz-fixedorig-npu4-7-20260904T1838Z`. All four workers proved NZ and
  MatMulAllReduce active and loaded 12.8785 GB of weights each, but
  `aclnnMatmulAllReduce` rejected its `x2` input because it was
  `FRACTAL_NZ` instead of the required `ND` format. No benchmark cell ran.
- BF16 NZ failure evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/bf16-nz-fixedorig-npu4-7-20260904T1838Z/service.log`
  (SHA256
  `0756f2a7770166afa54d4e4ff08178be13d6b81287a28fa861ec9e1b3ddf82b9`).
  The exact container was stopped. The next bounded recovery is NZ with
  MatMulAllReduce disabled, matching that setting in the fixed original.
- The NZ recovery run completed all four real cells with 32/32 requests, zero
  errors and natural stops. It improved TTFT by 2.03x/2.00x/1.97x at
  concurrency 1/5/8, but concurrency-16 TTFT regressed to 0.58x. TPOT improved
  only 1.33x-1.54x. Exact response hashes differed for 19/18/15/18 requests,
  so the analyzer returned `reject-correctness` and the treatment is excluded
  from the stack.
- NZ recovery decision:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/bf16-nz-mmar-off-fixedorig-npu4-7-20260904T1845Z/decision.json`
  (SHA256
  `323ee9620294fba17bfd678e30bab5012512e211c9016303e9c8ef0ddb2b791a`).
  The service log SHA256 is
  `bc6bb41f630cdaa2c2d44496e43ce591586d53566cb974d0066d379f08cfd438`.
- MatMulAllReduce enabled alone completed all four real NPU4-7 cells as run
  `mmar-on-fixedorig-npu4-7-20260904T1921Z`. Every cell completed 32/32
  requests with zero transport errors and natural stops. Against the immutable
  original, TTFT p50 improved 2.14x/2.11x/2.17x/2.25x at concurrency
  1/5/8/16, but TPOT p50 improved only 1.34x/1.38x/1.49x/1.55x. Exact response
  hashes differed for 17/20/17/15 requests, so the authoritative decision is
  `reject-correctness`; do not add MMAR to the cumulative stack.
- MMAR decision evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/mmar-on-fixedorig-npu4-7-20260904T1921Z/decision.json`
  (SHA256
  `870c8f04911b838670d4e0414b3846d14fa7cb2cb0774b15230a573f681ecc0b`).
  The service log SHA256 is
  `8ddc953a33dd994646d7214336a5a0a9b7d752d7fffc8e1b98f38120e1e610c0`.
  The exact candidate container self-cleaned; NPU4-7 have no running process,
  while the pre-existing NPU0-3 VLLM workers remained untouched.
- Because a nominally semantics-preserving MMAR switch still changed exact
  hashes and showed a large TTFT p50 shift, the next attribution step is a
  no-op BF16 control candidate on NPU4-7 matching the fixed original runtime
  switches (MMAR off, NZ mode 1, FlashComm1 off). It does not replace or
  relabel the immutable original; it calibrates run/device drift before the
  next operator or algorithm candidate is credited.
- The control is implemented as launcher mode `control-mmar-off` with
  `configs/qwen35-query-rewrite-control-mmar-off-candidate.yaml`. It keeps
  BF16, MMAR off, NZ mode 1, FlashComm1 off, TP4 and the frozen request
  protocol. It is an attribution control only: the fixed quick32-v3 artifacts
  remain the sole performance denominator and are not rerun or relabeled.
- The control completed as
  `control-mmar-off-fixedorig-npu4-7-20260904T1943Z` under AWMCP operation
  `exec-000000000000063b`. It reproduced the original runtime switches and
  completed every cell 32/32 with zero errors and natural stops. Its TTFT p50
  was 449.81/530.76/542.48/5903.78 ms and TPOT p50 was
  28.76/39.02/46.39/55.03 ms at concurrency 1/5/8/16.
- The control itself differed from the immutable original in 15/15/19/16
  response hashes. Therefore cross-run exact-hash equality is not a calibrated
  semantic correctness gate for this workload. Keep it as a reproducibility
  diagnostic and fail closed until aggregate reference-quality metrics pass.
  Future benchmark artifacts now add privacy-safe raw/whitespace-normalized
  exact-answer counts and normalized character-similarity summaries; they
  never store question, answer or response text.
- Relative to the same-device control, MMAR changed TTFT by
  1.04x/1.02x/1.09x/6.41x and TPOT by
  1.004x/1.000x/1.019x/1.053x. The c16 TTFT signal is large but comes from a
  single highly variable control cell; repeat/profile it before credit. MMAR
  remains outside the accepted stack because its net TPOT gain is at most
  5.3% and semantic correctness has not passed.
- Control evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/control-mmar-off-fixedorig-npu4-7-20260904T1943Z/decision.json`
  (SHA256
  `ff77a6fc8aadbf6d0561834b9f42a12a562cee76f5da4c4a6f9ae68eaf803b39`).
  The service log SHA256 is
  `6d3b7a82b31be3ab55d10107e68cd14c064bb2fdef90afe1567534692987c0bc`.
  NPU4-7 were released; NPU0-3 workers remained untouched.

## Authoritative comparison and stacking policy

This section supersedes later historical text that asks for a paired baseline,
three repetitions, all eight NPUs, or a new canonical baseline.

- Original: `tp4-dev-decodegraph/quick32-v3`, first 32 frozen records,
  one repetition, concurrency 1/5/8/16, seed 1024, natural EOS.
- The four original file hashes are embedded in
  `scripts/analyze_qwen35_candidate_vs_original.py`. A hash mismatch
  invalidates the run.
- Run only the candidate with
  `scripts/run_qwen35_tp4_candidate_vs_original.sh`. It starts one
  exact TP4 container on physical NPU4-7, runs four candidate cells, records the
  container/log/config hashes, stops only that container, then compares with
  the stored original.
- Correctness remains fail-closed: 32/32 completed, zero errors, natural stop,
  and exact per-request response hashes. Analyzer exit status is 0 for the 2x
  target, 2 for continue iterating, and 3 for correctness rejection.
- A treatment is isolated for attribution, then accepted treatments are added
  to the current best stack. Every single treatment and cumulative stack uses
  the same original denominator. The first supported cumulative mode is
  `flashcomm1-bf16-nz`; it combines two BF16 paths and is not
  quantization.
- Preserve the known caveat: quick32-v3 forced
  `enable_matmul_allreduce=false`. The user accepted it as the common
  denominator, so report the caveat but do not relaunch or relabel it.

## TP4 development evidence

- The user-supplied FULL_AND_PIECEWISE configuration with matmul-allreduce
  enabled failed during graph capture in `aclnnMatmulAllReduce`. The immutable
  startup log is
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/startup/original-config-matmul-allreduce-failure.log`
  (SHA256
  `fbe6f414bf5c5ced6295298bfe37e484e5e7f7efef4e94101ace599b4758fcb0`).
- Disabling matmul-allreduce removed that failure, but FULL_AND_PIECEWISE still
  failed with `EE1023 Too many streams are created`. Evidence:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/startup/matmul-allreduce-off-full-piecewise-stream-exhaustion.log`
  (SHA256
  `3d6091716a0d3356a79caba742e048cd2972ae4ba4d75e89da0a9297eb6213d9`).
- The next attributable treatment, FULL_DECODE_ONLY with
  matmul-allreduce disabled, started successfully. Decode graph capture covered
  request counts 1, 2, 4, 6, 8, 10, 12, 14 and 16 in 20 seconds and consumed
  0.42 GiB graph memory. The service has 10.84 GiB KV cache per card and reports
  maximum 5.03 concurrent 133K-token requests.
- A real one-record raw/natural-EOS smoke completed 1/1 with zero errors:
  TTFT 1085.71 ms, TPOT 41.68 ms, E2E 5378.28 ms, 104 completion tokens.
  Artifact:
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/tp4-dev-decodegraph/smoke-c1-r1.json`
  (SHA256
  `f2f959768f28b57d41e394b3be9379e3ef8e6cc65ebc9efea8d9650e0c2ae087`).
- The first 32-record run terminated at concurrency 1: 28/32 completed and four
  requests raised `RuntimeError`; it did not proceed to 5/8/16. The invalid
  artifact is
  `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/tp4-dev-decodegraph/quick32/c1-r1.json`
  (SHA256
  `a78b13517fe735f44f82f904fe4832e9a9371ad5dad1350f41c66fe8e1193768`).
  Do not use its latency values as a baseline.
- Diagnosis found that the harness recorded seed 1024 but omitted it from the
  request payload, and reduced all internal stream validation failures to only
  their exception type. The harness now sends the seed and emits only
  privacy-safe error-reason counts and failed-question SHA256 values.
- A concurrency-1 diagnostic rerun is active as AgentWeb operation
  `exec-0000000000000350`, writing to the new immutable
  `tp4-dev-decodegraph/quick32-v2/c1-r1.json` path.
- That rerun reproduced the same four cases and classified all of them as
  `stream completed without content`. A targeted privacy-safe SSE probe then
  proved each was a valid EOS-only completion: one choice event,
  `completion_tokens=1`, `finish_reason=stop`, zero visible characters and
  no HTTP/service error. The harness now defines TTFT at the first choice/token
  event, including EOS, rather than the first non-empty text fragment.
- The corrected quick32-v3 scaling run completed all four cells with 32/32
  natural-stop responses and zero errors:

  | concurrency | TTFT p50 | TPOT p50 | artifact SHA256 |
  |---:|---:|---:|---|
  | 1 | 928.33 ms | 38.47 ms | `ac39bc922b43d9472fe41f89bae25a0190cf20817147230f8725f151e3ce413a` |
  | 5 | 1092.27 ms | 53.83 ms | `68d2a3020bb52594e13560dd608afca1d611d61a37383aa94062bfe78784f7ae` |
  | 8 | 1082.31 ms | 67.62 ms | `4f9799a128128b1e34dca498256833c45f52373cd2486b4acd9298030d7d58ce` |
  | 16 | 2075.07 ms | 80.81 ms | `085c0a43a7a720ba42f1d83bf2ebacebb64e515d24bb3f040eabd5c046f777e4` |

  These are the user-designated immutable original baseline.
- The MTP candidate uses the same TP4 command plus only
  `{"method":"mtp","num_speculative_tokens":1}`. Readiness is tracked by
  AgentWeb operation `exec-0000000000000370`.

- MTP quick32-v1 completed under AgentWeb operation
  `exec-000000000000037d` in 762.12 s. Every cell completed 32/32 with zero
  transport errors and natural `stop`, but exact output hashes diverged.

  | concurrency | TTFT baseline -> MTP | speedup | TPOT baseline -> MTP | speedup | mismatches | artifact SHA256 |
  |---:|---:|---:|---:|---:|---:|---|
  | 1 | 928.33 -> 1166.99 ms | 0.795x | 38.47 -> 41.92 ms | 0.918x | 16/32 | `b57d8aa8346b8cebc1ce7c58163f0d25d8eab834091f2a1ede48fffccf8e6568` |
  | 5 | 1092.27 -> 1389.05 ms | 0.786x | 53.83 -> 62.28 ms | 0.864x | 20/32 | `1fd71a7d6bd5aa5a5629383d6528ea584cfa3be32760fa398fca01d493ef8337` |
  | 8 | 1082.31 -> 1408.59 ms | 0.768x | 67.62 -> 72.41 ms | 0.934x | 21/32 | `59bd1765d13ab5137fc4b7c4c83635788fb606271daecd6737b302ddf1e2d61a` |
  | 16 | 2075.07 -> 10619.90 ms | 0.195x | 80.81 -> 109.76 ms | 0.736x | 18/32 | `67bcd90ad027b21b8fdbc25bdddfb21c3b4f86256ad4d24902cb7052dbcc7035` |

  Decision: **reject MTP from the cumulative stack**. It fails correctness and
  regresses TTFT and TPOT at every measured concurrency.
- Source inspection proved `VLLM_ASCEND_PTO_CHUNK_GDN=1` has no reader in the
  installed vLLM/vLLM-Ascend source and is an inert legacy variable.
  Qwen3.5 actually binds to `AscendGatedDeltaNetAttention._forward_core`;
  decode uses the AscendC recurrent GDN op and prefill uses mixed chunk GDN.
- Torch/NPU profiling requires `--profiler-config.profiler=torch` and
  `--profiler-config.torch_profiler_dir=<dir>`. No comparable profile exists
  yet for this workload.

## Provisional algorithm and operator candidates

The first treatment after freezing the current development baseline is native
Qwen3.5 MTP speculative decoding. The frozen model is not merely compatible in
name: 'text_config.mtp_num_hidden_layers=1', and its weight index contains 15
MTP tensors covering 'mtp.fc', 'mtp.layers.0', 'mtp.norm' and the MTP embedding
norms. The installed vLLM 0.23.0 'SpeculativeConfig' explicitly declares the
'qwen3_5_mtp' method. Start with one speculative token, matching the single
model-provided MTP layer. Accept it only with exact response-hash equality,
zero errors, measured acceptance evidence and a paired decode profile. This is
the primary TPOT candidate because a one-layer MTP path can remove target-model
decode steps; the claim remains unproven until E2E A/B.

The next cumulative treatment is the fused GDN prefill path from vLLM-Ascend
upstream commit '77d13e2c0bfa9862b711b68811889e36b9d56aca'. It replaces the multi-kernel
chunk gated delta-rule prefill pipeline with
'torch_npu.npu_chunk_gated_delta_rule'. Reuse the audited patch from the
adjacent GDN workstream, but remeasure under this workstream's 133K,
prefix-cache-enabled protocol; its historical 41984/no-prefix-cache numbers
are not comparable. The current torch_npu package exposes the fused symbol, but
runtime applicability and correctness on 910B4 still require an isolated probe.

## Frozen inputs

- Model: `/cache/austinov/Qwen3.8-27B`; actual architecture
  `Qwen3_5ForConditionalGeneration`; all 18 indexed weight shards are present.
- Model config SHA256:
  `191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab`.
- Tokenizer config SHA256:
  `b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27`.
- Weight index SHA256:
  `77042094076611b69791a610065f28b7013b8c621795fa86ddccc8bac7d1b9df`.
- Dataset: `/cache/cch/query_rewrite.jsonl`, 357 records, 3,305,726 bytes.
- Dataset SHA256:
  `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`.
- Dataset records expose `question` and `answer`; never place raw content in Git or logs.

## Measurement target

Measure the first 32 records once at concurrency 1, 5, 8 and 16 for each
candidate, with one excluded warmup per cell. The final target is TTFT and
TPOT no greater than one half of the
original baseline at every concurrency, with zero request errors, passing
business correctness, and no unacceptable p95/p99 regression.

The workstream identifier retains the original `3x` label for audit
continuity; the authoritative goal was revised to 2x on 2026-09-04.

## Optimization loop

1. Acquire explicit exclusive ownership of the user-assigned physical NPU4-7.
2. Freeze request rendering, output policy, seed and service/runtime identity.
3. Verify, but do not rerun, the hash-locked original quick32-v3 artifacts.
4. Profile Prefill, Decode, GDN, MatMul/AllReduce, Attention, scheduling,
   graph coverage, layout conversion and host synchronization.
5. Add one attributable treatment to the latest accepted stack: operator,
   algorithm, or parameter.
6. Verify reference, microbenchmark, vLLM-Ascend integration, model
   correctness and query_rewrite E2E behavior.
7. Compare the treatment or cumulative stack against the immutable original.
   Use the retained single-treatment/ablation history to explain attribution.
8. Preserve accepted, rejected, failed and inconclusive results.
9. Add each accepted treatment to the current best stack and repeat until both
   TTFT and TPOT reach 2x at all four concurrencies.

The privacy-preserving streaming harness is
`scripts/qwen35_query_rewrite_bench.py`. One invocation measures one
concurrency/repetition cell, verifies the frozen dataset hash, and emits
TTFT/TPOT/E2E/throughput plus response hashes without recording prompts or
response text. It follows the maintainer-approved historical protocol: raw
`question` strings, temperature 0, natural EOS, and per-request
`max_tokens = max_model_len - real_prompt_tokens` resolved through
`/tokenize` before the measured window. Fixed-40 and normalized-2K protocols
are superseded and must not be mixed with this baseline.

`scripts/render_qwen35_runtime.py` validates the frozen final baseline
contract and renders a canonical argv/environment manifest. It fail-closes
unless topology is DP2/TP4 on NPU0-7, the benchmark grid is 1/5/8/16 × three
repetitions, request semantics remain raw-question/natural-EOS, and both
acceptance ratios remain 0.5. The manifest hashes both source YAML and
normalized runtime payload, preventing command drift when all eight NPUs
become available.

`scripts/run_qwen35_benchmark_matrix.py` executes the complete frozen
1/5/8/16 × three-repetition matrix against one already healthy service. It
checks the dataset hash before creating output, refuses an existing run
directory, validates every cell's model/data/concurrency/repetition identity,
requires zero errors, a complete request/hash set and natural stop for every
request, and checkpoints an atomic run manifest after each cell. A failed run
is retained with its exact failed cell and exception type; it is never silently
resumed or overwritten.

`scripts/run_qwen35_dp2tp4_baseline_service.sh` is the final-baseline
service entry point. It refuses an existing container or manifest, parses the
authoritative `npu-smi` process table and exits before rendering or Docker
when any physical NPU0-7 is occupied. On an idle host it renders the frozen
runtime manifest, passes its exact environment and argv to the fixed
`quay.io/ascend/vllm-ascend:v0.23.0` image, and exposes all eight devices.
Mocked occupied and idle-path tests prove both the ownership gate and the
rendered DP2/TP4/device/environment command.

`scripts/analyze_qwen35_candidate_vs_original.py` is the authoritative
decision gate. It verifies the four fixed baseline SHA256 values and requires
four candidate artifacts (concurrency 1/5/8/16 × repetition 1), identical
model/data/request identities, zero errors, complete natural-stop request sets
and exact response-hash equality. It emits `final-target-met` only when
both TTFT and TPOT ratios are at most 0.5 in every concurrency cell.

The final stack is expected to combine core operators, algorithms and
configuration. "One variable" applies to each attribution step, not to the
final candidate.

## Operator lane

Reusable sources under `/cache/cch` include `ops-transformer`,
`cannbot-skills`, `cann-recipes-infer` and `vllm-ascend`. Before editing
any of them, read their nearest `AGENTS.md`, create a dedicated source
worktree, and preserve existing dirty work. An operator is accepted only after:

1. reference correctness on real shapes;
2. repeated operator benchmark;
3. feature-flagged integration into vLLM-Ascend;
4. model-level correctness under DP2/TP4;
5. query_rewrite quick32 versus fixed-original E2E evidence and a
   candidate-only diagnostic profile.

## Profile analysis readiness

- `scripts/run_qwen35_profile_request.py` performs an unprofiled warmup on
  record 0, calls the service's `/start_profile` endpoint, profiles record 31,
  and always calls `/stop_profile` after a successful start. Warmup and
  profile use distinct, run-unique `cache_salt` values so prefix caching
  cannot hide the profiled prefill. Its artifact stores dataset, question and
  response hashes but no raw confidential text, and marks profiler timings as
  non-performance evidence.
- Use a unique `--run-id` for every capture. The service must expose both
  profiler endpoints; HTTP 404 means profiler configuration was not active.
  Never run this driver concurrently with a formal TTFT/TPOT cell.
- `scripts/analyze_ascend_profile.py` recursively discovers Ascend
  `kernel_details.csv` files, records each input SHA256, and emits
  `qwen35-ascend-profile-hotspots/v1` JSON with category shares and raw top
  kernels. It groups the complete GDN prefill pipeline rather than treating
  only `ChunkGatedDeltaRule` as the cost.
- Validation passed with a zero-dependency fixture, `py_compile`, and a
  15,298-row historical Ascend profile smoke. Summed kernel duration is
  explicitly marked as **not wall time** because streams can overlap; TTFT and
  TPOT remain authoritative only in the E2E benchmark artifacts.
- Current source routing is phase-specific: prefill uses the chunk GDN
  pipeline (including chunk rule, recompute, merge and transpose kernels);
  decode uses the AscendC `npu_recurrent_gated_delta_rule` custom operator.
  The next treatment must be chosen from the new fixed-request profile, not
  inferred from historical profiles belonging to another run.
- `scripts/capture_qwen35_tp4_profile.sh` is the fail-closed one-shot
  orchestration entry point. It requires explicit unique run/container/profile
  identities, delegates the NPU0-3 ownership guard to the service launcher,
  waits for health, verifies both profiler endpoints in OpenAPI, captures the
  isolated request, waits for `kernel_details.csv`, analyzes it, records
  artifact hashes, and stops only the exact container it started while
  retaining the stopped container and logs. Existing output paths are rejected.
- `scripts/compare_ascend_profiles.py` compares normalized baseline and
  candidate hotspot reports by category, kernel duration, calls, and
  microseconds per call. It rejects identical source profiles, hashes both
  reports, and labels every ratio diagnostic-only/non-acceptance evidence.
  Formal speed decisions remain exclusively in the frozen E2E A/B gate.
- At 2026-09-04 16:43:31 UTC, NPU0-3 remained owned by
  `qwen36_27b_dk64_treatment_npu0_3` (PIDs 4111982-4111985) and NPU4-7 by
  `qwen38_gdn_fused_candidate` (PIDs 1312892-1312895). Neither was touched.

## Resume

The real TP4 v5 profile attempt used record 31 (1845 prompt tokens, one
completion token) and proved `async_scheduling=False`, but `/stop_profile`
still returned HTTP 500 and killed the worker. This rejects the async scheduler
as the root cause; do not retry the same HTTP profiler path unchanged. The raw
rank0 data was nevertheless exported offline with `msprof`. Its immutable
`op_summary` CSV SHA256 is
`7a6578f697f00d9f0267b990931e6ec1770a064f1deb18c2e7ad7fa26163073f`.
Across 6,453 rows, `hcom_allReduce_` accounts for 4,299,824.02 us, 94.585%
of summed task duration, over 237 calls. This is diagnostic-only profiler
attribution, not wall time or acceptance evidence.

Do **not** treat MatMul+AllReduce enablement as a candidate over the canonical
baseline. Exact-image unit tests and `AscendConfig._get_config_value` prove
that the user-provided `VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1` is used when
the additional-config key is absent. The v5 TP4 development profile instead
explicitly forced both sources false, so its 94.585% AllReduce attribution is
useful failure evidence but is not a profile of the canonical baseline.
The baseline YAML and TP4 baseline/profile launchers now explicitly set
`enable_matmul_allreduce=true` to eliminate fallback ambiguity. Re-profile
that canonical configuration when NPU0-3 are free before selecting a new
treatment.

Offline inspection of the exact `quay.io/ascend/vllm-ascend:v0.23.0`
image confirms the activation chain: `ascend_config.py` gives the explicit
additional config precedence, `ops/linear_op.py` selects
`MatmulAllreduceRowParallelOp` for row-parallel layers, and TP>1 with
reduction enabled calls `torch_npu.npu_mm_all_reduce_base`. TP4 therefore
meets the static activation conditions for dense Qwen3.5. Runtime operator/log
evidence remains mandatory; static source inspection is not a performance
result.

The MTP route is complete and rejected. Preserve all baseline, invalid and MTP
artifacts. Wait for explicit exclusive ownership of NPU0-3, then launch the
accepted non-MTP TP4 configuration under a new immutable profile container name
and output directory, with explicit torch-profiler configuration, and profile a
fixed real request. Commit `439be7d` makes profile mode synchronous as the
leading fix hypothesis: the real v2 attempt completed its request but
`/stop_profile` returned HTTP 500 after torch_npu reported that its external
callback ran on a different thread. It emitted no `kernel_details.csv` and is
invalid. The fix still requires runtime validation because the v3 launch operation
`exec-0000000000000422` then exited 42 before Docker because `p0_ab` acquired
NPU0-3. Do not reuse either failed attempt's paths as evidence. Do
not treat `VLLM_ASCEND_PTO_CHUNK_GDN` as a treatment. Do not perturb either
external NPU0-3 or NPU4-7 workload. Do not wait for or acquire NPU4-7. When
NPU0-3 are explicitly released, run one candidate at a time with
`scripts/run_qwen35_tp4_candidate_vs_original.sh`; the original
baseline is never relaunched.

## Fused GDN portability boundary

The frozen upstream fused-prefill patch is commit `77d13e2c0` with SHA256
`d16712f909810c1dd1a7704d0a7d53434032f800cb2af1f9562d11475489a76e`.
It reports only a 5890us-to-4964us operator microbenchmark on a different model
and software baseline. The v0.23.0 image is vLLM-Ascend `5cb98caa` and its
`gdn.py` SHA256 is
`d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816`.
The image exports `torch_npu.npu_chunk_gated_delta_rule`, but the frozen patch
does not apply cleanly to that source. Do not mount the newer full `gdn.py`
from `/cache/cch/vllm-ascend`; it contains broader API changes. Port only the
minimal fused-op hunks against the exact image source, keep a feature flag and
fallback, then require activation proof, reference correctness, real
query_rewrite comparison with the fixed original and a candidate profile.
Treat it as one cumulative operator
treatment, not evidence of the requested 2x result.

## Quantization route — prohibited

The user explicitly prohibited quantization. Keep the current model and all
accepted candidates in BF16. Do not download, generate, load, benchmark, or
accept W8A8, INT8, FP8, weight-only, or activation-quantized checkpoints.
The file configs/qwen35-query-rewrite-w8a8-candidate.yaml is retained only as
historical research provenance; it is not an executable candidate.

The remaining route is cumulative BF16 optimization: attributable runtime
parameters, semantics-preserving inference algorithms, and native/fused Ascend
operators, each behind the frozen correctness and real query_rewrite E2E gates.

## FlashComm1 decision and next BF16 candidate

FlashComm1 was the first real candidate, not Fused MC2. The exact v0.23.0 source
and model guide describe FlashComm1 as a sequence-parallel communication path
for dense Qwen3/high-concurrency TP, decomposing traditional AllReduce into
ReduceScatter and AllGather. It is isolated in
`configs/qwen35-query-rewrite-flashcomm1-candidate.yaml` and launcher mode
`flashcomm1`; canonical MatMulAllReduce remains enabled. Fused MC2 is routed
through MoE code and is out of scope for this dense model. `enable_prefill_mc2`
is also not selected because its documented recommended
`max_num_batched_tokens=TP*512` conflicts with the frozen 32768 baseline.

The real NPU4-7 launch proved the switch active. The runtime automatically
removed graph sizes 1, 2, 6, 10 and 14 because sequence parallelism requires
TP4 multiples, then failed during KV-cache initialization with a symbolic
`s59` versus `ceil(s59/4)` assignment mismatch on every TP worker.
FlashComm1 therefore failed the startup gate. This is not latency evidence and
does not reject the general communication method; it rejects this unchanged
v0.23.0 Qwen3.5 TP4 integration.

Use `scripts/run_qwen35_tp4_candidate_vs_original.sh` for the real TP4
decision. It requires unique `RUN_ID` and absolute new
`OUTPUT_ROOT`, starts only the selected candidate, records its
container inspect and log, runs first-32 once at 1/5/8/16, and emits a
correctness plus 2x decision report and hashes. Its trap stops only the exact
container it started; the underlying launcher rejects any existing process on
the selected physical device set.

The next candidate was BF16 weight `FRACTAL_NZ`, isolated as
`weight_nz_mode=2` in
`configs/qwen35-query-rewrite-bf16-nz-candidate.yaml` and launcher mode
`bf16-nz`. This is not quantization: exact-image source applies
`maybe_trans_nz` inside `AscendUnquantizedLinearMethod` and continues
through `unquantized_gemm`. Mode 1 leaves BF16 weights in ND, while mode 2
converts eligible non-conv1d weights. The real launch proved the previously
unknown interaction negative: `aclnnMatmulAllReduce` requires the weight
input in ND and rejected FRACTAL_NZ before readiness. Do not stack it with the
failed FlashComm1 path.

The fixed original actually used MatMulAllReduce disabled. Therefore the next
bounded recovery is `weight_nz_mode=2` with MatMulAllReduce disabled: relative
to the fixed original this changes only the BF16 weight layout, while testing
whether the startup failure belongs specifically to the fused communication
path. This variant still needs activation, exact response correctness and real
  E2E evidence before it can enter the best stack.

The recovery was implemented as launcher mode `bf16-nz-mmar-off` with
`configs/qwen35-query-rewrite-bf16-nz-mmar-off-candidate.yaml`. Both the
environment and additional-config explicitly disable MatMulAllReduce, NZ is
explicitly mode 2, FlashComm1 is false, and no quantization argument exists.
The real run proves this combination starts and can reduce low-concurrency
TTFT, but its response hashes and concurrency-16 behavior reject it.

The next bounded candidate is MatMulAllReduce enabled alone with NZ mode 1 and
FlashComm1 disabled. This is a valid single-variable treatment relative to the
actual fixed original, which forced MatMulAllReduce false, and it targets the
profiled AllReduce bottleneck without either failed interaction.

That candidate was implemented as launcher mode `mmar-on` and
`configs/qwen35-query-rewrite-mmar-on-candidate.yaml`. It explicitly keeps
NZ mode 1, FlashComm1 false and BF16/no quantization. Its real run met the TTFT
p50 target but missed the TPOT target and exact-hash gate, so it is rejected.

### Active resource handoff

The user confirmed that physical NPU4-7 are assigned to this workstream;
continue to leave NPU0-3 untouched. The separate bounded
`/cache/austinov/p0/pin_ab_47.sh` run completed and self-cleaned. Watcher
operation `exec-00000000000005d7` proved NPU4-7 were released without
disturbing the NPU0-3 workers. Deferred operation
`exec-00000000000005e6` then ran the complete MMAR candidate and also
self-cleaned. The post-run snapshot shows no process on NPU4-7 and the same
four pre-existing VLLM worker PIDs on NPU0-3.

## Baseline evidence correction

The prior TP4 `quick32-v3` metrics are now the user-designated fixed
original denominator for the 2x goal. They forced
`enable_matmul_allreduce=false`; this remains a mandatory caveat in
decision reports, not a reason to rerun baseline. Every candidate must match
the original first-32/one-repeat/request semantics and pass the hash-locked
analyzer. MTP remains rejected because it regressed and changed response
hashes.
