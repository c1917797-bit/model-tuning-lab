import pytest
import torch

from dasc_vllm_ascend.runtime import ActiveStateBridge


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
