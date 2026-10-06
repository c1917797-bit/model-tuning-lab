# Integer-SIMD quantization certificate — NEW isolated draft

Status: uncompiled, no NPU execution, no E2E result. Not included in the
frozen16-file quantizer SOURCE_NAMES, any production/trace target or receipt.
Old floating Mul fast path remains OFF. MAIN exclusively owns builds/NPU/Git.
This repairs DAMP's packed-state RNE quantization seam, not unrelated fusion.

## Why replace the proposed float-Mul certificate

The actual CANN9.1 dav_c220 Mul implementation maps FP32 to vmul; the
[official9.1 Mul API](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Mul.md)
documents elementwise product and A2 INT32 support, but no rounding/FTZ
contract was located in that page or targeted official documentation searches.
This is NOT proof of a different ISA rule, and sample bitwise tests cannot
establish all-ISA RN32 behavior. Therefore the frozen RN32Mul-based helper
remains disabled. This new certificate uses NO float Mul/Compare/Cast.

## Exact two-stage boundary proof

Target remains clip[-127,127](RNE_integer(RN32(x/s))), s finite positive.
It is NOT RNE of the exact rational ratio.

Let transition index j=0..126, t=j+.5, separating integer codes j and j+1.
Every t has even FP32 significand LSB. If j is even, RNE_integer(t)=j:
the upper code requires x/s > midpoint(t,nextFP32(t)). If j is odd,
RNE_integer(t)=j+1: upper requires x/s >= midpoint(prevFP32(t),t).
The sole power-of-two t=.5 has j0 and uses the RIGHT midpoint, so no
left/right ULP-binade ambiguity remains.

Set k=2j+1, f=floorlog2(k)-1, C=(k<<(23-f))+(jodd?-1:+1).
Then that exact transition is C*2^(f-24), with 2^24 <= C < 2^25.
C=2^24-1 cannot occur: only k1 lies on a binade and its sign is +1.
A normal scale has significand M in [2^23,2^24), exponent raw E1..254.
Thus exact scale-times-transition P=M*C, times 2^(E-150+f-24);
P has bit length48 or49. No float multiplication is needed.

## INT32 SIMD product and every bound

B=4096, M=m0+B*m1, C=c0+B*c1+B^2; c2 is identically1.
m0,c0,c1 in0..4095; m1 in2048..4095.

p00=m0*c0
u1=(p00>>12)+m0*c1+m1*c0
u2=(u1>>12)+m1*c1+m0
u3=(u2>>12)+m1
d0=p00%B, d1=u1%B, d2=u2%B
P=d0+B*d1+B^2*d2+B^3*u3.

p00<=16,769,025 <2^24; u1<=33,542,144 <2^25;
u2<=16,781,309 <2^25; u3<8192. INT32 products/adds stay exact and
non-overflowing. u1/u2 must NEVER be converted to FP32; they exceed2^24.
Set b=u3>>12 (0/1), M48=(u3<<12)+d2, M49=(u3<<11)+(d2>>1).
The top24 exact product bits are M48+b*(M49-M48).
M48<2^25, M49<2^24, difference and b-product also fit signed INT32.
The positive-normal FP32 floor exponent is Eout=E+f+b, and its raw bits are
R=(Eout<<23)+(top24-2^23).

ONLY Eout1..254 is accepted. Eout is clamped BEFORE shift for invalid
placeholder lanes, and its domain flag stays0. Subnormal scale/used endpoint
or overflowing endpoint must use frozen ExactCode fallback; no scale floor.
Invalid scales still have bounded synthetic M and safely compute placeholders;
the final scale sign/normal/finite mask rejects them.

## Conservative certificate and all code/sign boundaries

Proposal n is independently sanitized to INT32 magnitude0..127 BEFORE gather:
ordinary Div may propose it but has no correctness/error-bound authority.
Generate lower j=max(n-1,0), upper j=min(n,126); LUT slot127 is a safe unused
duplicate126, not permission to index out of range.
Rlower and Rupper are exact FP32 FLOORS of the correct two-stage boundaries.

Accept only:
- n0 OR (lower normal AND rawAbsX > Rlower);
- n127 OR (upper normal AND rawAbsX < Rupper);
- positive NORMAL finite scale and finite original x.

Since positive float bit patterns are ordered, x>floor(lower) implies
x>exact lower threshold, and x<floor(upper) implies x<exact upper threshold.
The deliberately strict interior works for both parity inclusion rules:
some exactly valid boundary values are conservatively sent to fallback.
No finite x on an accepted lane can belong to another bin. n0 has no lower
boundary; n127 has no upper boundary because clipping is part of the contract.
Restore sign from ORIGINAL raw x, not Div proposal. +/-0 produce code0.
Subnormal x is safe: the certificate handles it only as raw integer bits.
NaN/Inf x, nonpositive/NaN/Inf scale never receive a certificate.

