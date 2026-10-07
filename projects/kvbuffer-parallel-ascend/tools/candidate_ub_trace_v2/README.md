# Candidate UB trace v2 — SOURCE PREPARED / DEFAULT OFF

This NEW independent namespace exports COPY-ONLY snapshots from the real
candidate AIV kernel. It is not a numeric repair, Torch reconstruction proxy,
persistent sidecar, model plugin, NPU PASS, performance or task quality evidence.
Original frozen64, SO77b4, all failed records and thresholds remain unchanged.

## Fixed observable seam and bytes

Only original failing token6/head5/slot4/Vtile0 (v rows0..31) writes trace data.
Payload49344B per call, plus1536B three redzones in the diagnostic allocator:
- trace_states FP32[3,32,128]: actual UB after ParallelFlush(previousScale),
  after currentScale Muls, and after current rank-one MulAddDst.
- trace_output FP32[32]: actual ReduceRows readout BEFORE BF16 CAST_RINT.
- trace_meta INT32[16]: token/head/slot/oldlength/Vstart/n,4 stage completion
  marks,merge,T,S,three untouchedzeroreserved fields.
Expected actual metadata [6,5,4,15,0,1,1,1,1,1,1,16,19,0,0,0].

The failing coordinate [6,5,6] had BF16 actual0.00396728515625(bits15234) vs
native0.003997802734375(bits15235); exact midpoint0.0039825439453125.
Its original slot4 oldlength15 means this step flushes. The trace must copy
the same actual UB used by computation; no CPU/Torch equation substitutes it.
Native exact FP32 precast remains UNOBSERVED. A candidate value near the midpoint
does not by itself prove native's exact distance or a unique error cause.

Each snapshot first copies into a dedicated16KiB VECOUT queue, enqueues/dequeues,
then copies that queue to independent GM. Original state/U/log/output arithmetic
UB slices,128KiB tmp buffer, native128reduction, exp/treefold/operation order and
base/log deferred-write policy are unchanged. No trace values are consumed by
original math. All original math functions and ProcessTile sans trace calls are
source-exact regressed; compiler/reordering/synchronization can still perturb
values. Extra UB is NOT certified by source-size arithmetic: actual CANN9.1
dav-2201 compile/resource report and later NPU anchoring are mandatory.

## Source-bound ABI

NEW7 under projects/kvbuffer-parallel-ascend/operator/candidate_ub_trace_v2,
legal source/notice reuse from actual original native_order_v2 seven files.
Original full SHA/bytes and exact NEW file SHA/bytes are in SOURCE_MANIFEST.json.
Runtime protocol/tests/this README under tools/candidate_ub_trace_v2.

namespace qwen36_kvbuffer_native_order_trace_v2; prepare(q,base) unchanged cold ABI.
decode_trace has original13args + explicit mutable FP32states/output/INT32meta,
alias sets g!/h!/i! independent of original a!..f!, returns original BF16output.
Caller-owned buffers must be physical ND/contiguous/same device/exact shapes;
wrapper checks all16 ranges against each mutable original/trace range.
Original6candidate mutable tensors are not overridden. QueryT16/baseS19 scope is
strict. Meta validates shapes/dtypes, NOT actualND/alias/source ordering/device.
New exports and OpCommand name are independent; no global torch.ops rebinding,
no donor/receiver/model-runtime edits. Torch loaded schema is explicitly compared;
cross-version changes fail closed, not guessed as compatible.

## MAIN build and preflight — NOT EXECUTED

Reuse the existing compiled native_order_v2 CMake/ASC direct-call design, only
new symbol/file/namespace names and copied trace outputs change. Parent controls
Docker/source publication and actual build. Example independent build subcommands
inside its pinned ordinary no-device660 image with ROrepo/RWnewresults:
 source /usr/local/Ascend/cann-9.1.0/set_env.sh
 cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/operator/candidate_ub_trace_v2 -B /kvbuffer-results/build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
 cmake --build /kvbuffer-results/build --parallel 1
Expected only libqwen36_gdn_kvbuffer_native_order_trace_v2_ops.so/dav-2201.
MAIN must retain exact7sources, real CANN/OPP/image/compiler argv/log/exit/newSO
SHA/exported-symbol receipt; source manifest never signs success. No recursive
cleanup, source overwrite, automaticretry or unknown result replay.

Actual no-device load/Meta required positives T16/S19 and negatives wrong trace
shape/dtype/queryT/baseS/meta17length; schema must exactly equal protocol.SCHEMA.
A Meta positive does not admit NPU. Actual ND/alias/guard negatives remain NPU
runtime checks; invalid ranges must reject BEFORE writer and immutable guards
must remain untouched. No schema or numeric evidence has been generated yet.

