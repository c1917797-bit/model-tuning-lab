# Renew24 portfolio decision seam (not an executor)

Pure DAG/queue and admission proposals for MAIN. Nothing here launches, stops,
signals, retries, signs authority, talks to Docker/NPU, or sends agent messages.
Existing main_serial_handoff_v1 already implements finite serial fail→verified
release→next; this work does not claim that as new. Its real checked/obj/publish
Ref readers are reused through an exact18451B/SHA-pinned parent.

## What is executable here
- scheduler.plan(nodes, leases, snapshot, now, policy): checked source/entry/
  adapter, actual consumer prerequisite Refs and exact MAIN reviewed packet;
  PREPARING never equals READY. Returns proposals, not dispatch.
- scheduler.released(...): original serial child terminal + exact owned-release
  contract, then repair off-device or result-pending. Unknown/reused/missing
  terminal never releases its lease. A successful child is not a passed gate.
- scheduler.refill(nodes, agents): distinct independent preparation follow-up
  proposals for idle/completed actual handles; scope/paper diversification and
  duplicates checked. Running/unknown handles retain their work.
- Single-card disjoint packing uses one summed cgroup/CPU budget and actual
  free RAM/disk plus unspent commitments. Existing actual usage is not charged
  twice. DockerRoot/output filesystems are separate explicit keys. Reserve
  values come unchanged from MAIN, never inferred from HBM.
- Ready TP4/model/profiling/formal stages reserve earliest safe start; bounded
  backfill must finish (including cleanup) before it. Exclusive timing admits
  no concurrent CPU preparation or device activity.
- Idle output is a timestamped actual-card sample with a blocker, NOT continuous
  utilization or a zero-gap claim.

## Integration with the actual owner (MAIN only)
1. MAIN registers a finite source-frozen packet per real paper/gate. The existing
   main.reviewed-stage-admission/v1 review needs extra joint_demand/stage_kind
   fields; unchanged old tickets therefore fail closed until reviewed. No READY
   packets are supplied in this directory.
2. MAIN's single serialized dispatcher calls plan while holding its shared
   dispatch lock, rechecks the original owner admission, records the lease
   BEFORE issuing its original owner launch. It invokes only the registered
   existing controller, not a command from this decision output.
3. Keep admitted/running/unknown/terminal-awaiting-release leases in the ledger.
   Register a newly observed unknown operation rather than omitting it. The
   snapshot must include every lease's actual usage, even an unknown one.
4. On actual original terminal + source-specific adapter release, call released.
   Continue original independent result adjudication without holding cards.
   Only its real acceptance Ref can mark a node passed and unlock successors.
5. Call refill immediately on delivery/terminal; actually send the returned
   follow-up through the permitted agent mechanism and reconcile live handles.
   A returned proposal is not an agent activation.

No production cross-paper handoff is claimed. The old SKVQ010 adapter is NOT
compatible with current BOLE/MXR/DeltaLog by name. A source-specific MAIN
release adapter must really emit/verify the original release contract before
released() is used. Pure planning does not authorize a new adapter or device.

Current concrete registration gaps: BOLE renewed source/window + the unresolved
current numerical predecessor; MXR current diagnostic source/entry and accepted
full numerical predecessor; other papers need their own legal actual source
and source-specific release consumer. These are PREPARING, not placeholder
READY jobs. DeltaLog source is not read by this work.

## Device-free validation / CLI
/usr/bin/python3 -I -B <this-dir>/test_scheduler.py

Default CLI outputs dispatch_executed=false; no --execute switch exists.
Optional --plan-ref '<Ref3 JSON>' consumes a bounded immutable input and emits
a proposal only. Input keys match plan arguments (without reader). The fixed
current user window is Oct24 07:51:43Z→Oct25 07:51:43Z; MAIN supplies that
unchanged policy and the actual per-owner cutoffs/reserves. Preparation does
not renew them. No current authority, actual snapshot, packet or owner is
created by tests; fixture MAIN labels live only in unique temporary files.

Focused controls cover real parent hashing/actual producer-consumer Ref triples,
DAG/cycles, preparation vs ready, failure/release/next, unknown lease retention,
disjoint/overlap/TP4 backfill, summed RAM/CPU/two-FS disk, fresh snapshots,
fixed full-stage deadline, agent continuation/scope uniqueness and isolated CLI.

## BOLE original-metadata seam (no parallel approval)
bole_metadata.normalize(C, source_ref=..., commands_ref=..., stage='CPU'|'model'|'consume',
 now=<MAIN current epoch>, cpu_millis=<registered original quota>,
 docker_write_bound=<registered original future-write cap>) returns inert
bole.scheduler-stage-metadata/v1. It reads the actual source-bound COMMANDS,
qualification_authority_ref and its existing MAIN_review_ref, validates the
original seven source-review operands/window/phase/resource profile and exact
CPU/model/consume source/output operands. It creates no new MAIN review.

COMMANDS.bound_source is SOURCE_BOUND. COMMANDS.source is SOURCE_TEMPLATE.
The model/CPU --source-ref is an embedded Ref3 JSON, not a SHA list member.
The real CPU preflight already runs INSIDE model: standalone CPU is optional
diagnosis, not another mandatory repeat. normalize always emits PREPARING and
ready=false. The planner's BOLE profile consumes this immutable metadata plus
MAIN's actual DAG passed edges and producer/consumer/acceptance Refs; only MAIN
can put its node in READY after consuming those original gates. No new
main.reviewed-stage-admission record is required for this BOLE profile.

Current prospective registration (NOT materialized/ready at source preparation):
ROOT .agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/
bole_phase_clock_prepare_v1_20261024/phase_runtime_renderer_v4/
prepared-source-short8-shared-phase-v4
OUT /opt/host/vnf/austinov/run-bole32k-cache-shared-phase-short8-v4-20261024
Missing: actual new SOURCE_BOUND/COMMANDS Refs, their original current authority,
accepted source-audit edge, registered CPU quota and Docker future-write bound,
fresh aggregate observation and MAIN handoff/owner lease.

Historical result API checks the real bole.actual-three-node-model-owned/v131
RESULT, unchanged source, original LOWERCASE <arm>/cleanup.json and its old
Ref2(path,sha256) leaves by full actual rehash. It never invents byte lengths or
fresh inspection. current_release_verified remains false even if historical
stopped/retained/errors=[] is present. BOLE's actual new lease remains held until
MAIN independently validates fresh exact owner/inspect/SMI release; do not route
this historical observation to generic released(), whose existing serial proof
schema is intentionally different.

A reservation safe-now is emitted only after actual full fit; resource-ineligible
TP4 cannot starve a fitting single-card node. Future bounded-release backfill is
separate exclusive_pending/safe_start_proven=false, not a claim of future resource
availability. Every actual launch must freshly recheck the original admission.
