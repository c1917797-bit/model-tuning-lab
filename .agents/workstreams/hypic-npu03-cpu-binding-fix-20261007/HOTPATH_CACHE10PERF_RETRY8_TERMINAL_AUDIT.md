# HYPIC phase-6 retry8 terminal audit

Retry8 was the frozen `hypic-only/repeat3` performance phase on physical
NPU0–3, launched asynchronously as operation
`exec-0000000000000201` after an immediate idle preflight. The controller
terminated before service health because its continuous lane guard observed
foreign PID `3967272` on physical NPU0 at `2026-10-09T11:16:41.323395Z`.

The guard captured four samples, with no probe errors. The PID exited before
its cgroup/container identity could be read; ownership is unknown and is not
attributed to any named container or person. There were zero scored requests,
no `service-start.json`, no benchmark command, and no performance result.
Only the exact retry8-owned container
`7f56dd0cc6ae95d113976a65b234e4aa151d3ba562fc6c92683a57a003ad80a7` was
removed. Post-cleanup, that exact container was absent, physical NPU0–3 had no
reported processes, and port 8223 was free.

This is an environmental pre-health isolation failure, not a HYPIC result.
The immutable root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry8`.

Evidence SHA-256:

- Contract: `af5c0d92782b74a13f75ceb2e2d00c7648921f7c8ff19f77990b5dcaba04c6fd`
- Arm result: `8983440e3bfcb63ddc30c18c6d7135562a2ec22835e0b85b6657813c060e464e`
- Guard: `abd898d77ce5344d00f3c37a242ad273a63169b66f02b55e87d133f6a9d328d4`
- Pre-health release: `5d734132c103c759468c7e2d507121a22a72f45c7bcc67b88737c5062e892d06`

Retry9 is separately preregistered. It preserves the same workload, image,
source, metrics, thresholds, and acceptance rules; only the immutable attempt
root changes. No NPU4–7 or foreign workload is touched.
