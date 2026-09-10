"""Dependency-free reference codec for NVIDIA ModelOpt NVFP4 weights.

This is deliberately a correctness oracle, not the performance kernel.  The
AscendC implementation must match these results before it is benchmarked.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence


NVFP4_GROUP_SIZE = 16
_E2M1_MAGNITUDES = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0)


def decode_e2m1(code: int) -> float:
    """Decode one unsigned nibble containing an E2M1 value."""
    if not 0 <= code <= 0xF:
        raise ValueError(f"E2M1 code must be a nibble, got {code}")
    value = _E2M1_MAGNITUDES[code & 0x7]
    return -value if code & 0x8 else value


def unpack_e2m1(packed: bytes | bytearray | memoryview, count: int | None = None) -> list[float]:
    """Unpack ModelOpt NVFP4 bytes (low nibble first)."""
    available = len(packed) * 2
    if count is None:
        count = available
    if count < 0 or count > available:
        raise ValueError(f"count must be between 0 and {available}, got {count}")

    result: list[float] = []
    for byte in packed:
        result.append(decode_e2m1(byte & 0xF))
        if len(result) == count:
            break
        result.append(decode_e2m1((byte >> 4) & 0xF))
        if len(result) == count:
            break
    return result


def decode_e4m3fn(code: int) -> float:
    """Decode one FP8 E4M3FN byte used by ModelOpt's local block scales."""
    if not 0 <= code <= 0xFF:
        raise ValueError(f"E4M3FN code must be a byte, got {code}")
    sign = -1.0 if code & 0x80 else 1.0
    exponent = (code >> 3) & 0xF
    mantissa = code & 0x7
    if exponent == 0:
        value = math.ldexp(mantissa / 8.0, -6)
    elif exponent == 0xF and mantissa == 0x7:
        return math.nan
    else:
        value = math.ldexp(1.0 + mantissa / 8.0, exponent - 7)
    return sign * value


def decode_e4m3fn_bytes(encoded: bytes | bytearray | memoryview) -> list[float]:
    return [decode_e4m3fn(code) for code in encoded]


def dequantize_nvfp4(
    packed: bytes | bytearray | memoryview,
    local_scales: Sequence[float] | Iterable[float],
    global_scale: float,
    *,
    count: int | None = None,
    group_size: int = NVFP4_GROUP_SIZE,
) -> list[float]:
    """Dequantize a contiguous ModelOpt NVFP4 tensor.

    Each E2M1 value is multiplied by its FP8 E4M3FN block scale and the
    tensor-level FP32 scale.  The official NVIDIA checkpoint contract fixes
    group_size to 16; accepting another value would silently change semantics.
    """
    if group_size != NVFP4_GROUP_SIZE:
        raise ValueError(
            f"ModelOpt NVFP4 requires group_size={NVFP4_GROUP_SIZE}, got {group_size}"
        )
    values = unpack_e2m1(packed, count=count)
    scales = list(local_scales)
    expected_groups = (len(values) + group_size - 1) // group_size
    if len(scales) != expected_groups:
        raise ValueError(
            f"expected {expected_groups} local scales for {len(values)} values, "
            f"got {len(scales)}"
        )
    if not math.isfinite(global_scale):
        raise ValueError("global_scale must be finite")

    return [
        value * scales[index // group_size] * global_scale
        for index, value in enumerate(values)
    ]

