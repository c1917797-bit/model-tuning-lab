# HYPIC phase-6 retry7 preregistration

- Scope: corrected launch of the already-frozen `hypic-only/repeat3` phase-6 unit after retry6 was terminated by an operator-configured 20-second executor timeout before any measured request.
- Authorization basis: the user's active request is to complete HYPIC validation within the four-hour continuation, and the latest instruction explicitly says the cards are ready for on-card validation. This is not permission to change the HYPIC protocol or to touch other NPU lanes.
- Root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry7`.
- Treatment, image, model, data, workload, metrics, thresholds, repetitions, and acceptance rules remain frozen and unchanged.
- Resource ceiling: physical NPU0–3 and port 8223 only. Never use NPU4–7. Do not stop, alter, or remove foreign workloads.
- Immediate gate: freshly resolve `chicaihong01/ma`, prove direct routing, confirm this root is absent, inspect physical NPU0–3 and port 8223 immediately before launch, and rely on the controller's continuous physical-process guard. No arbitrary idle-duration threshold.
- Executor handling: launch asynchronously (`sync=false`) with `timeout=14400` seconds; poll the returned operation ID. If a tool call times out, inspect its same operation and exact root; never blindly relaunch.
- Retry6 root/report remain immutable and untouched. This root is also immutable once created.
- Retry7 is one corrected launch. If it is invalidated, preserve evidence, release only exact resources owned by retry7, and report; do not infer a HYPIC result from an environmental/tooling failure.

The r13 paired quality conclusion remains `REJECT_OR_QUALIFY`; performance evidence cannot reverse it.
