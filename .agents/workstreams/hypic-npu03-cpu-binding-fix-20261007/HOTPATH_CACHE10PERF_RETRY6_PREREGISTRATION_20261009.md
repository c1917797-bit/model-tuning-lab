# HYPIC phase-6 retry6 preregistration

- Authorized by the user at 2026-10-09 10:51 UTC: “现在卡已经好了，可以上卡验证了”.
- Scope: one additional immutable attempt for the already-frozen `hypic-only/repeat3` phase-6 performance unit, after retry5's audited pre-measurement foreign-process failure.
- Root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry6`.
- No changes to source, service image, model, workload, metrics, thresholds, repetitions, phase order, or acceptance rules.
- Resource ceiling: physical NPU0–3 and port 8223 only. Never use NPU4–7. Do not stop, alter, or remove foreign processes or containers.
- Gate: freshly resolve `chicaihong01/ma`, prove direct routing, verify the unique retry6 root is absent, inspect physical NPU0–3 and port 8223 immediately before launch, then rely on the controller's continuous physical-process guard. No arbitrary idle-duration gate is added.
- Failure handling: any foreign physical NPU0–3 PID or guard probe error invalidates this root. Preserve raw evidence and remove only resources carrying this attempt's exact identity; do not reuse the root.
- Retry budget: exactly one attempt. No retry7 without fresh explicit user authorization.
- Prior failure receipt: retry5 root `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry5`; contract SHA256 `8a1020814dad5ea91520fb44c161137a2b7212d36e65a1c294f100c096a96057`; guard SHA256 `24d9e1f91596214903a95d9fe8b7ff91562a8fc5411eedd63a3e7845c9e8ce87`; zero-byte evidence SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

This is a performance-only retry. The separate r13 paired-quality conclusion remains `REJECT_OR_QUALIFY`; a speed result cannot change it.
