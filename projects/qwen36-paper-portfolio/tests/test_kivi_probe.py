"""Small-shape contract tests; not Ascend performance or accuracy evidence."""

import unittest

import torch

from qwen36_kivi_probe.patch import (
    _kivi_k,
    _kivi_v,
    _native_compatible_k,
    _native_compatible_v,
    _quant_dequant,
)


class KiviProbeTest(unittest.TestCase):
    def test_asymmetric_group_equation_and_constant_group(self):
        x = torch.tensor([[0.0, 1.0, 2.0, 3.0], [7.0, 7.0, 7.0, 7.0]])
        out, zeros = _quant_dequant(x)
        self.assertEqual(zeros, 1)
        self.assertTrue(torch.equal(out, x))

    def test_key_groups_follow_tokens_value_groups_follow_channels(self):
        x = torch.arange(259 * 256, dtype=torch.float32).reshape(259, 256)
        key, k_length, _ = _kivi_k(x)
        value, v_length, _ = _kivi_v(x)
        self.assertEqual(k_length, 256)
        self.assertEqual(v_length, 131)
        self.assertEqual(tuple(key.shape), tuple(x.shape))
        self.assertEqual(tuple(value.shape), tuple(x.shape))
        self.assertTrue(torch.equal(key[k_length:], x[k_length:]))
        self.assertTrue(torch.equal(value[v_length:], x[v_length:]))
        native_key, _ = _native_compatible_k(x, k_length)
        native_value, _ = _native_compatible_v(x, v_length)
        self.assertTrue(torch.equal(native_key[k_length:], x[k_length:]))
        self.assertTrue(torch.equal(native_value[v_length:], x[v_length:]))


if __name__ == "__main__":
    unittest.main()
