# Four-card MTP k1 comparison v1

05f3 completed exit0;0611 checked all12 raw hashes,384 requests,zero errors,
natural EOS. TP4/DP1,physical0-3,real query_rewrite first32,c1/5/8/16 x3.
Reference is current-configuration OFF reference, not exact original baseline;
see PARAMETER_PROVENANCE.md. Median of repeat-level request-p50 values.

| Concurrency | OFF TTFT ms | ON TTFT ms | TTFT ratio OFF/ON | OFF TPOT ms | ON TPOT ms | TPOT ratio OFF/ON |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 919.428 | 932.774 | 0.986 | 35.320 | 32.552 | 1.085 |
| 5 | 1068.339 | 1192.837 | 0.896 | 52.628 | 49.083 | 1.072 |
| 8 | 1061.065 | 1206.521 | 0.879 | 62.511 | 61.841 | 1.011 |
| 16 | 1941.482 | 2205.302 | 0.880 | 74.169 | 81.151 | 0.914 |

Ratio >1 means lower observed latency. No cell meets both >=2x. Do not adopt
MTP k1 as target solution. Small TPOT improvements at low concurrency do not
compensate for TTFT or high-concurrency regressions. These are measured ratios,
not isolated causal claims: OFF run overlapped changing p0 host workload,
outputs/lengths drifted, and cold/warm prefix reuse differs across cells.
Lossless accuracy remains UNPROVEN: zero errors and empty answer references
are not correctness evidence. Do not label accuracy rejected merely from hashes.

Candidate evidence directory:
/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/tp4dp1-npu03-mtp-k1-v1

candidate-summary.json SHA256:
a26b08ccb1a421f9a6da1a656813a15a83cfea87433dcdbbad106a0fa6f2b0df

Reference summary SHA256:
cef6713367f387fd67c15c2cc0bdf071c33f58846b8ef9a041a489186aa0d9d4

Next: preserve MTP final service evidence, exact-stop task-owned service,
start separate TP4/DP1 dynamic-profile OFF reference, use --expected-replicas1
(CLI spelling: --expected-replicas 1), capture prefill/decode bottleneck and
first-shape tails. Resolve accuracy determinism and original config provenance
before acceptance; optimize actual hot path without quantization or retraining.
