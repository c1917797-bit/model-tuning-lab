# Algorithm Feature Piercing Loop

## Purpose

Use one immutable evaluation ruler for every paper-derived optimization. Freeze data, load, metrics, runtime configuration and statistics before judging a treatment. Change only the declared algorithm switch.

## Seven-step loop

1. Freeze the suite: NIAH+, LongBench v2, GSM8K and CEval; fixed sample IDs/hashes, prompts, lengths, concurrency and request rate; TTFT/TPOT/OTT/E2E/throughput/batch-delay plus quality.
2. Run G1 unoptimized baseline with all optional optimizations disabled. It is the denominator for every result.
3. Run the orthogonal matrix: G2 native-only, G3 algorithm-only, G4 combined. Paired comparisons change exactly one switch.
4. Repeat on at least two compatible models of different sizes before claiming model-version independence.
5. Execute quality gates: discrete-score overlap, difference versus measured NPU nondeterminism, deterministic <=512-token canaries, and per-dataset/per-category regression checks.
6. Produce a decision containing relative performance, uncertainty, quality scope and the best configuration.
7. Preserve one-shot start/stop/test entry points, config templates, raw results, summaries and troubleshooting knowledge; then reuse the same ruler for the next algorithm.

## Phase isolation learned from the successful batch-size-32 run

Performance and quality are different measurement phases, not two commands against arbitrary accumulated server state. For each group: start the frozen configuration, wait for health 200, warm up, run performance three times, stop, restart the exact same group, wait for health 200 again, then run quality three times. The restart prevents profiler, graph compilation, caches and capture hooks from leaking into quality evidence.

Use fixed-output semantics (`ignore_eos=true`) only for performance load construction. Quality uses deterministic generation with seed 0, temperature 0, thinking disabled, `ignore_eos=false`, and `extract_non_reasoning_content`. Record a distinct service-instance ID and the same service-config hash for both phases.

## Adaptation for structural pruning

The employee Loop is retained, but 'difference <1-2pp' is not automatically lossless. Dk pruning changes weights and can create systematic errors. The 1-2pp value is only a prior until this exact model/suite's baseline nondeterminism is measured. A passing aggregate mean cannot hide a dataset, category, long-context or deterministic-canary cliff.

Fixed-first-channel and L1 remain feasibility probes outside G3. Only the paper-aligned DRRQR checkpoint may populate G3/G4 for an adoption decision.

## Current gap map

- GSM8K test data is present at /cache/austinov/eval-data/general/prepared/gsm8k_test.jsonl.
- A LongBench harness candidate exists, but the exact frozen LongBench v2 data has not been located.
- NIAH+ and CEval frozen data are not currently present in the searched paths.
- G2's exact native optimization switch is defined and hashed; runtime activation proof is pending.
- DRRQR is not constructed.
- Qwen3.5-4B is selected as the second compatible GDN model; its DRRQR conversion/load validation is pending.

Therefore the current speed and L1 probes cannot be promoted into the final four-group conclusion. Decision remains iterate.

## Result row contract

Each row must contain: experiment/group/model/checkpoint hash, dataset hash, container image digest, full serving config hash, run index (1..3), cold/warm classification, load shape, TTFT/TPOT/OTT/E2E/throughput/batch-delay, quality score, per-sample artifact path, profiler path and invalidation reason if excluded.

## Required order

Materialize and hash all four datasets -> freeze G1-G4 configuration -> run G1 three times -> G2/G3/G4 three times -> quality gate -> second model -> final performance/profile decision -> reusable one-shot assets.
