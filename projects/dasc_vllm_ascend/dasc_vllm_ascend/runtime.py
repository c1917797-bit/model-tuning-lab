"""Atomic DASC cache lifecycle for one Ascend GDN layer."""

from __future__ import annotations

from typing import Any

import torch

from .compact import CompactCheckpointArena, FullCheckpointArena


class ActiveStateBridge:
    """Bridge compact persistent checkpoints to fixed dense active workspaces.

    Temporal and convolution states are deliberately managed together.  A
    caller must restore before invoking the native GDN operator and checkpoint
    after it returns.  Prefix block copies and invalidation affect both arenas.
    """

    def __init__(
        self,
        *,
        num_blocks: int,
        max_active_blocks: int,
        conv_shape: tuple[int, ...],
        temporal_shape: tuple[int, ...],
        temporal_head_axis: int,
        retained_indices: Any,
        conv_dtype: Any,
        temporal_dtype: Any,
        device: Any,
    ) -> None:
        if max_active_blocks <= 0:
            raise ValueError("max_active_blocks must be positive")
        self.max_active_blocks = max_active_blocks
        self.conv = FullCheckpointArena(
            num_blocks=num_blocks,
            state_shape=conv_shape,
            dtype=conv_dtype,
            device=device,
        )
        self.temporal = CompactCheckpointArena(
            num_blocks=num_blocks,
            dense_shape=temporal_shape,
            head_axis=temporal_head_axis,
            retained_indices=retained_indices,
            dtype=temporal_dtype,
            device=device,
        )
        self.conv_workspace = torch.empty(
            (max_active_blocks, *conv_shape), dtype=conv_dtype, device=device
        )
        self.temporal_workspace = torch.empty(
            (max_active_blocks, *temporal_shape),
            dtype=temporal_dtype,
            device=device,
        )
        self._conv_ptr = self.conv_workspace.data_ptr()
        self._temporal_ptr = self.temporal_workspace.data_ptr()
        self._active_block_ids = None

    @property
    def physical_checkpoint_bytes(self) -> int:
        return self.conv.physical_bytes + self.temporal.physical_bytes

    def restore_active(self, block_ids: Any) -> tuple[Any, Any]:
        if self._active_block_ids is not None:
            raise RuntimeError("an active bridge transaction is already open")
        if block_ids.ndim != 1 or block_ids.numel() > self.max_active_blocks:
            raise ValueError("active block vector exceeds fixed workspace capacity")
        if block_ids.unique().numel() != block_ids.numel():
            raise ValueError("active block ids must be unique")
        if (
            self.conv_workspace.data_ptr() != self._conv_ptr
            or self.temporal_workspace.data_ptr() != self._temporal_ptr
        ):
            raise RuntimeError("active workspace pointer changed")
        count = block_ids.numel()
        conv = self.conv_workspace[:count]
        temporal = self.temporal_workspace[:count]
        self.conv.restore_many(block_ids, conv)
        self.temporal.restore_many(block_ids, temporal)
        self._active_block_ids = block_ids
        return conv, temporal

    def checkpoint_active(self) -> None:
        if self._active_block_ids is None:
            raise RuntimeError("no active bridge transaction")
        block_ids = self._active_block_ids
        count = block_ids.numel()
        try:
            self.conv.checkpoint_many(block_ids, self.conv_workspace[:count])
            self.temporal.checkpoint_many(
                block_ids, self.temporal_workspace[:count]
            )
        finally:
            self._active_block_ids = None

    def abort_active(self) -> None:
        self._active_block_ids = None

    def copy_blocks(self, source_block_ids: Any, destination_block_ids: Any) -> None:
        if self._active_block_ids is not None:
            raise RuntimeError("cannot copy blocks during an active transaction")
        self.conv.copy_many(source_block_ids, destination_block_ids)
        self.temporal.copy_many(source_block_ids, destination_block_ids)

    def invalidate(self, block_ids: Any) -> None:
        if self._active_block_ids is not None:
            raise RuntimeError("cannot invalidate during an active transaction")
        self.conv.invalidate_many(block_ids)
        self.temporal.invalidate_many(block_ids)
