# Pre-registered NPU matrix — integer certificate draft (NOT RUN)

MAIN owns all Docker/build/NPU/Git. No new wrapper, compiled entry or command
is claimed ready: first MAIN must bind an independently named probe using the
existing queued ASC wrapper/current public ND ABI; frozen16-file SOURCE_NAMES
and .so remain untouched. Old floatMul fast path stays OFF.

## Independent probe ABI proposal

certify_bits(INT32 xBits[N], INT32 scaleBits[N], INT32 proposalMagnitude[N],
INT32 Ctable[128], INT32 Ftable[128]) -> fresh INT32 accepted[N+16],
fresh INT32 lowerFloor[N+16], fresh INT32 upperFloor[N+16],
fresh INT32 lowerDomain[N+16], fresh INT32 upperDomain[N+16].
N64 and896 only initially. Preserve front/back8 INT32(32B) guards; distinct
sentinels per output. Preparing tables caches immutableND plans before launch.
Template helper endpoints are instrumented ONLY in this isolated probe;
production/trace bytes remain frozen. No persistent state is allocated.
The isolated wrapper synchronously rejects n<0 or>127 before dispatch (or
explicit device validation pre-pass outside graph); do NOT let unsafe n reach
Gather and hope final mask rejects. C/F table values must bind exact CPU
coefficient hash and byte-offset interpretation; no user table arbitrary ABI.

Same-version exported get_npu_format/npu_format_cast enforce actual ND;
Meta cannot prove it. Current getCurrentNPUStream().stream(false)+RunOpApi,
not mixing direct C++stream(true). Receipt must bind SoC Ascend910B4,
CANN9.1/dav-2201, sourceSHA, SO SHA/actual loading, fixture SHA, preflight,
physical4–7->logical mapping and non-overwriting output directory.

## Required correctness

1. Primitive edge vectors: UINT32 logical shifts(raw sign/high bit), INT32
   limb Mul/Add extrema(u1/u2>2^24), negative INT32 product b*(M49-M48),
   Maxs/Mins/clamp, signed safe subtraction and strict sign bit.
   All127 coefficient LUT entries, offset0/504, mixed proposals including0/127.
   Test vector head/tail lane63/64/895, padded guards and no input modification.
2. Every254 normal scale exponents x12 significand carry boundaries x127
   thresholds: normal-domain flags match independent Fraction floor.
   Include product-normalization u3=4095/4096 and endpoint exponent0/1/254/255;
   invalid placeholders must remain safe and acceptance0. Sample passing
   does not establish the whole floatMul ISA contract (floatMul is absent).
3. Reuse frozen40,316 labeled raw-bit fixtures(all halves±4, both RN32
   preimage midpoints±1, signs, subnormal scales, scales1/2/0x00800001/
   1.1/FLTmax, +/-zero, min/maxsubnormal/minnormal/FLTmax, invalid domains,
   savedstep45) with proposals truecode±1, 0,127 and arbitrary magnitudes.
   Every accepted lane MUST equal independent Fraction->RN32->RNE code.
   Include all128 arbitrary proposals on a stratified fixture subset.
4. Savedstep45: magnitude117 MUST reject,118 MUST accept, final signed-118.
   scale stays0x39919209, x0xbd05a10e, no mutation/snapping/flooring.
   Subnormal scale always falls back; subnormal x treated as raw bits.
5. N64/89620 repeated calls, changing fixtures/proposals, full raw outputs
   saved BEFORE assertions; guards/allinputs/LUT/storageptr bitwise unchanged.
   Fresh outputs cannot alias inputs, each other or persistent packedstate.
   N0/63/65/1792/897, wrongdtype/noncontiguous/misalignment/device/alias/
   malformedtable/proposal-range must fail BEFORE unsafe gather and preserve
   all input roots. Graph remains unsupported until separately verified.
6. Compact fallback: public CompareScalar(INT32 EQ0) emits byte mask;
   reinterpret mask for GatherMask, padded256B allocation, exact original
   indices. Verify empty/all/mixed lane sets, exact rsvdCnt and bytes, explicit
   V_S visibility before scalar reads and S_V before vector consumers.
   Run exact frozen fallback only rejected lanes, combine accepted/proven
   magnitudes, restore sign from original bits; whole codes bitwise golden.

## Then real DAMP — cannot skip

Only after above PASS, MAIN may integrate a NEW explicit-opt-in production
revision and independently retain old SO/trace/failed gate. Run actual packed
B1/B16 x160 changing inputs/indices, entire states/guards/staticplans untouched,
and frozen1e-5 state/output/bitwise packing gates. No dense FP32 sidecar.
GeneralSR and final192plans require independent reference scope, not merely
restrictednative SR1/power2. Real cache ownership/admission/graph remain gates.

Only then matched same-stack TP4 dense/candidate E2E: fixed1024 outputs,
profiling OFF, repeated TTFT/TPOT/outputthroughput, and taskaccuracy later.
Record fallback ratio/domainmix/integerCertificate kernel cost as diagnostics;
neither ratio nor a probe microbenchmark counts as E2E acceleration.

