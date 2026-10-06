// SPDX-License-Identifier: Apache-2.0
// NEW draft: not in any frozen SOURCE_NAMES or production build.
// Public API only. The float Div proposer and exact fallback are caller-owned.
#pragma once
#include "kernel_operator.h"
#if !defined(__NPU_ARCH__) || __NPU_ARCH__ != 2201
#error "This unvalidated certificate draft targets dav-2201 only"
#endif

namespace qwen36_damp_integer_certificate {
using I = AscendC::LocalTensor<int32_t>;
__aicore__ inline AscendC::LocalTensor<uint32_t> U(const I& v)
{
    return v.ReinterpretCast<uint32_t>();
}

// Pre: w[2]=raw abs-scale exponent; w[8]=M0; w[9]=M1;
// w[4]=CLAMPED logical j0..126; cTable/fTable immutable128-entry INT32 UB.
// Post: w[5]=safe positive normal floor bits; w[7]=endpoint-normal flag0/1.
// Scratch w[4..7,10..15]; preserves w[0..3,8,9].
template<int32_t N>
__aicore__ inline void EndpointFloor(const I& cTable, const I& fTable, I (&w)[16])
{
    static_assert(N >= 64 && N <= 896 && N % 64 == 0);
    AscendC::ShiftLeft(U(w[4]), U(w[4]), uint32_t(2), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Gather(w[5], cTable, U(w[4]), uint32_t(0), uint32_t(N));
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Gather(w[15], fTable, U(w[4]), uint32_t(0), uint32_t(N));
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[7]), U(w[5]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftLeft(U(w[6]), U(w[7]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Sub(w[6], w[5], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[7], w[7], int32_t(-4096), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[10], w[8], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[11], w[8], w[7], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[14], w[9], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[11], w[11], w[14], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[14]), U(w[10]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[11], w[11], w[14], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[12], w[9], w[7], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[12], w[12], w[8], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[14]), U(w[11]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[12], w[12], w[14], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[14]), U(w[12]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[13], w[14], w[9], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftLeft(U(w[14]), U(w[14]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Sub(w[12], w[12], w[14], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[14]), U(w[13]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftLeft(U(w[10]), U(w[13]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[10], w[10], w[12], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftLeft(U(w[11]), U(w[13]), uint32_t(11), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[6]), U(w[12]), uint32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[11], w[11], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Sub(w[11], w[11], w[10], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[11], w[11], w[14], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[10], w[10], w[11], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[15], w[15], w[2], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[15], w[15], w[14], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[6], w[15], int32_t(-1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[6]), U(w[6]), uint32_t(31), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Duplicate(w[7], int32_t(254), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Sub(w[7], w[7], w[15], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[7]), U(w[7]), uint32_t(31), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[7], w[7], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Muls(w[7], w[7], int32_t(-1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[7], w[7], int32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Maxs(w[5], w[15], int32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mins(w[5], w[5], int32_t(254), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftLeft(U(w[5]), U(w[5]), uint32_t(23), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[10], w[10], int32_t(-8388608), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[5], w[5], w[10], N);
    AscendC::PipeBarrier<PIPE_V>();
}

// Pre: magnitude is sanitized INT32 n0..127 BEFORE any gather (not trusted
// for correctness); raw inputs and tables have 32B alignment and no overlap
// with w[0..15]/accepted, all scratch planes mutually disjoint. Input/LUT
// MTE2->V readiness must be established by caller's TQue DeQue. No cold H2D.
// Post: accepted0/1 proves exact code magnitude n for the target
// clip(RNE_integer(RN32(x/s))). Restore sign from original x raw bits.
// All shifts are UINT32 logical, <=31; arithmetic bounds are in README.
// This function does not write state/output/GM and does not call scalar GetValue.
template<int32_t N>
__aicore__ inline void Certify(const I& accepted, const I& xBits,
    const I& scaleBits, const I& magnitude, const I& cTable,
    const I& fTable, I (&w)[16])
{
    static_assert(N >= 64 && N <= 896 && N % 64 == 0);
    AscendC::ShiftLeft(U(w[0]), U(xBits), uint32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[0]), U(w[0]), uint32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftLeft(U(w[1]), U(scaleBits), uint32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[1]), U(w[1]), uint32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[2]), U(w[1]), uint32_t(23), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftLeft(U(w[3]), U(w[2]), uint32_t(23), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Sub(w[3], w[1], w[3], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[3], w[3], int32_t(8388608), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[9]), U(w[3]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftLeft(U(w[8]), U(w[9]), uint32_t(12), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Sub(w[8], w[3], w[8], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[4], magnitude, int32_t(-1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Maxs(w[4], w[4], int32_t(0), N);
    AscendC::PipeBarrier<PIPE_V>();
    EndpointFloor<N>(cTable, fTable, w);
    AscendC::Sub(w[4], w[5], w[0], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[4]), U(w[4]), uint32_t(31), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[4], w[4], w[7], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mins(w[6], magnitude, int32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Muls(w[6], w[6], int32_t(-1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[6], w[6], int32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(accepted, w[4], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mins(accepted, accepted, int32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mins(w[4], magnitude, int32_t(126), N);
    AscendC::PipeBarrier<PIPE_V>();
    EndpointFloor<N>(cTable, fTable, w);
    AscendC::Sub(w[4], w[0], w[5], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[4]), U(w[4]), uint32_t(31), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[4], w[4], w[7], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[6], magnitude, int32_t(-126), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Maxs(w[6], w[6], int32_t(0), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Add(w[4], w[4], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mins(w[4], w[4], int32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(accepted, accepted, w[4], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[4]), U(scaleBits), uint32_t(31), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Muls(w[4], w[4], int32_t(-1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[4], w[4], int32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[6], w[1], int32_t(-8388608), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[6]), U(w[6]), uint32_t(31), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Muls(w[6], w[6], int32_t(-1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[6], w[6], int32_t(1), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[4], w[4], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[6], w[1], int32_t(-2139095040), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[6]), U(w[6]), uint32_t(31), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[4], w[4], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Adds(w[6], w[0], int32_t(-2139095040), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::ShiftRight(U(w[6]), U(w[6]), uint32_t(31), N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(w[4], w[4], w[6], N);
    AscendC::PipeBarrier<PIPE_V>();
    AscendC::Mul(accepted, accepted, w[4], N);
    AscendC::PipeBarrier<PIPE_V>();
}
} // namespace qwen36_damp_integer_certificate

