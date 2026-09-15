import pytest
import torch

from dasc_vllm_ascend.spec import (
    CompactSpecError,
    compact_mamba_spec,
    state_payload_elements,
)
from vllm.v1.attention.backends.registry import MambaAttentionBackendEnum
from vllm.v1.kv_cache_interface import MambaSpec


def make_spec(page_size_padded=None):
    return MambaSpec(
        block_size=1536,
        shapes=((3, 16), (12, 128, 128)),
        dtypes=(torch.bfloat16, torch.float32),
        page_size_padded=page_size_padded,
        mamba_type=MambaAttentionBackendEnum.GDN_ATTN,
        mamba_cache_mode="align",
    )


def test_compact_spec_changes_real_per_layer_shape_and_removes_dense_padding():
    dense = make_spec(page_size_padded=900000)
    compact = compact_mamba_spec(
        dense, state_index=1, head_axis=0, retained_heads=9
    )
    expected = 3 * 16 * 2 + 9 * 128 * 128 * 4
    assert compact.shapes == ((3, 16), (9, 128, 128))
    assert compact.page_size_padded is None
    assert compact.page_size_bytes == expected
    assert compact.page_size_bytes < dense.page_size_bytes
    assert dense.shapes == ((3, 16), (12, 128, 128))
    assert dense.page_size_padded == 900000


def test_heterogeneous_layers_preserve_their_own_page_sizes():
    dense = make_spec()
    layer2 = compact_mamba_spec(
        dense, state_index=1, head_axis=0, retained_heads=2
    )
    layer12 = compact_mamba_spec(
        dense, state_index=1, head_axis=0, retained_heads=12
    )
    assert layer2.page_size_bytes < layer12.page_size_bytes
    assert state_payload_elements(layer2) < state_payload_elements(layer12)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"state_index": 2, "head_axis": 0, "retained_heads": 1},
        {"state_index": 1, "head_axis": 3, "retained_heads": 1},
        {"state_index": 1, "head_axis": 0, "retained_heads": 0},
        {"state_index": 1, "head_axis": 0, "retained_heads": 13},
    ],
)
def test_compact_spec_rejects_unsafe_geometry(kwargs):
    with pytest.raises(CompactSpecError):
        compact_mamba_spec(make_spec(), **kwargs)
