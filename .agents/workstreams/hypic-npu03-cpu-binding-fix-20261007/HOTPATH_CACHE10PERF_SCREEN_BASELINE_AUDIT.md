# cache10perf no-cache/screen terminal baseline audit

2026-10-09 UTC. The first of six prospectively frozen performance phases
finished on physical NPU0–3. The controller handle
`exec-0000000000001c05` subsequently returned `not_found`; this is
a connector-observation limit, not a reason to restart or relabel the raw run.
The immutable raw root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-no-cache-screen`.

The frozen independent `audit_phase("no-cache", "screen", quality_sha)`
passed after controller release. It checked the exact r13 quality-audit hash,
source commit and official image, Qwen3.6-27B TP4 worker identity on physical
NPU0–3, fixed c16 input 32,768/output 1,024 protocol, 2 one-token warm
requests plus 40 successful measured rows with 42 unique request IDs, raw
metric arithmetic, 160 clean continuous isolation samples, source
attestation, and exact owned container/NPU/port release. No foreign task was
stopped or modified.

Raw SHA256: contract
`bf95c35e762f7cdc4901886b67ceb5bb881bc0beca1c89adbc3d12300cf52846`;
`arm-result.json`
`9b6fa4f7af6ac962d2d786b0b6b8beebbbf44c8ea7006d3564e3b514c883563c`;
`performance.json`
`07bef26011b84444244b92cbfc807325c27577aca6b9cc10906505278309aea0`.
Baseline-only weighted TPOT was 75.1451 ms/token, TPOT P95 112.0370 ms,
TTFT P95 86,628.5715 ms, throughput 101.3951 output token/s and benchmark
duration 403.9643 s. These are not a paired HYPIC effect or adoption verdict.
The r13 paired quality rejection and strict hot-coverage failure remain in force.
