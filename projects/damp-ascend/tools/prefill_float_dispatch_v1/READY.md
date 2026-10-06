# MAIN-only isolated DAMP prefill float dispatch — NEW, default OFF

This packet schedules one exact FP32 SR-division seam on one authorized physical
NPU4..7 mapped to logical0. It does not modify frozen float compiled9/runtime15,
fixed-buffer4, numerical helpers, collector, previous controllers or deadlines.
It has not itself run Docker, imported Torch, loaded a library or used an NPU.

## Exact dependencies and scope

The actual candidate library is:
 /cache/cch/qwen36-damp-20261006/prefill-float-build-v1/build/libqwen36_damp_prefill_float_probe_ops.so
 SHA80a06b48be444fbef9a37f7c9857c95518b8181cb8b5ba5ac6a1a21002cb85c0.
Actual receipt:
 /cache/cch/qwen36-damp-20261006/prefill-float-build-v1/build-receipt.json
 SHA7696732308c3dc7c9565cb91b471cf3df268cc94f59cde292c46dfaad60a6baf.
Frozen manifests: compiled e8e1bd5f..., runtime bfc7d359..., fixed44b4bb50...;
all full strings are in dispatch.py. Immutable image660ce23a... only.

Host preparation checks all9 compiled,15 runtime and4 fixed files, the actual
SO/build sources/image/arch, successful command log bytes and defined exported
kernel audit. It imports only pinned stdlib helpers. The image-local OPP file
does NOT exist on this host; host dry-plan therefore explicitly leaves original
source_bindings pending. In the new restricted immutable-image container,
--source-check calls the actual original.source_bindings and fixed.bind_sources
BEFORE any Torch import or NPU canary. No invented receipt projection or future
OPP identity is accepted. This actual call must pass before numerical execution.

One container runs these frozen arithmetic matrices in order:
1. Original complete N896 boundary/random chunks plus N64/N896 x20 changing
   fresh-allocation fixtures, exact/certificate independently,8 repeats each,
   all10 real malformed-input host rejections.
2. New fixed-address N64/N896 x exact/certificate:1 cold prepare/case,20 genuine
   input changes,8 identical replays/turn. Raw-before/after, complete guards and
   input pointers remain the original gate's contract.

Each child additionally records its own actual /proc/self/maps SO/libtorch_npu
paths and hashes without replacing the frozen arithmetic. A primary gate
exception is retained even if map collection fails. A child wrapper is not an
alternative oracle. Frozen gate reports, exact full matrix order/counts,
bitwise scope, source bindings, artifact hashes/nonempty raw-before files,
fixed source-before/after and loaded-library identity are verified before
moving to the successor. Raw tensor payload assertions remain source-bound
to the unchanged trusted runner; the host does not pretend to deserialize
Torch tensors without Torch.

No NPUGraph, selected-slot pack, recurrent feedback, model/cache lifecycle,
serving, matched performance or task accuracy is proved by this packet.
The all-scalar exact path is diagnostic, not a performance candidate.

## Actual execution prerequisites

MAIN supplies persisted original MA0455 structuredContent and its real SHA.
The controller verifies peer_direct/exact MA peer, found/job authoritative
completed record, uncancelled/no-timeout status and real integer exit.
A completed nonzero capture is preserved as failed, not transformed to pass.
Isolated float does not require unrelated SOURCE_LOCK/RESULT success.
The exact owned parent b6e2a151... must ALREADY be inspected stopped with
source-bound original create owner, immutable image, physical4..7 and mounts.
This controller never stops the parent or polls a remote operation.

Default mode creates nothing and claims no current idle fact:
 python3 -B projects/damp-ascend/tools/prefill_float_dispatch_v1/dispatch.py
 python3 -B projects/damp-ascend/tools/prefill_float_dispatch_v1/test_dispatch.py

