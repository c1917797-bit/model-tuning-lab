import pytest
import torch

from dasc_vllm_ascend.runtime import (
    ActiveStateBridge,
    BoundActiveStateBridge,
    RequestActiveStateBridge,
)


def make_bridge():
    return ActiveStateBridge(
        num_blocks=8,
        max_active_blocks=3,
        conv_shape=(2, 3),
        temporal_shape=(4, 2),
        temporal_head_axis=0,
        retained_indices=torch.tensor([0, 3], dtype=torch.long),
        conv_dtype=torch.float32,
        temporal_dtype=torch.float32,
        device="cpu",
    )


def test_atomic_restore_compute_checkpoint_and_prefix_copy():
    bridge = make_bridge()
    conv, temporal = bridge.restore_active(torch.tensor([6, 2]))
    assert torch.count_nonzero(conv).item() == 0
    assert torch.count_nonzero(temporal).item() == 0
    conv.add_(7)
    temporal.add_(5)
    bridge.checkpoint_active()

    bridge.copy_blocks(torch.tensor([6]), torch.tensor([4]))
    conv2, temporal2 = bridge.restore_active(torch.tensor([4]))
    assert torch.all(conv2 == 7)
    assert torch.all(temporal2[:, [0, 3]] == 5)
    assert torch.count_nonzero(temporal2[:, [1, 2]]).item() == 0
    bridge.checkpoint_active()


def test_bridge_is_transactional_and_fixed_capacity():
    bridge = make_bridge()
    conv_ptr = bridge.conv_workspace.data_ptr()
    temporal_ptr = bridge.temporal_workspace.data_ptr()
    bridge.restore_active(torch.tensor([1]))
    with pytest.raises(RuntimeError, match="already open"):
        bridge.restore_active(torch.tensor([2]))
    with pytest.raises(RuntimeError, match="active transaction"):
        bridge.invalidate(torch.tensor([1]))
    bridge.abort_active()
    with pytest.raises(ValueError, match="capacity"):
        bridge.restore_active(torch.tensor([0, 1, 2, 3]))
    assert bridge.conv_workspace.data_ptr() == conv_ptr
    assert bridge.temporal_workspace.data_ptr() == temporal_ptr


def test_bound_bridge_round_trips_runner_owned_compact_cache():
    conv_storage = torch.arange(8 * 2 * 3, dtype=torch.float32).view(8, 2, 3)
    temporal_storage = torch.arange(
        8 * 2 * 2, dtype=torch.float32
    ).view(8, 2, 2)
    retained = torch.tensor([0, 3], dtype=torch.long)
    bridge = BoundActiveStateBridge(
        conv_storage=conv_storage,
        compact_temporal_storage=temporal_storage,
        dense_temporal_shape=(4, 2),
        temporal_head_axis=0,
        retained_indices=retained,
        max_active_blocks=3,
    )
    conv_ptr = conv_storage.data_ptr()
    temporal_ptr = temporal_storage.data_ptr()
    cache = bridge.workspace_cache
    cache_ptrs = tuple(tensor.data_ptr() for tensor in cache)
    conv, temporal = bridge.restore_active(torch.tensor([6, 2]))
    assert (conv, temporal) == cache
    assert conv.shape == (3, 2, 3)
    assert temporal.shape == (3, 4, 2)
    assert torch.equal(conv[:2], conv_storage.index_select(0, torch.tensor([6, 2])))
    assert torch.equal(
        temporal[:2].index_select(1, retained),
        temporal_storage.index_select(0, torch.tensor([6, 2])),
    )
    assert torch.count_nonzero(temporal[:2, [1, 2]]).item() == 0
    conv[:2].add_(11)
    temporal[:2, retained].add_(13)
    bridge.checkpoint_active()
    assert bridge.workspace_cache is cache
    assert tuple(tensor.data_ptr() for tensor in bridge.workspace_cache) == cache_ptrs
    assert conv_storage.data_ptr() == conv_ptr
    assert temporal_storage.data_ptr() == temporal_ptr
    assert torch.equal(
        temporal_storage.index_select(0, torch.tensor([6, 2])),
        temporal[:2].index_select(1, retained),
    )


def test_bound_bridge_rejects_dense_runner_temporal_cache():
    with pytest.raises(ValueError, match="compact geometry"):
        BoundActiveStateBridge(
            conv_storage=torch.empty(4, 2, 3),
            compact_temporal_storage=torch.empty(4, 4, 2),
            dense_temporal_shape=(4, 2),
            temporal_head_axis=0,
            retained_indices=torch.tensor([0, 3], dtype=torch.long),
            max_active_blocks=2,
        )


def test_request_bridge_zero_fills_only_on_prefix_load():
    conv_storage = torch.zeros(8, 2, 3)
    temporal_storage = torch.zeros(8, 2, 2)
    temporal_storage[3].copy_(
        torch.tensor([[1.0, 2.0], [7.0, 8.0]])
    )
    retained = torch.tensor([0, 3], dtype=torch.long)
    bridge = RequestActiveStateBridge(
        conv_storage=conv_storage,
        compact_temporal_storage=temporal_storage,
        dense_temporal_shape=(4, 2),
        temporal_head_axis=0,
        retained_indices=retained,
        max_active_requests=2,
    )

    slots = bridge.activate(
        ("req-a",),
        torch.tensor([3]),
        torch.tensor([True]),
    )
    assert slots.tolist() == [0]
    active = bridge.temporal_workspace[0]
    assert torch.equal(active[retained], temporal_storage[3])
    assert torch.count_nonzero(active[[1, 2]]).item() == 0

    # A normal recurrent step updates every head, including omitted heads.
    active.add_(10)
    omitted_after_step = active[[1, 2]].clone()
    bridge.checkpoint(("req-a",), torch.tensor([5]))

    # A scheduler block transition for the same live request must not perform
    # a second DASC-NR load or erase the newly accumulated omitted-head state.
    slots_again = bridge.activate(
        ("req-a",),
        torch.tensor([5]),
        torch.tensor([True]),
    )
    assert slots_again.tolist() == [0]
    assert torch.equal(bridge.temporal_workspace[0, [1, 2]], omitted_after_step)

    # Releasing and later reactivating is a real checkpoint load boundary:
    # retained heads restore from compact storage and omitted heads start zero.
    retained_checkpoint = temporal_storage[5].clone()
    bridge.release(("req-a",))
    bridge.activate(("req-a",), torch.tensor([5]), torch.tensor([True]))
    assert torch.equal(
        bridge.temporal_workspace[0, retained], retained_checkpoint
    )
    assert torch.count_nonzero(
        bridge.temporal_workspace[0, [1, 2]]
    ).item() == 0
