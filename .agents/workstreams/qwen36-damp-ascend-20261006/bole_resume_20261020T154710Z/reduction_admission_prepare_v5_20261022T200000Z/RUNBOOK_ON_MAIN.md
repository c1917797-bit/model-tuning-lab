# MAIN ON V5 exact admission sequence

Prepared only. This runbook does not grant a lease or fill a MAIN review.
Complete three-file comparison is V4_FULL_DIFF_REVIEW.json.

## Reviewed delta inventory

main_admission_ON_v5.py: no added/removed functions. Only historical_owners
(count8 to10) and main (exact current substrate Ref joined to manifest and MAIN
review before historical construction) changed. All15 other top-level functions,
including source_inputs, snapshot_inputs, current_live_checks, create argv,
complete receipt handling, original failure policy and execution limits, are
AST-identical. Constants change only scope/source/output/evidence, two latest
V4 CIDs, one latest V4 unit, draft flag and pending snapshot/history pins.

final_snapshot_ON_v5.py: main adds V4 two-owner joins and count10; one pure
textonly_identities function added by deriving the exact continuation identity
reader. All7 original other top-level functions are AST-identical. Original
whole snapshot/mount interning/caps stay unchanged.

historical_owner_context_reduction_v5.py: only build changes, selecting the exact
V4 substrate only for the two named V4 CIDs/source. All7 other functions stay
AST-identical. NEW_OWNED stays null in this authored module; launcher assigns it
only after actual manifest and genuine MAIN review repeat the exact same Ref.
No old controller is installed into active globals.

Actual V4 unit was read with systemctl cat in exec-00000000000007d2. It has
Type=exec, RemainAfterExit=yes, RuntimeMaxSec4080, TimeoutStopSec180,
MemoryMax536870912, CPUAffinity166, LimitCPU/FSIZE/AS=infinity,
KillMode=control-group. A new unit derives those properties with new names and
logs. Old unit is evidence only and must remain stopped/PID0.

## Canonical current paths

Builder: /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_probe_prepare_v5_20261022T200000Z/ON/prepare_boundary.py
Auditor: /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_probe_prepare_v5_20261022T200000Z/ON/audit_boundary_source.py
SOURCE: /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-reduction-ON-v5_20261022T200000Z
OUTPUT: /opt/host/vnf/austinov/run-bole-reduction-ON-v5_20261022T200000Z
SOURCE-AUDIT output: /opt/host/vnf/austinov/run-bole-reduction-ON-v5_20261022T200000Z-SOURCE-AUDIT
Admission EVIDENCE: /opt/host/vnf/austinov/run-bole-reduction-main-admission-ON_v5_20261022T200000Z
Scope string: reduction_ON_v5_20261022T200000Z
Lock: /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock

The underscore inside scope/admission EVIDENCE is intentionally internally
consistent; SOURCE and model OUTPUT use ON-v5 and must equal actual builder.
The revised preparation test checks those actual independently owned producers.

## Exact MAIN patch list before any readonly snapshot

1. Review all three actual files and the complete current V5 observer/source.
2. In final_snapshot_ON_v5.py set REVIEWED_FROZEN=True only after its review.
   Do not change HELPER, CONFIG, DIAGNOSTIC, original CUT/caps or owner pins.
3. Compute whole-file Ref3 after that edit. In main_admission_ON_v5.py set
   SNAPSHOT_PROGRAM_PIN=(actual_snapshot_bytes, actual_snapshot_sha256).
   The eventual config snapshot_program_ref is its full Ref3.
4. In main_admission_ON_v5.py set HISTORICAL_CONTEXT_PIN to full Ref3 of
   historical_owner_context_reduction_v5.py, after reviewing its exact current
   bytes. Do not replace its NEW_OWNED=None with a guessed current identity.
5. Set main_admission_ON_v5.py REVIEWED_FROZEN=True after final code/pin review.
   Then compute launcher_ref. Any later launcher edit invalidates launcher_ref.
6. Keep SNAPSHOT_HELPER, RESTORE_PIN and COMPLETE_RECEIPT_PIN unchanged:
   their original full files are reused, not newly implemented.

Current authored hashes are in V4_FULL_DIFF_REVIEW.json and PATH_REPAIR_V1.json.
They are draft hashes and change when MAIN performs the three explicit freeze
edits. Freeze/pin edits require a new final readset and review, not an old hash.

## Execution order (MAIN only)

First source-only freeze using MAIN's actual source review Ref:
```sh
/usr/bin/python3 -I -B '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_probe_prepare_v5_20261022T200000Z/ON/prepare_boundary.py' --review-ref "$SOURCE_REVIEW_REF"
```
Read actual BUILD_RECORD.json, SOURCE_BOUND.json and COMMANDS.json. Hash actual
auditor after reviewing it; expected currently7377B SHA
8b6ade333640b376fad0e1554d4863e4a2bf32eb29fdd7fc235460f7f1e96d39.
The source auditor requires BOTH exact CLI operands:
```sh
/usr/bin/python3 -I -B '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_probe_prepare_v5_20261022T200000Z/ON/audit_boundary_source.py' --source-ref "$SOURCE_REF" --audit-program-ref "$AUDITOR_REF"
```
SOURCE_REF is the exact full JSON operand also used in generated model command;
not a different whitespace serialization substituted after command binding.

