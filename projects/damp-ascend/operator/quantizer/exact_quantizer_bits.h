// SPDX-License-Identifier: Apache-2.0
// Original DAMP-specific exact RN32 division -> integer RNE bin decision.
// Isolated draft: NOT included by the frozen production operator.
#ifndef QWEN36_DAMP_EXACT_QUANTIZER_BITS_H
#define QWEN36_DAMP_EXACT_QUANTIZER_BITS_H
#include <cstdint>
#ifdef DAMP_QUANTIZER_ASCENDC
#include "kernel_operator.h"
#define DAMP_Q_INLINE __aicore__ inline
#else
#define DAMP_Q_INLINE inline
#endif

namespace Qwen36DampQuantizer {
struct Result { bool valid; int32_t code; };

DAMP_Q_INLINE uint32_t BitLength(uint64_t value)
{
#ifdef DAMP_QUANTIZER_ASCENDC
    return value == 0 ? 0 : 64 - AscendC::CountLeadingZero(value);
#else
    uint32_t count = 0;
    while (value != 0) { ++count; value >>= 1; }
    return count;
#endif
}
DAMP_Q_INLINE bool ValidMagnitude(uint32_t bits)
{
    return bits < 0x7f800000U;
}
DAMP_Q_INLINE bool ValidScale(uint32_t bits)
{
    return bits > 0 && bits < 0x7f800000U; // also rejects negative / -0
}
struct Dyadic { uint32_t significand; int32_t exponent; };
DAMP_Q_INLINE Dyadic DecodePositive(uint32_t bits)
{
    const uint32_t rawExponent = bits >> 23;
    return {rawExponent == 0 ? bits & 0x7fffffU
                            : (bits & 0x7fffffU) | 0x800000U,
            rawExponent == 0 ? -149 : static_cast<int32_t>(rawExponent) - 150};
}
// Transition j separates integer outputs j and j+1, 0 <= j <= 126.
// j even: upper code iff x/s > midpoint(t,next(t)); t=j+0.5.
// j odd:  upper code iff x/s >= midpoint(prev(t),t).
// Every t here has an even FP32 significand. C is a positive 25-bit odd
// integer, threshold = C * 2^(floor(log2(t))-24).
DAMP_Q_INLINE int32_t CompareTransition(uint32_t xMagnitudeBits,
                                       uint32_t scaleBits, uint32_t j)
{
    const Dyadic x = DecodePositive(xMagnitudeBits);
    if (x.significand == 0) { return -1; }
    const Dyadic s = DecodePositive(scaleBits);
    const uint32_t twiceT = 2 * j + 1;
    const int32_t tExponent = static_cast<int32_t>(BitLength(twiceT)) - 2;
    const uint32_t center = twiceT << (23 - tExponent);
    const uint32_t thresholdSignificand = (j & 1) ? center - 1 : center + 1;
    const uint64_t product =
        static_cast<uint64_t>(s.significand) * thresholdSignificand; // < 2^49
    const int32_t productExponent = s.exponent + tExponent - 24;
    const uint32_t xLength = BitLength(x.significand);
    const uint32_t productLength = BitLength(product);
    const int32_t xTop = x.exponent + static_cast<int32_t>(xLength);
    const int32_t productTop =
        productExponent + static_cast<int32_t>(productLength);
    if (xTop < productTop) { return -1; }
    if (xTop > productTop) { return 1; }
    // productLength >= 25 > xLength <= 24; shift <= 48; result < 2^49.
    const uint64_t alignedX =
        static_cast<uint64_t>(x.significand) << (productLength - xLength);
    return alignedX < product ? -1 : alignedX > product ? 1 : 0;
}
DAMP_Q_INLINE bool CrossesTransition(int32_t compare, uint32_t j)
{
    return compare > 0 || (compare == 0 && (j & 1) != 0);
}
DAMP_Q_INLINE bool CertifiesMagnitude(uint32_t xMagnitudeBits,
                                      uint32_t scaleBits, uint32_t n)
{
    if (!ValidMagnitude(xMagnitudeBits) || !ValidScale(scaleBits) || n > 127) {
        return false;
    }
    if (n > 0 &&
        !CrossesTransition(CompareTransition(xMagnitudeBits, scaleBits, n-1), n-1)) {
        return false;
    }
    if (n < 127 &&
        CrossesTransition(CompareTransition(xMagnitudeBits, scaleBits, n), n)) {
        return false;
    }
    return true;
}
DAMP_Q_INLINE Result ExactCode(uint32_t xBits, uint32_t scaleBits)
{
    const uint32_t xMagnitude = xBits & 0x7fffffffU;
    if (!ValidMagnitude(xMagnitude) || !ValidScale(scaleBits)) {
        return {false, 0};
    }
    uint32_t lower = 0, upper = 127;
    while (lower < upper) { // at most 7 exact comparisons
        const uint32_t j = (lower + upper) >> 1;
        if (CrossesTransition(CompareTransition(xMagnitude, scaleBits, j), j)) {
            lower = j + 1;
        } else {
            upper = j;
        }
    }
    const int32_t positive = static_cast<int32_t>(lower);
    return {true, (xBits & 0x80000000U) ? -positive : positive};
}
// Arbitrary approximate candidate is optional. Its precision is NOT trusted.
// Two exact integer-bin checks can certify it; otherwise use exact search.
DAMP_Q_INLINE Result ExactWithCandidate(uint32_t xBits, uint32_t scaleBits,
                                        int32_t candidate)
{
    if (candidate >= -127 && candidate <= 127) {
        const uint32_t n =
            static_cast<uint32_t>(candidate < 0 ? -candidate : candidate);
        const bool signMatches = n == 0 ||
            ((candidate < 0) == ((xBits & 0x80000000U) != 0));
        if (signMatches &&
            CertifiesMagnitude(xBits & 0x7fffffffU, scaleBits, n)) {
            return {true, candidate};
        }
    }
    return ExactCode(xBits, scaleBits);
}
} // namespace Qwen36DampQuantizer
#undef DAMP_Q_INLINE
#endif

