# HYPIC-only/repeat3 retry13 preregistration

The user confirmed physical NPU0–3 may now be used. Retry12 is preserved as
an environmental pre-health isolation failure; no HYPIC performance
conclusion was produced.

## Frozen identity

- Campaign/phase: cache10perf, hypic-only, repeat3 (the sixth and final
  matched phase).
- Unique immutable root:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry13
- Treatment, source, service image, model, workload, metrics, thresholds,
  repetition, ordering, and independent audit: unchanged from the frozen
  six-phase plan.
- Resource ceiling: physical NPU0–3 plus port 8223 only; never NPU4–7.
- Isolation: refresh the direct target route and perform an immediate
  physical preflight; retain the continuous physical-PID/cgroup guard.
  Never stop or modify foreign work. On a violation, preserve this immutable
  attempt, remove only its exact owned service, and report no performance
  conclusion.
- Executor: asynchronous, timeout=14400; poll the same operation handle.

The controller admits retry13 only after validating retry12's exact
pre-health failure evidence and release. This retry changes no scientific
acceptance rule.
