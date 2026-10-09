# cache10perf no-cache repeat3: terminal independent phase audit

2026-10-09 UTC. The fifth of six prospectively frozen matched performance
phases completed under controller `exec-0000000000000024` (exit 0).
Its immutable raw root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-no-cache-repeat3`.
Do not rerun or reuse it.

The frozen independent `audit_phase('no-cache', 'repeat3', quality_sha)`
passed: two one-token warm requests, 40 successful fixed 1,024-token c16
measured requests, 42 unique IDs, source/image and four physical NPU0–3
worker identity, raw-metric arithmetic, 164 clean continuous isolation
samples, and exact owned container/NPU/port release. This is the disabled
control, so no HYPIC hot-path events were expected.

SHA256: contract
`4a98f16ee4ba8fefefd9539aaf9f7ff919d9c50fb2de973a0d27a8ebbf9b89bb`;
arm-result
`00a6681e6adfd9c6b2916a1f0657204dc06eca975a382c1f2c702569c302075b`;
performance
`7aaf7c28999935a6217d46aa734289a6e3c90e4990af2996c8ac785c8ff797a9`.
Weighted TPOT was 74.727578 ms/token, TPOT P95 111.744995 ms,
TTFT P95 86,694.139190 ms, and output throughput 102.754813 tokens/s.

The remaining frozen phase is HYPIC-only/repeat3, controller
`exec-000000000000004b` already running. Do not infer the three-repeat
performance decision until its terminal root and the six-phase independent
audit pass. The separate r13 quality decision remains REJECT_OR_QUALIFY
(230/381 → 219/381), strict quality hot coverage 368/381 FAIL; favorable
speed cannot override either gate.
