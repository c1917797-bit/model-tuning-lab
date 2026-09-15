"""Physical retained-head checkpoint primitives for DASC.

The active recurrent state remains dense because the native Ascend GDN ABI
expects a fixed head dimension.  Only persistent prefix checkpoints are
compact.  These helpers deliberately keep that distinction explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Any

import torch


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
        self._valid = torch.zeros(num_blocks, dtype=torch.bool, device=device)
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
        if not bool(self._valid[block_id].item()):
            raise RuntimeError(f"compact checkpoint block {block_id} is not valid")
        return unpack_retained_heads(
            self.storage[block_id], dense_workspace, self.retained_indices,
            self.layout.head_axis,
        )

    def invalidate(self, block_id: int) -> None:
        self._check_block(block_id)
        self._valid[block_id] = False

    def checkpoint_many(self, block_ids: Any, dense_states: Any) -> None:
        """Pack a batch of dense active slots into persistent block rows."""
        if block_ids.ndim != 1:
            raise ValueError("block_ids must be one-dimensional")
        if tuple(dense_states.shape[1:]) != self.layout.dense_shape:
            raise ValueError("dense_states trailing shape does not match arena layout")
        if dense_states.shape[0] != block_ids.numel():
            raise ValueError("dense_states batch must match block_ids")
        if block_ids.numel() == 0:
            return
        if int(block_ids.min().item()) < 0 or int(block_ids.max().item()) >= self.num_blocks:
            raise IndexError("block_ids outside compact arena")
        if block_ids.unique().numel() != block_ids.numel():
            raise ValueError("block_ids must be unique for checkpoint_many")
        if self.storage.data_ptr() != self._storage_ptr:
            raise RuntimeError("compact checkpoint storage pointer changed")
        compact = pack_retained_heads(
            dense_states, self.retained_indices, self.layout.head_axis + 1
        )
        ids = block_ids.to(device=self.storage.device, dtype=torch.long)
        self.storage.index_copy_(0, ids, compact)
        self._valid.index_fill_(0, ids, True)

    def restore_many(self, block_ids: Any, dense_workspaces: Any) -> Any:
        """Restore live blocks; invalid/new blocks become all-zero workspaces."""
        if block_ids.ndim != 1:
            raise ValueError("block_ids must be one-dimensional")
        if tuple(dense_workspaces.shape[1:]) != self.layout.dense_shape:
            raise ValueError("dense_workspaces trailing shape does not match arena layout")
        if dense_workspaces.shape[0] != block_ids.numel():
            raise ValueError("dense_workspaces batch must match block_ids")
        if block_ids.numel() == 0:
            return dense_workspaces
        if int(block_ids.min().item()) < 0 or int(block_ids.max().item()) >= self.num_blocks:
            raise IndexError("block_ids outside compact arena")
        ids = block_ids.to(device=self.storage.device, dtype=torch.long)
        compact = self.storage.index_select(0, ids)
        valid = self._valid.index_select(0, ids)
        broadcast = valid.view(valid.shape[0], *([1] * len(self.layout.compact_shape)))
        compact = torch.where(broadcast, compact, torch.zeros_like(compact))
        return unpack_retained_heads(
            compact, dense_workspaces, self.retained_indices,
            self.layout.head_axis + 1,
        )

    def invalidate_many(self, block_ids: Any) -> None:
        if block_ids.ndim != 1:
            raise ValueError("block_ids must be one-dimensional")
        if block_ids.numel() == 0:
            return
        ids = block_ids.to(device=self.storage.device, dtype=torch.long)
        self._valid.index_fill_(0, ids, False)


@dataclass(frozen=True)
class ActiveSlotPlan:
    """Vectorized mapping from scheduler block ids to dense workspace slots."""

    block_ids: Any
    remapped_indices: tuple[Any, ...]

    @property
    def num_slots(self) -> int:
        return self.block_ids.numel()


def build_active_slot_plan(*index_tensors: Any, pad_slot_id: int = -1) -> ActiveSlotPlan:
    """Map all live scheduler block ids to contiguous active slot ids.

    PAD entries remain PAD. The implementation stays tensor-only so the later
    NPU integration does not require a device-to-host list conversion.
    """
    if not index_tensors:
        raise ValueError("at least one state-index tensor is required")
    device = index_tensors[0].device
    dtype = index_tensors[0].dtype
    if any(t.device != device or t.dtype != dtype for t in index_tensors):
        raise ValueError("all state-index tensors must share device and dtype")
    flattened = torch.cat([tensor.reshape(-1) for tensor in index_tensors])
    live = flattened[flattened != pad_slot_id]
    block_ids = torch.unique(live, sorted=True)
    remapped = []
    for tensor in index_tensors:
        live_mask = tensor != pad_slot_id
        safe = torch.where(live_mask, tensor, torch.zeros_like(tensor))
        slots = torch.searchsorted(block_ids, safe)
        remapped.append(
            torch.where(live_mask, slots.to(dtype=dtype), torch.full_like(tensor, pad_slot_id))
        )
    return ActiveSlotPlan(block_ids=block_ids, remapped_indices=tuple(remapped))
