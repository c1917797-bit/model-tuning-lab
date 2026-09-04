# Qwen3.5-27B query_rewrite 3x E2E Optimization

## State

- Execution: `oriented-resource-blocked`; integration: `not-ready`.
- Branch: `work/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Worktree: `/opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e`.
- Physical NPU0-3 are currently free.
- Physical NPU4-7 are owned by `qwen38_gdn_fused_candidate` on loopback port 8210. Do not stop, restart, inspect inside, or otherwise perturb it.
- The frozen DP2/TP4 baseline requires all eight NPUs, so no valid baseline has started.

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
cell. The final target is TTFT and TPOT no greater than one third of the
original baseline at every concurrency, with zero request errors, passing
business correctness, and no unacceptable p95/p99 regression.

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

First re-run `npu-smi info`, container device-map inspection, port checks and
CPU ownership checks. Start nothing until NPU4-7 are explicitly released.
Then render the exact command from
`configs/qwen35-query-rewrite-baseline.yaml`, freeze its normalized JSON
arguments and run the four-cell original baseline.
