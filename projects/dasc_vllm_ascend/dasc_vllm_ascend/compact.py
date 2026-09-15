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


class CompactCheckpointArena:
    """Fixed-address persistent storage for retained temporal heads.

    The arena owns exactly num_blocks compact rows. Callers keep dense active
    workspaces separately and explicitly pack/unpack at lifecycle boundaries.
    A validity bitmap prevents restoring uninitialized blocks.
    """

    def __init__(
        self,
        *,
        num_blocks: int,
        dense_shape: tuple[int, ...],
        head_axis: int,
        retained_indices: Any,
        dtype: Any,
        device: Any,
    ) -> None:
        import torch

        if num_blocks <= 0:
            raise ValueError("num_blocks must be positive")
        if retained_indices.ndim != 1 or retained_indices.numel() == 0:
            raise ValueError("retained_indices must be a non-empty vector")
        if retained_indices.dtype != torch.long:
            raise ValueError("retained_indices must use torch.long")
        total_heads = dense_shape[head_axis]
        if int(retained_indices.min().item()) < 0:
            raise ValueError("retained head index must be non-negative")
        if int(retained_indices.max().item()) >= total_heads:
            raise ValueError("retained head index exceeds dense head dimension")
        if retained_indices.unique().numel() != retained_indices.numel():
            raise ValueError("retained head indices must be unique")

        self.layout = CompactCheckpointLayout(
            dense_shape=dense_shape,
            head_axis=head_axis,
            retained_heads=retained_indices.numel(),
            element_size=torch.empty((), dtype=dtype).element_size(),
        )
        self.num_blocks = num_blocks
        self.retained_indices = retained_indices.to(device=device)
        self.storage = torch.empty(
            (num_blocks, *self.layout.compact_shape), dtype=dtype, device=device
        )
        self._valid = [False] * num_blocks
        self._storage_ptr = self.storage.data_ptr()

    @property
    def physical_bytes(self) -> int:
        return self.storage.numel() * self.storage.element_size()

    def _check_block(self, block_id: int) -> None:
        if not 0 <= block_id < self.num_blocks:
            raise IndexError(f"block_id {block_id} outside [0, {self.num_blocks})")
        if self.storage.data_ptr() != self._storage_ptr:
            raise RuntimeError("compact checkpoint storage pointer changed")

    def checkpoint(self, block_id: int, dense_state: Any) -> None:
        self._check_block(block_id)
        if tuple(dense_state.shape) != self.layout.dense_shape:
            raise ValueError(
                f"dense shape {tuple(dense_state.shape)} != {self.layout.dense_shape}"
            )
        compact = pack_retained_heads(
            dense_state, self.retained_indices, self.layout.head_axis
        )
        self.storage[block_id].copy_(compact)
        self._valid[block_id] = True

    def restore(self, block_id: int, dense_workspace: Any) -> Any:
        self._check_block(block_id)
        if not self._valid[block_id]:
            raise RuntimeError(f"compact checkpoint block {block_id} is not valid")
        return unpack_retained_heads(
            self.storage[block_id], dense_workspace, self.retained_indices,
            self.layout.head_axis,
        )

    def invalidate(self, block_id: int) -> None:
        self._check_block(block_id)
        self._valid[block_id] = False
