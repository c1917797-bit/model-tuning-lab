"""Independent table/neighbor oracle checks for the exact BF16 diagnostic."""
import bisect
from itertools import permutations
import random
import unittest

from reduction_math import (
    INF, NAN, add_bf16, bf16_tree_results, exact_sum, is_finite,
    round_scaled, scaled_integer,
)


def table_value(bits):
    # Independent integer encoding of a positive BF16 lookup entry.
    exponent = bits // 128
    fraction = bits % 128
    return fraction if exponent == 0 else (128 + fraction) * 2 ** (exponent - 1)


POSITIVE = [table_value(x) for x in range(INF)]
OVERFLOW_MIDPOINT = (POSITIVE[-1] + 2 ** 261) // 2


def nearest_table(value):
    sign = 0x8000 if value < 0 else 0
    magnitude = abs(value)
    if magnitude >= OVERFLOW_MIDPOINT:
        return sign | INF
    index = bisect.bisect_left(POSITIVE, magnitude)
    if index == len(POSITIVE):
        return sign | (INF - 1)
    if POSITIVE[index] == magnitude:
        return sign | index
    low, high = index - 1, index
    dl, dh = magnitude - POSITIVE[low], POSITIVE[high] - magnitude
    winner = low if dl < dh or (dl == dh and low % 2 == 0) else high
    return sign | winner


class ExactBF16Tests(unittest.TestCase):
    def test_all_finite_words(self):
        for word in range(65536):
            if is_finite(word):
                value = scaled_integer(word)
                self.assertEqual(value, -table_value(word & 0x7FFF) if word & 0x8000
                                 else table_value(word))
                self.assertEqual(round_scaled(value), 0 if word == 0x8000 else word)

    def test_all_representable_midpoints(self):
        checked = 0
        for low in range(INF - 1):
            left, right = POSITIVE[low], POSITIVE[low + 1]
            if (left + right) % 2:
                continue
            middle = (left + right) // 2
            for value in (middle - 1, middle, middle + 1):
                for signed in (value, -value):
                    self.assertEqual(round_scaled(signed), nearest_table(signed))
                    checked += 1
        self.assertGreater(checked, 100000)

    def test_overflow_boundary(self):
        for magnitude in (OVERFLOW_MIDPOINT - 1, OVERFLOW_MIDPOINT,
                          OVERFLOW_MIDPOINT + 1, 2 ** 262):
            for value in (magnitude, -magnitude):
                self.assertEqual(round_scaled(value), nearest_table(value))

    def test_random_sums_against_neighbor_search(self):
        generator = random.Random(20261022)
        finite = [x for x in range(65536) if is_finite(x)]
        for _ in range(5000):
            words = generator.choices(finite, k=4)
            integer = sum((-table_value(x & 0x7FFF) if x & 0x8000
                           else table_value(x)) for x in words)
            self.assertEqual(exact_sum(words), nearest_table(integer))
            self.assertEqual(add_bf16(words[0], words[1]),
                             nearest_table(sum(scaled_integer(x) for x in words[:2])))

    def test_tree_set_against_explicit_120_orders(self):
        cases = (
            (0x3F80, 0x3B80, 0xBF80, 0x3B80),
            (0x7F7F, 0x7F7F, 0xFF7F, 0xFF7F),
            (0, 0x8000, 1, 0x8001),
            (0x3F81, 0xBF80, 0x3B80, 0xBB80),
        )
        for words in cases:
            expected = set()
            for a, b, c, d in permutations(words):
                expected.update((
                    add_bf16(add_bf16(add_bf16(a, b), c), d),
                    add_bf16(add_bf16(a, add_bf16(b, c)), d),
                    add_bf16(add_bf16(a, b), add_bf16(c, d)),
                    add_bf16(a, add_bf16(add_bf16(b, c), d)),
                    add_bf16(a, add_bf16(b, add_bf16(c, d))),
                ))
            self.assertEqual(bf16_tree_results(words), expected)

    def test_cancellation_and_signed_zero(self):
        self.assertEqual(exact_sum((0x3F80, 0xBF80, 1, 1)), 2)
        self.assertEqual(add_bf16(0x8000, 0x8000), 0x8000)
        self.assertEqual(add_bf16(INF, 0xFF80), NAN)
        with self.assertRaises(ValueError):
            exact_sum((INF, 0))
        with self.assertRaises(ValueError):
            bf16_tree_results((0,) * 5)


if __name__ == "__main__":
    unittest.main()
