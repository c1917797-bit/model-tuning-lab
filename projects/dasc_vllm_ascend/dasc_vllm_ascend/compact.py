"""Physical retained-head checkpoint primitives for DASC.

The active recurrent state remains dense because the native Ascend GDN ABI
expects a fixed head dimension.  Only persistent prefix checkpoints are
compact.  These helpers deliberately keep that distinction explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Any


@dataclass(frozen=True)
class CompactCheckpointLayout:
    dense_shape: tuple[int, ...]
    head_axis: int
    retained_heads: int
    element_size: int

    def __post_init__(self) -> None:
        if not self.dense_shape or any(size <= 0 for size in self.dense_shape):
            raise ValueError("dense_shape must contain only positive dimensions")
        if not 0 <= self.head_axis < len(self.dense_shape):
            raise ValueError("head_axis is outside dense_shape")
        total_heads = self.dense_shape[self.head_axis]
        if not 0 < self.retained_heads <= total_heads:
            raise ValueError("retained_heads must be in (0, total_heads]")
        if self.element_size <= 0:
            raise ValueError("element_size must be positive")

    @property
    def total_heads(self) -> int:
        return self.dense_shape[self.head_axis]

    @property
    def compact_shape(self) -> tuple[int, ...]:
        shape = list(self.dense_shape)
        shape[self.head_axis] = self.retained_heads
        return tuple(shape)

    @property
    def dense_bytes(self) -> int:
        return prod(self.dense_shape) * self.element_size

    @property
    def compact_bytes(self) -> int:
        return prod(self.compact_shape) * self.element_size

    @property
    def compression_ratio(self) -> float:
        return self.dense_bytes / self.compact_bytes


def pack_retained_heads(
    dense_state: Any, retained_indices: Any, head_axis: int
) -> Any:
    """Gather retained heads into contiguous physical checkpoint storage."""
    if retained_indices.ndim != 1:
        raise ValueError("retained_indices must be one-dimensional")
    if retained_indices.numel() == 0:
        raise ValueError("at least one retained head is required")
    return dense_state.index_select(head_axis, retained_indices).contiguous()


def unpack_retained_heads(
    compact_state: Any,
    dense_state: Any,
    retained_indices: Any,
    head_axis: int,
) -> Any:
    """Restore a compact checkpoint into a zero-filled dense GDN workspace."""
    if retained_indices.ndim != 1:
        raise ValueError("retained_indices must be one-dimensional")
    expected = list(dense_state.shape)
    expected[head_axis] = retained_indices.numel()
    if tuple(compact_state.shape) != tuple(expected):
        raise ValueError(
            f"compact shape {tuple(compact_state.shape)} != expected {tuple(expected)}"
        )
    dense_state.zero_()
    dense_state.index_copy_(head_axis, retained_indices, compact_state)
    return dense_state
