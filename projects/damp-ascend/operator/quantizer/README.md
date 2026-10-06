# DAMP exact low-state quantizer proposal

Status: NEW ISOLATED DRAFT, not included by production, not compiled on CANN, not
executed on NPU, not a performance result. Main agent owns all builds and NPU
execution. Do not replace the frozen operator / trace libraries in place.

## Evidence that motivates this algorithm-specific change

Saved-step45 trace v2 reproduced production output and packed state. Candidate
updated FP32 state and scale were bitwise equal to actual native golden.
The one disputed low cell was x=-0.032624296844005585 (0xbd05a10e),
s=0.0002776535984594375 (0x39919209). IEEE RN32(x/s)=-117.5
(0xc2eb0000), hence integer RNE=-118. Actual 910B4 vector Div produced
-117.49999237060547 (0xc2eaffff), hence -117.
This is a division-before-quantization boundary, not an update/FMA error.
No epsilon, half-tie snap, relaxed tolerance, or new scale floor is proposed.

Actual report:
 /cache/cch/qwen36-damp-20261006/saved-step45-trace-v2/report.json

Production v4 SO:
22f522cf5befcf6afa12560dd2624fd6ddb1c99cc8d9bf04a4b08502363b3937
Production header:
ecc24fada002dafbca962de5265f1bddc27a03d1e723070d9b317b415e3ca856
Trace v2 SO:
a148e259482febf614f56fcf982a18e4d98c3bdf7c6e8ce573239a5ef39b1b2f

## Frozen quantization contract

For finite FP32 x and positive finite FP32 s:

 code = clip[-127,127](RNE_integer(RN32(x/s))).

RN32 is IEEE binary32 round-to-nearest, ties-to-even. The two rounds are
essential: rounding the exact rational x/s straight to an integer is a different
algorithm. The group32 scale remains RN32(amax * FP32 reciprocal bits 0x3c010204).
Only amax==0 gets scale=1. Positive nonzero underflow to s==0 remains invalid.
There is NO 1e-12 floor in the frozen implementation. This proposal does not
change hi FP16 conversion, recurrent update, SR, permutation, group axis,
readout-before-pack order, DMA ownership, or persistent state layout.

The exact helper accepts positive subnormal scale and finite subnormal x.
Signed zero maps to integer zero. Invalid finite-domain inputs return valid=false;
the eventual wrapper must reject them before any persistent state mutation.
The isolated helper never writes GM. It cannot prove whole-wrapper fail-closed
admission by itself.

## Exact integer-bin decision and proof

Use abs(x), then restore the original sign. Let j=0..126 separate output integers
j and j+1, and t=j+1/2. All these t are exactly representable binary32 and have an
even final significand bit. Therefore:

- j even: t rounds to integer j. Output is >=j+1 precisely when
  x/s > (t+nextafter(t,+infinity))/2.
- j odd: t rounds to integer j+1. Output is >=j+1 precisely when
  x/s >= (prev(t)+t)/2.

Equality uses the even significand of t in the first rounding, followed by the
integer parity in the second. t=0.5 (j=0) uses its upper midpoint; there is no
incorrect symmetric-ULP assumption at the only binade corner among these t.

Let k=2j+1 and f=floor(log2(k))-1. The applicable threshold is

 T_j = C_j * 2^(f-24),
 C_j = (k << (23-f)) + (j odd ? -1 : +1).

C_j is positive, odd, and 25 bits. Decode x=Mx*2^px and s=Ms*2^ps, where
normal operands have 24-bit M and p=rawExponent-150; subnormal operands have
M=rawFraction and p=-149. Compare x with s*T_j exactly using the <=49-bit product
P=Ms*C_j, with no floating multiplication or division.

If top exponents differ they determine the ordering. Otherwise left-shift Mx by
bit_length(P)-bit_length(Mx) and compare with P. The shift is nonnegative and
<=48; the result stays <2^49. Zero is handled separately. An ordered binary
search among 127 transitions finds the clamped code in at most seven comparisons.
The last transition j=126 proves saturation at 127 without performing a
potentially overflowing float division. Signed saturation follows by symmetry.

