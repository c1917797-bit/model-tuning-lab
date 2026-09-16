"""Atomic DASC cache lifecycle for one Ascend GDN layer."""

from __future__ import annotations

from typing import Any

import torch

from .compact import (
    CompactCheckpointArena,
    FullCheckpointArena,
    pack_retained_heads,
    unpack_retained_heads,
)


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


class BoundActiveStateBridge:
    """Expand runner-owned compact cache tensors for the dense native ABI.

    Unlike ActiveStateBridge, persistent storage is supplied by vLLM's cache
    allocator. Consequently scheduler block copy and invalidation continue to
    operate on the authoritative tensors instead of a plugin side arena.
    """

    def __init__(
        self,
        *,
        conv_storage: Any,
        compact_temporal_storage: Any,
        dense_temporal_shape: tuple[int, ...],
        temporal_head_axis: int,
        retained_indices: Any,
        max_active_blocks: int,
    ) -> None:
        if max_active_blocks <= 0:
            raise ValueError("max_active_blocks must be positive")
        if conv_storage.ndim < 2 or compact_temporal_storage.ndim < 2:
            raise ValueError("runner cache tensors must include a block axis")
        if conv_storage.shape[0] != compact_temporal_storage.shape[0]:
            raise ValueError("conv and temporal cache block counts differ")
        if retained_indices.ndim != 1 or retained_indices.dtype != torch.long:
            raise ValueError("retained_indices must be a torch.long vector")
        if not 0 <= temporal_head_axis < len(dense_temporal_shape):
            raise ValueError("temporal_head_axis outside dense shape")
        compact_shape = list(dense_temporal_shape)
        compact_shape[temporal_head_axis] = retained_indices.numel()
        if tuple(compact_temporal_storage.shape[1:]) != tuple(compact_shape):
            raise ValueError("runner temporal cache does not match compact geometry")

        self.conv_storage = conv_storage
        self.temporal_storage = compact_temporal_storage
        self.dense_temporal_shape = dense_temporal_shape
        self.temporal_head_axis = temporal_head_axis
        self.retained_indices = retained_indices.to(
            device=compact_temporal_storage.device
        )
        self.max_active_blocks = max_active_blocks
        self.conv_workspace = torch.empty(
            (max_active_blocks, *conv_storage.shape[1:]),
            dtype=conv_storage.dtype,
            device=conv_storage.device,
        )
        self.temporal_workspace = torch.empty(
            (max_active_blocks, *dense_temporal_shape),
            dtype=compact_temporal_storage.dtype,
            device=compact_temporal_storage.device,
        )
        self._conv_storage_ptr = conv_storage.data_ptr()
        self._temporal_storage_ptr = compact_temporal_storage.data_ptr()
        self._conv_workspace_ptr = self.conv_workspace.data_ptr()
        self._temporal_workspace_ptr = self.temporal_workspace.data_ptr()
        self._active_ids = None

    @property
    def persistent_bytes(self) -> int:
        return (
            self.conv_storage.numel() * self.conv_storage.element_size()
            + self.temporal_storage.numel()
            * self.temporal_storage.element_size()
        )

    @property
    def workspace_cache(self) -> tuple[Any, Any]:
        """Return the one fixed-address dense cache tuple used by native GDN.

        The tuple and both tensors are intentionally stable for the lifetime of
        the bridge. Active rows occupy the prefix selected by _active_ids;
        unused rows must never be referenced by remapped metadata.
        """
        cache = getattr(self, "_workspace_cache", None)
        if cache is None:
            cache = (self.conv_workspace, self.temporal_workspace)
            self._workspace_cache = cache
        return cache

    def _check_pointers(self) -> None:
        pointers = (
            self.conv_storage.data_ptr(),
            self.temporal_storage.data_ptr(),
            self.conv_workspace.data_ptr(),
            self.temporal_workspace.data_ptr(),
        )
        expected = (
            self._conv_storage_ptr,
            self._temporal_storage_ptr,
            self._conv_workspace_ptr,
            self._temporal_workspace_ptr,
        )
        if pointers != expected:
            raise RuntimeError("bound cache or active workspace pointer changed")

    def restore_active(self, block_ids: Any) -> tuple[Any, Any]:
        if self._active_ids is not None:
            raise RuntimeError("an active bridge transaction is already open")
        if block_ids.ndim != 1 or block_ids.numel() > self.max_active_blocks:
            raise ValueError("active block vector exceeds fixed workspace capacity")
        ids = block_ids.to(device=self.conv_storage.device, dtype=torch.long)
        if ids.numel() and (
            int(ids.min().item()) < 0
            or int(ids.max().item()) >= self.conv_storage.shape[0]
        ):
            raise IndexError("active block id outside runner cache")
        if ids.unique().numel() != ids.numel():
            raise ValueError("active block ids must be unique")
        self._check_pointers()
        count = ids.numel()
        conv = self.conv_workspace[:count]
        temporal = self.temporal_workspace[:count]
        conv.copy_(self.conv_storage.index_select(0, ids))
        compact = self.temporal_storage.index_select(0, ids)
        unpack_retained_heads(
            compact,
            temporal,
            self.retained_indices,
            self.temporal_head_axis + 1,
        )
        self._active_ids = ids
        # Native GDN is permanently bound to the full, fixed-address
        # workspaces. Metadata restricts execution to the populated prefix.
        return self.workspace_cache

    def checkpoint_active(self) -> None:
        if self._active_ids is None:
            raise RuntimeError("no active bridge transaction")
        ids = self._active_ids
        count = ids.numel()
        self._check_pointers()
        try:
            self.conv_storage.index_copy_(0, ids, self.conv_workspace[:count])
            compact = pack_retained_heads(
                self.temporal_workspace[:count],
                self.retained_indices,
                self.temporal_head_axis + 1,
            )
            self.temporal_storage.index_copy_(0, ids, compact)
        finally:
            self._active_ids = None

    def abort_active(self) -> None:
        self._active_ids = None
