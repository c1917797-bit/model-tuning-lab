"""Pure-CPU controls: analytical positives, negatives and precision boundaries."""
import math
import unittest
import probe as P


class Controls(unittest.TestCase):
    def test_equal_logit_mean(self):
        p = P.probabilities64([0.0, 0.0], [[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(P.pv64(p, [[1.0, 3.0], [3.0, 5.0]]), [2.0, 4.0])

    def test_nonzero_logits_use_fixed_scale(self):
        p = P.probabilities64([16.0], [[0.0], [1.0]])
        self.assertAlmostEqual(p[1], math.exp(1)/(1+math.exp(1)), places=15)

    def test_compensated_cancellation(self):
        self.assertEqual(P.pv64([1.0, 1.0, 1.0], [[1e16], [1.0], [-1e16]]), [1.0])

    def test_nearest_even_midpoint_and_both_sides(self):
        for sign in (1, -1):
            for value in (1.0, 1.00390625, 1.00390625+2**-30, 1.00390625-2**-30):
                _, represented = P.nearest_bf16(sign*value)
                expected = min(abs(value-y) for y in (1.0, 1.0078125))
                self.assertEqual(abs(represented-sign*value), expected)
            self.assertEqual(P.nearest_bf16(sign*1.00390625)[1], sign*1.0)
            self.assertEqual(P.nearest_bf16(sign*1.01171875)[1], sign*1.015625)

    def test_signed_zero_bits_preserved(self):
        self.assertEqual(P.nearest_bf16(0.0)[0], 0)
        self.assertEqual(P.nearest_bf16(-0.0)[0], 0x8000)
        self.assertEqual(P.actual_comparison([0.0], [-0.0])['bitwise_equal_elements'], 0)

    def test_nonfinite_rejected(self):
        for value in (float('inf'), -float('inf'), float('nan'), 3.4e38):
            with self.assertRaises(ValueError):
                P.nearest_bf16(value)

    def test_bad_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            P.probabilities64([1.0, 2.0], [[1.0]])
        with self.assertRaises(ValueError):
            P.pv64([1.0], [[1.0], [2.0]])

    def test_exact_probability_no_arm_difference(self):
        result = P.evaluate_paths([[0.0]], [[0.0], [0.0]], [[1.0], [3.0]], [[2.0]])
        self.assertEqual(result['original_actual']['failed_elements'], 0)
        self.assertEqual(result['intervention_changed_output_elements'], 0)
        self.assertEqual(result['probability_bf16']['actual']['bitwise_equal_elements'], 1)

    def test_probability_rounding_is_not_renormalized(self):
        result = P.evaluate_paths([[0.0]], [[0.0]]*3, [[1.0], [1.0], [3.0]], [[1.671875]])
        self.assertFalse(result['renormalized_after_probability_rounding'])
        self.assertEqual(result['probability_heads'][0]['probability_bf16_sum'], 1.001953125)
        self.assertEqual(result['intervention_changed_output_elements'], 1)
        self.assertEqual(result['probability_bf16']['actual']['bitwise_equal_elements'], 1)
        self.assertEqual(result['final_only_bf16']['actual']['bitwise_equal_elements'], 0)

    def test_wrong_output_preserves_failure(self):
        result = P.evaluate_paths([[0.0]], [[0.0], [0.0]], [[1.0], [1.0]], [[2.0]])
        self.assertEqual(result['original_actual']['failed_elements'], 1)
        self.assertEqual(result['final_only_bf16']['reference']['failed_elements'], 0)
        self.assertFalse(result['failed_points'][0]['intervention_exact_actual_bits'])

    def test_unchanged_pointwise_gate_boundary(self):
        self.assertEqual(P.reference_comparison([0.001], [0.0])['failed_elements'], 0)
        self.assertEqual(P.reference_comparison([0.001001], [0.0])['failed_elements'], 1)

    def test_nonrepresentable_input_rejected(self):
        with self.assertRaisesRegex(ValueError, 'finite BF16'):
            P.evaluate_paths([[0.1]], [[0.0]], [[1.0]], [[1.0]])


if __name__ == '__main__':
    unittest.main()
