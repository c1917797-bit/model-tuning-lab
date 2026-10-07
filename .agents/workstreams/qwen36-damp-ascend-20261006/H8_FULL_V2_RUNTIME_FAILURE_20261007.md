# H8 full v2: first real device exception

Current outcome: **failed implementation/device matrix; operator attribution pending**.
MA0e6e ended exit1 after1205.774s. Original full operation is retained in
H8_FULL_V2_OPERATION_20261007.json; original RESULT remains outside Git:
`/cache/cch/qwen36-paper-preparation-20261007/recurrent/MAIN-h8-full-v2-20261007-001/RESULT.json`,
SHA591349c231326ca04372e74303355a2bce93fa7fbde860eba5a8fafa7401552e.

## Actual coverage and failure

Physical6 failed at B6/eager/trial0 before its first recorded step, at
2026-10-07T18:06:51Z. TorchNPU synchronize returned507035, vector-core/scalar
invalid-GM-address or cross-device-access-timeout signature. Native and H8 were
both enqueued before that fence; this does not identify which operator faulted.
It is not a numerical-tolerance violation or task-accuracy conclusion.

Independent MA0e9c saw physical4/5/6/7 recorded passing steps1315/1329/1280/1201
(total5125). Complete cases8/8/8/7(total31), partial cases remain uncompleted.
Reports4/5/7 retain running flags because MAIN aborted their processes after
physical6 failure; they are not live or full PASS. Full11520 and lifecycle/model
gates are not accepted. Earlier scoped B16/640-step PASS remains valid.

No first-failed raw CPU tensor snapshot exists in the report roots. The observer
copied before-state on NPU but saved CPU raw data only after the failed fence.
Preserve the original exception, not fabricated replay data. The next diagnostic
must persist actual CPU inputs/state before dispatch and isolate native/H8 fences
or processes; original library, arithmetic and thresholds remain frozen.

## Independent retention and hardware audit

MA0e9c exit0 verifies all four exact owned CIDs stopped/Pid0/noExec/noOOM and
retained, not deleted. MA0e9f exit0 at18:17:24Z verifies the original protected
physical0–3 PIDs585850–53/starttimes/cgroups/argv unchanged. All4–7 healthOK,
AICore0, no running compute process, HBM2866/2865/2865/2861MiB. Ordinary
MemAvailable94352520KiB (~89.98GiB). These are observation-time facts, not fresh
authorization for a future launch. Original receipts are in
H8_FULL_V2_INDEPENDENT_20261007.json.

MA0e88 read a nonatomic report during write and failed JSON parsing: an observer
race, not the kernel cause. MA0e90 and0e9c stdout bounds truncated later telemetry
after unexpectedly large error/identity fields; original exits retained, no full
SMI claim from those dumps. Changed bounded MA0e9f closes only hardware/identity.
Direct full RESULT read exceeded MCP response limit; bounded hashing/parsing
verified all5509078 original bytes, not a missing result or fabricated PASS.

## Queue and goal alignment

FlashInfer v5's actual whole operation_get receipt reader failed before any
device dispatch (MAIN MA0e8a): route exists inside operation, not at outer root.
Retain its68 software/source tests; withdraw prior whole-entry numerical-ready
claim until an independent source-bound successor consumes real original bytes.
See FLASHINFER_V5_RECEIPT_GAP_20261007.json. Do not flatten/fabricate legacy PASS.

SparQ v3 CPU-FP64 V dtype and receipt-format gaps were found in MAIN source
review before reservation. Independent v4 is delivered/software-only, awaiting
MAIN review/actual CPU prerequisite; no oldv3 device run. W4 and recurrent/mixed
preparations continue in parallel, MAIN alone serializes devices.

Next short goal: source-supported first-fault attribution, then relevant
native correctness and model/lifecycle -> same-stack fixed1024 paired E2E ->
final2048 tasks. No new non-HYPIC accepted technique. KVBuffer cutoff
2026-10-08T08:29:54Z and portfolio2026-10-09T11:17:31Z unchanged.
Authorized32GiB release complete; OVS/NUMA3 retained; no additional release,
outside stop, NPU0–3 action, original runtime modification or relaxed gate.
Checkpoint remains local while known HTTPS credential-helper blocker persists.
