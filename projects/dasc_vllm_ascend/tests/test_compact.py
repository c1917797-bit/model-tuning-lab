import pytest
import torch

from dasc_vllm_ascend.compact import (
    CompactCheckpointLayout,
    CompactCheckpointArena,
    pack_retained_heads,
    unpack_retained_heads,
)


def test_layout_reports_real_physical_bytes():
    layout = CompactCheckpointLayout((12, 128, 128), 0, 8, 4)
    assert layout.compact_shape == (8, 128, 128)
    assert layout.dense_bytes == 12 * 128 * 128 * 4
    assert layout.compact_bytes == 8 * 128 * 128 * 4
    assert layout.compression_ratio == pytest.approx(1.5)


def test_pack_unpack_retains_selected_heads_and_zeros_others():
    dense = torch.arange(2 * 4 * 3, dtype=torch.float32).view(2, 4, 3)
    indices = torch.tensor([0, 3], dtype=torch.long)
    compact = pack_retained_heads(dense, indices, 1)
    workspace = torch.full_like(dense, -1)
    restored = unpack_retained_heads(compact, workspace, indices, 1)
    assert compact.is_contiguous()
    assert torch.equal(restored.index_select(1, indices), compact)
    assert torch.count_nonzero(restored[:, 1:3]).item() == 0


def test_checkpoint_arena_owns_compact_rows_and_tracks_validity():
    indices = torch.tensor([0, 3], dtype=torch.long)
    arena = CompactCheckpointArena(
        num_blocks=3, dense_shape=(4, 3), head_axis=0,
        retained_indices=indices, dtype=torch.float32, device="cpu",
    )
    dense = torch.arange(12, dtype=torch.float32).view(4, 3)
    pointer = arena.storage.data_ptr()
    assert arena.storage.shape == (3, 2, 3)
    assert arena.physical_bytes == 3 * 2 * 3 * 4
    with pytest.raises(RuntimeError, match="not valid"):
        arena.restore(1, torch.empty_like(dense))
    arena.checkpoint(1, dense)
    restored = arena.restore(1, torch.empty_like(dense))
    assert arena.storage.data_ptr() == pointer
    assert torch.equal(restored.index_select(0, indices), dense.index_select(0, indices))
    assert torch.count_nonzero(restored[1:3]).item() == 0
    arena.invalidate(1)
    with pytest.raises(RuntimeError, match="not valid"):
        arena.restore(1, torch.empty_like(dense))


def test_checkpoint_arena_rejects_duplicate_indices():
    with pytest.raises(ValueError, match="unique"):
        CompactCheckpointArena(
            num_blocks=2, dense_shape=(4, 3), head_axis=0,
            retained_indices=torch.tensor([1, 1], dtype=torch.long),
            dtype=torch.float32, device="cpu",
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dense_shape": (12, 128, 128), "head_axis": 3, "retained_heads": 8, "element_size": 4},
        {"dense_shape": (12, 128, 128), "head_axis": 0, "retained_heads": 0, "element_size": 4},
        {"dense_shape": (12, 128, 128), "head_axis": 0, "retained_heads": 13, "element_size": 4},
    ],
)
def test_layout_rejects_unsafe_shapes(kwargs):
    with pytest.raises(ValueError):
        CompactCheckpointLayout(**kwargs)
