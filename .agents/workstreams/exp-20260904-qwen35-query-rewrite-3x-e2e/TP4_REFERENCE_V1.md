# Four-card MTP OFF reference v1

User confirmed on 2026-09-06: continue toward at least 3x acceleration of both
TTFT and TPOT (each <= reference/3), not the stale 2x goal. Physical NPU0-3,
TP4/DP1 only; leave NPU4-7 untouched. No quantization or retraining.

Operation05c7 completed exit0; independent verification05ec checked all12
raw cell hashes, 384 completed requests, zero errors, natural EOS throughout.
Dataset /cache/cch/query_rewrite.jsonl, first32 requests per cell, c1/5/8/16,
three repetitions. Aggregation: median of the three request-p50 values;
throughput is median of the three run-level output-token throughput values.

| Concurrency | TTFT p50 ms | TPOT p50 ms | Output tokens/s |
|---:|---:|---:|---:|
| 1 | 919.427870 | 35.319914 | 24.380334 |
| 5 | 1068.339205 | 52.628031 | 68.755542 |
| 8 | 1061.065425 | 62.510540 | 85.368806 |
| 16 | 1941.482455 | 74.169196 | 115.566124 |

Evidence root:
/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp4dp1-npu03-ref-v1

baseline-summary.json SHA256:
cef6713367f387fd67c15c2cc0bdf071c33f58846b8ef9a041a489186aa0d9d4

This is a measured reference, not a performance win or quality PASS. Empty
answer references do not establish semantic quality. Same-host p0_mp changed
containers during measurement; shared resource interference is unresolved.
Cold/warm and prefix-cache reuse differ over repetitions. Preserve every raw
cell and its tails; do not select only fastest runs or infer cross-topology gains.
Next: same-protocol four-card MTP ON k1 control, then target-runtime profiling,
joint parameter/algorithm/operator implementation, correctness and E2E gates.
