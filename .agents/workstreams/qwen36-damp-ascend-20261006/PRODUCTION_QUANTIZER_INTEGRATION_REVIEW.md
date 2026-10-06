# DAMP production quantizer integration review

Status: preparation / MAIN review required. No production file, frozen helper,
collector, diagnostic, probe or Git state was modified by this reviewer.
No Docker, compiler, NPU load or performance measurement was started.
This document is NOT a production admission receipt.

Reviewed on 2026-10-06 in canonical
/opt/host/vnf/austinov/model-tuning-lab, branch
work/qwen36-damp-ascend-20261006, source snapshot
28a96944307dc36117a355cb7efa206fa7af1901.
Fresh AWMCP topology resolved chicaihong01/mb; each read proved peer_direct.
MAIN exclusively owns physical NPU4-7 execution and publication.

## Objective and time boundary

DAMP is an equation-derived, training-free mixed-precision recurrent-state
migration, not a generic operator campaign or an author-code-fidelity claim.
The concrete repair is the proven Div-before-RNE quantization seam in its
compressed feedback state. Preserve the paper mechanism, fitted SR/permutations,
and meaningful compressed storage while fixing the implementation.

Individual cutoff remains 2026-10-07T08:48:03Z; portfolio cutoff remains
2026-10-09T11:17:31Z. Do not spend that budget only on isolated probes.
MAIN should serialize: isolated certificate/compaction correctness -> actual
production seam -> full feedback -> supported graph/cache/service -> paired
fixed-1024 timing -> final task quality. Preparation does not reset either clock.
Use the current branch HANDOFF and SCHEDULING, not the historical global
2026-09-04 hardware allocation.

Relevant maintainer instructions reviewed: host-maintenance, paper-to-ascend,
ascend-inference-tuning-loop and its damp-migration-gates reference,
ascend-benchmark-evidence, environment-orientation, ascend-cannbot-profiler.
They require preserving failure scope, explicit source/binary identities,
untouched slots and independent feedback, and prohibit microbenchmark-to-E2E
promotion or relaxed state thresholds.

## Proven seam, not an update/FMA hypothesis

The failed restricted-native-v2 B1 identity run was packed-state exact through
step44. Step45 failed the frozen 1e-5 state gate; current output was exact.
The saved trace v2 subsequently found the complete updated FP32 state and
scales bitwise native. At the disputed low cell:

- x bits 0xbd05a10e, s bits 0x39919209;
- IEEE RN32(x/s) is -117.5, bits 0xc2eb0000, then integer RNE gives -118;
- actual 910B4 vector Div returned -117.49999237060547, bits 0xc2eaffff,
  then RNE gave -117.

Artifacts remain external:
restricted-native-golden-v2/first_failure.pt SHA256
59795deab9d00328df79dfeeefa08ff6d917f455bfe9d7565d0fd9c3cbf70598;
saved-step45-trace-v2/report.json SHA256
685e6cf1011d29a4c31f70b254c5192252e1a296717994246a1f5291093ad0b4,
both below /cache/cch/qwen36-damp-20261006/.
This is one-step attribution, not a recovered closed-loop pass.

The production kernel at op_kernel/qwen36_gdn_damp_decode.h:327-394 computes
group32 scales, then :369 overwrites lowFloat_ in place with the approximate
division before :373 RINT. An exact fallback cannot recover the original x
from that quotient. The minimal repair must preserve raw lowFloat_ until
all code decisions are complete.

## Frozen algorithm and public ABI must not change

Target: clip[-127,127](RNE_integer(RN32(x/s))). Direct exact-rational-to-integer
rounding is different near half ties. No epsilon, half snapping, scale floor,
FP16-before-RINT or loosened parity/state gate is permitted.

Keep all of the following:
- high16 FP16, low112 INT8, group32 reordered-V FP32 scales;
- scale = RN32(amax * reciprocal FP32 bits 0x3c010204);
  scale1 only if original amax is exactly zero;
- native BF16 normalized Q/K, per-Hv Pk with Hv/Hqk=3;
- SR c is positive FP32 in original V coordinates;
- original BF16 V -> FP32 V/c -> Pv, unchanged recurrent update;
- updated FP32 readout BEFORE pack, then inversePv and original c -> one BF16 cast;
- one AIV task owns its whole token/Hv, four groups and whole output;
- no persistent GM FP32 state, no changed DMA owner or arbitrary-Pv GM scatter.

