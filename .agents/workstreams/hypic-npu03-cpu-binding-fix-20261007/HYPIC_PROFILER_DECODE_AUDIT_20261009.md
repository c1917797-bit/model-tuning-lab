# HYPIC profiler Decode terminal audit

Date: 2026-10-09. Diagnostic profiler evidence only; the frozen HYPIC
quality and six-phase performance verdicts are not changed.

## Device capture and immutable raw evidence

- Root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r6/decode`.
- Controller `exec-000000000000059e` terminated with exit 0. The frozen
  512-token, `ignore_eos=true` Decode stream returned 512 tokens and 64
  nonempty chunks after successful `/start_profile`; the successful
  `/stop_profile` followed. Recorded interval:
  18:44:39.499421–18:44:42.175946 UTC.
- Physical NPU0–3 workers were 119291, 119292, 119293, 119294. The
  continuous guard recorded 85 samples, zero foreign PIDs, zero probe
  errors. The exact owned container, worker processes, and port 8223 were
  released. NPU4–7 were never mapped.
- 441 nonempty raw files across four rank trees match the original artifact
  inventory sizes and SHA256 hashes. Original raw files were not parsed or
  modified. Control SHA256: contract
  `a6ad132a6ccaf0f49632a9233560910ef9849de062807f3637178f16d0a8d9c7`;
  capture `179c5aec5b2e155f360e31278d4d1917b46b69368e7f5f`;
  artifact inventory
  `7639b43ca22109c4abc0d0f879febff7dffbc6e65603278417240ddae4ea520a`;
  guard `22b64c880836a8c038e5b8406caa98f63785f72feb64e2ba56b9c5b4e477c3f3`;
  release `4ac3630c49c532b582b3ee0789e61d996814aebc8d3360c174c495ba592e4b4b`;
  result `80981b54f21957da3c46559b67dead569b73abcae1c9a9eef12b066a3e370d09`.

## Independent offline parse and failure retained

The first copy, `profiler-offline-parse-20261009-r6-decode`, was parsed in
the pinned image with no network or numbered NPU devices. Its parser
controller `exec-00000000000005b6` returned exit 0 but logged four
`CANNExportParser` failures, and the resulting traces were invalid. Direct
`msprof --export=on` on this *copy* returned exit 255 with
`Init platform by driver faild!` when only the driver library directory was
bound. This is a parser-environment failure, not a failed NPU capture.

On that failed copy, a bounded diagnostic mapped only the shared
`/dev/davinci_manager` management node (no numbered NPU compute devices)
and a read-only driver library bind. `msprof` rank0 export then succeeded
and produced 99,603 operator rows. The failed copy remains separate.

A new 209 MiB copy,
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-offline-parse-20261009-r6-decode-manager`,
was verified byte-identical to the raw profile tree before parsing. In
the same pinned image, with no network and no numbered NPU devices,
controller `exec-00000000000005cb` parsed all four ranks with
`analyse('/profiles', max_process_number=4, export_type='text')` and exited
0 without parser errors.

The pre-registered independent verifier
`verify_hypic_profiler_decode.py` passed against this clean copy. Each
rank has nonempty `kernel_details.csv`, `op_statistic.csv`,
`api_statistic.csv`, `operator_details.csv`, `step_trace_time.csv`,
and valid `trace_view.json`; torch_npu 2.10.0.post4 / CANN 9.1.0
records Level1 and PipeUtilization. Each rank has 99,603 detailed kernel
rows, 46 columns with required semantic fields, and 83,223 actual NPU
compute-kernel events timestamped *inside* the 2.676525-second capture
interval, spanning 1.8106 seconds. This exceeds the prospective per-rank
64-event/1-second gate. HTTP chunks alone were not used as device proof.

## Decision and remaining boundary

The bounded Prefill-plus-Decode collection and parser path is now
behaviorally verified on physical NPU0–3, with the failed first offline
parse retained as an environment lesson. The original Prefill
preregistration's exact `>=47`-column threshold remains missed; its
46-column output is **not** retroactively passed. These profiles alone do
not establish a CANN, HCCL, or kernel root cause for the HYPIC quality
regression. Frozen paired quality remains 230/381 → 219/381
(`REJECT_OR_QUALIFY`); frozen matched-performance TPOT gain remains
21.5243%. No HYPIC deployment or paper-complete conclusion follows.
