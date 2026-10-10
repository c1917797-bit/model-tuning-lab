"""Independent old-scalar comparisons; this suite never executes an NPU."""
import hashlib
import importlib.util
import json
import math
import struct
import sys
import time
import unittest
from pathlib import Path

import numpy as np
import fast_oracle as fast

LEGACY = Path(__file__).parent / "legacy_scalar_oracle.py"
LEGACY_SHA = "ab03630d988a2f1fbda7f5f0d880d8eb09afd8451f986d5c3875d8f8422b2782"


def old_oracle():
    if hashlib.sha256(LEGACY.read_bytes()).hexdigest() != LEGACY_SHA:
        raise ValueError("unaltered independent scalar source identity")
    spec = importlib.util.spec_from_file_location("_legacy_independent_oracle", LEGACY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OLD = old_oracle()


def encode(values, dtype):
    if dtype == "float16":
        return np.asarray(values, dtype="<f2").tobytes()
    words = np.asarray(values, dtype="<f4").view("<u4")
    words = words + np.uint32(0x7fff) + ((words >> 16) & np.uint32(1))
    return (words >> 16).astype("<u2").tobytes()


def fixture(length, bits, dtype):
    # Raw random packed words, not candidate quantization. Reversed physical
    # maps, unused guards and nonzero residual slot exercise independent indexing.
    kp = ((length - 1) // 128) * 128
    vp = max(0, length - 65)
    pages, records, slots = kp // 128 + 2, vp + 3, 2
    rng = np.random.default_rng(90210 + length + bits)
    pool = {}
    for name, words, metas in (
        ("key", pages * 128 * 256 * bits // 32, pages * 1024),
        ("value", records * 256 * bits // 32, records * 8),
    ):
        packed = rng.integers(0, 2**32, words, dtype=np.uint32)
        packed[0] = np.uint32(0xffffffff)
        pool[name + "_codes"] = packed.astype("<u4").tobytes()
        pool[name + "_scales"] = encode(rng.uniform(0.001, 0.02, metas), dtype)
        pool[name + "_minima"] = encode(rng.uniform(-0.25, 0.0, metas), dtype)
        cap = 128 if name == "key" else 129
        pool[name + "_residual"] = encode(rng.uniform(-0.5, 0.5, slots * cap * 256), dtype)
    row = {"controls": [length, kp, vp, 1],
           "kp": list(range(kp // 128, 0, -1)), "vp": list(range(vp, 0, -1))}
    qraw = encode(rng.uniform(-0.5, 0.5, 6 * 256), dtype)
    query = [[OLD.scalar(qraw, h * 256 + d, dtype) for d in range(256)] for h in range(6)]
    return pool, row, query


def wire(result, key):
    return b"".join(struct.pack("<d", v) for h in result[key] for v in h)


class ReferenceTests(unittest.TestCase):
    def test_all_raw_a16_values(self):
        raw = np.arange(65536, dtype="<u2").tobytes()
        for dtype in ("float16", "bfloat16"):
            decoded = fast._a16(raw, dtype)
            for i, value in enumerate(decoded):
                expected = OLD.scalar(raw, i, dtype)
                if math.isnan(expected):
                    self.assertTrue(math.isnan(value))
                else:
                    self.assertEqual(struct.pack("<d", value), struct.pack("<d", expected))

    def test_rounding_boundaries(self):
        for dtype in ("float16", "bfloat16"):
            words = np.arange(0, 65536, 13, dtype="<u2").tobytes()
            base = fast._a16(words, dtype)
            base = base[np.isfinite(base) & (np.abs(base) < 60000)]
            values = np.concatenate((base, np.nextafter(base, np.inf), np.nextafter(base, -np.inf)))
            expected = np.array([OLD.cast(float(x), dtype) for x in values])
            actual = fast._cast_array(values, dtype)
            self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_all_decoded_cells(self):
        for bits in (2, 4):
            for dtype in ("float16", "bfloat16"):
                pool, row, _ = fixture(257, bits, dtype)
                for axis in ("K", "V"):
                    actual = fast.decode(pool, row, axis, bits, dtype)
                    expected = np.array([[OLD.decoded(pool, row, axis, t, d, bits, dtype)
                                          for d in range(256)] for t in range(257)])
                    self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_full_attention_all_bits_dtypes_lengths(self):
        for length in (128, 129, 257):
            for bits in (2, 4):
                for dtype in ("float16", "bfloat16"):
                    with self.subTest(length=length, bits=bits, dtype=dtype):
                        pool, row, query = fixture(length, bits, dtype)
                        expected = OLD.attention(pool, row, query, bits, dtype)
                        actual = fast.attention(pool, row, query, bits, dtype)
                        for key in ("scalar_a16_boundary_output", "official_python_split_boundary_output"):
                            self.assertEqual(wire(actual, key), wire(expected, key))

    def test_no_quantized_prefix(self):
        for dtype in ("float16", "bfloat16"):
            pool, row, query = fixture(1, 2, dtype)
            expected = OLD.attention(pool, row, query, 2, dtype)
            actual = fast.attention(pool, row, query, 2, dtype)
            for key in ("scalar_a16_boundary_output", "official_python_split_boundary_output"):
                self.assertEqual(wire(actual, key), wire(expected, key))

    def test_reject_invalid_bounds(self):
        pool, row, query = fixture(129, 2, "float16")
        for bad in ([-1, 128, 64, 1], [129, 127, 64, 1], [129, 128, 64, -1]):
            with self.assertRaises(ValueError):
                fast.attention(pool, dict(row, controls=bad), query, 2, "float16")
        with self.assertRaises((ValueError, IndexError)):
            fast.decode(pool, dict(row, kp=[10000000]), "K", 2, "float16")
        with self.assertRaises(ValueError):
            fast.decode(pool, row, "K", 3, "float16")

    def test_reject_nonfinite_and_extent(self):
        with self.assertRaises(ValueError):
            fast._cast_array([math.nan], "float16")
        with self.assertRaises(ValueError):
            fast.scalar(b"a", 0, "float16")
        with self.assertRaises(ValueError):
            fast.compare([0.0, math.inf], [0.0, 1.0])

    def test_unchanged_tolerance(self):
        self.assertEqual(fast.compare([1.0, 2.0], [1.0, 2.0]), OLD.compare([1.0, 2.0], [1.0, 2.0]))
        with self.assertRaises(ValueError):
            fast.compare([1.01], [1.0])


def long_cost():
    pool, row, query = fixture(32769, 4, "bfloat16")
    start = time.monotonic()
    result = fast.attention(pool, row, query, 4, "bfloat16")
    elapsed = time.monotonic() - start
    for axis in ("K", "V"):
        decoded = fast.decode(pool, row, axis, 4, "bfloat16")
        for token in (0, 31, 127, 128, 16384, 32639, 32704, 32767, 32768):
            for channel in (0, 31, 32, 127, 255):
                assert decoded[token, channel] == OLD.decoded(pool, row, axis, token, channel, 4, "bfloat16")
    print(json.dumps({"schema": "kivi.reference-long-cost/software-only-v1",
                      "length": 32769, "output_elements": 1536, "seconds": elapsed,
                      "output_sha256": hashlib.sha256(wire(result, "scalar_a16_boundary_output")).hexdigest(),
                      "sampled_independent_decode_cells": 90, "full_long_scalar_equivalence": False,
                      "scalar_math_fsum_exp_preserved": True, "NPU_executed": False,
                      "model_pass": False, "performance_pass": False}))


if __name__ == "__main__":
    if sys.argv[1:] == ["--long-cost"]:
        long_cost()
    else:
        unittest.main(verbosity=2)
