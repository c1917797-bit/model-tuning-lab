# HYPIC-only/repeat3 retry19 terminal audit — 2026-10-09

## Decision

Retry19 is an **environmental pre-health isolation failure**, not a HYPIC
performance result. The frozen candidate arm was invalidated before service
health or any scored request. It contributes no latency, throughput, or
performance acceptance evidence and cannot be pooled with another root.

## Immutable receipts

Root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry19`

| Receipt | SHA-256 |
| --- | --- |
| `contract.json` | `fe59917a8ddf62cb538e7a5e9ef30d63d2eae8d14fd5f3798a495211d303b8f9` |
| `arm-result.json` | `25cce108c805d785d4ac01b092990bafced2a3409667cdf1fa2813d572d78506` |
| `hypic-only/lane-guard.json` | `f4d59b8e9553aa1b526af1e3d6b9e03d5e9a6b90cb9175c9f14f1958eeee91e5` |
| `hypic-only/pre-health-release.json` | `e938b1a0e99c76d281bf781909bc4392b853f3af424c3a33f925f54125ae59e7` |
| `hypic-only/hypic-evidence.jsonl` | `9df31bb84fa849c581e7815390e9e120b8fcb2ff2152050463b1c9db9ad15ffd` |

## Evidence and resource boundary

- Controller `exec-0000000000000347`; HYPIC-only/repeat3; 46 guard samples,
  zero probe errors.
- At 14:19:09.373833 and 14:19:12.096625 UTC, the guard captured foreign
  PID 1731309 on physical NPU2 in container
  `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`.
- Health was never proven; no `service-start.json`, benchmark command, or
  `performance.json` exists. There were zero scored requests.
- Only the exact retry19 service container
  `2e92362738a88715789c8bb291fbc0d162a8dde19576529a25668e6a62c23973` was
  removed. The release receipt records `worker_release_proven=false` because
  the service never reached worker health. No foreign work was stopped/changed.
- A post-cleanup live check observed no processes on physical NPU0–3, no
  listener on port 8223, and no exact retry19-owned container. This point
  observation is not a lease; fresh preflight and the continuous guard remain
  required. The foreign process's human launcher is not established here.

Replay with `python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_retry19_environmental_failure.py`.
The verifier checks all five hashes, the physical PID/container identity,
zero probe errors/scoring, and exact owned-resource release. The sixth phase
remains incomplete; the r13 quality rejection is unchanged.
