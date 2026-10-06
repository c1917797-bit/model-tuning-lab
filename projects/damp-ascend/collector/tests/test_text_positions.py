"""Metadata admission tests; not a real MRoPE/NPU numerical result."""
import unittest
from damp_capture.text_positions import (TEXT_METADATA_SOURCES, decode_lengths,
                                         ordered_text_positions, text_axis, text_request)


class TextPositionsTests(unittest.TestCase):
    def test_six_frozen_source_identities_are_full_sha256(self):
        self.assertEqual(len(TEXT_METADATA_SOURCES), 6)
        for path, value in TEXT_METADATA_SOURCES.items():
            self.assertTrue(path.startswith("/vllm-workspace/"))
            self.assertEqual(len(value), 64)
            int(value, 16)

    def test_native_forward_args_are_not_rewritten(self):
        import ast
        from pathlib import Path
        source = Path(__file__).parents[1] / "damp_capture" / "patch.py"
        tree = ast.parse(source.read_text())
        forward = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "forward")
        calls = [n for n in ast.walk(forward) if isinstance(n, ast.Call) and
                 isinstance(n.func, ast.Name) and n.func.id == "original_forward"]
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertEqual(ast.dump(call.args[0]), ast.dump(ast.Name(id="runner", ctx=ast.Load())))
            self.assertIsInstance(call.args[1], ast.Starred)
            self.assertEqual(call.args[1].value.id, "args")
            self.assertEqual([(k.arg, k.value.id) for k in call.keywords], [(None, "kwargs")])
        # No assignment can target a position Tensor subscript or original kwargs.
        targets = [t for n in ast.walk(forward) if isinstance(n, ast.Assign) for t in n.targets]
        self.assertFalse(any(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and
                             t.value.id in ("positions", "kwargs", "args") for t in targets))

    def test_pure_text_three_rows_exact(self):
        expected = ordered_text_positions([0, 3, 5], [0, 0], 5)
        self.assertEqual(expected, (0, 1, 2, 0, 1))
        self.assertEqual(text_axis([list(expected)] * 3, expected, True), expected)

    def test_mixed_decode_and_prefill_text_order(self):
        expected = ordered_text_positions([0, 1, 4], [85, 0], 4)
        self.assertEqual(text_axis([[85, 0, 1, 2]] * 3, expected, True), (85, 0, 1, 2))

    def test_1d_text_path(self):
        self.assertEqual(text_axis([72, 85], [72, 85], False), (72, 85))

    def test_different_mrope_rows_are_not_flattened(self):
        for rows in ([[0, 1], [0, 2], [0, 1]], [[0, 1]] * 2, [[0, 1]] * 4,
                     [[0, 1]] * 1, [[0, 1.0]] * 3):
            with self.subTest(rows=rows), self.assertRaises(ValueError): text_axis(rows, [0, 1], True)

    def test_equal_rows_wrong_request_order_rejected(self):
        with self.assertRaises(ValueError): text_axis([[85, 72]] * 3, [72, 85], True)

    def test_pure_text_request_prompt_proof(self):
        text_request(3, [], None, None, True, 0, [[0, 1, 2]] * 3)
        text_request(3, [], None, [True] * 3, True, 0, [[0, 1, 2]] * 3)

    def test_nonzero_or_unknown_delta_rejected(self):
        for delta in (1, -1, None, False):
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                text_request(3, [], None, None, True, delta, [[0, 1, 2]] * 3)

    def test_multimodal_or_prompt_embeddings_rejected_even_broadcast(self):
        for features, embeds, mask in (([object()], None, None), ([], object(), None),
                                       ([], None, [True, False, True]), (None, None, None)):
            with self.subTest(features=features), self.assertRaises(ValueError):
                text_request(3, features, embeds, mask, True, 0, [[0, 1, 2]] * 3)

    def test_prompt_positions_nontext_rejected(self):
        with self.assertRaises(ValueError): text_request(3, [], None, None, True, 0, [[1, 2, 3]] * 3)

    def test_cpu_scheduling_cardinality_and_nonempty(self):
        for starts, computed, n in (([0, 1], [0, 0], 1), ([0, 0], [0], 0),
                                     ([1, 2], [0], 2), ([0, 2, 1], [0, 0], 1)):
            with self.subTest(starts=starts), self.assertRaises(ValueError):
                ordered_text_positions(starts, computed, n)

    def test_native_decode_abi_batch1_and16(self):
        for n in (1, 2, 16):
            self.assertEqual(decode_lengths([0] + [1] * n, list(range(n + 1)), list(range(n)), n),
                             (0,) + (1,) * n)

    def test_native_decode_abi_mixed_prefill_tail(self):
        self.assertEqual(decode_lengths([0, 1], [0, 1, 73], [8], 1), (0, 1))

    def test_wrong_cumulative_or_missing_zero_decode_abi_rejected(self):
        for actual in ([1, 2], [0, 1, 2], [0, 1], [0, True, 1]):
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                decode_lengths(actual, [0, 1, 2], [1, 3], 2)

    def test_non_one_token_decode_or_aliased_slots_rejected(self):
        for starts, slots in (([0, 2, 3], [1, 3]), ([0, 1, 2], [1, 1])):
            with self.subTest(starts=starts), self.assertRaises(ValueError):
                decode_lengths([0, 1, 1], starts, slots, 2)


if __name__ == "__main__":
    unittest.main()
