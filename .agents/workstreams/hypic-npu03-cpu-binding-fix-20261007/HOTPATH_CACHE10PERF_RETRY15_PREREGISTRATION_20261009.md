# HYPIC-only/repeat3 retry15 preregistration

This is a distinct continuation of the frozen sixth matched performance phase.
It does not change the treatment, workload, thresholds, or acceptance rule.

## Identity

- Campaign/arm/phase: `cache10perf` / `hypic-only` / `repeat3`.
- Immutable artifact root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry15`.
- Source: plugin checkout `/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008`, commit `c12060cd47e7575ead059983d7a8bb4704165c98`.
- Frozen identity: Qwen3.6-27B, TP4 on physical NPU0–3, cache10, max output 1024, 40 fixed-output requests, 2 warmups, same service/image/CPU binding, no-cache/HYPIC one-switch pair, and existing ordered screen/repeat2/repeat3 schedule.
- Image: `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
- Port: 8223 only; NPU4–7 are out of scope.
- Retry predecessor: retry14 terminated before service health and produced zero scored requests. Its immutable audit verified 18 clean guard samples followed by foreign `cannbench_ds` PID 242978 on physical NPU1; only the exact retry14-owned service was removed. See `HOTPATH_CACHE10PERF_RETRY14_TERMINAL_AUDIT.md` and retry14 contract/result hashes in `task.json`.

## Availability and execution gate

At 2026-10-09 12:42 UTC, a fresh direct-route snapshot showed no running
processes on physical NPU0–3 and no listener on port 8223. This is an
observation, not a lease. The user authorized opportunistic monitoring and
execution only while those resources are actually unused; no coordinated
no-submission window or fixed idle-duration threshold is required.

Immediately before launch, resolve `chicaihong01/ma` again through AWMCP,
require direct target proof, inspect physical NPU0–3 process/cgroup state,
port 8223, and active controller/root. Launch only if all remain clear. Keep
the frozen continuous physical-process guard active. Any foreign process or
probe error invalidates the attempt; preserve all evidence and clean up only
the exact retry15-owned service. Never inspect, stop, or modify external work.

The controller addition is limited to registering retry15's unique root and
requiring the exact retry14 pre-health environmental-failure receipts before
allowing this retry. The scientific benchmark contract is unchanged. Run the
same independent phase audit before reporting a performance measurement.
