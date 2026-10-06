# DAMP selected-slot native prefill-pack v1 — NEW, default OFF

This is actual algorithm-required source preparation, NOT a passed compiler/NPU
or fast service. It does not change the frozen decode binary, recurrence, image
or original runtime. Isolated namespace qwen36_damp_selected_prefill_v1, library
libqwen36_damp_selected_prefill_v1_ops.so, annotated kernel
qwen36_damp_selected_prefill_pack_kernel. Build requires
-D DAMP_BUILD_SELECTED_PREFILL_V1=ON (without the space after -D).

Inputs: transient native FP32[P,12,V128,K128] final-prefill state, true P1..16;
typed hi[S,12,128,16] FP16 / lo[S,12,128,112] INT8 / scales[S,12,4,112] FP32;
per-Hv INT32[12,128] Pk/Pv logical reordered->original, FP32 original-V SR,
INT32[P] ordered selected cache slots. This dense input contains ONLY P
prefill requests and is freed after packing; never keep S-slot FP32 sidecar.
State regions may share a real allocator arena when actual byte intervals are
ND/contiguous/32B/bounded/nonoverlapping. Every readonly/state/output/tiling
interval is checked. No silent format/dtype cast of supplied inputs.

prepare uses static CPU permutation/SR validation and cold1056B LUT upload,
outside capture; retains only static plans/tiling, not dense or packed state.
pack has no dynamic slot/state D2H. Return is guarded INT32[P*96+16], NOT a
sliced status: 8 front and8 tail sentinel0x13579bdf; middle P*12 rows of8 ints:
success,error,completed_groups,float_certified,float_exact_fallback,16384,0,0.
Metadata PAD/out-of-range/duplicate invalidates the ENTIRE invocation before
any state writer; status error1, complete packed state must stay unchanged.
Numeric transform overflow/nonfinite/FP16 overflow error2, quantizer error3:
earlier groups/tasks may already be stored. There is no transactional rollback.
Service must abort/retire affected slots/worker permanently and never feedback,
retry or publish partial state. Static plans are immutable, per original ABI.

Load original Pv-selected 128-K FP32 row, RN32(S/c) in original V coordinates,
then gather Pk into reordered UB group32. c=1 copies original raw bits exactly.
Default float candidate OFF uses exact25-step restoring divide from frozen
bca2ab... helper (not integer ExactCode). Optional approximate Div proposes only;
exact dyadic Float certificate or restoring fallback decides every value.
Invalid/overflow never gets clipped. This first scalar source is correctness
preparation: its all-lane costs may be excessive. Exact Float probe/NPU and
timing are mandatory before enabling it; scalar certificate is not SIMD.
Only final integer requantization uses the already NPU-proven SIMD certificate
and rejected-lane GatherMask exact fallback. Do not confuse their scopes.

Byte-exact methods PackStore, QuantizeChunk, VectorToScalar,
LoadQuantizerTables from frozen production header SHA
15142a8360043e30cafbaebd19e2f528573819dcfdb519580867732e69340ff1.
No change to group32 scale reciprocal0x3c010204, zero-amax-only scale1,
FP16hi16/INT8lo112, row/head writer,1024/3584/448B group DMA.
New loader, metadata, status and float SR transform are the only device seam.
PackStore high finite admission uses exact FP16-RNE overflow midpoint65520
(raw0x477ff000), not max65504 clipping. Tensor oracle still governs all bits.

Explicit UB115392B: work59904, integer quantizer42496, meta160, plan2048,
row512, packedOut2*5120, status32. Full offsets tested disjoint/aligned.
No Broadcast/high-level hidden tmp allocation, no std::array device methods,
no uint8 Duplicate. Compiled stack/allocator/event correctness still needs
actual ASC and NPU. Queued ASC stream(false)+RunOpApi; host global definition
visible, device body/2201 implementation guarded. Require real exported non-UND
symbol and no-device load/schema/Meta before any device load.

MAIN only: fresh external build root (never overwrite), exact-image no devices,
real CANN/Python metadata. Example:
cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1
  -B /cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build
  -DDAMP_BUILD_SELECTED_PREFILL_V1=ON
  -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
cmake --build /cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build -j2

Required NPU gate, before serving: actual native chunk-prefill final FP32
state -> independent exact Float SR/Pv/Pk -> independent group32 pack compared
bitwise; same real shared arena adjacent/guard-gap layouts, first/last slots,
P1/P16 (then P2..15), arbitrary per-Hv plans/generalSR,zero/tiny/half ties,
fullraw conv/FA/padding/untouched-input guards, source/SO/proof/pointers bound.
Save CPU fixture before H2D and nullable raw results before assert.
Then native-prefill->pack->160 decode own-feedback numerical states/output
at frozen1e-5/.00303; final192 plans separately. Unknown allocator shared_by,
FA live page footprint/zeroing must be rejected before ANY runtime writer.

Continuation selected unpack may reuse NPU index_select/cast/Mul/cat and static
inverse permutations into ONLY P transient original-coordinate states, then
native K-major chunk initial_state and has_initial semantics. Mixed non-spec
requires actual native builder decode-prefix/prefill-suffix ordering; run one
native conv/gating over the entire mixed batch, compressed prefix decode,
selected chunk+pack suffix, merge original token order. These are NOT yet
wired or tested by this packet. CPU service diagnostic cannot replace them.
No E2E/formalC16/graph/task-accuracy/performance acceptance is claimed.
