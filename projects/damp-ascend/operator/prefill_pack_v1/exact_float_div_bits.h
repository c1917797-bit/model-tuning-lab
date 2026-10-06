// SPDX-License-Identifier: Apache-2.0
// DAMP prefill SR transform: correctly rounded binary32 quotient, NOT INT8 code.
// Isolated source preparation; no ASC compilation/NPU performance claim.
#ifndef QWEN36_DAMP_PREFILL_EXACT_FLOAT_DIV_BITS_H
#define QWEN36_DAMP_PREFILL_EXACT_FLOAT_DIV_BITS_H
#include <cstdint>
#include "../quantizer/exact_quantizer_bits.h"
#ifdef DAMP_QUANTIZER_ASCENDC
#define DAMP_F_INLINE __aicore__ inline
#else
#define DAMP_F_INLINE inline
#endif
namespace Qwen36DampPrefill {
using Qwen36DampQuantizer::BitLength;
using Qwen36DampQuantizer::DecodePositive;
struct FloatResult { bool valid; bool finite; uint32_t bits; };
struct Normalized { uint32_t mantissa; int32_t exponent; };
DAMP_F_INLINE Normalized Normalize(uint32_t magnitude)
{
    const auto d = DecodePositive(magnitude);
    const uint32_t shift = 24 - BitLength(d.significand); // nonzero input only
    return {d.significand << shift, d.exponent - static_cast<int32_t>(shift)};
}
// Numerator < 2^48, denominator <= 2^25, quotient < 2^25.
// No scalar integer division instruction or floating arithmetic is required.
DAMP_F_INLINE uint32_t RoundedRatio(uint64_t numerator, uint32_t denominator)
{
    uint32_t quotient = 0;
    for (int32_t bit = 24; bit >= 0; --bit) {
        const uint64_t unit = static_cast<uint64_t>(denominator) << bit;
        if (numerator >= unit) {
            numerator -= unit;
            quotient |= 1U << bit;
        }
    }
    // remainder < denominator <= 2^25; twice remainder cannot overflow.
    const uint64_t twice = numerator << 1;
    if (twice > denominator || (twice == denominator && (quotient & 1U))) {
        ++quotient;
    }
    return quotient;
}
DAMP_F_INLINE FloatResult ExactFloatDiv(uint32_t xBits, uint32_t cBits)
{
    const uint32_t magnitude = xBits & 0x7fffffffU;
    const uint32_t sign = xBits & 0x80000000U;
    if (magnitude >= 0x7f800000U || cBits == 0 || cBits >= 0x7f800000U) {
        return {false, false, 0};
    }
    if (magnitude == 0) { return {true, true, sign}; }
    const auto x = Normalize(magnitude);
    const auto c = Normalize(cBits);
    const int32_t d = x.exponent - c.exponent;
    int32_t exponent = d - (x.mantissa < c.mantissa ? 1 : 0);
    if (exponent > 127) { return {true, false, sign | 0x7f800000U}; }
    uint32_t rounded;
    if (exponent >= -126) {
        const uint32_t shift = static_cast<uint32_t>(d - exponent + 23); // 23/24
        rounded = RoundedRatio(static_cast<uint64_t>(x.mantissa) << shift, c.mantissa);
        if (rounded == 0x1000000U) { rounded >>= 1; ++exponent; }
        if (exponent > 127) { return {true, false, sign | 0x7f800000U}; }
        return {true, true, sign | (static_cast<uint32_t>(exponent + 127) << 23) |
                            (rounded - 0x800000U)};
    }
    // Subnormal target quantum is 2^-149. Mantissa ratio is strictly < 2.
    if (d <= -151) { return {true, true, sign}; }
    const int32_t shift = d + 149; // -1 .. 23 on the remaining subnormal path
    rounded = shift == -1
        ? RoundedRatio(x.mantissa, c.mantissa << 1)
        : RoundedRatio(static_cast<uint64_t>(x.mantissa) << shift, c.mantissa);
    // 0x00800000 is the correctly rounded carry into the minimum normal.
    return {true, true, sign | rounded};
}
DAMP_F_INLINE int32_t CompareDyadic(uint64_t a, int32_t ea, uint64_t b, int32_t eb)
{
    if (a == 0 || b == 0) { return a == b ? 0 : a == 0 ? -1 : 1; }
    const uint32_t la = BitLength(a), lb = BitLength(b);
    const int32_t ta = ea + static_cast<int32_t>(la);
    const int32_t tb = eb + static_cast<int32_t>(lb);
    if (ta != tb) { return ta < tb ? -1 : 1; }
    // Same top exponent: align by significand lengths only, never exponent gaps.
    // Both inputs <= 49 bits, thus shift <= 48 and aligned result < 2^49.
    if (la < lb) { a <<= lb - la; }
    else if (lb < la) { b <<= la - lb; }
    return a < b ? -1 : a > b ? 1 : 0;
}
DAMP_F_INLINE int32_t CompareMidpoint(uint32_t xMagnitude, uint32_t cBits,
                                    uint32_t coefficient, int32_t exponent)
{
    const auto x = DecodePositive(xMagnitude);
    const auto c = DecodePositive(cBits);
    return CompareDyadic(x.significand, x.exponent,
                         static_cast<uint64_t>(coefficient) * c.significand,
                         exponent + c.exponent);
}
// Arbitrary finite FLOAT proposal is certified against exact rounding preimages.
// Does not trust approximate Div, vmul rounding, FTZ, or an error bound.
// This scalar certificate is source-only and default OFF in the future pack seam.
DAMP_F_INLINE bool CertifiesFloat(uint32_t xBits, uint32_t cBits, uint32_t proposalBits)
{
    const uint32_t magnitude = xBits & 0x7fffffffU;
    if (magnitude >= 0x7f800000U || cBits == 0 || cBits >= 0x7f800000U ||
        proposalBits >= 0x7f800000U) { return false; }
    // proposalBits is explicitly a nonnegative magnitude; negative proposals reject.
    const bool even = (proposalBits & 1U) == 0;
    if (proposalBits == 0) {
        return CompareMidpoint(magnitude, cBits, 1, -150) <= 0;
    }
    const auto q = DecodePositive(proposalBits);
    uint32_t lowerCoefficient = 2 * q.significand - 1;
    int32_t lowerExponent = q.exponent - 1;
    const uint32_t rawExponent = proposalBits >> 23;
    // Minimum normal is excluded: its predecessor has the SAME spacing.
    if (rawExponent > 1 && (proposalBits & 0x7fffffU) == 0) {
        lowerCoefficient = 4 * q.significand - 1;
        lowerExponent = q.exponent - 2;
    }
    const int32_t lower = CompareMidpoint(magnitude, cBits,
                                         lowerCoefficient, lowerExponent);
    if (lower < 0 || (lower == 0 && !even)) { return false; }
    // FLTMAX's next rounding boundary leads to infinity. It is odd, so strict.
    const int32_t upper = CompareMidpoint(magnitude, cBits,
                                         2 * q.significand + 1, q.exponent - 1);
    return upper < 0 || (upper == 0 && even);
}
DAMP_F_INLINE FloatResult ExactFloatWithCandidate(uint32_t xBits, uint32_t cBits,
                                                 uint32_t proposalMagnitudeBits)
{
    if (CertifiesFloat(xBits, cBits, proposalMagnitudeBits)) {
        return {true, true, (xBits & 0x80000000U) | proposalMagnitudeBits};
    }
    return ExactFloatDiv(xBits, cBits);
}
} // namespace Qwen36DampPrefill
#undef DAMP_F_INLINE
#endif