## Reuse of the already published saved-step producer

The existing B16 saved-step host supplies physical6->logical0,8GiB/1CPU,
8GiB ordinary reserve, original600second total cap, separate real canary/PID
proof/exact own stop+retain and immutable raw/artifact mounts. DO NOT change its
frozen code or outputs. MAIN may create a narrowly source-bound successor entry
loading NEWtraceSO and call protocol.diagnostic after source/ABI admission.

Exact Python API (default enabled=False):
 diagnostic(torch,helper,old,fixture,production_ops,trace_ops,new_output,
            enabled=True,raw_path=actual_raw_path,
            source_manifest_sha256=MAIN_actual_manifest_SHA,
            libraries={production:{path,sha256},trace:{path,sha256},native:{path,sha256}})

helper is unchanged source64 oracle.py exactly pinned by its manifest; old is frozen saved replaybf83…
loaded after exact source checking. fixture is weights_only CPU payload of the
original rawff6c…99004309B, source manifest source_admission verifies64 plus NEW
and upstream7. MAIN supplies real newSORef (unknown now, never filled with77b4).
Parent must retain same immutable actual910B4/source nativeSOeaa and full owner
admission; this API alone is NOT host/controller/operation authority.

Default CLI only prints OFF, imports no Torch/writes nothing:
 /usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/candidate_ub_trace_v2/protocol.py
Explicit source-only CLI requires the actual manifest SHA:
 /usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/candidate_ub_trace_v2/protocol.py --source-audit-only --source-manifest-sha256 MAIN_SHA

## First mandatory anchor, then interpretation

For eager and graph each ONE actual saved step:
1. Uninstrumented77b4 original native FIRST/candidate second via frozen step(),
   must reproduce original AFTER/all16output/native and expected active12 bytes.
2. NEWtrace same native-first order,complete before restoration and guards,
   cold prepare outsidecapture; warm3/capture/restoreraw then one graph replay.
3. Save full original/trace raw, copies/exception errors and trace payload BEFORE
   finite/math/assertion. Never discard failure or override a primary native
   error with observation/save cleanup failure.
4. Require NEWcomplete AFTER/all16output/guards/inputs/native bitwise==77b4;
   only native expected12defined rows compared. No candidate padding masking.
   Three trace redzones/pointers/missingcompletion/NaN checks are mandatory.
5. Sinceactualoldlength15/merge, copied updated UB must equal actual flushed GM
   base[slot4,head5,rows0..31] bitwise. Fail means trace not admissible.
6. Report real copied reconstructed input vs native_before,updated vs native_after
   FP32 distances and exactFP32precast; do NOT call Torch logical(before) UBtrace.

Successlabel anchored-copy-only-trace-diagnostic has matrix/numeric/service/
cause_proved/native_precast_observed allfalse. If anchor fails,STOP: a compiler/
instrumentation perturbation cannot become algorithm evidence or paperno-go.
Original output.00303/state2e-6 limits are not raised. Precise causal repair only
after actual results; compensated exp/fold may reduce equation error but need
not reproduce native temporal FP32rounding or guarantee a speedup.

## Historical v1 preparation status (not current v2 authority)

The following section records the earlier v1 preparer's state only. v2 is a
MAIN-derived independent successor after the real v1 CANN compile failed.
At v2 preparation it remains unbuilt/unverified; actual stage notes supersede
this frozen source document. No NPU/E2E result is signed by this manifest.
MB0577/0579/057e read actual original7/hash/ABI on MBdirect peer, original bytes
fully preserved. Stdlib tests cover source arithmetic equality, aliases,
schemas/defaultOFF/raw-before-assert/guard/API contracts; NOT device proof.
MAIN full review/build/loadedMeta/actualsingle-step/release proof remain PENDING.

Actual MB0585 small-argv, exact-source-derived test completed0:14 stdlib PASS,
noTorch import/NPU/Docker/canonicalwrite. Earlier two84KB argv requests returned
retryable direct-route timeout/no operationId (traces0705c1a6…/1b595467…);
MB0583 found no retained own test process. Errors remain preserved, not PASS.

## v2 repair scope

Original v1 compile command-1.json failed with C++ list-initialization narrowing
at TraceCopy's elements*sizeof(float). Its original SHA is
bf67e9fa83ba1f3d98d6077262cb484cd5e0246fbf3940d5f44718ba776c6188.
v2 makes that byte-count conversion explicit as uint32_t; the fixed copy sizes
(4096,32,16 elements) all fit exactly. Independent v2 symbols/source/output roots
retain v1 unchanged. No arithmetic/threshold/device protocol changes are intended;
actual compile, Meta, output/state/guard eager+graph anchors remain mandatory.
