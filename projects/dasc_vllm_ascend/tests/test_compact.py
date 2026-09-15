import pytest
import torch

from dasc_vllm_ascend.compact import (
    CompactCheckpointLayout,
    CompactCheckpointArena,
    FullCheckpointArena,
    build_active_slot_plan,
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


def test_checkpoint_arena_vectorized_lifecycle():
    retained = torch.tensor([0, 2], dtype=torch.long)
    arena = CompactCheckpointArena(
        num_blocks=8, dense_shape=(4, 2), head_axis=0,
        retained_indices=retained, dtype=torch.float32, device="cpu",
    )
    blocks = torch.tensor([6, 2, 5], dtype=torch.int32)
    dense = torch.arange(3 * 4 * 2, dtype=torch.float32).view(3, 4, 2)
    arena.checkpoint_many(blocks, dense)
    restored = arena.restore_many(blocks, torch.empty_like(dense))
    assert torch.equal(restored.index_select(1, retained), dense.index_select(1, retained))
    omitted = torch.tensor([1, 3], dtype=torch.long)
    assert torch.count_nonzero(restored.index_select(1, omitted)).item() == 0

    new_block = torch.tensor([7], dtype=torch.int32)
    new_state = arena.restore_many(new_block, torch.full((1, 4, 2), 9.0))
    assert torch.count_nonzero(new_state).item() == 0
    arena.invalidate_many(torch.tensor([2, 6], dtype=torch.int32))
    invalid = arena.restore_many(
        torch.tensor([2, 6], dtype=torch.int32), torch.full((2, 4, 2), 9.0)
    )
    assert torch.count_nonzero(invalid).item() == 0


def test_compact_arena_prefix_copy_propagates_payload_and_validity():
    retained = torch.tensor([1, 3], dtype=torch.long)
    arena = CompactCheckpointArena(
        num_blocks=6, dense_shape=(4, 2), head_axis=0,
        retained_indices=retained, dtype=torch.float32, device="cpu",
    )
    dense = torch.arange(8, dtype=torch.float32).view(1, 4, 2)
    arena.checkpoint_many(torch.tensor([1]), dense)
    arena.copy_many(torch.tensor([1, 4]), torch.tensor([3, 5]))
    restored = arena.restore_many(
        torch.tensor([3, 5]), torch.full((2, 4, 2), -1.0)
    )
    assert torch.equal(restored[0].index_select(0, retained), dense[0].index_select(0, retained))
    assert torch.count_nonzero(restored[1]).item() == 0


def test_full_checkpoint_arena_lifecycle_and_copy():
    arena = FullCheckpointArena(
        num_blocks=5, state_shape=(2, 3), dtype=torch.float32, device="cpu"
    )
    payload = torch.arange(6, dtype=torch.float32).view(1, 2, 3)
    arena.checkpoint_many(torch.tensor([1]), payload)
    arena.copy_many(torch.tensor([1]), torch.tensor([4]))
    restored = arena.restore_many(torch.tensor([4]), torch.empty_like(payload))
    assert torch.equal(restored, payload)
    arena.invalidate_many(torch.tensor([4]))
    assert torch.count_nonzero(
        arena.restore_many(torch.tensor([4]), torch.full_like(payload, 9))
    ).item() == 0


def test_active_slot_plan_is_contiguous_and_preserves_padding():
    decode = torch.tensor([[17], [4], [-1]], dtype=torch.int32)
    prefill = torch.tensor([9, 17], dtype=torch.int32)
    plan = build_active_slot_plan(decode, prefill, pad_slot_id=-1)
    assert torch.equal(plan.block_ids, torch.tensor([4, 9, 17], dtype=torch.int32))
    assert plan.num_slots == 3
    assert torch.equal(
        plan.remapped_indices[0], torch.tensor([[2], [0], [-1]], dtype=torch.int32)
    )
    assert torch.equal(plan.remapped_indices[1], torch.tensor([1, 2], dtype=torch.int32))


def test_active_slot_plan_requires_consistent_tensor_types():
    with pytest.raises(ValueError, match="share device and dtype"):
        build_active_slot_plan(
            torch.tensor([1], dtype=torch.int32),
            torch.tensor([1], dtype=torch.int64),
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
