# HYPIC cache10 performance retry21 and six-phase terminal audit

Date: 2026-10-09

## Decision

Retry21 is a valid HYPIC-only/repeat3 measurement, and the frozen six-phase
matched performance campaign is complete.

- Controller operation: `exec-00000000000003a4`
- Controller terminal state: completed, exit code 0
- Root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry21`
- Scope: physical NPU0-3 only, TP4, input 32768, output 1024, concurrency 16
- Source: `c12060c`
- Workload identity: unchanged from the frozen plan

## Retry21 evidence

- 40/40 scored requests completed with exactly 1024 output tokens.
- Two one-token warmups plus 40 scored requests produced 42 unique request IDs.
- All 40 scored request IDs have four-worker hot-path proof.
- Continuous lane guard recorded 164 samples, no foreign process and no probe
  error.
- The exact owned container was removed, physical NPU0-3 were released, and
  port 8223 was released.
- Post-run `npu-smi info` showed no process on physical NPU0-3.

Retry21 metrics:

| Metric | Value |
| --- | ---: |
| weighted TPOT | 58.896690 ms |
| TPOT P95 | 78.740563 ms |
| TTFT P95 | 45,759.196170 ms |
| output throughput | 133.329578 token/s |
| benchmark duration | 307.208653 s |

Immutable receipt hashes:

- `arm-result.json`: `a0c88a883dda5513c4fe579e70d5be0028bb338963bcd9ee1d7d5f6d1183e05e`
- `lane-guard.json`: `c7917f198b1c9f555c8caded4e62f5bb3542273b59b90bc951f7497de4b66295`
- `service-stop.json`: `6aa4c4dfc1ed9808bc46792f3b653ec84a96deb58cf934b428dce1dc827f7331`
- HYPIC evidence: `476de4fd1842ac47b76cdaf8918eaea4c01c5e37986c6152a6bfb9749407e253`

## Frozen six-phase result

Independent audit:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hotpath-cache10r13-matched-performance-audit.json`

Audit SHA256:
`d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062`

All six phases passed identity, row cardinality, fixed-output, source,
isolation, exact-release, and raw-to-summary checks. The three HYPIC phases
also passed strict 120/120 four-worker request coverage.

Three-run medians:

| Metric | no-cache | HYPIC | Effect |
| --- | ---: | ---: | ---: |
| weighted TPOT | 74.727578 ms | 58.643006 ms | 16.084572 ms saved (21.5243%) |
| TPOT P95 | 111.744995 ms | 78.603832 ms | 33.141162 ms saved |
| TTFT P95 | 86,628.571480 ms | 45,759.196170 ms | 40.869375 s saved |
| throughput | 102.754813 token/s | 133.451314 token/s | 1.298735x |

Performance conclusion: `EFFECT_SCREEN_PASS`.

## Quality boundary

This performance success does not overwrite the paired max-2048 quality
result:

- no-cache: 230/381
- HYPIC: 219/381
- delta: -2.8871 percentage points
- deployed quality decision: `REJECT_OR_QUALIFY`
- strict quality decision: `NOT_ACCEPTED_HOT_COVERAGE` because quality hot
  coverage was 368/381, not universal

Therefore HYPIC is successfully reproduced as a performance mechanism on this
frozen workload, but it is not unconditionally accepted for deployment. The
quality regression and incomplete quality-path attribution require
qualification or follow-up isolation.
