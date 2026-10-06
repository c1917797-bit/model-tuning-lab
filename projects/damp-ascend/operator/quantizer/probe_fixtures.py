# SPDX-License-Identifier: Apache-2.0
"""Raw-bit fixtures; golden uses independent Fraction->RN32->integerRNE."""
import hashlib
import json
import random
from fractions import Fraction
from test_exact_quantizer import (
    MAX_FINITE_BITS, FIXTURE, SCALES, exact_fraction,
    round_ratio_to_f32, half_bits, mul_f32_bits, oracle)

def build_fixtures(random_count=2048):
    if random_count < 0:
        raise ValueError("random-count must be nonnegative")
    rows = []
    def append(label, x, scale):
        valid, code = oracle(x, scale)
        rows.append({"label": label, "x_bits": x, "scale_bits": scale,
                     "valid": int(valid), "code": code})
    append("saved_step45", *FIXTURE)
    scales = tuple(dict.fromkeys((*SCALES, 2, 0x00800001, 0x3F8CCCCD)))
    extremes = (0, 1, 2, 0x007FFFFF, 0x00800000, 0x00800001, MAX_FINITE_BITS)
    for x in extremes:
        for scale in scales:
            for sign in (0, 0x80000000):
                append("extrema_cross", x | sign, scale)
    invalids = ((0x7F800000, 0x3F800000), (0xFF800000, 0x3F800000),
                (0x7FC00000, 0x3F800000), (0xFFC00000, 0x3F800000),
                (1, 0), (1, 0x80000000), (1, 0xBF800000),
                (1, 0x7F800000), (1, 0x7FC00000))
    for x, scale in invalids:
        append("invalid_flag_and_zero_code", x, scale)
    for j in range(127):
        t_bits = half_bits(j)
        t = exact_fraction(t_bits)
        thresholds = (
            ("left_RN32_preimage_midpoint", (exact_fraction(t_bits-1)+t)/2),
            ("right_RN32_preimage_midpoint", (t+exact_fraction(t_bits+1))/2))
        for scale in scales:
            center = mul_f32_bits(t_bits, scale)
            if center <= MAX_FINITE_BITS:
                for delta in range(-4, 5):
                    x = center+delta
                    if 0 <= x <= MAX_FINITE_BITS:
                        for sign in (0, 0x80000000):
                            append(f"integer_half_j{j}_delta{delta}", x | sign, scale)
            for label, threshold in thresholds:
                product = threshold*exact_fraction(scale)
                center = round_ratio_to_f32(product.numerator, product.denominator)
                if center <= MAX_FINITE_BITS:
                    for delta in (-1, 0, 1):
                        x = center+delta
                        if 0 <= x <= MAX_FINITE_BITS:
                            for sign in (0, 0x80000000):
                                append(f"{label}_j{j}_delta{delta}", x | sign, scale)
    rng = random.Random(0xDA4F2026)
    for i in range(random_count):
        append(f"random_{i}", rng.randrange(MAX_FINITE_BITS+1) |
               (rng.randrange(2)<<31), rng.randrange(1, MAX_FINITE_BITS+1))
    return rows

def fixture_sha(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"))
                          .encode()).hexdigest()

def chunk_cases(rows):
    # N64 lifecycle smoke mixes the saved cell, all invalid flags, and spread
    # normal/subnormal/sign/extreme/boundary cases. N1792 covers ALL rows.
    smoke = [rows[0]] + [r for r in rows if r["valid"] == 0]
    stride = max(1, len(rows)//(64-len(smoke)))
    smoke.extend(rows[i] for i in range(0, len(rows), stride))
    smoke = smoke[:64]
    while len(smoke) < 64:
        smoke.append(rows[0])
    cases = [("N64_lifecycle", smoke, len(smoke))]
    for begin in range(0, len(rows), 1792):
        chunk = rows[begin:begin+1792]
        useful = len(chunk)
        chunk += [rows[0]]*(1792-useful)
        cases.append((f"N1792_rows_{begin}_{begin+useful}", chunk, useful))
    return cases

