"""Fail-closed BF16-compute reference adapter for ModelOpt mixed precision.

This module deliberately does not claim native NVFP4 or FP8 acceleration on
Ascend 910B4.  It reconstructs the serialized quantized weights exactly and
executes the resulting linear layers through vLLM's unquantized linear method.
Activation quantization is not emulated, so this is a weight-fidelity reference
and an accuracy upper bound, not the final quantized runtime.
"""

from __future__ import annotations

import os
from collections.abc import Sequence

import torch
from torch.nn import Parameter

from vllm.model_executor.layers.quantization import register_quantization_config
from vllm.model_executor.layers.quantization.modelopt import (
    Attention,
    LinearBase,
    ModelOptFp8LinearMethod,
    ModelOptKVCacheMethod,
    ModelOptMixedPrecisionConfig,
    ModelOptNvFp4LinearMethod,
    ParallelLMHead,
    RoutedExperts,
)
from vllm.model_executor.layers.linear import (
    UnquantizedLinearMethod,
)


QUANTIZATION_NAME = "modelopt_mixed_ascend_bf16_reference"
_ENABLE_ENV = "QWEN38_ENABLE_BF16_REFERENCE"
_NVFP4_GROUP_SIZE = 16
_E2M1 = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0,
         -0.0, -0.5, -1.0, -1.5, -2.0, -3.0, -4.0, -6.0)


def _require_reference_opt_in() -> None:
    if os.environ.get(_ENABLE_ENV) != "1":
        raise RuntimeError(
            f"{QUANTIZATION_NAME} is a BF16-compute reference, not native "
            "NVFP4/FP8 acceleration. Set "
            f"{_ENABLE_ENV}=1 only for explicit reference validation."
        )


def _row_scales(
    scales: torch.Tensor,
    logical_widths: Sequence[int],
    output_rows: int,
) -> torch.Tensor:
    flat = scales.reshape(-1).to(dtype=torch.float32)
    widths = tuple(int(width) for width in logical_widths)
    if sum(widths) != output_rows:
        raise ValueError(
            f"logical widths sum to {sum(widths)}, expected {output_rows}"
        )
    if flat.numel() == 1:
        return flat.expand(output_rows)
    if flat.numel() != len(widths):
        raise ValueError(
            f"expected one scale or {len(widths)} partition scales, "
            f"got {flat.numel()}"
        )
    return torch.cat(
        [flat[index].expand(width) for index, width in enumerate(widths)]
    )