Future MAIN invocation, only after full review; ACTUAL_* are required real
arguments, not generated pass placeholders:
 DAMP_PREFILL_FLOAT_DISPATCH_EXECUTE=1 python3 -B projects/damp-ascend/tools/prefill_float_dispatch_v1/dispatch.py --execute --run-id v1 --physical-card 4 --packet-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tools/prefill_float_dispatch_v1/PACKET.json --packet-sha256 ACTUAL_PACKET_SHA --parent-operation-receipt ACTUAL_PERSISTED_MA0455_JSON --parent-operation-sha256 ACTUAL_OPERATION_SHA

Canonical cwd is /opt/host/vnf/austinov/model-tuning-lab. NEW output root and
name must not exist. Main alone admits resources and chooses4/5/6/7.

## Fresh resource and failure contract

One nonprivileged container, one physical card +3 necessary control nodes,
no network/capabilities, no-new-privileges,1CPU/8GiB cgroup/no swap.
Repository, entire actual build/log/ELF root and driver are RO; only the NEW
result child is RW. It does not mount the full prior experiment root writable.
The host-created launch/audit subdirectory is separately nested RO so both
phase-specific physical proofs and source/command receipts cannot be written by
the child; the child writes its LOADED_LIBRARIES.json only in its own gate output.
Actual inspect validates all5 mounts, every device, environment, startup and label.

Fresh complete process table plus910B4 telemetry must show selected-card
no actual process, AICore0, HBM<=3165MiB. Idle device/UDA declarations are
recorded, not killed. Actual canary before EACH matrix proves successful
single logical-device mul and current SoC; physical authority is actual
host inspection, not a string inside the canary. New phase-specific device
proofs come only from those observed successes. No TTL is extended.

At admission ordinary MemAvailable>=16GiB (8cap+8reserve), disk>=8GiB,
actual Docker NCPU>=1. Known existing MAIN one-card correctness/CPU-selector
leases are additionally charged their full actual caps/quotas. Unknown real
workers on other authorized cards block joint scheduling; they are never
stopped. At runtime ordinary reserve>=8GiB/disk>=1GiB, owned cgroup/quota and
process-cgroup identities are checked. NPU0..3 PID/start/cgroup fingerprints
must remain unchanged. Conservative mount headroom2560 is a policy reserve,
not a proven kernel upper bound. No HugeTLB/mount-max/external workload changes.

Both matrices have fixed3600s timeouts under unchanged DAMP cutoff
2026-10-07T08:48:03Z. Admission requires enough remaining time for both plus
600s setup/cleanup; each phase must fit its budget. No automatic retry,
background service or scheduler is installed. Formal timing must not overlap
this correctness dispatch or its sibling/selector jobs.

Commands retain original stdout/stderr/exit hashes. On first failure,
FAILURE.json preserves the primary error and nullable old/fixed reports BEFORE
cleanup. CPU-before/raw fixture artifacts remain in frozen gate directories.
Source-after and secondary load/copy/stop/release errors are separate.
Only the exact confirmed NEW owned ID can be stop-retained; an unknown create
outcome is neither guessed nor recreated. No delete or external kill exists.
Successful completion requires both real reports plus owned stop/release proof,
and can only claim isolated eager FP32-division correctness scheduling.

## Child evidence failure boundary (source-only repair)

The actual frozen old gate runs source_bindings before creating its output
directory. A pre-mkdir failure can therefore leave no gate-result directory.
The wrapper now catches LOADED_LIBRARIES.json write failures, emits a finite
failed diagnostic with the original error and secondary write error to stderr,
and rethrows the original runner exception unchanged. It never creates/retries
a gate output to hide this failure. If there is no runner error but library
evidence fails, the child still fails; it cannot report PASS.

Closure, argument parsing, output-path admission and source_check happen before
the runner/evidence try block. Those early failures have no child loaded-maps
JSON promise: their original stderr/nonzero exit and the parent's command
receipt/FAILURE evidence are authoritative. The parent does not fabricate an
uncreated report or valid device proof. If the stderr stream itself is broken,
the primary exception/failed exit is preserved but the diagnostic stream is
explicitly not guaranteed. Software regressions simulate both a real absent
output directory and an injected write error; they are not NPU execution.
