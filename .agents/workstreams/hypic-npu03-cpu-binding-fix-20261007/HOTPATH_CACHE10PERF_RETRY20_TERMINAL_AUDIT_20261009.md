# HYPIC repeat3 retry20 terminal audit

## Decision

Retry20 is an environmental pre-health isolation failure, not a HYPIC performance result. The controller stopped before service health and before any scored request. Do not pool it with another root or infer a performance regression.

## Immutable attempt

- Controller: `exec-0000000000000362`, terminal exit 1 at 2026-10-09 14:36:51 UTC.
- Arm/phase: `hypic-only/repeat3`; attempt root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry20`
- Owned service container: `ea9357cfc3af46cc01a413bf9d0392e368b5381e9436899e3bcff2d7f7df74cc`.
- Foreign lane process captured by the guard: PID `1890601`, physical NPU3, container `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6` (`cannbench_ds)); human launcher/owner is unknown.
- Guard: 36 samples, zero probe errors; it invalidated on the foreign process. No service-health proof, no benchmark rows, and no performance metrics.
- The controller removed only the exact retry20-owned container. Release receipt says `container_removed=true`; `worker_release_proven=false` is expected because the worker never reached the measured phase.

## Post-cleanup observation

At 2026-10-09 14:38 UTC, `npu-smi` still showed external PIDs 1890601 and 1920829 on physical NPU3; NPU0–2 showed no running processes. The same external container was running. Port 8223 had no listener, and the retry20-owned container was absent from the running-container list. This is a point-in-time observation, not an availability lease; no next attempt may start until a fresh direct-route check proves all physical NPU0–3 and port 8223 idle.

No foreign task/container was stopped, modified, or cleaned up. NPU4–7 were not used.

## Replayable receipts

| Receipt | SHA-256 |
| --- | --- |
| `contract.json` | `58ab99d5742582a6e66b256844324742480dc882bff77edf91910711796c750f` |
| `arm-result.json` | `8a5c6cdbda2344615dae10f14e10bfcc36924c6b567004311aebcdb4a58f9046` |
| `hypic-only/hypic-evidence.jsonl` | `7c94c68175fa496a766ca9c5670787c0680a81bcc1798b29f0ed01ab9f51ba59` |
| `hypic-only/lane-guard.json` | `4efe09fe5750e112356e6029fad68e712358f993f9474bd58035720492b72690` |
| `hypic-only/pre-health-release.json` | `c184f1d0af692b0b93b3deaef12cc4a49c3269f0dae66141d522ef11a6135576` |

Run `python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_retry20_environmental_failure.py` from the repository root to replay the immutable receipt checks.

## Next action

Continue user-authorized opportunistic monitoring. Start a fresh, uniquely preregistered retry only after a fresh physical NPU0–3 and port 8223 idle proof. If an external process reappears, wait; never stop or modify it. Preserve this root unchanged.
