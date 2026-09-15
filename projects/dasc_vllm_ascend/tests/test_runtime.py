import pytest
import torch

from dasc_vllm_ascend.runtime import ActiveStateBridge, BoundActiveStateBridge


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
    conv, temporal = bridge.restore_active(torch.tensor([6, 2]))
    assert torch.equal(conv, conv_storage.index_select(0, torch.tensor([6, 2])))
    assert torch.equal(
        temporal.index_select(1, retained),
        temporal_storage.index_select(0, torch.tensor([6, 2])),
    )
    assert torch.count_nonzero(temporal[:, [1, 2]]).item() == 0
    conv.add_(11)
    temporal[:, retained].add_(13)
    bridge.checkpoint_active()
    assert conv_storage.data_ptr() == conv_ptr
    assert temporal_storage.data_ptr() == temporal_ptr
    assert torch.equal(
        temporal_storage.index_select(0, torch.tensor([6, 2])),
        temporal.index_select(1, retained),
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
