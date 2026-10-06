// SPDX-License-Identifier: Apache-2.0
// Isolated public-API draft for CANN 9.1 / 910B4 (2201), not production-linked.
// API pattern attribution and numerical assumptions: see README.md.
#ifndef QWEN36_DAMP_QUANTIZER_ASCENDC_H
#define QWEN36_DAMP_QUANTIZER_ASCENDC_H
#include "kernel_operator.h"
#ifndef DAMP_QUANTIZER_ASCENDC
#define DAMP_QUANTIZER_ASCENDC
#endif
#include "exact_quantizer_bits.h"

namespace Qwen36DampQuantizer {
using namespace AscendC;
constexpr uint32_t CHUNK_MAX = 1792; // 16 V rows * 112 low K columns
constexpr float MIN_NORMAL = 0x1p-126f;
constexpr float MAX_FINITE = 0x1.fffffep127f;

struct Scratch {
    // All planes are disjoint, caller-allocated UB, 32-byte aligned.
    // broadcastScales contains immutable copies of the group's original
    // 112 scales repeated over 16 rows; NOT a new scale algorithm.
    LocalTensor<float> quotient, lowerEndpoint, upperEndpoint, broadcastScales;
    LocalTensor<int32_t> indices, compactIndices;
    LocalTensor<uint8_t> masks[6]; // each >= CHUNK_MAX/8 = 224 bytes
};
struct Stats { uint32_t exactLanes; bool valid; };

__aicore__ inline void WaitVectorToScalar()
{
    const event_t event = static_cast<event_t>(
        GetTPipePtr()->FetchEventID(HardEvent::V_S));
    SetFlag<HardEvent::V_S>(event);
    WaitFlag<HardEvent::V_S>(event);
}
__aicore__ inline void WaitScalarToVector()
{
    const event_t event = static_cast<event_t>(
        GetTPipePtr()->FetchEventID(HardEvent::S_V));
    SetFlag<HardEvent::S_V>(event);
    WaitFlag<HardEvent::S_V>(event);
}
__aicore__ inline void MaskAnd(LocalTensor<uint8_t> dst,
    LocalTensor<uint8_t> left, LocalTensor<uint8_t> right, uint32_t count)
{
    And(dst.ReinterpretCast<uint16_t>(), left.ReinterpretCast<uint16_t>(),
        right.ReinterpretCast<uint16_t>(), count / 16);
    PipeBarrier<PIPE_V>();
}
__aicore__ inline void MaskOr(LocalTensor<uint8_t> dst,
    LocalTensor<uint8_t> left, LocalTensor<uint8_t> right, uint32_t count)
{
    Or(dst.ReinterpretCast<uint16_t>(), left.ReinterpretCast<uint16_t>(),
       right.ReinterpretCast<uint16_t>(), count / 16);
    PipeBarrier<PIPE_V>();
}
// count must be 64-aligned, 64..1792; no tail mask truncation in this draft.
// Inputs rawX/scales immutable; absX/codes are disjoint caller-owned scratch.
// Caller completes inbound MTE2 (queue DeQue or MTE2_V) before entry and owns
// outbound V_MTE3 / queue synchronization after return. No GM writes here.
// rnMulReceipt must stay false until real 910B4 FP32 Mul parity is established
// across the registered certificate domain. Meta registration is irrelevant.
__aicore__ inline Stats Quantize(LocalTensor<float> rawX,
    LocalTensor<float> absX, LocalTensor<int32_t> codes, Scratch& scratch,
    uint32_t count, bool rnMulReceipt = false)
{
    if (count < 64 || count > CHUNK_MAX || (count % 64) != 0) {
        return {0, false};
    }
    if (!rnMulReceipt) {
        WaitVectorToScalar();
        bool valid = true;
        for (uint32_t lane = 0; lane < count; ++lane) {
            const Result result = ExactCode(
                rawX.ReinterpretCast<uint32_t>().GetValue(lane),
                scratch.broadcastScales.ReinterpretCast<uint32_t>().GetValue(lane));
            codes.SetValue(lane, result.code);
            valid = valid && result.valid;
        }
        WaitScalarToVector();
        return {count, valid}; // safe mathematical route; not a performance claim
    }

    // Approximate division supplies ONLY a candidate code.
    Div(scratch.quotient, rawX, scratch.broadcastScales, count);
    Abs(absX, rawX, count);
    PipeBarrier<PIPE_V>();
    Abs(scratch.lowerEndpoint, scratch.quotient, count);
    PipeBarrier<PIPE_V>();
    CompareScalar(scratch.masks[0], scratch.lowerEndpoint, MAX_FINITE,
                  CMPMODE::LE, count);
    PipeBarrier<PIPE_V>();
    // Select scalar mode requires the compiler's reserved UB (see accounting).
    Select(scratch.quotient, scratch.masks[0], scratch.quotient, 0.0f,
           SELMODE::VSEL_TENSOR_SCALAR_MODE, count);
    PipeBarrier<PIPE_V>();
    // Clamp BEFORE CAST_RINT: otherwise finite out-of-range q can overflow i32.
    Maxs(scratch.quotient, scratch.quotient, -127.0f, count);
    PipeBarrier<PIPE_V>();
    Mins(scratch.quotient, scratch.quotient, 127.0f, count);
    PipeBarrier<PIPE_V>();
    Cast(codes, scratch.quotient, RoundMode::CAST_RINT, count);
    PipeBarrier<PIPE_V>();
    Cast(scratch.quotient, codes, RoundMode::CAST_NONE, count);
    PipeBarrier<PIPE_V>();
    Abs(scratch.quotient, scratch.quotient, count); // magnitude integer n
    PipeBarrier<PIPE_V>();
    // Never trust the approximate quotient's sign either. Restore the sign
    // from immutable rawX; +/-0 both produce integer zero.
    Muls(scratch.lowerEndpoint, scratch.quotient, -1.0f, count);
    CompareScalar(scratch.masks[1], rawX, 0.0f, CMPMODE::LT, count);
    PipeBarrier<PIPE_V>();
    Select(scratch.lowerEndpoint, scratch.masks[1], scratch.lowerEndpoint,
           scratch.quotient, SELMODE::VSEL_TENSOR_TENSOR_MODE, count);
    PipeBarrier<PIPE_V>();
    Cast(codes, scratch.lowerEndpoint, RoundMode::CAST_RINT, count);
    PipeBarrier<PIPE_V>();

    Maxs(scratch.lowerEndpoint, scratch.quotient, 1.0f, count);
    Mins(scratch.upperEndpoint, scratch.quotient, 126.0f, count);
    PipeBarrier<PIPE_V>();
    Adds(scratch.lowerEndpoint, scratch.lowerEndpoint, -0.5f, count);
    Adds(scratch.upperEndpoint, scratch.upperEndpoint, 0.5f, count);
    PipeBarrier<PIPE_V>();
    Mul(scratch.lowerEndpoint, scratch.lowerEndpoint, scratch.broadcastScales, count);
    Mul(scratch.upperEndpoint, scratch.upperEndpoint, scratch.broadcastScales, count);
    PipeBarrier<PIPE_V>();

    // Domain certificate: x finite; s and both RN32 products positive normal
    // finite. There is NO scale floor. Subnormal inputs/products -> exact path.
    CompareScalar(scratch.masks[0], absX, MAX_FINITE, CMPMODE::LE, count);
    PipeBarrier<PIPE_V>();
    CompareScalar(scratch.masks[1], scratch.broadcastScales,
                  MIN_NORMAL, CMPMODE::GE, count);
    PipeBarrier<PIPE_V>();
    MaskAnd(scratch.masks[0], scratch.masks[0], scratch.masks[1], count);
    CompareScalar(scratch.masks[1], scratch.broadcastScales,
                  MAX_FINITE, CMPMODE::LE, count);
    PipeBarrier<PIPE_V>();
    MaskAnd(scratch.masks[0], scratch.masks[0], scratch.masks[1], count);
    CompareScalar(scratch.masks[1], scratch.lowerEndpoint,
                  MIN_NORMAL, CMPMODE::GE, count);
    PipeBarrier<PIPE_V>();
    MaskAnd(scratch.masks[0], scratch.masks[0], scratch.masks[1], count);
    CompareScalar(scratch.masks[1], scratch.lowerEndpoint,
                  MAX_FINITE, CMPMODE::LE, count);
    PipeBarrier<PIPE_V>();
    MaskAnd(scratch.masks[0], scratch.masks[0], scratch.masks[1], count);
    CompareScalar(scratch.masks[1], scratch.upperEndpoint,
                  MIN_NORMAL, CMPMODE::GE, count);
    PipeBarrier<PIPE_V>();
    MaskAnd(scratch.masks[0], scratch.masks[0], scratch.masks[1], count);
    CompareScalar(scratch.masks[1], scratch.upperEndpoint,
                  MAX_FINITE, CMPMODE::LE, count);
    PipeBarrier<PIPE_V>();
    MaskAnd(scratch.masks[0], scratch.masks[0], scratch.masks[1], count);

    // Positive FP32 bit increment is nextafter. Strict +/-4 neighbors form a
    // conservative interior certificate, conditional on real RN32 Mul.
    Adds(scratch.lowerEndpoint.ReinterpretCast<int32_t>(),
         scratch.lowerEndpoint.ReinterpretCast<int32_t>(), int32_t{4}, count);
    Adds(scratch.upperEndpoint.ReinterpretCast<int32_t>(),
         scratch.upperEndpoint.ReinterpretCast<int32_t>(), int32_t{-4}, count);
    PipeBarrier<PIPE_V>();
    Compare(scratch.masks[2], absX, scratch.lowerEndpoint, CMPMODE::GT, count);
    Compare(scratch.masks[3], absX, scratch.upperEndpoint, CMPMODE::LT, count);
    PipeBarrier<PIPE_V>();
    CompareScalar(scratch.masks[1], scratch.quotient, 0.0f, CMPMODE::EQ, count);
    PipeBarrier<PIPE_V>();
    MaskOr(scratch.masks[2], scratch.masks[2], scratch.masks[1], count);
    CompareScalar(scratch.masks[1], scratch.quotient, 127.0f, CMPMODE::EQ, count);
    PipeBarrier<PIPE_V>();
    MaskOr(scratch.masks[3], scratch.masks[3], scratch.masks[1], count);
    MaskAnd(scratch.masks[4], scratch.masks[2], scratch.masks[3], count);
    MaskAnd(scratch.masks[4], scratch.masks[4], scratch.masks[0], count);
    Not(scratch.masks[5].ReinterpretCast<uint16_t>(),
        scratch.masks[4].ReinterpretCast<uint16_t>(), count / 16);
    PipeBarrier<PIPE_V>();

    // Minimal upstream-compatible counter-mode GatherMask. Gate exact mask
    // count/order for count=64/1792; no assumption that syntax proves behavior.
    CreateVecIndex(scratch.indices, int32_t{0}, count);
    PipeBarrier<PIPE_V>();
    GatherMaskParams params;
    params.repeatTimes = 1;
    params.src0BlockStride = 1;
    params.src0RepeatStride = 8;
    params.src1RepeatStride = 8;
    uint64_t retained = 0;
    GatherMask(scratch.compactIndices, scratch.indices,
        scratch.masks[5].ReinterpretCast<uint32_t>(), true, count, params, retained);
    // Explicit same-site pair approved after full audit SYNC-02 candidate.
    // The previous helper contains this identical V_S Fetch/Set/Wait body;
    // preserve the barrier semantics while exposing the producer-consumer seam.
    const event_t gatherToScalar = static_cast<event_t>(
        GetTPipePtr()->FetchEventID(HardEvent::V_S));
    SetFlag<HardEvent::V_S>(gatherToScalar);
    WaitFlag<HardEvent::V_S>(gatherToScalar);
    if (retained > count) { return {0, false}; }
    bool valid = true;
    for (uint32_t item = 0; item < static_cast<uint32_t>(retained); ++item) {
        const int32_t lane = scratch.compactIndices.GetValue(item);
        if (lane < 0 || static_cast<uint32_t>(lane) >= count) {
            valid = false;
            continue;
        }
        const Result result = ExactCode(
            rawX.ReinterpretCast<uint32_t>().GetValue(lane),
            scratch.broadcastScales.ReinterpretCast<uint32_t>().GetValue(lane));
        codes.SetValue(lane, result.code);
        valid = valid && result.valid;
    }
    WaitScalarToVector();
    return {static_cast<uint32_t>(retained), valid};
}
} // namespace Qwen36DampQuantizer
#endif
