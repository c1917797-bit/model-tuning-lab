# HYPIC-only/repeat3 retry14 preregistration

The user continues to authorize the final HYPIC-only/repeat3 stage on physical
NPU0–3 only when actually idle. Retry13 is preserved as an environmental
pre-health failure; no HYPIC performance conclusion was produced.

## Frozen identity

- Campaign/phase: cache10perf, hypic-only, repeat3 (the sixth and final
  matched phase).
- Unique immutable root:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry14
- Treatment, source, service image, model, workload, metrics, thresholds,
  repetition, ordering, and independent audit: unchanged from the frozen
  six-phase plan.
- Resource ceiling: physical NPU0–3 plus port 8223 only; never NPU4–7.
- Isolation: immediate physical preflight and continuous physical-PID/cgroup
  guard. Never stop or modify foreign work. On violation, preserve this root,
  release only its exact owned service, and make no performance claim.
- Executor: asynchronous, timeout=14400; poll the same operation handle.

The controller admits retry14 only after validating retry13's exact
pre-health foreign-process evidence and release. No scientific threshold or
benchmark setting changes.