Fill CONFIG.ON.template.json into a NEW control-output location only after
actual source/audit refs exist. Initial template remains true and null Refs
until that point. Do not use the template itself as an executable config.
The complete config keys and review fields are in MAIN_PENDING_ON.template.json.

Before obtaining the fresh snapshot, finalize launcher/helper bytes and code
reviews, prepare every config/review field that does not depend on live snapshot,
and verify final source/control output paths do not exist. This minimizes the
180-second snapshot freshness interval. A separate check-only run repeats the
large input hashing; if it consumes freshness, acquire a new snapshot, never
alter the timestamp or reuse an old one.

Run snapshot command under the same bounded outer read-only execution pattern
used in V4:
```sh
/usr/bin/python3 -I -B '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_admission_prepare_v5_20261022T200000Z/final_snapshot_ON_v5.py' --execute-readonly
```
The OUTER executor must actually capture:
- exact argv above, started_epoch and ended_epoch from real clock;
- real exit_code, child_reaped and timeout;
- source_before and source_after Ref3s, computed from the actual program;
- stdout saved as NEW SNAPSHOT.json, stderr saved as NEW snapshot.stderr;
- full Ref3 of both saved files, not captured/truncated tool text;
- schema bole.final-readonly-snapshot-execution/v1, NPU=false,
  resource_admission=false, source_unchanged=(actual full Ref equality).
Write EXECUTION.json only from that actual execution; success requires exit0,
reaped, no timeout, empty stderr and unchanged source. It is not a hand-filled
PASS. Do not add synthetic oldowner fields or call stdout a resource admission.

Fill final config with snapshot_ref, snapshot_execution_ref and
snapshot_program_ref. Recompute actual config_ref. MAIN then writes the genuine
review binding this config and every reviewed input. Its approved_dispatch is
MAIN's decision; no prepared JSON here supplies that claim.
At dispatch the outer execution ended_epoch must be <=180 seconds old, and
the launcher itself repeats source/history/live checks under an alarm180.

New unit name example (must first be absent):
bole-reduction-on-v5-20261022t200000z-u1.service
New separate unit log directory example (must first be absent):
/opt/host/vnf/austinov/run-bole-reduction-on-v5-unit-20261022T200000Z-u1

After MAIN review/admission, the exact launch argv is:
```sh
/usr/bin/systemd-run --unit=bole-reduction-on-v5-20261022t200000z-u1.service --property=Type=exec --property=RemainAfterExit=yes --property=RuntimeMaxSec=4080 --property=TimeoutStopSec=180 --property=MemoryMax=536870912 --property=CPUAffinity=166 --property=LimitCPU=infinity --property=LimitFSIZE=infinity --property=LimitAS=infinity --property=KillMode=control-group --property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab --property=StandardOutput=append:/opt/host/vnf/austinov/run-bole-reduction-on-v5-unit-20261022T200000Z-u1/unit.stdout --property=StandardError=append:/opt/host/vnf/austinov/run-bole-reduction-on-v5-unit-20261022T200000Z-u1/unit.stderr /usr/bin/env DENSE090_EXTERNAL_OUTPUT_ENABLE=1 BOLE_CONTINUATION_MAIN_ENABLE=1 /usr/bin/python3 -I -B '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/reduction_admission_prepare_v5_20261022T200000Z/main_admission_ON_v5.py' --execute --config-ref "$CONFIG_REF" --review-ref "$MAIN_REVIEW_REF"
```
This command is a prepared example, not executed by this workstream.
Use explicit JSON tool argv, not shell interpolation, for actual AWMCP dispatch.

Do not take an external flock around this invocation: launcher acquires the
ordinary existing lock itself and rejects a conflicting owner. It verifies
the same inode before exec and marks its FD inheritable; the exact original
model owner inherits the lock through full run/cleanup. Do not unlock on
parent observation timeout, expire a live handle or launch a duplicate unit.

Observe the SAME operation and exact unit PID/cgroup/owned CID. Terminal
means original host RESULT plus own retained cleanup/stop and physical-device
release, not just inactive caller. active/exited with both PIDs0 can be terminal
for this RemainAfterExit unit. No next overlapping owner until proved release.

## Time and conclusion boundaries

Authority cutoff stays1792710600/23:10UTC. Admission requires actual now+3780
strictly less than cutoff, not <=. Phase3600/shared cleanup180 and original
resource/reserve/protected0-3 gates stay unchanged. Runtime4080 is an outer
safety cap from V4, not an authority extension.
Only ON raw capture is prioritized. OFF is observer-policy backup and is not
an untouched nativeAR/dense baseline. Independent same-input TP4 reduction
replay is the next diagnostic consumer; no candidate/performance/task PASS
follows from source audit, snapshot or a short successful HTTP request.

