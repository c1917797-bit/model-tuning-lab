# cache10r9 request-level hot-path traceability — live interim audit

Status: **running observation, not a terminal quality or HYPIC verdict**.
Observed 2026-10-08 17:36 UTC. Controller operation
`exec-000000000000158e` was still running on the directly resolved
`chicaihong01/ma` peer. Preserve this exact operation and the immutable
attempt root after it terminates:

`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r9-full-hypic`.

The interim read-only scan found 38 complete sample files, 114 scored
request IDs and 76 warm request IDs. Every scored ID had a unique matching
`explicit_segment_boundary_active` and `independent_segment_observation`
event. Four `worker_hot_path` events and 118
`complete_hybrid_repair` events existed, but neither event type contained
`request_id`; no event carrying a scored request ID proved worker hot-path
execution. The first serialized scored sentinel had four worker events and
positive repair counters; that observation is valid only for the sentinel.
The remainder ran at concurrency 8, so aggregate repair counts can include
other scored or warm requests and cannot be assigned to each scored ID.

Source inspection of the pinned HYPIC plugin
`3ad0967589304cd8fc4e7cff02f48ecc6125c89f` explains the gap:
`patches/runner.py` emits `worker_hot_path` only once per worker,
without request IDs; `patches/scheduler.py` emits
`complete_hybrid_repair` as a batch report without request IDs.
`hotpath_quality_full.py` joins scored IDs only to scheduler boundary
events, then compares the aggregate repair count with the scored-row count.
This controller gate is weaker than
`ascend-model-quality-evaluation/references/quality-test-contract.md`:
that contract requires request-level work-performing proof for an
each-scored-request in-path claim. Boundary admission plus a batch counter
does not satisfy it.

Do not alter the live r9 service, plugin checkout, controller, requests or
protocol. Finish or stop r9 only under its frozen authorization and
continuous physical NPU0–3 guard; retain raw rows and final hashes. At
terminal state, independently audit all 127×3 scored rows, event integrity,
isolation and exact release. Classify r9's per-scored-request hot-path
coverage as **unverified** unless a stronger pre-existing joinable signal
is found; a controller exit code of zero alone does not override this
boundary. This is an evidence/telemetry limitation, not evidence that
HYPIC is ineffective or that outputs are wrong.

For a subsequent original-protocol attempt, design a diagnostic-only
request-ID event emitted by every TP worker after its complete hybrid-repair
check, with positive skipped tokens, and verify unique scored-ID joins to
the four expected physical NPU0–3 worker PIDs. Add offline tests proving a
batch-only counter and a missing worker both fail closed. Do not edit the
currently mounted plugin while r9 is live; its checkout also has unrelated
dirty files. Any new candidate service is a new identity and needs a
matching control under the same 0.85 GPU-memory budget; the old 0.9
no-cache arm is not reusable. Attempt new device arms only when physical
0–3 have no foreign processes and port 8223 is free; passive container
mapping alone is not a veto. Never touch NPU4–7 or foreign workloads.

The branch-local `verify_hotpath_request_coverage.py` specifies a narrow
future event contract: `worker_hot_request_verified` must carry the
scheduler-internal `request_id`, one of the four expected worker PIDs,
positive `skipped_prefix_tokens`, and
`complete_hybrid_repair_validated=true`. It fails closed unless all
381 scored API IDs join uniquely to boundary IDs and then to post-repair
events from all four workers. This script is an independent activation
gate, not a quality-score or isolation audit; its offline unit tests
explicitly reject boundary-plus-batch-counter evidence.

At 17:48 UTC, a read-only replay of the live r9 snapshot through
`audit_coverage` found 162 completed scored IDs and the expected four
worker PIDs. It returned `UNVERIFIED`: 162/162 scored IDs lacked a
four-worker post-repair request-level event. Six focused counterexample
tests and all 43 workstream offline tests passed. This snapshot is
intentionally not a terminal arm audit; final raw hashes and the 127×3
cardinality gate must wait for the controller to finish.
