# HYPIC profiler Prefill terminal audit

Date: 2026-10-09. This audits the new diagnostic profiler pass, not the
frozen HYPIC quality or six-phase performance conclusion.

## Device capture

- Immutable raw root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r2/prefill`.
- The exact Qwen3.6-27B TP4 HYPIC-only service used physical NPU0-3 and port
  8223. Two 32-token warmups ran before the measured 32768-token segmented
  Prefill-focused request, which returned one output token.
- The four physical workers were 3234105, 3234106, 3234107, and 3234108.
  The continuous guard recorded 88 samples, zero foreign-process detections,
  and zero probe errors. The exact owned container, workers, and port were
  released.
- The integrated start/stop path emitted 281 nonempty raw files across four
  rank `*_ascend_pt` trees. Each `profiler_info_<rank>.json` records CPU+NPU
  activities, Level1, `ACL_AICORE_PIPE_UTILIZATION`, text export,
  torch_npu 2.10.0.post4, and CANN 9.1.0.
- Contract SHA256:
  `54f72f823bf88c4ba9163ca4497c537280dec1067b5393b9a8b42425399fb138`.
  Capture SHA256:
  `5853dff8f335939116d7ee89deae839fad9c8d983b8c38f98df10c156d3c8a5b`.
  Guard SHA256:
  `4734d3678d2aebe4c4b2b4694f72e7667cbde1f83631e6ee94301d120737f6a7`.
  Terminal result SHA256:
  `c400e15775c82675f5ee57761370302460319b1ab2457deae2fd8978e071de15`.

## Independent offline parse

The original raw root was preserved. A copy at
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-offline-parse-20261009-r2-prefill`
was parsed by `torch_npu.profiler.profiler.analyse` in the same pinned image,
with no NPU devices mapped and no network. Controller
`exec-00000000000004cc` completed with exit 0.

Each of four ranks has a valid `ASCEND_PROFILER_OUTPUT` with a parseable
`trace_view.json`, nonempty `op_statistic.csv`, `api_statistic.csv`,
`operator_details.csv`, `step_trace_time.csv`, and `kernel_details.csv`.
Each kernel file has 5,622 rows and 46 columns. The 46 include `Stream ID`,
`Input Shapes`, `Output Shapes`, `aic_mac_ratio`, `aic_mte2_ratio`, and
`aiv_vec_ratio`; this is detailed Level1/PipeUtilization data, not a shallow
nine-column export. The same `/cache/cch` filesystem parsed successfully.

The preregistration said at least 47 columns if a kernel CSV was emitted.
That exact numeric gate did not pass. The current CANN 9.1.0 schema has 46
columns while retaining the specified metrics. The maintainer Skill now
defines a prospective version-aware semantic-field gate, but this audit does
not rewrite the preregistered verdict. The profiler Skill as a whole remains
partial until valid Decode capture and parsing are independently audited.

The profile has not yet been used to assert a CANN, HCCL, operator, or device
root cause for the HYPIC quality regression.
