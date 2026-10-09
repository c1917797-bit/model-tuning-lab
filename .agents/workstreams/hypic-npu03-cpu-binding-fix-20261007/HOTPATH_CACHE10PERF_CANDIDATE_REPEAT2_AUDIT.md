# cache10perf HYPIC-only repeat2: terminal independent phase audit

2026-10-09 UTC. This is the third of six prospectively frozen matched
performance phases, not a final HYPIC or paper-success conclusion. The
controller handle `exec-0000000000001c3a` later became unavailable, but
the immutable raw root contains a valid terminal `arm-result.json` and
exact owned-service release. Do not restart or reuse this root:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat2`.

The frozen independent `audit_phase('hypic-only', 'repeat2', quality_sha)`
passed again after the direct `chicaihong01/ma` route recovered. It
checked source/image and physical NPU0–3 worker identity, two one-token warm
requests, 40 fixed 1,024-token c16 measured requests, 42 unique request
IDs, all 40 explicit-boundary joins and **40/40 four-worker hot proofs**,
150 clean continuous isolation samples, raw-metric arithmetic, and exact
owned container/NPU/port release. It reported zero coverage issues.

SHA256: contract
`754a8a0b8ed78b64d0cd4042a2c5e867ebbc9758df922591ad71ca25f32499c9`;
arm-result
`ca6e355b654cc82e33b2a0af5d1f908f379e24bbedcd6b783b8f8318c2668d09`;
performance
`9acf718ac530a2c8a6a6a2b6a99605c4a7ed7d3c87b6314885eeb7cb74f7b9dc`.
Weighted TPOT was 58.498860 ms/token, TPOT P95 78.441900 ms,
TTFT P95 45,794.394730 ms, and output throughput 133.685142 tokens/s.

The separate full r13 quality decision remains REJECT_OR_QUALIFY
(230/381 → 219/381), with strict quality hot coverage 368/381 FAIL.
Neither this single phase nor speed benefit overrides quality failure.
The next frozen phase is no-cache/repeat2, already started under
`exec-000000000000000a`; poll the same handle and independently audit
its terminal root before any further phase.
