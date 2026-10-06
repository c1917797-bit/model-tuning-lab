# MAIN selected-prefill real child producer (NEW, default OFF)

This is a thin, one-stage correctness dispatcher. It has not executed Docker,
Torch, NPU or a real child. It does not grant serving, graph, final192 plans,
TP4, scheduler C16, LongBench/GSM8K or end-to-end performance acceptance.
Frozen selected11/gate11/admission4, allbatch9, reference, original oracles,
numeric limits and existing receipts are unchanged.

## One operation, one owned single card, one frozen gate stage

Each --stage isolated|native_feedback is a separate AWMCP exec operation and
a fresh container mapping exactly one physical NPU4..7 to logical0.
No scheduler/daemon/automatic retry is installed. MAIN decides when to run.
The actual immutable image is 660ce23a...; selected SO28684cb4... and its
build50f161e6..., allbatch SOa802d258.../builda9c8a682..., reference853f655c...
and actual native image SOeaa9457... are byte-pinned in controller.py.
Source preflight validates selected11, gate9+50 dependencies, original
admission4, actual raw build logs/export audits and four native snapshots.
The same-image frozen run.admission executes before Torch, checking actual
OPP9.1 and, for native feedback,23 actual-image files. Original native .so
is observed in /proc/self/maps in the SAME PID that calls frozen run.main;
a Docker-copy snapshot or file presence cannot substitute for loaded proof.

The frozen matrix remains B1/B16, not a shrunken sample:
- isolated:134 packing cases,57 host rejections,12 whole-call retirement
  records, full shared-arena/status/pointer/untouched bytes and79 negative
  artifacts;20 changing same-buffer turns and8 resets for both layouts.
- native_feedback:8 actual native chunk fresh/continuation cases, each
  selected pack plus160 compressed own-feedback steps under state1e-5 and
  output.00303 limits. Explicit PCP1 standalone context, not full model.
  Three FP16/INT8/FP32 regions remain the only persistent recurrent state.
  All12P status rows must pass before feedback; any numeric partial-write
  failure retires the ENTIRE selected call, never just the failing head.

The child shim invokes existing functions, never reassigns torch.ops,
rewrites oracle arithmetic or uses snapshots as actual native execution.
stdout/stderr and real Popen returncode are preserved. Timeout, received
SIGINT/SIGTERM, monitor failure and normal completion produce distinct
execution fields from those actual branches, not assumed success defaults.
Missing report/observation/copies stay nullable in failure evidence.
No synthetically populated success receipts are produced.

## Resource admission and ownership

Before creating anything, require MAIN's preserved ORIGINAL operation_get
structuredContent for MA0455 to be genuinely terminal and the exact
b6e2a151... parent container to be already stopped. Nonzero completed
capture remains failed but releases scheduling; calibration success is not
required for this independent component. The dispatcher does not poll,
stop or infer parent terminal from a timeout, sleep container or partial log.

Fresh checks reuse pinned float-dispatch resources/parent_stopped and allT
Commands/protected/process/cgroup/mount helpers; a private imported owner
setting is configuration, not a mutation of their frozen sources.
Unknown real workers on4..7 block scheduling but are never killed.
Declared idle devices/UDA/node holders are recorded, not treated as an
automatic stop target. NPU0..3 PID/start/cgroup fingerprints must remain
unchanged. No HugeTLB, external tasks, mount limits, image or runtime is edited.

The exact created immutable container ID/name/image/owner/run/stage is
checked repeatedly. Nonprivileged, no network, no caps, no-new-privileges,
one numeric1CPU/8GiB/no-swap cgroup. Joint known MAIN quotas/RAM caps and
actual Docker NCPU are checked; admission includes8GiB ordinary RAM
reserve and8GiB disk; runtime reserve8GiB and disk1GiB. Mount headroom
2560 is a conservative policy reserve, not a proved maximum footprint.

Repository, build roots, driver, source snapshots, anchor and MAIN launch/
audit/proof are RO host binds. ONLY the new stage-output host bind is RW;
the containing result root is NOT mounted. This is a host-evidence boundary,
not a claim the image COW filesystem itself is read-only. The child cannot
overwrite MAIN's owner proof, EXECUTION or child-receipt audit files.
An actual nonprivileged single-card mul canary checks logicalcount1/910B4,
mapping/source argv identities and actual result[1,4,9] before the full stage.
Canary proves only tiny mul, not packing or correctness.

During the stage, protected identity/owned PID cgroups/actual memory/CPU/
OOM/ordinary RAM/disk/mount state are monitored. On failure only the local
owned docker-exec client and exact inspected owned container are stopped.
Container is retained, never deleted. Unknown create outcomes are not
retried or guessed to be owned. Stop/release failure is a distinct retained
error and prevents a successful outer operation.

Fixed cutoff remains 2026-10-07T08:48:03Z; phase timeout3600 seconds.
The cutoff/timeout never resets because this is a new directory.

## Actual commands, not execution claims

From canonical /opt/host/vnf/austinov/model-tuning-lab:

    /usr/bin/python3 -B projects/damp-ascend/tools/selected_prefill_dispatch_v1/test_dispatch.py
    /usr/bin/python3 -B projects/damp-ascend/tools/selected_prefill_dispatch_v1/controller.py --stage isolated --physical-card 4
    /usr/bin/python3 -B projects/damp-ascend/tools/selected_prefill_dispatch_v1/controller.py --stage native_feedback --physical-card 7

These are stdlib tests/dry plans, not Docker/Torch/NPU acceptance.
Tests use labelled synthetic fixtures; they cannot authenticate AWMCP JSON.