The current wrapper's check_tensor validates ND/dtype/contiguity but not an
explicit32B base-pointer alignment; check_disjoint compares accessed contiguous
byte ranges, not full backing allocations. Do not claim a stronger existing
alias/alignment gate. New LUT/raw-pointer integration should require and test
aligned bases for whole-group state/output DMA, reject misaligned views, and
retain full backing/guard checks in the independent harness. This is a small
admission seam, not permission to change unrelated math.

External prepare6/decode14 argument order and mutable aliases hi(a!),lo(b!),
scales(c!) can remain unchanged. Do not silently import a differently typed plan.
Internal tiling/LUT identity is a separate ABI and should receive a new version
if its layout changes. Preserve the old SO and build a fresh opt-in SO/process;
do not load two conflicting qwen36_damp registrations or overwrite a bound binary.

## Proposed production route: SIMD certificate plus sparse exact fallback

This is a ready-to-review design, not implemented or proved fast.

1. Extract high and raw low state exactly as today; compute the unchanged
   group32 scale before dividing any low value.
2. Process raw low V rows in 64-aligned chunks. N448 = four V rows x112
   is a conservative first integration tile; N896 = eight rows x112 is
   a later space/cost option. They do NOT change the group32 amax.
3. Broadcast the original 112 scale values to each chunk by exact UB copy /
   repeated vector source addressing, not a new arithmetic scale calculation.
4. Ordinary Div proposes a magnitude only. Sanitize NaN/Inf proposals, clamp
   finite magnitude to [0,127] BEFORE FP32->INT32 RINT. Ensure every proposal
   is valid before LUT Gather. An arbitrary wrong proposal is harmless only
   because the following certificate, not Div accuracy, owns admission.
5. Run the reviewed integer-SIMD Certify on original x/scale raw bits and the
   proposal. It uses exact integer endpoint products, strict interior acceptance,
   raw original sign/finite checks, normal positive scale and used endpoints.
   Non-normal or uncertain lanes reject to the exact helper. No RN32-Mul
   certificate or Float-abs zero-bin shortcut is enabled.
6. Write all proposed signed codes with vector INT32 operations using the
   ORIGINAL x sign bit. Accepted lanes must never require a scalar scan.
7. Build a PACKED bit mask for accepted==0. Do not reinterpret an INT32 0/1
   lane array as GatherMask pattern bits. One API-compatible option is exact
   INT32 multiplication of 0/1 by 0x3f800000 into a DEAD scratch plane,
   reinterpret as FP32 0/1, then CompareScalar EQ0 to make the mask.
   This does not rely on a float-Mul rounding contract; the INT32 product fits.
   The actual mask layout and API lowering still need their isolated NPU gate.
8. Create vector indices, GatherMask ONLY the rejected original lane indices.
   After explicit V_S Set/Wait, visit exactly retained entries and call frozen
   ExactCode on original x/scale bits. Check retained<=N and each index range.
   Restore S_V readiness before any vector conversion of scalar-written codes.
9. Convert corrected small INT32 codes to exact FP32 -> FP16 -> INT8, populate
   the existing whole-group packed buffer, copy original scales, and use the
   unchanged whole-head writer/queues. No FP32 quotient is persistent.
10. Debug-only receipts may count rejected lanes, worst chunks and finite-domain
    failures. Disable diagnostics and their extra output copies for timing;
    do not write adjacent per-core scalar counters with unsafe DMA ownership.

The frozen quantizer_ascendc.h rnMulReceipt=false route recomputes ALL lanes
with scalar ExactCode. The isolated integer probe also visits every lane
scalar to expose diagnostics. Neither is the production performance candidate.
Do not include the old float-Mul conditional fast path just because it compiles.
ExactWithCandidate on every lane is also scalar and is only a correctness/cost
fallback, not an assumed deployment win.

## Public CANN GatherMask evidence and required seam gate

[Official CANN9.1 GatherMask API](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/GatherMask.md)
supports A2 INT32 source/destination with UINT32 tensor mask. Counter mode
uses mask elements per repeat on A2; retained is the number of selected
destination elements. The documentation requires aligned buffers and describes
mask-mode restoration. This is API capability, not a measured count/order pass.

