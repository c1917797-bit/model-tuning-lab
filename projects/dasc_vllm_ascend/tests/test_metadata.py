from dataclasses import dataclass

import pytest
import torch

from dasc_vllm_ascend.metadata import remap_ascend_gdn_metadata


@dataclass
class Conv:
    cache_indices: torch.Tensor


@dataclass
class Prefill:
    causal_conv1d: Conv


@dataclass
class Decode:
    causal_conv1d: Conv


@dataclass
class SpecConv:
    cache_indices: torch.Tensor


@dataclass
class SpecDecode:
    spec_causal_conv1d: SpecConv


@dataclass
class Metadata:
    non_spec_state_indices_tensor: torch.Tensor | None
    spec_state_indices_tensor: torch.Tensor | None
    prefill_state_indices: torch.Tensor | None
    non_spec_prefill_metadata: Prefill | None
    non_spec_decode_metadata: Decode | None
    spec_decode_metadata: SpecDecode | None


def test_remaps_temporal_and_conv_indices_together_without_mutation():
    metadata = Metadata(
        non_spec_state_indices_tensor=torch.tensor([7, 3], dtype=torch.int32),
        spec_state_indices_tensor=None,
        prefill_state_indices=torch.tensor([3], dtype=torch.int32),
        non_spec_prefill_metadata=Prefill(
            Conv(torch.tensor([7, 3], dtype=torch.int32))
        ),
        non_spec_decode_metadata=Decode(
            Conv(torch.tensor([7, 3], dtype=torch.int32))
        ),
        spec_decode_metadata=None,
    )
    remapped, plan = remap_ascend_gdn_metadata(metadata)
    assert torch.equal(plan.block_ids, torch.tensor([3, 7], dtype=torch.int32))
    assert torch.equal(remapped.non_spec_state_indices_tensor, torch.tensor([1, 0], dtype=torch.int32))
    assert torch.equal(remapped.prefill_state_indices, torch.tensor([0], dtype=torch.int32))
    assert torch.equal(
        remapped.non_spec_prefill_metadata.causal_conv1d.cache_indices,
        torch.tensor([1, 0], dtype=torch.int32),
    )
    assert torch.equal(metadata.non_spec_state_indices_tensor, torch.tensor([7, 3], dtype=torch.int32))


@dataclass
class DriftedMetadata:
    cache_indices: torch.Tensor


def test_rejects_unreviewed_metadata_index_field():
    with pytest.raises(ValueError, match="unhandled"):
        remap_ascend_gdn_metadata(
            DriftedMetadata(torch.tensor([1], dtype=torch.int32))
        )


def test_rejects_metadata_without_state_indices():
    empty = Metadata(None, None, None, None, None, None)
    with pytest.raises(ValueError, match="contains no"):
        remap_ascend_gdn_metadata(empty)
