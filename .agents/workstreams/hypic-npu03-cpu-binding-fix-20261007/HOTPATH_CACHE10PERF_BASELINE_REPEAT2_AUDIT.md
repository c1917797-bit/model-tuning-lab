# cache10perf no-cache repeat2: terminal independent phase audit

2026-10-09 UTC. The fourth of six prospectively frozen matched performance
phases completed under controller `exec-000000000000000a` (exit 0).
Its immutable raw root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-no-cache-repeat2`.
Do not rerun or reuse it.

The frozen independent `audit_phase('no-cache', 'repeat2', quality_sha)`
passed: two one-token warm requests, 40 successful fixed 1,024-token c16
measured requests, 42 unique IDs, source/image and four physical NPU0–3
worker identity, raw-metric arithmetic, 162 clean continuous isolation
samples, and exact owned container/NPU/port release. This is the disabled
control, so no HYPIC hot-path events were expected.

SHA256: contract
`cc727013994611795fa400c90457af6b25ae41fb6104a3d5858a11255059ae0e`;
arm-result
`7353974ae26a612d5989cff6a1941c664d50f4173e46e34275516ee476630dfb`;
performance
`8d8b5dfbc665c6969a27705aadc49e4d8e4249e6a9363db5b24e4ab00d156c79`.
Weighted TPOT was 73.372920 ms/token, TPOT P95 110.941315 ms,
TTFT P95 85,695.069490 ms, and output throughput 102.926251 tokens/s.

Against the independently audited HYPIC-only repeat2 (run earlier in
the frozen order), the bounded within-repeat weighted TPOT saving was
14.874060 ms/token and TTFT P95 saving was 39.901 s. Two repeats do not
establish the predeclared three-repeat performance decision. The separate
full r13 quality decision remains REJECT_OR_QUALIFY (230/381 → 219/381),
strict quality hot coverage 368/381 FAIL; speed cannot override them.
Next frozen phase: no-cache/repeat3, controller
`exec-0000000000000024` already running. Poll the same handle.