Read-only actual SDK snapshot:
- include-basic_api/kernel_operator_vec_gather_mask_intf.h exposes the public
  tensor-pattern overload; SHA256
  12b1fad08130ae03f7830128fec984629221242af58beb6fffb761824ce74737.
- impl-basic_api/kernel_operator_vec_gather_mask_intf_impl.h selects dav_c220
  for __NPU_ARCH__==2201.
- impl-basic_api/dav_c220/kernel_operator_vec_gather_mask_impl.h:
  SHA256 cf306aead716ada7cef8f448226e5655de917809f9adcc803c6a2ba3afddb0f7;
  custom UINT32 pattern supports INT32 source/dst; AIV uses SetMaskCount,
  set_vector_mask(0,mask), vreducev2, GetRsvdCnt, then SetMaskNorm.
Paths are under /cache/cch/qwen36-damp-20261006/sdk-div-audit-v1/.
Inspect impl for provenance, but production includes ONLY kernel_operator.h.

Pinned ops-transformer moe_init_routing_v3/op_kernel/moe_v3_full_load_base.h
uses the actual custom-mask call at lines216-234:
repeatTimes1, src0BlockStride1, src0RepeatStride8, src1RepeatStride8,
reduceMode=true, mask=totalLength. Reuse that public-API call pattern, not its
MoE algorithm or CAST_ROUND semantics.

Before production, MAIN must test counts N64/N448/N896; zero/all rejected,
one rejection at indices0/31/32/63/64/last, alternating and random masks,
changed masks on the same buffers, full input/output guards, retained count,
ordered unique original indices and exact fallback scatter-back. Source API
presence does not prove these. Zero retained is legal output, but count0 is
not a legal counter-mode input: call GatherMask with fixed N>0 and an all-zero
mask, then skip only the scalar fallback loop. Preserve V_S/S_V correctness.
No AIC or arch35/950 substitute is admissible on this production AIV path.
The older exact_bits target did NOT execute GatherMask.

## Real UB liveness and allocator constraints

Current authored UB = work79872 + queue18944 = 98816B. The group has raw
lowFloat_ at [43008,57344), which must stay immutable through the repair.
attn_ and plans/q/k/v/SR must remain alive across groups / final StoreHead.

Conservative NEW disjoint N448 allocation:
- 16 certificate work planes + accepted: 30464B;
- quotient, magnitude, corrected codes, scale copies, indices, compact indices:
  six x1792 =10752B;
- immutable C/F LUTs:1024B; padded bit-mask:256B;
- total additional authored UB42496B;
- old98816 + new42496 + illustrative8192 implementation reservation =149504B.

These are authored sums, NOT an actual runtime/compiler budget proof.
Four-argument Broadcast in the existing recurrence can use hidden shared
LCM stack memory; Select/other API temporaries and all queue/event slots must
be included in the actual CANN build report. Do not claim 8192 is a measured
upper bound. Use existing planIn_ sequentially for LUT inbound readiness
instead of blindly adding another queue/event slot; persist the LUT in its
own immutable UB region after the queue is freed.

N896 with the same six-plane design adds83712B; old+new+the illustrative8192
is190720B, too close to192KiB to admit without actual allocator/LCM proof.
N448 is a preparation choice to keep headroom, NOT a prediction that it is
faster. More/smaller chunks add certificate and V_S/GatherMask fixed costs.

After high/low extraction and the reduction, state_, broad_, absA_, scratchB_
are dead UNTIL the next group LoadState; they can eventually host disjoint
quantizer planes with an explicit offset/liveness proof. But lowFloat_ is
still raw, and attn_ is accumulated. First prove correctness with explicit
new scratch; do not change native recurrence arithmetic while repairing Div.
Every chunk offset N*4 and every plane start is32B aligned. Reinterpreting
bits is allowed; input/LUT/code/work overlaps are not. Before any reuse,
complete the old vector producer and packed-output consumer events.
No accepted-state buffer may alias the candidate or independent golden arena.

## Minimal source change set for MAIN approval

Do NOT apply this list before real isolated proof:
1. NEW integration helper wrapping integer Certify + typed packed rejection
   mask + GatherMask + sparse frozen ExactCode + sign restoration.
