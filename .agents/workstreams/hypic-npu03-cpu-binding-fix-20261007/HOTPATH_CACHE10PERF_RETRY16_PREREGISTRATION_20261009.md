# HYPIC retry16 preregistration — 2026-10-09

## Purpose

Complete the one remaining frozen matched-performance phase: `hypic-only/repeat3`.
Retry15 is an environmental pre-health failure, not a benchmark result. Its
continuous guard recorded foreign `cannbench_ds` PID 865188 on physical NPU2
at 12:57:31 and 12:57:33 UTC (container
`efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`). The
exact retry15-owned container was removed; no service health or scored request
was reached.

## Frozen identity and protocol

- Arm/phase: `hypic-only/repeat3`.
- Attempt: `hotpath-cache10perf-hypic-only-repeat3-retry16`.
- Immutable raw root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry16`.
- Controller: `hotpath_cache10_matched_performance.py --arm hypic-only --phase repeat3 --environmental-retry16 --run`.
- Preserve the existing source revision, official container image, model, workload, request IDs, metrics, thresholds, repetitions, and acceptance rules. No tuning or denominator changes.
- Use only physical NPU0–3 and port 8223. Never use NPU4–7. Never stop, modify, or claim ownership of an external process or container.
- Keep the controller under its stable asynchronous operation ID. Do not restart it while that operation remains authoritative and live.

## Admission and isolation

The latest point-in-time `npu-smi` snapshot had no process on physical NPU0–3,
and `ss -ltnp` showed no listener on 8223. These observations authorize only
an opportunistic attempt, not an isolation guarantee. The controller's
continuous physical-process guard is authoritative: any foreign process or
probe failure invalidates the attempt before scoring; clean up only its exact
owned container and retain the immutable failure evidence. Recheck host route,
processes, cards, port, and root immediately before launch.

## Decision boundary

Only a valid, independently audited 40-request phase with complete
per-request four-worker hot-path evidence can fill the missing performance
phase. Keep the already-frozen r13 quality decision
`REJECT_OR_QUALIFY` and strict hot-coverage failure separate; a speed result
cannot override either quality conclusion.
