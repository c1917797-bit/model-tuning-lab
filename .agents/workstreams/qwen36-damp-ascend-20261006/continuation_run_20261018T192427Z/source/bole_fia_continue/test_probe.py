"""Twenty stdlib CPU controls. No tensor, TorchNPU, model or device import."""
import tempfile
import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TEMP_ROOT = Path(os.environ.get('TMPDIR', str(HERE)))
import plan as R
import probe as P


def good_rows():
    return [dict(branch=branch, role='baseline', primary=None, operator_completed=True,
                 transfer_and_inputs_unchanged=True, original_failure_sets_reproduced=True,
                 whole_output=dict(bitwise_equal=True, elements=count))
            for branch, count in (('tree', 4608), ('native', 1536))]


class Controls(unittest.TestCase):
    def test_all_bf16_words_match(self):
        result = P.words_comparison([0, 32768, 1, 65535], [0, 32768, 1, 65535])
        self.assertTrue(result['bitwise_equal'])
        self.assertEqual(result['bitwise_equal_elements'], 4)

    def test_signed_zero_is_not_bitwise_equal(self):
        self.assertEqual(P.words_comparison([0], [32768])['different_flat_indices'], [0])

    def test_full_vector_not_only_old_failure_point(self):
        expected = [0]*1536
        actual = expected.copy()
        actual[1535] = 1
        result = P.words_comparison(actual, expected)
        self.assertFalse(result['bitwise_equal'])
        self.assertEqual(result['different_flat_indices'], [1535])

    def test_bad_bf16_vector_rejected(self):
        for left, right in (([], []), ([1], [1, 2]), ([True], [1]), ([-1], [0]), ([65536], [0])):
            with self.assertRaises(ValueError):
                P.words_comparison(left, right)

    def test_unchanged_pointwise_boundary(self):
        self.assertTrue(P.pointwise([0.001], [0.0])['pointwise_pass'])
        self.assertFalse(P.pointwise([0.001001], [0.0])['pointwise_pass'])

    def test_full_failure_set_and_exact_mean(self):
        result = P.pointwise([1.0, 2.2, 3.0], [1.0, 2.0, 3.0])
        self.assertEqual(result['failed_flat_indices'], [1])
        self.assertEqual(result['elements'], 3)
        self.assertEqual(P.pointwise([2.0], [2.0])['relative_l2'], 0.0)

    def test_nonfinite_reference_or_actual_rejected(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                P.pointwise([value], [0.0])
            with self.assertRaises(ValueError):
                P.pointwise([0.0], [value])

    def test_original_full_tree_parameters(self):
        value = R.call_parameters('tree')
        self.assertEqual(value['actual_seq_lengths'], [3])
        self.assertEqual(value['actual_seq_lengths_kv'], [134])
        self.assertEqual((value['sparse_mode'], value['inner_precise'], value['block_size']), (1, 2, 128))
        self.assertEqual((value['scale'], value['input_layout']), (0.0625, 'BNSD'))

    def test_original_native_omitted_arguments_stay_omitted(self):
        value = R.call_parameters('native')
        self.assertEqual(value['actual_seq_lengths'], [1])
        self.assertEqual(value['actual_seq_lengths_kv'], [133])
        self.assertEqual((value['sparse_mode'], value['inner_precise']), (0, 0))
        self.assertFalse({'atten_mask', 'block_table', 'block_size'} & set(value))

    def test_two_valid_single_parameter_interventions(self):
        for branch in ('tree', 'native'):
            original = R.call_parameters(branch)
            changed = R.call_parameters(branch, True)
            delta = P.parameter_delta(original, changed)
            self.assertEqual({delta['original'], delta['changed']}, {0, 2})
            self.assertIsNone(delta['numeric_semantics'])
            self.assertEqual(R.call_parameters(branch), original)

    def test_second_parameter_change_rejected(self):
        original = R.call_parameters('tree')
        changed = R.call_parameters('tree', True)
        changed['sparse_mode'] = 0
        with self.assertRaises(ValueError):
            P.parameter_delta(original, changed)

    def test_added_argument_same_value_or_bool_rejected(self):
        original = R.call_parameters('native')
        for changed in (dict(R.call_parameters('native', True), atten_mask=None),
                        dict(original), dict(original, inner_precise=True)):
            with self.assertRaises(ValueError):
                P.parameter_delta(original, changed)

    def test_both_complete_baselines_admit(self):
        self.assertTrue(P.baseline_gate(good_rows()))

    def test_one_baseline_mismatch_blocks_both_interventions(self):
        rows = good_rows()
        rows[0]['whole_output']['bitwise_equal'] = False
        self.assertFalse(P.baseline_gate(rows))

    def test_missing_original_failure_or_transfer_blocks(self):
        for field in ('original_failure_sets_reproduced', 'transfer_and_inputs_unchanged'):
            rows = good_rows()
            rows[1][field] = False
            self.assertFalse(P.baseline_gate(rows))

    def test_incomplete_or_exception_baseline_blocks(self):
        rows = good_rows()
        self.assertFalse(P.baseline_gate(rows[:1]))
        rows[1]['primary'] = {'error': 'unsupported operator parameter'}
        self.assertFalse(P.baseline_gate(rows))
        rows = good_rows()
        rows[0]['whole_output']['elements'] = 1536
        self.assertFalse(P.baseline_gate(rows))

    def test_fixed_plan_preserves_three_frames_and_failure(self):
        value = R.expected()
        self.assertEqual(len(value['cases']), 3)
        self.assertEqual([case['original_failed_flat_indices'] for case in value['cases']], [[573], [573], []])
        self.assertEqual(len(value['input_readset']), 9)
        self.assertEqual(value['cutoff'], 1792437867)
        self.assertFalse(value['qualified'])
        self.assertTrue(value['original_failures_unchanged'])
        self.assertIsNone(value['inner_precise_numeric_semantics'])

    def test_exact_reference_and_drift(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            path = Path(directory)/'receipt.json'
            path.write_bytes(b'{}\n')
            reference = R.ref(path)
            self.assertEqual(R.checked(reference), path)
            path.write_bytes(b'[]\n')
            with self.assertRaises(ValueError):
                R.checked(reference)

    def test_symlink_and_untyped_reference_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as directory:
            path = Path(directory)/'receipt.json'
            path.write_bytes(b'{}\n')
            reference = R.ref(path)
            alias = Path(directory)/'alias.json'
            alias.symlink_to(path)
            with self.assertRaises(ValueError):
                R.checked(dict(reference, path=str(alias)))
            with self.assertRaises(ValueError):
                R.checked(dict(reference, bytes=True))

    def test_cutoff_and_actual_arm_fail_closed(self):
        with patch('probe.time.time', return_value=1792437866):
            P.deadline(1792437867)
            for value in (1792437868, 1792437866, float('nan')):
                with self.assertRaises(ValueError):
                    P.deadline(value)
        with self.assertRaisesRegex(ValueError, 'MAIN_ARM'):
            P.run({}, {}, '/never-created', work_deadline=1792437867)


if __name__ == '__main__':
    unittest.main()
