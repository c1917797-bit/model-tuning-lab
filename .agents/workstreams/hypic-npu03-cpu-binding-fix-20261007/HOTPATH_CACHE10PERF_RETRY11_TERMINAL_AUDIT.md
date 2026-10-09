# HYPIC-only/repeat3 retry11 terminal audit

Date: 2026-10-09 UTC

## Classification

Environmental pre-health isolation failure. This attempt produced no HYPIC
performance result and must not be counted as a failed HYPIC treatment.

## Evidence

- Frozen arm/phase: HYPIC-only / repeat3, unchanged cache10perf workload.
- Immutable raw root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry11`
- Controller: `exec-0000000000000220`; focused controller regressions passed
  18/18 before the immediate NPU/port preflight and launch.
- The continuous lane guard recorded foreign PID `4177138` on physical NPU2
  at `2026-10-09T11:36:11.408969Z`, attributed by cgroup to the existing
  `cannbench_ds` container
  `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`.
- Four guard samples; zero probe errors; no expected HYPIC workers; no scored
  requests; no health proof; no performance JSON.
- The exact owned service container
  `adcd23e61677409f9d76ff0b8e97f18fba896495c376344d45ed3adede6f07da` was
  removed with `container_removed=true`. Post-cleanup inspection found
  physical NPU0–3 empty and port 8223 free. The external container was not
  changed.
- A subsequent resource snapshot observed PID `4189958` on physical NPU1
  while `cannbench_ds` remained running, confirming intermittent shared-lane
  use after an earlier all-clear snapshot.

## Integrity hashes

| Artifact | SHA-256 |
|---|---|
| contract.json | `6f322856a535b4e72a9bdc3ea67d3fbf5c1953fc0e4349ceb5de78b183c48ef6` |
| arm-result.json | `bf1dc55873a6d4f4ee00cd118e76f5927d62cef2f72f7686e078bb27c23bbc7b` |
| lane-guard.json | `968cfbf1e5ead7b048e080b54c70935b1405ef83e847e4943e72528431bbb2ae` |
| pre-health-release.json | `140b3d84cc8d46faace562c2767229d6c8cfa1c24ea7715d9a3a3898ad55e596` |

## Decision

Do not weaken or bypass the continuous isolation guard, do not stop or modify
`cannbench_ds`, and do not use NPU4–7. The frozen sixth performance phase
remains incomplete. If the authorized window continues, retry only from a new
preregistered immutable root after a fresh direct preflight proves physical
NPU0–3 and port 8223 are actually free. A performance result still cannot
override the independent r13 quality rejection.
