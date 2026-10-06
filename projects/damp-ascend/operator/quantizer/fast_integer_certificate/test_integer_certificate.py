# SPDX-License-Identifier: Apache-2.0
"""CPU mathematical/software contracts ONLY; no Docker, C++ build or NPU."""
import hashlib
import json
import random
import sys
from fractions import Fraction
from pathlib import Path
from integer_certificate import coefficient, tables, floor_endpoint, certificate, restore_sign, limb_boundaries

FROZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FROZEN))
from test_exact_quantizer import exact_fraction, half_bits, oracle
from probe_fixtures import build_fixtures, fixture_sha

def threshold_independent(j):
    t = half_bits(j)
    # Independent FP32 neighboring values, no coefficient/C limb helper.
    return ((exact_fraction(t-1)+exact_fraction(t))/2 if j & 1 else
            (exact_fraction(t)+exact_fraction(t+1))/2)

def power2(e):
    return Fraction(1 << e) if e >= 0 else Fraction(1, 1 << -e)

def normal_floor_fraction(value):
    f = value.numerator.bit_length()-value.denominator.bit_length()
    if value < power2(f):
        f -= 1
    if not -126 <= f <= 127:
        return None
    shifted = value/power2(f-23)
    mant = shifted.numerator//shifted.denominator
    assert (1 << 23) <= mant < (1 << 24)
    return ((f+127) << 23)+(mant-(1 << 23))

def run():
    # Bind immutable imported mathematical oracle/fixtures.
    expected = {
        "test_exact_quantizer.py": "b1c9d10bf9e24e095fe048235693e426f5437be27a9e21b39503bd7825a50c3d",
        "probe_fixtures.py": "a4ce599438c7d0e325e78f7d22f51fa1c4f1133d9904dfcd12b3a48696763bf0"}
    for name, digest in expected.items():
        assert hashlib.sha256((FROZEN/name).read_bytes()).hexdigest() == digest
    table = tables()
    assert len(table) == 128 and table[-1] == table[-2]
    for j in range(127):
        c, f = coefficient(j)
        assert Fraction(c)*power2(f-24) == threshold_independent(j)
    mantissas = (0, 1, 2, 4094, 4095, 4096, 4097, 0x3ffffe, 0x3fffff,
                 0x7ffffd, 0x7ffffe, 0x7fffff)
    checked = outside = 0
    for e in range(1, 255):
        for frac in mantissas:
            sb = (e << 23)+frac
            ms = (1 << 23)+frac
            for j in range(127):
                c, _ = coefficient(j)
                limbs = limb_boundaries(ms, c)
                assert sum(v << (12*i) for i, v in enumerate(limbs)) == ms*c
                domain, actual = floor_endpoint(sb, j)
                gold = normal_floor_fraction(exact_fraction(sb)*threshold_independent(j))
                assert domain == (gold is not None)
                if domain:
                    assert actual == gold, (hex(sb), j, hex(actual), hex(gold))
                else:
                    outside += 1
                checked += 1
    rows = build_fixtures(2048)
    proposals = accepted = 0
    for i, row in enumerate(rows):
        x, s, code = row["x_bits"], row["scale_bits"], row["code"]
        n = abs(code)
        candidates = {0, 127, n, max(0, n-1), min(127, n+1), i % 128}
        if i % 257 == 0:
            candidates = range(128)  # all arbitrary proposals on labeled samples
        for n in candidates:
            ok = certificate(x, s, n)
            if ok:
                assert row["valid"] and restore_sign(x, n) == code, (row, n)
                accepted += 1
            proposals += 1
    rng = random.Random(0xDA4C2026)
    # Arbitrary proposals stress rejection independent of any Div error bound.
    random_pairs = 10000
    random_accepts = 0
    for _ in range(random_pairs):
        x, s, n = rng.randrange(1 << 32), rng.randrange(1 << 32), rng.randrange(128)
        ok = certificate(x, s, n)
        if ok:
            valid, code = oracle(x, s)
            assert valid and restore_sign(x, n) == code, (hex(x), hex(s), n)
            random_accepts += 1
    # Explicit saved failure, zero/sign, endpoint and subnormal domains.
    assert not certificate(0xbd05a10e, 0x39919209, 117)
    assert certificate(0xbd05a10e, 0x39919209, 118)
    for x in (0, 0x80000000):
        assert certificate(x, 0x3f800000, 0) and restore_sign(x, 0) == 0
    for s in (1, 2, 0x007fffff):
        for n in (0, 1, 126, 127):
            assert not certificate(0, s, n)
    for n in (-1, 128):
        try:
            certificate(0, 0x3f800000, n)
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-range candidate did not reject")
    print(json.dumps({
        "status": "software_math_pass", "product_floor_cases": checked,
        "non_normal_endpoint_cases": outside, "fixture_rows": len(rows),
        "fixture_sha256": fixture_sha(rows), "candidate_certificates": proposals,
        "accepted_certificates": accepted, "unsafe_acceptances": 0,
        "arbitrary_random_pairs": random_pairs, "random_acceptances": random_accepts,
        "saved_step45_wrong117_rejected_correct118_accepted": True,
        "cxx_compiled": False, "asc_compiled": False, "npu_executed": False,
        "fallback_fraction_is_diagnostic_not_throughput": True}, sort_keys=True))

if __name__ == "__main__":
    run()