def decode_nvfp4_weight(
    packed: torch.Tensor,
    local_scales: torch.Tensor,
    global_scales: torch.Tensor,
    logical_widths: Sequence[int],
    *,
    output_dtype: torch.dtype,
    group_size: int = _NVFP4_GROUP_SIZE,
    rows_per_chunk: int = 256,
) -> torch.Tensor:
    """Decode ModelOpt packed NVFP4 weights without merging shard scales."""
    if packed.dtype != torch.uint8 or packed.ndim != 2:
        raise ValueError("packed NVFP4 weight must be a rank-2 uint8 tensor")
    if local_scales.ndim != 2:
        raise ValueError("NVFP4 local scales must be rank 2")
    if group_size != _NVFP4_GROUP_SIZE:
        raise ValueError(f"ModelOpt NVFP4 group size must be 16, got {group_size}")
    if rows_per_chunk <= 0:
        raise ValueError("rows_per_chunk must be positive")

    output_rows, packed_columns = packed.shape
    input_columns = packed_columns * 2
    expected_scale_shape = (output_rows, input_columns // group_size)
    if input_columns % group_size or tuple(local_scales.shape) != expected_scale_shape:
        raise ValueError(
            f"local scale shape {tuple(local_scales.shape)} does not match "
            f"expected {expected_scale_shape}"
        )
    if not torch.isfinite(local_scales.float()).all():
        raise ValueError("NVFP4 local scales must be finite")
    if not torch.isfinite(global_scales.float()).all():
        raise ValueError("NVFP4 global scales must be finite")

    per_row_global = _row_scales(
        global_scales, logical_widths, output_rows
    ).reshape(-1, 1)
    lookup = torch.tensor(_E2M1, dtype=torch.float32, device=packed.device)
    decoded = torch.empty(
        (output_rows, input_columns), dtype=output_dtype, device=packed.device
    )

    for start in range(0, output_rows, rows_per_chunk):
        end = min(start + rows_per_chunk, output_rows)
        chunk = packed[start:end]
        values = torch.empty(
            (end - start, input_columns),
            dtype=torch.float32,
            device=packed.device,
        )
        values[:, 0::2] = lookup[(chunk & 0x0F).long()]
        values[:, 1::2] = lookup[(chunk >> 4).long()]
        scale = (
            local_scales[start:end]
            .float()
            .repeat_interleave(group_size, dim=1)
        )
        values.mul_(scale).mul_(per_row_global[start:end])
        decoded[start:end].copy_(values.to(output_dtype))
    return decoded.contiguous()


def decode_fp8_weight(
    weight: torch.Tensor,
    weight_scales: torch.Tensor,
    logical_widths: Sequence[int],
    *,
    output_dtype: torch.dtype,
    rows_per_chunk: int = 256,
) -> torch.Tensor:
    """Decode per-tensor ModelOpt FP8 weights with per-fused-shard scales."""
    if weight.ndim != 2 or weight.dtype != torch.float8_e4m3fn:
        raise ValueError("FP8 weight must be rank-2 torch.float8_e4m3fn")
    if rows_per_chunk <= 0:
        raise ValueError("rows_per_chunk must be positive")
    if not torch.isfinite(weight_scales.float()).all():
        raise ValueError("FP8 weight scales must be finite")

    output_rows = weight.shape[0]
    per_row_scale = _row_scales(
        weight_scales, logical_widths, output_rows
    ).reshape(-1, 1)
    decoded = torch.empty_like(weight, dtype=output_dtype)
    for start in range(0, output_rows, rows_per_chunk):
        end = min(start + rows_per_chunk, output_rows)
        values = weight[start:end].float() * per_row_scale[start:end]
        decoded[start:end].copy_(values.to(output_dtype))
    return decoded.contiguous()


class _Bf16ReferenceMixin:
    def __init__(self) -> None:
        self._linear = UnquantizedLinearMethod()

    def apply(
        self,
        layer: torch.nn.Module,
        x: torch.Tensor,
        bias: torch.Tensor | None = None,
    ) -> torch.Tensor:
        return self._linear.apply(layer, x, bias)


class AscendBf16ReferenceNvFp4LinearMethod(
    _Bf16ReferenceMixin, ModelOptNvFp4LinearMethod
):
    def __init__(self, quant_config) -> None:
        _Bf16ReferenceMixin.__init__(self)
        self.quant_config = quant_config

    def process_weights_after_loading(self, layer: torch.nn.Module) -> None:
        decoded = decode_nvfp4_weight(
            layer.weight.data,
            layer.weight_scale.data,
            layer.weight_scale_2.data,
            layer.logical_widths,
            output_dtype=torch.bfloat16,
            group_size=self.quant_config.group_size,
        )
        layer.weight = Parameter(decoded, requires_grad=False)
        del layer.weight_scale
        del layer.weight_scale_2
        if hasattr(layer, "input_scale"):
            del layer.input_scale


class AscendBf16ReferenceFp8LinearMethod(
    _Bf16ReferenceMixin, ModelOptFp8LinearMethod
):
    def __init__(self, quant_config) -> None:
        _Bf16ReferenceMixin.__init__(self)
        self.quant_config = quant_config

    def process_weights_after_loading(self, layer: torch.nn.Module) -> None:
        decoded = decode_fp8_weight(
            layer.weight.data,
            layer.weight_scale.data,
            layer.logical_widths,
            output_dtype=torch.bfloat16,
        )
        layer.weight = Parameter(decoded, requires_grad=False)
        del layer.weight_scale
        if hasattr(layer, "input_scale"):
            del layer.input_scale


@register_quantization_config(QUANTIZATION_NAME)
class AscendBf16ReferenceMixedConfig(ModelOptMixedPrecisionConfig):
    """ModelOpt resolver with explicit BF16-compute reference methods."""

    def __init__(self, *args, **kwargs) -> None:
        _require_reference_opt_in()
        super().__init__(*args, **kwargs)

    def get_name(self) -> str:
        return QUANTIZATION_NAME

    @classmethod
    def get_min_capability(cls) -> int:
        return 0

    def get_quant_method(self, layer: torch.nn.Module, prefix: str):
        if isinstance(layer, Attention):
            if self.kv_cache_quant_method:
                return ModelOptKVCacheMethod(self)
            return None
        if self.is_layer_excluded(prefix):
            if isinstance(layer, (LinearBase, ParallelLMHead)):
                return UnquantizedLinearMethod()
            return None

        quant_algo = self._resolve_quant_algo(prefix)
        if isinstance(layer, (LinearBase, ParallelLMHead)):
            if quant_algo == "FP8":
                return AscendBf16ReferenceFp8LinearMethod(self.fp8_config)
            if quant_algo in ("NVFP4", "W4A16_NVFP4"):
                return AscendBf16ReferenceNvFp4LinearMethod(self.nvfp4_config)
            if quant_algo is None:
                return UnquantizedLinearMethod()
            raise ValueError(
                f"unsupported ModelOpt algorithm {quant_algo!r} for {prefix}"
            )
        if isinstance(layer, RoutedExperts):
            raise ValueError(
                "The BF16 reference adapter supports dense Qwen3.8 layers only"
            )
        if quant_algo is not None:
            raise ValueError(
                f"quantized mapping {prefix} resolved to non-linear "
                f"layer type {type(layer).__name__}"
            )
        return None


def register() -> None:
    """vLLM general-plugin entry point; registration occurs at import time."""