2. Production Init/PackStore: new disjoint UB scratch/LUT views; retain raw
   lowFloat_; replace only in-place LowBroadcast/RINT selection seam; retain
   high cast, scale tree, readout, code-to-INT8 and whole-group DMA.
3. Tiling/prepare only if needed for immutable C/F LUT upload. Suggested
   internal v2 tiling has an explicitly padded32B control header followed by
   C[128] and F[128], total1056B. Verify sizeof/offsetof/alignment statically;
   validate/hash C/F constants and keep their upload outside capture.
   Existing prepare can cache this by the same device/T/S/plan identity,
   retaining original static plans. LUT is immutable, not a recurrent sidecar.
4. New source pin/build receipts and fresh tests/launchers. Existing general-SR
   CANDIDATE_HASHES/manifest explicitly binds v4 and must NOT be bypassed;
   a new reviewed pin dictionary/manifest binds the repaired version while
   mathematical fixtures, oracle, thresholds and old FAILED reports stay intact.

No operator-name-wide replacement, reference-source modification, native image
edit or CANN/ops-transformer edit is needed.

The scalar exact helper returns valid=false for nonfinite x or nonpositive/
nonfinite s; positive subnormal s is supported. Do not store arbitrary code0
and claim valid output. A head/group return after earlier GM writes does NOT
provide invocation-wide rollback. The existing all-NaN/untouched guarantee is
for metadata failure BEFORE any writer, not arbitrary arithmetic failures.
If deployment requires full arithmetic fail-closed atomicity, it needs a
separately designed prevalidation/transaction seam. The repaired numerical
gate must exercise invalid helper inputs in the isolated probe and admit
only finite positive generated-scale trajectories; do not silently claim this
narrow patch proves a new whole-invocation arithmetic transaction.

## MAIN-only validation and commands

Prerequisites: live source, immutable image/CANN, fresh physical4->logical0
mapping/nonprivileged device proof, actual loaded paths/SHA, no overlapping
TP4 capture. MAIN owns launches, timing, directories and rollback. A no-device
compile/Meta or software certificate receipt cannot replace any NPU stage.

A. Isolated certificate + compaction route above:
strict all-code/half±ULP/subnormal/extreme/sign domain and count/order/guard
tests. Original scale has NO floor. Preserve every first failed report.

B. NEW saved-step45 production fixture test:
use the immutable initial packed arena, q/k/v/g/beta/plans/indices from the
saved fixture; create repaired candidate arena independently. Compare full
high/low/scales, untouched slots, output, static/dynamic inputs and pointers
to SAVED native golden. Require the disputed code -118 and complete packed
bitwise equality for this fixed seam. Do not use candidate trace as its oracle.
The old trace runner hard-pins the OLD production SO: prepare a NEW fixture
runner/pins, rather than relaxing or modifying its existing evidence.

C. Full existing restricted feedback protocol, NEW output root and repaired SO:

    ASCEND_RT_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 python3 \
      projects/damp-ascend/tests/restricted_native_golden_gate.py \
      --steps 160 \
      --operator-library /ABS/NEW-REVIEWED-PRODUCTION.so \
      --operator-sha256 FROZEN-NEW-SHA256 \
      --device-proof /ABS/FRESH-DEVICE-PROOF.json \
      --native-source-manifest /ABS/NEW-SOURCE-MANIFEST.json \
      --output-dir /damp-results/restricted-native-repaired-v1

This is a command template requiring MAIN's real paths/hashes, not executed.
The runner starts native HQ12 dyadic smoke, then B1/B16 x identity/power2,
random per-Hv permutations,160 changed turns/active slots, S=B+3.
Golden and candidate feed back their OWN packed states; no per-step resync.
Unchanged state gate max-head-relative-L2<=1e-5, output<=0.00303.
Require finite complete state and outputs, selected/untouched regions,
static/turn inputs, pointer/ND/alias guards. The existing restricted runner's
output_nonalias is pointer inequality, not full storage-interval proof; add a
NEW reviewed full-interval negative/guard test or use the independent general
runner's interval checks, rather than describing the old check as stronger.
Restricted power2 cannot certify
arbitrary SR or the fitted model plan.

