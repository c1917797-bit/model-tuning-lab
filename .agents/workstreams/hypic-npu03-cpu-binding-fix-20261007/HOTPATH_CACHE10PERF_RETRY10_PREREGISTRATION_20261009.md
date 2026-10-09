# HYPIC phase-6 retry10 preregistration

The user has authorized continued on-card HYPIC validation within the active
four-hour window. Retry10 is one new immutable root for the already-frozen
`hypic-only/repeat3` phase:

`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry10`

No source, image, model, workload, serving flag, metric, threshold, repetition,
or acceptance rule changes. This attempt may use physical NPU0–3 and port
8223 only; NPU4–7 and all foreign work remain untouched. Immediately before
launch, re-prove the topology, physical process table, port, and root absence.
The controller retains its continuous lane guard. Launch asynchronously with
a 14,400-second executor timeout and poll the stable operation ID. If a
foreign PID or probe error appears, invalidate this root, preserve raw
evidence, and release only exact retry10-owned resources. On connector
ambiguity, inspect the same operation and root before any retry.

The existing paired r13 quality rejection and strict hot-coverage failure
remain unchanged regardless of performance.
