"""Device-free tests for the BF16-compute ModelOpt reference adapter."""

from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QWEN38_ENABLE_BF16_REFERENCE", "1")

import torch

from qwen38_nvfp4_ascend.adapter import (
    AscendBf16ReferenceFp8LinearMethod,
    AscendBf16ReferenceMixedConfig,
    AscendBf16ReferenceNvFp4LinearMethod,
    QUANTIZATION_NAME,
    decode_fp8_weight,
    decode_nvfp4_weight,
)
from nvfp4_codec import dequantize_nvfp4


class ReferenceDecoderTest(unittest.TestCase):
    def test_nvfp4_preserves_low_nibble_first_and_partition_scales(self):
        packed = torch.tensor(
            [[0x21] * 8, [0x98] * 8, [0x76] * 8], dtype=torch.uint8
        )
        local = torch.tensor(
            [[1.0], [2.0], [0.5]], dtype=torch.float8_e4m3fn
        )
        global_scale = torch.tensor([3.0, 5.0], dtype=torch.float32)
        actual = decode_nvfp4_weight(
            packed,
            local,
            global_scale,
            [2, 1],
            output_dtype=torch.float32,
            rows_per_chunk=1,
        )
        self.assertEqual(tuple(actual.shape), (3, 16))
        self.assertTrue(torch.equal(actual[0, :2], torch.tensor([1.5, 3.0])))
        self.assertTrue(torch.equal(actual[1, :2], torch.tensor([-0.0, -3.0])))
        self.assertTrue(torch.equal(actual[2, :2], torch.tensor([10.0, 15.0])))

        for row, global_value in enumerate((3.0, 3.0, 5.0)):
            expected = dequantize_nvfp4(
                bytes(packed[row].tolist()),
                local[row].float().tolist(),
                global_value,
            )
            self.assertEqual(actual[row].tolist(), expected)

    def test_fp8_preserves_fused_partition_scales(self):
        weight = torch.tensor(
            [[1.0, -2.0], [0.5, 3.0], [-1.0, 2.0]],
            dtype=torch.float8_e4m3fn,
        )
        actual = decode_fp8_weight(
            weight,
            torch.tensor([2.0, 4.0]),
            [1, 2],
            output_dtype=torch.float32,
            rows_per_chunk=1,
        )
        expected = torch.tensor(
            [[2.0, -4.0], [2.0, 12.0], [-4.0, 8.0]]
        )
        self.assertTrue(torch.equal(actual, expected))

    def test_invalid_group_size_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "group size must be 16"):
            decode_nvfp4_weight(
                torch.zeros((1, 8), dtype=torch.uint8),
                torch.ones((1, 1), dtype=torch.float8_e4m3fn),
                torch.ones(1),
                [1],
                output_dtype=torch.bfloat16,
                group_size=32,
            )

    def test_plugin_name_is_explicitly_reference_only(self):
        self.assertIn("bf16_reference", QUANTIZATION_NAME)

    def test_nvfp4_linear_method_replaces_serialized_parameters(self):
        method = AscendBf16ReferenceNvFp4LinearMethod(
            SimpleNamespace(is_checkpoint_nvfp4_serialized=True, group_size=16)
        )
        layer = torch.nn.Module()
        layer.logical_widths = [2, 1]
        layer.register_parameter(
            "weight",
            torch.nn.Parameter(
                torch.tensor(
                    [[0x21] * 8, [0x98] * 8, [0x76] * 8],
                    dtype=torch.uint8,
                ),
                requires_grad=False,
            ),
        )
        layer.register_parameter(
            "weight_scale",
            torch.nn.Parameter(
                torch.tensor(
                    [[1.0], [2.0], [0.5]], dtype=torch.float8_e4m3fn
                ),
                requires_grad=False,
            ),
        )
        layer.register_parameter(
            "weight_scale_2",
            torch.nn.Parameter(torch.tensor([3.0, 5.0]), requires_grad=False),
        )
        layer.register_parameter(
            "input_scale",
            torch.nn.Parameter(torch.ones(2), requires_grad=False),
        )
        method.process_weights_after_loading(layer)
        self.assertEqual(layer.weight.dtype, torch.bfloat16)
        self.assertFalse(hasattr(layer, "weight_scale"))
        self.assertFalse(hasattr(layer, "weight_scale_2"))
        self.assertFalse(hasattr(layer, "input_scale"))
        self.assertEqual(layer.weight[2, :2].float().tolist(), [10.0, 15.0])

    def test_fp8_linear_method_replaces_serialized_parameters(self):
        method = AscendBf16ReferenceFp8LinearMethod(
            SimpleNamespace(is_checkpoint_fp8_serialized=True)
        )
        layer = torch.nn.Module()
        layer.logical_widths = [1, 2]
        layer.register_parameter(
            "weight",
            torch.nn.Parameter(
                torch.tensor(
                    [[1.0, -2.0], [0.5, 3.0], [-1.0, 2.0]],
                    dtype=torch.float8_e4m3fn,
                ),
                requires_grad=False,
            ),
        )
        layer.register_parameter(
            "weight_scale",
            torch.nn.Parameter(torch.tensor([2.0, 4.0]), requires_grad=False),
        )
        layer.register_parameter(
            "input_scale",
            torch.nn.Parameter(torch.ones(2), requires_grad=False),
        )
        method.process_weights_after_loading(layer)
        self.assertEqual(layer.weight.dtype, torch.bfloat16)
        self.assertFalse(hasattr(layer, "weight_scale"))
        self.assertFalse(hasattr(layer, "input_scale"))
        self.assertEqual(
            layer.weight.float().tolist(),
            [[2.0, -4.0], [2.0, 12.0], [-4.0, 8.0]],
        )

    def test_config_requires_explicit_reference_opt_in(self):
        previous = os.environ.pop("QWEN38_ENABLE_BF16_REFERENCE", None)
        try:
            with self.assertRaisesRegex(RuntimeError, "not native"):
                AscendBf16ReferenceMixedConfig(
                    kv_cache_quant_method=None,
                    exclude_modules=[],
                    quantized_layers={},
                    fp8_config=None,
                    nvfp4_config=None,
                    w4a16_nvfp4_config=None,
                )
        finally:
            if previous is not None:
                os.environ["QWEN38_ENABLE_BF16_REFERENCE"] = previous



if __name__ == "__main__":
    unittest.main()
