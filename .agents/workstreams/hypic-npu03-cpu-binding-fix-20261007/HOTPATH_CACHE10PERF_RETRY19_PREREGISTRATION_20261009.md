# HYPIC repeat3 retry19 preregistration — 2026-10-09

## Objective and immutable decision boundary

Run only the missing sixth matched performance phase, `hypic-only/repeat3`,
under the already frozen cache10r13 performance contract. This retry changes
neither the HYPIC technique nor workload, quality ruler, thresholds, nor
comparison denominator. The paired r13 quality decision remains
`REJECT_OR_QUALIFY`: 230/381 baseline versus 219/381 HYPIC (−2.8871 pp);
strict four-worker hot coverage remains 368/381. Performance cannot reverse
either finding.

## Frozen treatment and identities

- Target: `chicaihong01/ma`, physical NPU0–3 only. NPU4–7 are forbidden.
- Worktree: `/cache/cch/model-tuning-lab-hypic-e2e-20261006`,
  branch `work/hypic-npu03-cpu-binding-fix-20261007`.
- HYPIC plugin source commit: `c12060cd47e7575ead059983d7a8bb4704165c98`.
- Official serving image:
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
- Frozen phase: 40 measured requests, concurrency 16, 32768 input tokens,
  16384 prefix tokens, fixed 1024-token output, two warmups, explicit HYPIC
  segment-end evidence, same service identity and request-ID sequence as the
  other five independently audited phases.
- Controller SHA256:
  `9dd349f01619084849624c9ef0ce14bd7b8777e560820d70e339d18ad29b4cd9`.
- Request-ID benchmark SHA256:
  `0d88b054a91e4985f131187d84899d76d57a1da1d97f842c2f51052534abc6ac`.
- Retry18 environmental receipts are immutable and replay-verified; retry19
  controller admission checked their exact hashes, external physical NPU1 PID
  identity, 80 clean guard samples, zero scored rows, and exact-owned-service
  removal. The offline admission check passed without creating retry19's root.
- Unique retry19 root (must remain absent until the launch):
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry19`.
- Launch command from the workstream directory:
  `python3 -B hotpath_cache10_matched_performance.py --arm hypic-only --phase repeat3 --environmental-retry19 --run`.

## Resource admission and safety

The user authorized opportunistic monitoring and task execution only when
physical NPU0, NPU1, NPU2, NPU3 have no running processes and TCP 8223 has no
listener. Re-resolve `chicaihong01/ma`, prove direct routing, inspect physical
processes and port, and confirm this unique root is absent immediately before
launch. A prior idle snapshot is not a lease. Keep the controller's continuous
physical PID/cgroup guard active throughout. Container mappings alone do not
block the lane; physical process evidence does. Do not stop, signal, or modify
foreign work.

If a foreign process or guard probe error occurs before health/scoring, preserve
the immutable retry19 root and detection-time evidence, classify it as
environmental/no-result, and clean up only retry19's exact owned service.
Do not call it HYPIC success or regression. Never restart a live or ambiguous
controller.

## Acceptance

Retry19 is a valid measurement only with 40/40 successful fixed-output rows,
two warmups, all 40 measured request IDs proven on all four HYPIC workers,
continuous clean isolation, exact owned-resource cleanup, and a passing
independent phase audit. Only after that gate may the frozen six-phase
independent comparison run. Until then, phase six remains unmeasured.
