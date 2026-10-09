# HYPIC phase-6 retry9 preregistration

The user renewed the active four-hour HYPIC on-card validation after retry8's
audited pre-health environmental failure. This authorizes one distinct
immutable root for the already-frozen `hypic-only/repeat3` phase only:

`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry9`

No source, image, model, workload, serving flag, metric, threshold, repetition,
phase order, or acceptance rule changes. The run is limited to physical NPU0–3
and port 8223. Do not use NPU4–7 or stop/modify foreign work. Require an
immediate same-session `npu-smi`/8223/root preflight and retain the continuous
physical-process guard. Launch once using asynchronous execution with a
14,400-second process timeout, then poll the stable operation ID. If a foreign
PID or probe error appears, invalidate this root, preserve raw evidence, and
release only exact retry9-owned resources. A connector timeout requires
inspection of the same operation and root, never blind relaunch.

The paired r13 quality rejection and strict hot-coverage failure remain
unchanged regardless of any performance result.