exact_quantizer_bits.h implements this decision. ExactWithCandidate can first
certify an arbitrary proposed signed code with one/two exact boundary tests, then
fall back to the full search. Its correctness assumes nothing about approximate
Div accuracy. This all-scalar option is a correctness anchor, not a speed claim.

## Conservative SIMD fast certificate

quantizer_ascendc.h computes ordinary Div only to propose an integer magnitude n.
NaN/Inf q is sanitized, q is clamped to +/-127 BEFORE CAST_RINT to avoid int32
overflow, and the final code sign is restored from raw x, not the approximate
quotient sign.

For interior n the ordinary integer half boundaries are tL=n-1/2 and tU=n+1/2.
For n=0 ignore lower; for n=127 ignore upper. Construct products
pL=RN32(tL*s), pU=RN32(tU*s) and require:

 abs(x) > four-nextafter(pL)   (unless n=0),
 abs(x) < four-prev(pU)        (unless n=127).

Both checks are STRICT. The fast domain additionally requires finite x, positive
normal finite s, and BOTH endpoint products normal finite. Subnormal s/product,
overflow, NaN and invalid scales are never accepted by this certificate.
Masked endpoint products for n=0/127 are still checked: this is conservatively
narrower, not a change to the exact contract.

Proof is conditional on the endpoint Mul being IEEE RN32. An applicable
binary32 quotient-rounding midpoint is at distance <=t*2^-24 from t.
After multiplying by s its distance from t*s is strictly less than one ULP
at t*s; the endpoint RN32 product contributes <=0.5 ULP. Across a binade corner,
four representable neighbors cover at least two ULPs of the upper binade, larger
than the 1.5-ULP total bound. Strict interior thus implies the exact bin,
independent of the Div proposal/error. Near-boundary proposals take exact search.
No "|approxDiv|<0.5 -> zero" shortcut is legal.

IMPORTANT: a dav_c220 vmul instruction alone does not prove its RN32 contract.
rnMulReceipt defaults false. Actual 910B4 endpoint-Mul bitwise fixtures and
domain/no-FTZ behavior must pass before opting in. If this cannot be proved,
keep all-exact correctness anchor, or design an independently proved integer
SIMD certificate. Do not silently enable the float certificate.

The fallback mask compacts uncertain lane indices with public GatherMask.
All lane codes on that list are recomputed by ExactCode. Sign restoration makes
the certificate independent of the proposal's sign too. The host wrapper must
validate disjoint UB spans and immutable inputs; current draft trusts that
construction and documents it rather than claiming it is enforced.

## Source / API reuse

Read-only source identities:

- ops-transformer 9.1.0 ref: 0684247214bae5abb5cb6dc7d90b34a6ad401cdd.
  /cache/cch/ops-transformer/moe/moe_init_routing_v3/op_kernel/moe_v3_full_load_base.h
  lines 200-234: Compare masks + Uint16 And + counter-mode GatherMask
  repeatTimes=1, src0BlockStride=1, src0RepeatStride=8, src1RepeatStride=8.
  This is a public-API call pattern, not reuse of that MOE algorithm.
- CANN9.1 dav_c220 kernel_operator_vec_binary_impl.h
  c090b0c428b92238b509cbc949421d2e1c6000be22692a801393080171e58323:
  ordinary float Div -> vdiv, Mul -> vmul. DivConfig 0ULP is arch3510-only;
  never port that 950/arch35 path onto 910B4.
- CANN9.1 dav_c220 kernel_operator_vec_vconv_impl.h
  a22a3a291d191a6009862863986c9436fa6a70f0d72a3c2084847cb281987e9d:
  float->int32 CAST_RINT -> vconv_f322s32r. Keep this final integer rounding.
