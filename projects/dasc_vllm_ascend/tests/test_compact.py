import pytest
import torch

from dasc_vllm_ascend.compact import (
    CompactCheckpointLayout,
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
