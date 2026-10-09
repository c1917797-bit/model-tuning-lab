# HYPIC phase-6 retry6 terminal audit

- Classification: operator/executor timeout before any scored benchmark request; not a HYPIC performance verdict and not a foreign-workload collision.
- Controller operation: `exec-00000000000001c9`, launched with an explicit 20-second executor timeout. The tool returned terminal `timeout` at 20.002 seconds while the detached attempt-owned service container continued starting.
- Immutable attempt root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry6`.
- Contract SHA256: `6da197fb0cbf5cbf61bf7fe27384e80753a7702d3d6ab201f632998b6967ef7d`.
- Startup evidence SHA256: `813d98cd8047acc064f32835f77b465ca43944ceff712bc6d1c21aff234a4fe7` (28 plugin/capability/material-cache startup events; no request or scored-result events).
- The exact attempt-owned container ID `9c29bcc5e26d8380f98d559b76021e1103464b2e5088e35cf39026bb776a1e24` was verified by its attempt label and retry6 name. It had the frozen service command and only physical `/dev/davinci0`–`3` device declarations. Its logs showed model/service initialization but no benchmark launch. The continuous host controller had terminated, so no unguarded service was left running.
- Removed only that exact retry6-owned container. Foreign containers were untouched. Post-cleanup checks: no process on physical NPU0–3, port 8223 free, and no retry6-labeled container.
- No `performance.json`, `arm-result.json`, or `benchmark-command.json` exists. No performance sample was measured; the startup event file is retained as raw evidence.

## Root cause and correction

The mistake was an executor timeout configured to 20 seconds for a multi-hour campaign. The process timeout killed the host-side controller while Docker's detached service survived. For the corrected launch, use `sync=false`, a campaign-length executor timeout (14,400 seconds), poll the stable operation ID, and inspect the same immutable root after any tool timeout before considering recovery. This must not add an arbitrary NPU-idle duration.

The next attempt, if launched under the user's still-active HYPIC on-card validation request, uses a distinct preregistered root and unchanged experiment contract. The r13 paired quality remains `REJECT_OR_QUALIFY`; this startup failure does not alter it.