- kernel_scalar.h
  77b045251d9db47540a6ea5acea9bd16f6c41c20988b0cd122d0cf13b8eef40f:
  CountLeadingZero(uint64) public helper -> clz. GetUintDivMagic's implementation
  is arch3510-only and is not used.
- dav_c220 kernel_operator_vec_gather_mask_impl.h
  cf306aead716ada7cef8f448226e5655de917809f9adcc803c6a2ba3afddb0f7:
  int32/float/uint32 vector source + uint32 custom mask -> vreducev2.
- dav_c220 CreateVecIndex generates the first 8 scalar entries then uses Adds;
  the draft does not fill 1792 scalar indices individually.
- MOE gather_dynamic_quant ordinary Div/half/int8 conversion is not the DAMP
  FP32 RN32->RNE contract. It cannot be used as a drop-in quantizer.

Actual SDK snapshots, read only:
 /cache/cch/qwen36-damp-20261006/sdk-div-audit-v1/include-basic_api
 /cache/cch/qwen36-damp-20261006/sdk-div-audit-v1/impl-basic_api

Only public kernel_operator.h APIs are included; no direct internal headers.

## Ownership, synchronization, UB, and costs

One original production task continues to own its whole (token,Hv) state/output.
Quantize a V16*112=1792 half-group twice, AFTER the unchanged group32 amax/scale.
Do not change scale grouping to 16, scatter stores by Pv, or split 32B DMA
ownership. Keep raw low FP32 immutable until code selection finishes; the old
in-place LowBroadcast cannot overwrite it before the exact fallback.

Caller supplies 32B-aligned disjoint scratch; count is 64-aligned, 64..1792.
Six new 1792*4B planes (q/endL/endU/scale-broadcast/indices/compactIndices)
=43,008B; six 224B masks =1,344B; total 44,352B.
Reuse production broad codes and absA for absX after reduction, not its raw x.
Old declared UB 98,816B +44,352=143,168B. Allow at least another 8KiB for Select's
reserved UB: 151,360B (~147.8KiB), below a 192KiB budget. Compiler tiling / queue
liveness / actual UB reports remain required. Full 3584-lane planes would be
needlessly close to the UB ceiling.

V dependencies have explicit PIPE_V barriers. Vector/Gather producers ->
scalar GetValue use V_S Set/Wait. Scalar code SetValue -> future Cast uses S_V.
Inbound MTE2 readiness and outbound MTE3 readiness remain caller obligations.
No CrossCore, atomic or arbitrary scatter is introduced. NPU count/order and
data hazards must still be measured. Regex audit is not a numerical proof.

Worst-case all restoring division: 23*14,336=329,728 scalar iterations/head;
B16*12 heads=63,307,776/layer/token; 48 layers ~3.04 billion/rank/token.
That is not proposed as the deployment fast path.
All exact-bin search: <=100,352 comparisons/head; candidate exact-bin certification
<=28,672 plus failures/head; still potentially expensive.
Fast path has vector endpoint/mask work, 8 compactions/head (two chunks*4 groups),
and <=7 comparisons for only uncertain lanes. Report fallback density and
vector-to-scalar stall cost; do not assume density is small. Per-head packed state
is 20,224B vs 65,536B dense, but theoretical memory saving does not prove speed.

## Commands and acceptance chain

Parent-owned compile in a NEW external directory (example path must not exist):

 c++ -std=c++17 -O2 -Wall -Wextra -Werror \
   projects/damp-ascend/operator/quantizer/quantizer_host_harness.cpp \
   -o /cache/cch/qwen36-damp-20261006/quantizer-host-v1/quantizer_host

Stdlib math test (no C++ build, no NPU):

 PYTHONDONTWRITEBYTECODE=1 python3 \
   projects/damp-ascend/operator/quantizer/test_exact_quantizer.py

Add --harness with the explicitly built path to test compiled C++ against the
independent Fraction->RN32->integerRNE oracle. C++ and AscendC compilation are
separate gates. The initial stdlib result tests the mathematical algorithm only.

