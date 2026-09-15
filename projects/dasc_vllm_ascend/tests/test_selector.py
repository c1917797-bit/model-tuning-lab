from types import SimpleNamespace

import pytest
import torch

from dasc_vllm_ascend.selector import (
    DascSelectorError,
    align_retained_heads_tp,
    head_horizons,
    retained_head_indices,
    unique_head_axis,
)


def test_loaded_weight_selector_is_cached_and_nonempty():
    module = SimpleNamespace(
        A_log=torch.log(torch.tensor([0.01, 0.1, 1.0])),
        dt_bias=torch.zeros(3),
    )
    config = SimpleNamespace(representative_a=-0.3, epsilon=0.001, w_max=64)
    selected = retained_head_indices(module, config)
    assert selected.dtype == torch.long
    assert selected.numel() > 0
    assert retained_head_indices(module, config) is selected


def test_selector_padding_preserves_threshold_heads():
    module = SimpleNamespace(
        A_log=torch.log(torch.tensor([0.01, 0.02, 0.1, 1.0])),
        dt_bias=torch.zeros(4),
    )
    config = SimpleNamespace(representative_a=-0.3, epsilon=0.001, w_max=64)
    horizon = head_horizons(module, config)
    threshold = set(
        (horizon > config.w_max).nonzero(as_tuple=False).flatten().tolist()
    )
    selected = retained_head_indices(module, config, target_count=3)
    assert selected.numel() == 3
    assert threshold.issubset(set(selected.tolist()))


def test_selector_rejects_cached_geometry_change():
    module = SimpleNamespace(
        A_log=torch.log(torch.tensor([0.01, 0.1, 1.0])),
        dt_bias=torch.zeros(3),
    )
    config = SimpleNamespace(representative_a=-0.3, epsilon=0.001, w_max=64)
    retained_head_indices(module, config)
    with pytest.raises(DascSelectorError, match="different TP geometry"):
        retained_head_indices(module, config, target_count=3)


def test_tp_alignment_uses_layerwise_max_and_rank_local_indices(monkeypatch):
    modules = [
        SimpleNamespace(
            A_log=torch.log(torch.tensor([0.01, 0.1, 1.0])),
            dt_bias=torch.zeros(3),
        ),
        SimpleNamespace(
            A_log=torch.log(torch.tensor([0.01, 0.02, 0.1, 1.0])),
            dt_bias=torch.zeros(4),
        ),
    ]
    config = SimpleNamespace(representative_a=-0.3, epsilon=0.001, w_max=64)

    def fake_all_reduce(tensor, op, group):
        assert op == torch.distributed.ReduceOp.MAX
        assert group == "tp"
        tensor.copy_(torch.tensor([2, 3], dtype=tensor.dtype))

    monkeypatch.setattr(torch.distributed, "all_reduce", fake_all_reduce)
    summary = align_retained_heads_tp(
        [("layer.0", modules[0]), ("layer.1", modules[1])], config, "tp"
    )
    assert summary["common_counts"] == [2, 3]
    assert [module._mst_dasc_retained_indices.numel() for module in modules] == [2, 3]


def test_unique_head_axis_fails_closed_on_ambiguous_shape():
    assert unique_head_axis((12, 128, 128), 12) == 0
    with pytest.raises(DascSelectorError, match="uniquely"):
        unique_head_axis((12, 128, 12), 12)
