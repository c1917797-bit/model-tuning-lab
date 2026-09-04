# Qwen3.5-27B query_rewrite 2x E2E Optimization

## State

- Execution: `tp4-development-baseline-running`; integration: `not-ready`.
- Branch: `work/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Worktree: `/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Physical NPU0-3 are currently owned by this workstream's
  `qwen35_query_rewrite_tp4_dev_decodegraph` service on loopback port 10010.
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
- A 32-record development scaling run for concurrency 1, 5, 8 and 16 is
  currently active as AgentWeb operation `exec-0000000000000335`.

## Provisional operator candidate

The first operator/algorithm treatment to evaluate after freezing the current
development baseline is the fused GDN prefill path from vLLM-Ascend upstream
commit `77d13e2c0bfa9862b711b68811889e36b9d56aca`. It replaces the multi-kernel
chunk gated delta-rule prefill pipeline with
`torch_npu.npu_chunk_gated_delta_rule`. Reuse the audited patch from the
adjacent GDN workstream, but remeasure under this workstream's 133K,
prefix-cache-enabled protocol; its historical 41984/no-prefix-cache numbers
are not comparable.

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

## Resume

First poll `exec-0000000000000335`, verify the TP4 service and benchmark client
ownership, and summarize all completed quick32 artifacts. Do not start a second
client. Preserve NPU4-7. When all eight NPUs are explicitly released, render
the exact command from `configs/qwen35-query-rewrite-baseline.yaml`, freeze
its normalized JSON arguments and run the final four-cell original baseline.