Actual stdlib execution on 2026-10-06, AWMCP exec-00000000000001cc:
116,015 pairs including 100,000 random pairs, zero exact-bin mismatches;
99,593 accepted magnitude proposals, zero unsafe certificates in the RN32-Mul
mathematical model; saved-step45 code -118. C++ harness not compiled/executed.
This supplements the earlier in-memory arithmetic check; it is not NPU evidence.

Full synchronization scripts were run read-only after verifying the case DB
already existed and the retriever only queried SELECT (no DB regeneration).
sync_audit exec01d9 returned the following complete red/high candidate:

1. SYNC-02 [red], quantizer_ascendc.h original line195:
   "疑似 V 计算后未同步即 Scalar 读: Scalar@195 (计算@189)".
   Detail: "候选：Vector 计算（如 ReduceSum）后、GetValue 前需 V→S 同步
   （PipeBarrier<PIPE_V> 或 SetFlag/WaitFlag<V_S>） | 历史 case:
   cann/ops-nn PR#1678 (flag_pair) | 修复提示: 补齐缺失的 SetFlag 或
   WaitFlag，确保所有路径都触发 SetFlag | diff证据: @@ -166,12 +166,12 @@
   private: PipeBarrier<PIPE_V>(); Cast(xLocal, x1Fp32,...".
   Submitted without dismissal. Main approved a same-site explicit V_S pair
   after GatherMask. Before this change WaitVectorToScalar already contained
   exactly FetchEventID(V_S), SetFlag<V_S>, WaitFlag<V_S>. The approved patch
   expands that body at this producer-consumer call site; it changes visibility,
   not numerical arithmetic. Original candidate is retained here; a clean
   rescan would still not be NPU proof.

Performance-only suggestions (not automatic repairs):
SYNC-09 original line47: "同一文件 PipeBarrier<PIPE_V> 过多: 30 个";
SYNC-09 original line86: "同一函数连续 PipeBarrier 过多: 28 个 in Or".
ascendc_flow_analyzer exec01db returned no findings, but operations,
buffer_accesses and dependencies were empty. This regex frontend limitation is
not a semantic synchronization pass. Caller/UB/sync obligations and isolated
actual NPU tests remain necessary.

NPU matrix is preregistered in NPU_FIXTURES.md. Next required sequence:
The new default-fast-OFF exact_bits operator/CMake/runner preparation and full
guard ABI are described in PROBE_ABI.md. None has been compiled or run on NPU.

After the approved explicit GatherMask V_S expansion, sync_audit exec01e3
reported a NEW candidate, retained without dismissal:
SYNC-08 [red], quantizer_ascendc.h:196:
"SetFlag 前存在提前退出（可能跳过 Set → 死锁）: SetFlag<HardEvent::V_S>".
Detail: "同函数 Or 内未被兜底的 return/break: [67, 80]；确认所有路径都触发
SetFlag | 历史 case: cann/ops-transformer PR#6996 (flag_pair) | 修复提示:
补齐缺失的 SetFlag 或 WaitFlag，确保所有路径都触发 SetFlag | diff证据:
@@ -262,6 +262,7 @@ public: auto layoutUbBias = LayoutBias::template MakeLayoutInUb...".
Main requested preserving this for actual-path review, not blindly chasing zero
regex candidates. Flow rescan exec01e5 again had no operations/accesses/dependencies.
The unchanged arithmetic software rerun's AWMCP wrapper returned no structured
route result, and was not repeated; subsequent exec01ef found no active matching
test process. The earlier terminal exec01cc mathematical PASS remains evidence,
not a claim that the unknown rerun passed.

isolated exact-bin/Gather/Mul gates -> SAME saved-step45 production fixture ->
real packed decode B1/B16 changing slots 160 steps with untouched-state/input
checks -> restricted native anchors and general SR -> final calibrated plans ->
true typed-cache integration -> eager/graph checks as supported -> same-config
dense paired output1024 performance -> final LongBench-v2/GSM8K.
No isolated pass replaces any later stage. No FP32 GM state sidecar is allowed.
