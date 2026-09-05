# Qwen3.5-27B TP8 dual baseline comparison

Both groups use physical NPU0-7, TP8/DP1, BF16 without quantization, the same first 32 query_rewrite records, c1/c5/c8/c16, three repetitions, and the median of the three request-level p50 values.

| Concurrency | MTP OFF TTFT ms | MTP ON TTFT ms | TTFT speedup | MTP OFF TPOT ms | MTP ON TPOT ms | TPOT speedup | OFF/ON output tok/s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 889.694 | 952.419 | 0.934x | 35.450 | 33.646 | 1.054x | 25.268 / 26.150 |
| 5 | 1028.583 | 1185.176 | 0.868x | 47.841 | 49.580 | 0.965x | 72.587 / 68.514 |
| 8 | 1043.884 | 1194.705 | 0.874x | 60.821 | 58.292 | 1.043x | 79.129 / 81.810 |
| 16 | 1966.446 | 2171.249 | 0.906x | 69.305 | 69.132 | 1.003x | 112.980 / 115.851 |

A speedup above 1.0x is better. The final target is at least 2.0x for both TTFT and TPOT at every concurrency.

## Evidence

- MTP OFF summary: `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp8-user-baseline-v5-20260905T184600Z/matrix/baseline-summary.json` (SHA256 `e3e03a5f1a5ce8d3e2d5f35ccf6a410d5d96555ad9012ba5881fd9227246639d`)
- MTP ON summary: `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/candidates/tp8-mtp-local-argmax-k1-v3-20260905T205300Z/matrix/candidate-summary.json` (SHA256 `cd0e31e37f3e6c8a3eda9801480e3e951c4a61f44c0b5cbad7211f0d9a03ef17`)
- MTP ON source: `37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd`
- Machine-readable table: `/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp8-dual-baseline-20260905T213000Z/baseline-comparison.csv` (SHA256 `7e928e02387a661a2190503b65cebbfdd94b412e2e39d8b232c99f4057affda9`)

## Protocol audit

- These frozen v1 results include EOS-only requests in the legacy TPOT summary and reuse identical prompts with prefix caching enabled. Treat them as cache-policy-specific.
- Natural EOS and zero request errors prove runtime validity. Task correctness is reported separately; string hashes and character similarity are diagnostic.
- MTP acceptance metrics and the full per-repeat results remain in the external evidence root.
