# HYPIC profiler retry4 amendment

Retry3 Decode controller `exec-00000000000004c3` was rejected by its
preflight because a physical NPU0-3 process appeared after the prior free-lane
snapshot and before container creation. The immutable retry3 root records an
invalid result and no captured profile. No owned container was created.

Retry4 uses only a new Decode root,
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r4`.
The already valid retry2 Prefill is not repeated. All model, image, source,
HYPIC, profiler, warmup, capture, evidence, resource, and acceptance settings
remain as preregistered. A fresh direct-route, physical NPU0-3, and port 8223
admission is required. External work is left untouched.

The copied retry2 Prefill raw profile parsed offline in the same pinned image.
All four ranks produced complete trace and statistics. `kernel_details.csv`
has 46 columns on torch_npu 2.10.0.post4 / CANN 9.1.0, including the required
PipeUtilization fields, rather than the preregistered minimum of 47. This is
recorded as a strict numeric-gate deviation; it is not silently recast as a
preregistered pass. The semantic-field acceptance question is handled
separately in the maintainer Skill review.
