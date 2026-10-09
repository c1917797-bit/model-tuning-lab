# HYPIC phase-6 retry8 preregistration

- Scope: one new immutable attempt for the frozen `hypic-only/repeat3` phase-6 performance unit after retry7's independently recorded foreign PID on physical NPU1.
- Authorization basis: the user's active four-hour request is to finish HYPIC validation, and the latest instruction permits on-card validation now that cards are ready. No change to the HYPIC question or gates is authorized or planned.
- Root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry8`.
- Source, service image, model, workload, metrics, thresholds, repetitions, and acceptance rules remain frozen.
- Resource ceiling: physical NPU0–3 and port 8223 only. Never use NPU4–7. Never stop, alter, or remove a foreign task/container.
- Gate: freshly resolve `chicaihong01/ma`; prove direct route; verify retry8 root absent, physical NPU0–3 free, and port 8223 free immediately before launch; retain the existing continuous physical-process guard. No arbitrary idle-duration rule.
- Executor: `sync=false`, `timeout=14400`; poll the stable operation ID. On timeout inspect the same operation/root before taking action.
- If a foreign PID or probe error appears, preserve evidence and release only retry8-owned resources. This does not change the r13 quality rejection.