D. Independent native-source reference anchors, then general-SR feedback:
general_sr_native_gate.py --anchor-only, NEW root; source-bound six anchors
must pass before full synthetic arbitrary-positive-FP32 SR and cancellation
stress B1/B16x160. Full mode removes --anchor-only, preserving the same state/
output gates and selected-only independent CPU packing of reference output.
NEW candidate/reference source pins/manifest and real loaded-SO identities
are mandatory. Finally test all fitted192 layer/rank plans, not merely
identity/power2/synthetic SR. The training collector is NOT this gate.

E. NEW graph replay gate after eager:
same prepared device/T/S/static-plan identity, immutable LUT/plans, separate
candidate graph arena and reference feedback. Preallocate ND dynamic inputs
and indices; prepare/upload outside capture. Warmup and capture mutate state,
so restore BOTH arms to identical initial packed bytes ONCE before the measured
loop; never overwrite candidate feedback with golden during replay. Copy changed
q/k/v/g/beta/indices into static input buffers and explicitly synchronize device
visibility BEFORE replay. B1/B16x160 changed turns, changing valid unique slots;
same complete-state/output/untouched/input/pointer limits, no cold H2D or new
tensor creation inside capture. Preserve graph failure before changing harness.
Meta registration and a pure-UB kernel are not proof of capture safety.

F. Typed-cache/model path then paired service:
48 GDN layers x4 ranks use real compressed regions, no resident FP32 sidecar.
Test prefix identity, slot recycle/isolation, continuation/mixed-turn support
or explicit fail-closed fallback, scheduler and graph keys. Prove actual worker
dispatch and source/binary identity. Only numerical-pass candidates enter one
same-config dense E2E fixed1024 screen, including all adapter/packing/launch/
fallback costs; dense gets the same generic optimizations. Record TTFT/TPOT,
then repeat promising candidate and final normal-EOS, no-thinking max2048
LongBench-v2/GSM8K. Latest user permits1% task loss: report pp and relative loss
and also original no-loss acceptance; never use1% for tensor gate.

## Failure preservation, cost decision and rollback

Do not rerun v4 unchanged. Repaired source needs fresh build/output roots;
old failed fixtures/SOs/source hashes remain recoverable. Record schema,
actual source/library/hash/image/SoC/device mapping and static LUT identity.
Before assertions, save CPU input-before/expected data and raw obtainable
outputs/state. Capture dispatch error separately from D2H/fixture-save errors:
a poisoned device context must not replace the original failure with a copy
exception or lose the CPU fixture. Save finite JSON with nullable unavailable
returns, first failure only, no automatic retry.

After correctness, measure whole repaired recurrent call at B1/B16 and actual
model decode/serving. Count accepted and fallback density/long tails per real
layer/rank/chunk, vector work, V_S/S_V stalls, queue/event/UB/resource behavior.
The draft has135 vector operations/barriers per certificate subtile: it is not
free even if nearly every lane is accepted. Include Div proposer, mask packing,
compaction, exact fallback and unchanged recurrence; microseconds of the scalar
probe and kernel-time sums are not E2E gains or impossibility proofs.
If this implementation loses, preserve implementation-scoped evidence and the
mechanism bottleneck; do not call all DAMP/other papers disproved.

Rollback is disable the opt-in plugin/repaired version and restore the known
native service path; stop/retain only MAIN-owned completed containers. No
mutation of native runtime, original image, protected0-3 or shared reference
repos is authorized by this review.

## Source fingerprints actually re-read for this review

- production decode header:
  ecc24fada002dafbca962de5265f1bddc27a03d1e723070d9b317b415e3ca856
- production tiling header:
  3dae709efa2bfdce83ca90dd21fd2013896307db677c7363a337316b3dca6257
- production torch wrapper:
  0329433adda1821600026df9b8449b64aa9b3d48c4bdcfec82ad07b8f3a94ed4
- frozen exact_quantizer_bits.h:
  f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169
- new integer_certificate_ascendc.h:
  e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb
- restricted_native_golden_gate.py:
  f8b04cc7650cf2cc330a526cb261ffd85062454e56e1a9692b5913c18445a6b4
- general_sr_native_gate.py:
  7eed726fd46e2e39c6bdd560fb769742d32d68861efb075fbca9647f976b4155

All paths above relative to projects/damp-ascend/operator or tests as named.
These hashes prove reviewed bytes, NOT the yet-to-be-built integration.
