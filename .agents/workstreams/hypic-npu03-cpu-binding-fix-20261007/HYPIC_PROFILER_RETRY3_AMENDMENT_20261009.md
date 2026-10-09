# HYPIC profiler retry3 amendment

The retry2 Prefill phase succeeded and remains frozen under
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r2/prefill`.
It is not repeated.

The retry2 Decode controller `exec-00000000000004ac` ended invalid before
capture. Its continuous guard observed PID 3418373 on physical NPU0 at
2026-10-09T17:06:17.580046Z, traced to the pre-existing `Maxon4ick_vllm`
container `87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa`.
The guard had 88 samples and zero probe errors. Its exact owned container,
workers, and port 8223 were released. This is an isolation failure, not a
Decode profiling or HYPIC result.

Retry3 runs only the missing Decode phase under new root
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r3`.
All model, image, source, HYPIC, profiler, warmup, capture, evidence, resource,
and acceptance settings from the original preregistration remain unchanged.
It may start only when a fresh direct-route snapshot proves physical NPU0-3
and port 8223 idle. No external process or container is stopped or modified.
