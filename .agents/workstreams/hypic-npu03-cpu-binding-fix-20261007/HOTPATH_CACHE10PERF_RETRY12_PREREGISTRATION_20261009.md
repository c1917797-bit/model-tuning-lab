# HYPIC-only/repeat3 retry12 preregistration

Authorized continuation: user granted four hours to complete the already
active HYPIC validation and then confirmed NPU0–3 may be used when actually
available. Retry11 was independently classified as a pre-health environmental
failure caused by foreign cannbench_ds PID 4177138 on physical NPU2, with no
scored requests and exact owned-container release.

## Frozen identity

- Campaign/phase: cache10perf, hypic-only, repeat3 (the sixth and final matched
  phase).
- Unique immutable root:
  /cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry12
- Treatment, source, service image, model, workload, metrics, thresholds,
  repetition, ordering, and independent audit: unchanged from the frozen
  six-phase plan.
- Resource ceiling: physical NPU0–3 plus port 8223 only; never NPU4–7.
- Isolation: fresh physical preflight immediately before start and continuous
  physical-PID/cgroup guard during execution. Never stop or modify foreign
  work. On violation, preserve the immutable attempt, remove only its exact
  owned service, and report no performance conclusion.
- Executor: asynchronous, timeout=14400; poll the same operation handle.

The retry flag is admitted only when the immutable retry11 artifacts prove its
foreign pre-health failure, zero measurement, no probe errors, and exact owned
release. This amendment does not alter any scientific acceptance rule.
