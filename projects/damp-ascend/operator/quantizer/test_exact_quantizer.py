#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stdlib mathematical contract test. Optional --harness checks compiled C++.
No device/build action. No files written. This is NOT NPU or performance evidence.
"""
import argparse
import json
import random
import subprocess
from fractions import Fraction

MAX_FINITE_BITS = 0x7F7FFFFF
FIXTURE = (0xBD05A10E, 0x39919209)
SCALES = (1, 0x007FFFFF, 0x00800000, 0x2B8CBCCC, 0x39919209,
          0x3F800000, 0x7C010203, MAX_FINITE_BITS)

def dyadic(bits):
    frac = bits & 0x7FFFFF
    exponent = bits >> 23
    return (frac, -149) if exponent == 0 else (
        frac | 0x800000, exponent - 150)

def exact_fraction(bits):
    m, e = dyadic(bits)
    return Fraction(m << e, 1) if e >= 0 else Fraction(m, 1 << -e)

def round_ratio_to_f32(numerator, denominator):
    """Independent exact rational -> IEEE RN32. Returns positive raw bits."""
    if numerator == 0:
        return 0
    e = numerator.bit_length() - denominator.bit_length()
    if (numerator < (denominator << e) if e >= 0
            else (numerator << -e) < denominator):
        e -= 1
    if e > 127:
        return 0x7F800000
    quantum = max(e - 23, -149)
    n, d = (numerator, denominator << quantum) if quantum >= 0 else (
        numerator << -quantum, denominator)
    mantissa, remainder = divmod(n, d)
    twice = remainder * 2
    if twice > d or (twice == d and (mantissa & 1)):
        mantissa += 1
    if mantissa == 0:
        return 0
    # Exact rounded mantissa * 2**quantum -> canonical FP32 bits.
    top_e = mantissa.bit_length() - 1 + quantum
    if top_e > 127:
        return 0x7F800000
    if top_e < -126:
        return mantissa << (quantum + 149)
    length = mantissa.bit_length()
    significand = (mantissa << (24-length) if length <= 24
                   else mantissa >> (length-24))
    return ((top_e + 127) << 23) | (significand & 0x7FFFFF)

def oracle(x_bits, scale_bits):
    ax = x_bits & 0x7FFFFFFF
    if ax >= 0x7F800000 or not 0 < scale_bits < 0x7F800000:
        return False, 0
    x, scale = exact_fraction(ax), exact_fraction(scale_bits)
    ratio = x / scale
    rounded_bits = round_ratio_to_f32(ratio.numerator, ratio.denominator)
    if rounded_bits == 0x7F800000:
        code = 127
    else:
        rounded = exact_fraction(rounded_bits)
        base, remainder = divmod(rounded.numerator, rounded.denominator)
        twice = remainder * 2
        code = base + (twice > rounded.denominator or
                       (twice == rounded.denominator and bool(base & 1)))
        code = min(code, 127)
    return True, -code if x_bits & 0x80000000 else code

def compare_transition(ax_bits, scale_bits, j):
    mx, ex = dyadic(ax_bits)
    if mx == 0:
        return -1
    ms, es = dyadic(scale_bits)
    k = 2*j + 1
    f = k.bit_length()-2
    c = (k << (23-f)) + (-1 if j & 1 else 1)
    product = ms*c
    ep = es+f-24
    lx, lp = mx.bit_length(), product.bit_length()
    hx, hp = ex+lx, ep+lp
    if hx != hp:
        return -1 if hx < hp else 1
    aligned_x = mx << (lp-lx)
    return (aligned_x > product) - (aligned_x < product)

def crosses(compare, j):
    return compare > 0 or (compare == 0 and bool(j & 1))

def exact_bin_model(x_bits, scale_bits):
    ax = x_bits & 0x7FFFFFFF
    if ax >= 0x7F800000 or not 0 < scale_bits < 0x7F800000:
        return False, 0
    lower, upper = 0, 127
    while lower < upper:
        j = (lower+upper)//2
        if crosses(compare_transition(ax, scale_bits, j), j):
            lower = j+1
        else:
            upper = j
    return True, -lower if x_bits & 0x80000000 else lower

def mul_f32_bits(left_bits, right_bits):
    product = exact_fraction(left_bits) * exact_fraction(right_bits)
    return round_ratio_to_f32(product.numerator, product.denominator)

def half_bits(j):
    half = Fraction(2*j+1, 2)
    return round_ratio_to_f32(half.numerator, half.denominator)

def fast_certificate(x_bits, scale_bits, magnitude):
    """Math model assumes exact RN32 Mul, not unverified device vMul."""
    ax = x_bits & 0x7FFFFFFF
    if (ax >= 0x7F800000 or not 0x00800000 <= scale_bits <= MAX_FINITE_BITS
            or not 0 <= magnitude <= 127):
        return False
    lo = mul_f32_bits(half_bits(max(magnitude, 1)-1), scale_bits)
    hi = mul_f32_bits(half_bits(min(magnitude, 126)), scale_bits)
    if not (0x00800000 <= lo <= MAX_FINITE_BITS and
            0x00800000 <= hi <= MAX_FINITE_BITS):
        return False
    # Integer bit order equals numeric order for positive finite FP32.
    return ((magnitude == 0 or ax > lo+4) and
            (magnitude == 127 or ax < hi-4))

def fixtures(random_count):
    pairs = [FIXTURE, (0, 1), (0x80000000, 1)]
    for j in range(127):
        t = half_bits(j)
        for scale in SCALES:
            midpoint_product = mul_f32_bits(t, scale)
            if midpoint_product >= 0x7F800000:
                continue
            for delta in range(-4, 5):
                x = midpoint_product+delta
                if 0 <= x <= MAX_FINITE_BITS:
                    pairs.extend(((x, scale), (x | 0x80000000, scale)))
    # Invalids must return invalid, not a code silently presented as correct.
    pairs.extend(((0x7F800000, 0x3F800000), (0x7FC00000, 0x3F800000),
                  (0xFF800000, 0x3F800000), (1, 0), (1, 0x80000000),
                  (1, 0xBF800000), (1, 0x7F800000), (1, 0x7FC00000)))
    rng = random.Random(0xDA4F2026)
    for _ in range(random_count):
        x = rng.randrange(MAX_FINITE_BITS+1) | (rng.randrange(2) << 31)
        scale = rng.randrange(1, MAX_FINITE_BITS+1)
        pairs.append((x, scale))
    return pairs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-count", type=int, default=100000)
    parser.add_argument("--harness", help="Already built, explicitly supplied C++ binary")
    args = parser.parse_args()
    if args.random_count < 0:
        raise ValueError("negative random-count")
    pairs = fixtures(args.random_count)
    expected = [oracle(x, s) for x, s in pairs]
    for i, ((x, s), golden) in enumerate(zip(pairs, expected)):
        actual = exact_bin_model(x, s)
        if actual != golden:
            raise AssertionError(("bin mismatch", i, hex(x), hex(s), actual, golden))
    # Candidate-independent certificate checks arbitrary wrong magnitudes, not
    # only the approximate division's normal output. Exact search stays fallback.
    certified = 0
    for i, ((x, s), golden) in enumerate(zip(pairs, expected)):
        if not golden[0]:
            continue
        choices = {abs(golden[1]), 0, 127, (i*37) % 128}
        for n in choices:
            if fast_certificate(x, s, n):
                certified += 1
                if n != abs(golden[1]):
                    raise AssertionError(("unsafe fast certificate", hex(x), hex(s), n, golden))
    cpp = None
    if args.harness:
        request = "".join(f"{x:08x} {s:08x}\n" for x, s in pairs)
        result = subprocess.run([args.harness], input=request, text=True,
                                capture_output=True, check=True)
        lines = result.stdout.splitlines()
        if len(lines) != len(pairs):
            raise AssertionError(("C++ row count", len(lines), len(pairs)))
        for i, (line, golden) in enumerate(zip(lines, expected)):
            valid, code = map(int, line.split())
            if (bool(valid), code) != golden:
                raise AssertionError(("C++ mismatch", i, pairs[i], line, golden))
        cpp = "pass"
    fixture_code = oracle(*FIXTURE)
    assert fixture_code == (True, -118)
    print(json.dumps({
        "status": "pass", "scope": "stdlib mathematical software only",
        "pairs": len(pairs), "random_pairs": args.random_count,
        "bin_mismatches": 0, "unsafe_fast_certificates": 0,
        "certified_proposals": certified, "fast_mul_model": "exact RN32 assumed, NOT NPU proof",
        "saved_step45_code": fixture_code[1], "cpp_compiled_harness": cpp,
        "npu_executed": False, "production_integrated": False
    }, sort_keys=True))
if __name__ == "__main__":
    main()