Only after MAIN review, actual MA0455 terminal/stopped/resource facts and
the ORIGINAL packet hash, dispatch each stage in its own actual operation:

    DAMP_SELECTED_PREFILL_DISPATCH_EXECUTE=1 /usr/bin/python3 -B projects/damp-ascend/tools/selected_prefill_dispatch_v1/controller.py --execute --stage isolated --physical-card 4 --run-id ACTUAL_NEW_SAFE_ID --packet-sha256 ACTUAL_PACKET_SHA --parent-operation-receipt ACTUAL_MAIN_MA0455_JSON_PATH --parent-operation-sha256 ACTUAL_ORIGINAL_JSON_SHA

Use the same command in another operation with --stage native_feedback,
another new run ID and a selected physical4..7 card after fresh admission.
There is no fixture/calibration success dependency. No environment credential
or AWMCP verification value appears in this package.

Each root is /cache/cch/qwen36-damp-20261006/selected-prefill-dispatch-ID-STAGE,
must not exist, and contains launch/ (MAIN only) and stage-output/ (child RW).
Gate creates stage-output/STAGE itself. No overwrite/resume is accepted.

## Receipt and MAIN's original terminal authority

controller launch/child-receipt.json uses damp-selected-prefill-child/v1:
exact real command/args/cwd/start/end/duration/returncode/rawstdout/stderr,
actual container/image/single-card mapping and owner-proof Ref, same-process
runtime/maps and23 sources, loaded-library path/SHA, artifact byte Refs,
runtime manifest and these4 controller source identities.
The controller checks the frozen admission's complete stage case/check/status/
guard matrix before declaring this operation complete. Both stages and the
original AWMCP terminal authority are still needed for component admission.

Only after actual full stage + exact stop/release succeed, stdout contains
exactly one MAIN_SELECTED_PREFILL_CHILD marker binding child/report path/SHA
and stage. MAIN then persists the ORIGINAL operation_get structuredContent,
its actual SHA and expected operationId/outercommand/args/cwd.
No tool JSON is generated/filled by this producer. The Ref/RunAuthority/
TerminalAuthority values are MAIN-issued expectations, not cryptographic
signatures. Future strict admission_v1.validate_complete consumes both
actual stage receipts and original tool bytes; it always returns serving/
performance/graph/all-P/full-model-cache false even when complete.

For failure, raw output, original execution error, nullable report/observation
and secondary copy/cleanup errors are retained before assertions. The frozen
gate owns its own artifacts. This is not a predispatch crash-consistent
golden journal; in-memory oracle-before clones are not claimed durable.

## CPU exact oracle cost risk (static count, NOT measured)

Isolated20-changing+8-reset × two layouts × (P1+P16) yields approximately
187,170,816 exact_divide calls. Its513 integer values × seven SR values
fit well inside the frozen65536-entry LRU; high hit rate is plausible,
not measured. Native8 pack cases require13,369,344 FP32/SR divide calls;
random native final states may have poor reuse and expensive Fraction work.
The actual1CPU/3600s stage may fail for time/resource before a numerical
conclusion. No matrix, cache, oracle or threshold was changed to suppress
this risk. MAIN may separately review reusable CPU fixture/golden
pregeneration; actual native final state cannot be fabricated/prelabelled
from a CPU fixture. This package performs no such oracle substitution.

## Actual software-only validation (not execution evidence)

AWMCP direct target exec060b completed0:33 stdlib behavioral tests in0.562s,
including original frozen-gate exception retention, nonzero-return preservation
and secondary-map/save failure refusing complete0. Its intentional traceback
is a synthetic injected ValueError, not an actual operator failure.
exec05fd/0607 parsed three Python sources and measured source SHA only.
Default plan and old9+50/selected11/build/export/source closure passed without
Torch import or subprocess device work. Original exec0601's30-test draft
result remains a separate earlier receipt; it is not rewritten.
These tool observations establish software preparation only. The two NPU
stages, same-image runtime maps, actual owned container, native8 feedback
and strict two-stage/original-terminal admission remain unexecuted/pending.

## Reviewed producer interoperability and primary failure repair

Actual direct operation exec061f completed with exit0:38/38 stdlib behavior
tests passed in3.884s. The original admission_v1.validate_complete accepted
a producer-shaped two-stage SOFTWARE_ONLY_SYNTHETIC fixture with the original
134 isolated cases and8 native cases×160 steps, exact shim/preflight/batch/
native authority argv, RO owner-proof and four controller source bindings.
A duplicate outer marker was rejected. This is not genuine tool-terminal
authentication or real loaded/runtime evidence: the native image SO path was
aliased ONLY to MAIN's actual stopped-image snapshot bytes eaa9457..., and
both outer tool JSON objects are explicitly synthetic and temporary.

Source-drift before directory creation retains the original exception and
creates neither observation nor report. The host failure record now prefers
the observed dispatch error, then same-process shim primary error, then gate
error, while recording the controller/copy error separately. A failing exact
owned-container cleanup records a distinct cleanup error without replacing
the original dispatch failure or printing a success marker. No frozen
runner, reference, numerical limit or operator source changed.

These regression sources remain stdlib preparation. A software fixture is
not a MAIN-issued actual operation authority. Real stage report, same-process
maps/source23, actual Popen/container/preflight/canary and genuine original
operation_get bytes are still mandatory and have not been collected here.

Final expanded behavior suite: actual direct exec062d completed exit0,
39/39 tests in3.898s, including exact native authority flags and an original
runner exception BEFORE its output mkdir. Nullable runtime/absent report and
no success marker were verified. This remains SOFTWARE ONLY, no real stage.
