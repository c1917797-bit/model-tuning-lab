# Separated DAMP NPU parity diagnostic: not yet executed

Parent owns all builds, devices and executions. Keep existing CPU failures,
1e-5 state / 0.00303 BF16-output gates, and production ABI unchanged. This
protocol is equation-derived preparation, not author-code fidelity or an
NPU/performance/task-quality result.

## Why a separated diagnostic is necessary

CPU v2 B16 step2 failed selected-state max-head relative L2 7.879801577310659e-5;
output 0.00021241980203049154 passed. Untouched slots were exact. Retained
fixture SHA256: e6f50b1245f88aa4802ec3dfb5c58159473dc3ac57cb8f490c563230c43dce2a.
The same-before mv versus sum prepack error was only 2.7903632515274373e-8,
but INT8 quotients crossed 116.499992/116.500008 (116/117) and
57.499996/57.5 (57/58). This is arithmetic/tie-propagation evidence, not the
previous v1 all-slot-repack bug. No old run is relabeled PASS.

The inspected reference commit is 5cb98caaadeff42b5b62b996e34bb2aaa29d20fd.
Its recurrent_gated_delta_rule.h SHA256 is
96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b;
working-tree bytes matched the commit. Both native K128 and the new kernel
fold lower64+upper64, call WholeReduceSum64, apply beta to the residual,
use MulAddDst for outer update, and scale Q BEFORE readout. Source identity
does not establish the dynamic library loaded by a future process.

Independent CPU torch.mv does not promise that accumulation topology and
scales AFTER readout; provider multiply/sum also differs. Do not silently
adopt a guessed WholeReduceSum tree or torch.addcmul as bit-exact hardware.
[MulAddDst API](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/MulAddDst.md)
and [reduction overview](https://www.hiascend.com/doc_center/source/en/canncommercial/850/opdevg/Ascendcopdevg/atlas_ascendc_10_0023.html)
document operation semantics, not a cross-backend rounding promise.

## Independent native compressed golden (narrow, new preregistered scope)

Native tiling AnalyzeDtype admits FP32 state and requires BF16 Q/K/V/beta.
CheckShapeValueRangeAndRule admits NK=NV=12: each <=256 and NV%NK==0.
FillTilingShapeData takes query dim1 directly; kernel ProcessHead maps
head/(NV/NK), hence ratio1 for NK12. HQ12 is thus source-supported, but
must still pass an explicit real-NPU smoke on the actually loaded library.

The helper native_compressed_golden.py imports only the independent group
oracle. It expands native HQ4 Q/K to per-Hv HQ12 and applies each Pk, keeping
native BF16. SR is restricted to identity or powers of two; it checks that
V/c converts to BF16 exactly and rejects overflow/underflow. This restriction
is a diagnostic scope, not a model calibration or final algorithm choice.

For each step, golden uses only its OWN packed arena: independent CPU unpack,
native FP32 recurrent update, independent CPU pack of SELECTED slots only,
then feedback to the next step. Candidate keeps a separate packed arena and
feedback. Never replace either state from the other, never repack all slots,
and never resynchronize each step. B1/B16, 160 changing turns, unique rotating
slots; per-head original-coordinate metrics and untouched bytes are required.

Native output is BF16 in reordered/scaled coordinates before restoration;
candidate restores updated FP32 readout and then casts BF16. Save both cast
boundaries separately. Power-of-two scaling is exact for normal outputs but
cannot hide underflow/overflow; helper rejects unsupported restored values.
Non-power-of-two SR entails another native V BF16 rounding and is OUTSIDE
this narrow golden. It needs separate FP64-equation/FP32-checkpoint evidence,
not a silent cast or the claim that this restricted run covers calibrated SR.

Proposed new native-golden gate preserves <=1e-5 selected original-coordinate
state max-head relative L2 and <=0.00303 BF16 output, with bitwise independent
packing and untouched slots. Preregister the actual runner and source/library
hashes before execution. This is not retroactive repair of CPU v2, and a pass
would prove neither general-SR correctness, graph/mixed-batch support, TP4
48-layer serving, throughput nor GSM8K/LongBench-v2 quality.

## Same-input / FP32-update / quantizer separation

If native-golden parity differs, operator owner may add an explicit opt-in
diagnostic namespace/library; production prepare/decode aliases stay intact.
Required seams are proposals until schemas are frozen by the operator owner:

1. decode_trace must use the SAME LoadState/UpdateReadout/PackStore code, adding
   only disjoint ND GM stores. Expose updated FP32 [B,12,128,128] in reordered
   SR-scaled coordinates BEFORE packing, restored FP32 readout [B,12,128]
   BEFORE BF16, and optionally dot [B,12,128] and decay [B,12]. Verify normal
   output and hi/lo/scales match production decode on identical clones.
2. Feed that captured FP32 update UNCHANGED to independent CPU group32 pack;
   compare hi/lo/scales bitwise. This isolates packing from recurrence but
   does not independently prove the recurrence itself.
3. A pack_fp32 diagnostic must reuse the SAME PackStore arithmetic on fixed
   immutable FP32 input. Include +/-half/ULP, non-power-of-two amax, zero group,
   INT8 endpoints, FP16 +/-65504 and supported tiny scales. Freeze reciprocal
   bits 0x3c010204, zero amax->1, one FP32 RNE before clamp[-127,127]. Save
   amax/scales/quotients/codes on failure. Never epsilon-floor or accept code
   mismatches with a loose tolerance. Division lowering must be observed.
4. Exact recurrence uses g=0, dyadic inputs, identity SR/permutations; then
   realistic same-before data, then retained v2 boundary fixture. Same-before
   resets are attribution only, not substitutes for closed-loop feedback.

Use original-coordinate FP64 equation diagnostics for axes/SR/Pk/Pv invariants,
and actual native arithmetic for the explicitly restricted execution contract.
No guessed CPU reducer is a native correctness proof. Instrumented paths are
never eligible for performance timing.

## Provenance and failures

One new external output root per justified experiment, no overwrites or
unchanged retries. Record loaded library path/SHA, source/build identity,
torch/torch_npu/CANN, format ID, actual physical4->logical0 proof and ownership.
Save each phase, primary error, finite-safe JSON, input/checkpoint tensors and
SHA; secondary fixture-write error cannot replace the primary failure.
Stop on unmet gate, preserve it, and diagnose only the isolated new hypothesis.
