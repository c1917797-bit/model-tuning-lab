from types import SimpleNamespace

import pytest
import torch

from dasc_vllm_ascend.selector import (
    DascSelectorError,
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


def test_unique_head_axis_fails_closed_on_ambiguous_shape():
    assert unique_head_axis((12, 128, 128), 12) == 0
    with pytest.raises(DascSelectorError, match="uniquely"):
        unique_head_axis((12, 128, 12), 12)
