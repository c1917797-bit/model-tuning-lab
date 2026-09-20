import unittest

from ssm_tp_ascend.runtime import _is_gdn_out_proj, _sample_call


class RuntimeProbeTest(unittest.TestCase):
    def test_only_gdn_output_projection_is_selected(self):
        self.assertTrue(
            _is_gdn_out_proj("model.layers.3.linear_attn.out_proj")
        )
        self.assertFalse(_is_gdn_out_proj("model.layers.3.self_attn.o_proj"))
        self.assertFalse(_is_gdn_out_proj("model.layers.3.mlp.down_proj"))

    def test_call_sampling_is_bounded(self):
        selected = [value for value in range(1, 34) if _sample_call(value)]
        self.assertEqual(selected, [1, 2, 3, 4, 8, 16, 32])


if __name__ == "__main__":
    unittest.main()
