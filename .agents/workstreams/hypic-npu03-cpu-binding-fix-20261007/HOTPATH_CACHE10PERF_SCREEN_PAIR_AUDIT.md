# cache10perf screen pair: valid bounded performance, quality still rejected

2026-10-09 UTC. The prospectively frozen first two phases completed in order
with separate owned services on physical NPU0–3. The independent frozen
`audit_phase` passed each phase's 2 one-token warm requests, 40 successful
fixed 1,024-token c16 measured requests, 42 unique request IDs, source/image
identity, physical worker proof, raw-metric arithmetic, 160/150 clean
continuous isolation samples, and exact owned container/NPU/port release.
The HYPIC-only screen proved the explicit boundary and post-repair four-worker
hot path for all **40/40 measured request IDs**, with no audit issues.

Baseline raw root:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-no-cache-screen`.
Candidate raw root:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-screen`.
The candidate contract, arm-result, performance and HYPIC-event SHA256 values
are respectively `2a47b32f003ac9cb351171aef3c19a6a22372db8b7128d18a98430ab4bcd3f28`,
`f4a42f59561a4d10fe246bc4067b20c99805e6a52639b879a2dd2a6fa1b7a56f`,
`e68133dd61ae2310fec4494353ad17d78ab026e237c5033e3a2d1d5799d68c98`,
and `04b1e773699947bb0cde31f2f7677eb76ced4d09e5d3f83ecdc80b24d05a21b8`.
The baseline hashes are in HOTPATH_CACHE10PERF_SCREEN_BASELINE_AUDIT.md.

For this single screen only, no-cache → HYPIC weighted TPOT was
75.1451 → 58.6430 ms/token (16.5021 ms/token, 21.96% lower);
TTFT P95 was 86,628.57 → 45,695.64 ms (40.933 s lower);
TPOT P95 was 112.0370 → 78.6038 ms; output throughput was
101.3951 → 133.4513 tokens/s. This passes the predeclared screen-effect
thresholds, but it is **one matched screen pair**, not the three-repeat
independent campaign conclusion. The separate r13 paired quality decision
remains REJECT_OR_QUALIFY (230/381 → 219/381), strict quality hot coverage
368/381 FAIL, and C3 remains unimplemented. Favorable speed cannot promote
HYPIC to paper-complete or production adoption.
