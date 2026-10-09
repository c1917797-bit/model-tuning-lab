# HYPIC profiler retry2 amendment

The first Prefill launch at
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r1`
ended before health or capture. The continuous guard observed PID 3148909 on
physical NPU0 at 2026-10-09T16:41:33Z and resolved it to the pre-existing
`Maxon4ick_vllm` container
`87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa`.
The exact owned profiler container was removed and its workers and port 8223
were released. This is an environmental isolation failure, not a profiler or
HYPIC result.

Retry2 uses the new immutable root
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r2`.
All model, image, source, HYPIC, profiler, warmup, capture, evidence, resource,
and acceptance settings from
`HYPIC_PROFILER_PREREGISTRATION_20261009.md` remain unchanged. It may start
only after a fresh direct-route snapshot proves physical NPU0-3 and port 8223
idle; no external process or container may be stopped or modified.
