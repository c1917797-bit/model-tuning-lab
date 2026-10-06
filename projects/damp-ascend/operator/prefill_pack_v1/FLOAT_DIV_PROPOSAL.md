# DAMP prefill exact binary32 SR division — source preparation

Default OFF. Not compiled, not loaded, not run on NPU, not a service/performance
result. Original decode, collectors, quantizer and all receipts are unchanged.

## Contract and frozen reuse

NEW namespace Qwen36DampPrefill. ExactFloatDiv(x_bits,c_bits) returns
{valid,finite,bits}. Inputs are raw binary32 bits, finite signed x and finite
strictly-positive c (including subnormal c). Invalid inputs return false,false,0.
IEEE RN32 signed-zero is preserved. A legitimate quotient overflowing RN32
returns valid=true,finite=false,signed Infinity; caller must fail/retire the
affected cache state, never clip it. Underflow rounds ties-even to signed zero
or the correct subnormal. This is a FLOAT quotient, not INT8 ExactCode.

Only BitLength/DecodePositive are reused from frozen
operator/quantizer/exact_quantizer_bits.h SHA
f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169.
Define DAMP_QUANTIZER_ASCENDC only in a device compilation pass with its actual
2201 arch guard. The helper uses scalar integer instructions; no floating
division/multiplication contract, FTZ assumption, DMA or synchronization API.

## Restoring path proof

Normalize each nonzero significand to 24 bits, adjusting its exponent. Let
d=e_x-e_c, E=d if M_x>=M_c else d-1. For normal E>=-126 the quotient in units
2^(E-23) is exactly (M_x << (23 or 24))/M_c; numerator is below 2^48.
25 restoring compare/subtract iterations produce floor quotient plus exact
remainder, then 2*remainder compared with denominator implements ties-even.
Mantissa carry increments E; E>127 yields Infinity.

For E<-126 use subnormal units 2^-149. Mantissa ratio is strictly below 2:
d<=-151 is strictly below the zero/min-subnormal midpoint. At d=-150 divide
M_x by 2*M_c; otherwise shift d+149 is 0..23. The rounded result is the raw
subnormal payload, including carry to 0x00800000. No shift exceeds24 here;
remainder-doubling is below2^26.

## Optional exact scalar certificate (future fast path, OFF)

For arbitrary nonnegative finite FLOAT proposal q, compare original x/c with
the exact midpoints between neighboring binary32 values. Each midpoint has
at most25 significand bits; multiplying by c's <=24-bit significand is below
2^49. Compare dyadics by top exponent first, then align significand lengths
only (at most48-bit shift), never a potentially huge exponent-gap shift.

For nonzero q with decoded mantissa m/exponent e, upper is
(2m+1)2^(e-1). Lower is ordinarily (2m-1)2^(e-1); exact powers of two above
the minimum normal use (4m-1)2^(e-2). Minimum normal explicitly takes the
ordinary branch because its subnormal predecessor spacing is unchanged.
q=0 has upper2^-150. FLTMAX upper is (2^25-1)2^103 and is strict.
A proposal with even least-significand bit includes both ties; odd excludes
both. Sign is restored from x only. Invalid/Infinity proposals reject;
fallback is ExactFloatDiv, not INT8 code, snapping or a changed oracle.

## Cost and required deployment proof

All-lane fallback costs25 scalar compare/subtract iterations per FP32 cell.
For one local layer's12*128*128 final state cells that is up to4,915,200
iterations per request;48 local GDN layers multiply that by48. This is a
correctness starting point, not evidence of useful prefill throughput.
Two scalar midpoint checks per cell can certify an arbitrary vector Div
proposal, but an all-lane scalar scan is not accepted as a proven performant
route. Device SIMD certificates/compacted rejects or another actually proven
IEEE native divide path remain performance alternatives; do not silently
enable approximate Div.

The Fraction golden does not import the candidate model/helper. It rounds by
binary-searching all positive finite binary32 values and exact distances,
including overflow midpoint. Source-mapped Python tests do NOT prove C++
lowering or Ascend scalar/UB behavior. MAIN must compile a separately named
raw-bits NPU probe, bind CANN/SoC/source/SO, preserve raw results before asserts,
then test full raw bits/valid/finite/guards/input immutability, changing inputs
and repeated execution. Need zero/subnormal/normal-boundary/power2/overflow
midpoints and neighbors for both signs, general c, actual native prefill
state and final192 plans before the pack->decode seam can pass.

## Future minimal pack seam (not yet implemented)

Reuse source-bound production integer certificate/GatherMask exact INT8 pack
and group32 RA reduction. Read native immutable FP32 final state
[T,12,128,128] (value-major), per-Hv INT32 Pk/Pv and original-coordinate FP32 SR,
write selected original hi/lo/scales contiguous SoA slot regions. Whole-head
ownership; transformed group32 has4096 temporary FP32 UB cells only. Read Pv
rows; gather Pk in UB; exact SR divide before FP16/amax. Never retain dense
FP32 feedback or write arbitrary Pv-scattered cache rows. Per-head status owns
one complete32B row. Duplicate/PAD/out-of-range indices must be checked across
allT before any writer. Data failures may require permanent slot+worker
retirement; no retry/native fallback over partly-written cache.

Native prefill -> pack -> packed decode oracle must independently retain
full selected/untouched/raw FA+conv/padding guards and immutable source/plans.
Mixed/continuation turns require actual pre-writer atomic admission and
device-side materialization; rejecting them is not formal C16 performance.
