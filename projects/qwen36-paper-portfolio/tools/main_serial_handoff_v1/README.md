# MAIN finite serial device-stage handoff

This is a bounded, explicit-opt-in foreground dispatcher, not a daemon or recurring automation. MAIN reviews a finite list of exact source-bound stage tickets. Physical NPU4–7 has one device-stage owner; NPU0–3 is protected.

## Scheduling behavior

- A ticket with missing preparation is returned to preparation; independent READY tickets may continue.
- A failed device stage yields only after the original child is reaped and exact owned release is independently verified. Repair, raw CPU analysis, reports and Git do not retain the device lease.
- Original controllers retain their stop/retain cleanup, resource reserve, numerical gates, no-overwrite outputs and deadlines. Unknown ownership or release stops dispatch.
- No unchanged failed experiment is retried. An empty READY queue exits with a concrete reason instead of occupying cards with dummy work.
- Finite pre-review binds argv, source, adapter, resources, devices, prerequisite evidence, cutoff and unique outputs. Adding arbitrary unreviewed work is not supported.

## Verified scope on 2026-10-10

- MAIN actual Linux operation0542: 36 tests passed, zero skips, including a real local child exit/wait/reap/log exercise.
- MAIN actual operation0543: read-only consumption of original SKVQ010 operation052b (exit1), original cleanup plus fresh exact-owned container inspection and NPU inventory passed.
- These checks verify dispatcher behavior and a real failed-stage release, NOT observed automatic cross-paper handoff, continuous utilization, paper correctness or performance.
- The supplied adapter is restricted to the frozen SKVQ010 contract. SKVQ010 is failed and must NOT be rerun. A separate KIVI018 profile is in preparation.
- No executable future multi-paper plan is supplied; EMPTY_PLAN_TEMPLATE.json is not a READY ticket.

## Paths and execution

This canonical directory contains the actual deployed, tested bytes. PREPARER_ENTRY.json is retained unchanged for provenance; its proposed /cache/cch/.../recurrent deployment path is not the deployed root. Do not blindly execute those old path examples.

Read SOURCE_MANIFEST.json and serial_batch.py before creating a MAIN-reviewed plan. Use this canonical directory's serial_batch.py and SOURCE_MANIFEST.json together. Default invocation is OFF; actual execution requires the explicit environment enable, --execute, source-manifest hash, reviewed-plan hash and a fresh output directory. Every stage adapter must match its frozen producer version; do not generalize the SKVQ010 profile to later versions.

Actual release proof:
 /cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-SKVQ010-052B-READONLY-RELEASE-20261010-001.json

The current device queue is maintained in .agents/workstreams/qwen36-damp-ascend-20261006/SERIAL_DEVICE_STAGE_QUEUE_20261010.json. Its ready count is evidence-based, not a count of drafts.
