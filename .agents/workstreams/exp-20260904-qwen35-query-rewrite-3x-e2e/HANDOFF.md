# Qwen3.5-27B query_rewrite 2x E2E Optimization

## State

- Execution: `profile-blocked-external-npu0-3`; integration: `not-ready`.
- Branch: `work/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Worktree: `/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Physical NPU0-3 are externally owned by `p0_ab`
  (`cd07d22999ba42890bdb1a5773406415fc8fd4564783812cfe3d66ecb3e4d8e2`,
  PIDs 172441-172444 as of 2026-09-04 17:04:48 UTC).
  Do not stop, restart, inspect inside, or otherwise perturb it.
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
- Physical NPU4-7 are owned by `qwen38_gdn_fused_candidate` on loopback port 8210. Do not stop, restart, inspect inside, or otherwise perturb it.
- The frozen DP2/TP4 baseline requires all eight NPUs, so no final baseline has
  started. The running TP4 service is a development baseline only and must not
  be substituted for final DP2/TP4 evidence.

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

  These are development A/B anchors only, not the final DP2/TP4 baseline.
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

Measure concurrency 1, 5, 8 and 16 with three valid warm repetitions per
cell. The final target is TTFT and TPOT no greater than one half of the
original baseline at every concurrency, with zero request errors, passing
business correctness, and no unacceptable p95/p99 regression.

The workstream identifier retains the original `3x` label for audit
continuity; the authoritative goal was revised to 2x on 2026-09-04.

## Optimization loop

1. Acquire explicit exclusive ownership of physical NPU0-7.
2. Freeze request rendering, output policy, seed and service/runtime identity.
3. Record the original DP2/TP4 baseline for concurrency 1/5/8/16.
4. Profile Prefill, Decode, GDN, MatMul/AllReduce, Attention, scheduling,
   graph coverage, layout conversion and host synchronization.
5. Add one attributable treatment to the latest accepted stack: operator,
   algorithm, or parameter.
6. Verify reference, microbenchmark, vLLM-Ascend integration, model
   correctness and query_rewrite E2E behavior.
7. Compare both against the immediately previous accepted stack and the
   immutable original baseline.
8. Preserve accepted, rejected, failed and inconclusive results.
9. After individual treatments pass, run combination and ablation A/B.

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

`scripts/analyze_qwen35_query_rewrite_ab.py` is the fail-closed decision
gate. It requires all 24 artifacts (baseline/candidate × concurrency 1/5/8/16
× repetitions 1/2/3), identical model/data/request identities, zero errors,
complete request sets and exact response-hash equality. It emits
`final-target-met` only when both median-of-run-p50 TTFT and TPOT ratios are
at most 0.5 in every concurrency cell.

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
5. query_rewrite E2E A/B and paired profile evidence.

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
external NPU0-3 or NPU4-7 workload. When all eight NPUs are explicitly released,
render
the exact command from `configs/qwen35-query-rewrite-baseline.yaml`, freeze
its normalized JSON arguments and run the final four-cell original baseline.