For raw positive-bit comparisons, each operand is in0..0x7fffffff:
signed INT32 subtraction is in[-2147483647,2147483647], no overflow.
Logical UINT32 rightshift31 of the difference gives the strict-negative bit.
Thus Compare<int32,GT> is unnecessary; A2 only supports INT32 EQ.

## Actual public APIs / source provenance

Do not include the internal impl headers. The draft includes kernel_operator.h
and uses public INT32 Add/Sub/Mul/Adds/Muls/Maxs/Mins, UINT32 logical
ShiftLeft/ShiftRight, and INT32 Gather with UINT32 BYTE offsets.

Copied CANN9.1 SDK root (MAIN exported; original repo/image unchanged):
/cache/cch/qwen36-damp-20261006/sdk-div-audit-v1/
- impl-basic_api/dav_c220/kernel_operator_vec_binary_impl.h
  c090b0c428b92238b509cbc949421d2e1c6000be22692a801393080171e58323:
  INT32 Add/Sub/Mul, Mul lines131-173 -> vmul.
- impl-basic_api/dav_c220/kernel_operator_vec_binary_scalar_impl.h
  ecb847914fd96534ac89d056cefbd7f198a63eb7850b04c6c5c7c1e9df0bda43:
  INT32 Adds/Muls/Maxs/Mins, UINT32 shifts with scalar count.
- impl-basic_api/dav_c220/kernel_operator_vec_cmp_impl.h
  02648f3b173b98017cec9b99869a089e8779072983ba3c5955b16df97935a5cd:
  INT32 comparison supports EQ only; GT is not silently assumed.
- impl-basic_api/dav_c220/kernel_operator_vec_gather_impl.h
  fd7cf11d0c71971fd417afbfd10953759a64ad2d05f22c91b2a19f466677255b:
  INT32/UINT32 Gather -> vgather32 with byte offset tensor.
- include-basic_api/kernel_operator_vec_gather_intf.h:
  Gather(dst,src,UINT32offset,baseOffset,count), Level2 public declaration.

No arch3510 Mull, variable-shift SIMD or integer division is assumed.
No And(INT32,count) compatibility alias is used (actual2201 implementation
reinterprets as INT16 with same count); bit fields use shifts/subtraction.
Integer instruction behavior and compiler lowering STILL require isolated
910B4 NPU gates; source plus mathematical proof is not a device PASS.

## Complete AscendC draft and UB/synchronization ownership

integer_certificate_ascendc.h contains the entire helper, no external
arithmetic helper. Template N64..896, multiple64. A production low16V x112
tile of1792 lanes is processed as two896-lane subtiles; do not instantiate1792.

Sixteen disjoint INT32 scratch planes + one accepted plane:
17*N*4=60,928B atN896. Two immutable128-entry LUT planes=1024B.
A padded256B mask +896-index GatherMask buffer3584B adds3840B:
total65,792B additional UB. Even retaining old98,816B plus conservative
8192B reservation gives172,800B <192KiB. Integration must re-account ACTUAL
all live buffers/queue depths/guards; this estimate is not allocator evidence.

The current draft is135 vector API operations plus135 PIPE_V barriers per
subtile (45 outer,45 per endpoint). It avoids per-element scalar compare
on accepted lanes, but its cost is NOT assumed negligible or fast.
After real correctness, profile/reuse registers and dependency fences only
with evidence; do not blindly remove barriers for a prettier static report.

Caller establishes LUT/input MTE2->V via TQue DeQue, no cold capture H2D.
Inputs/LUTs/17 planes must be 32B aligned and mutually disjoint.
Helper writes UB only; original x/scale/code/LUT remain unchanged.
GatherMask over accepted==0 produces sparse original indices; explicitly
FetchEventID/SetFlag/WaitFlag V_S BEFORE scalar reads/count/ExactCode fallback,
then S_V BEFORE vector sees scalar code writes. Caller keeps fullhead32B DMA
owner, updates FP32 readout BEFORE unchanged pack, no persistent FP32 sidecar.

## Skills: project-specific deviations

Reviewed API best-practice and precision/sync guidance. Generic reciprocal
substitution, epsilon/scale floor, CAST_ROUND or clearing shared caches are
not valid repairs of the frozen two-stage RNE contract. They are not applied.
New files only; coherent checkpoint/push is MAIN's serialized responsibility.

## Validation status

No source here has been compiled, integrated, or executed on NPU.
test_integer_certificate.py imports hash-bound FROZEN independent Fraction
oracle for mathematical testing; it never changes that oracle/threshold.
See NPU_MATRIX.md for real admission/device/lifecycle/packed feedback gates.

