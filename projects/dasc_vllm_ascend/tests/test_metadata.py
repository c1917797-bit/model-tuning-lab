from dataclasses import dataclass

import pytest
import torch

from dasc_vllm_ascend.metadata import (
    StableAscendGDNMetadataRemapper,
    remap_ascend_gdn_metadata,
)


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


@dataclass
class UpstreamMetadata:
    non_spec_state_indices_tensor: torch.Tensor


def test_preserves_ascend_runtime_attributes_while_replacing_dataclass_fields():
    metadata = UpstreamMetadata(torch.tensor([7, 3], dtype=torch.int32))
    metadata.non_spec_prefill_metadata = Prefill(
        Conv(torch.tensor([7, 3], dtype=torch.int32))
    )

    remapped, plan = remap_ascend_gdn_metadata(metadata)

    assert torch.equal(plan.block_ids, torch.tensor([3, 7], dtype=torch.int32))
    assert torch.equal(
        remapped.non_spec_state_indices_tensor,
        torch.tensor([1, 0], dtype=torch.int32),
    )
    assert torch.equal(
        remapped.non_spec_prefill_metadata.causal_conv1d.cache_indices,
        torch.tensor([1, 0], dtype=torch.int32),
    )
    assert hasattr(metadata, "non_spec_prefill_metadata")


def test_stable_remapper_reuses_index_buffer_addresses():
    first = Metadata(
        torch.tensor([6, 2]), None, None, None, None, None
    )
    second = Metadata(
        torch.tensor([4, 7]), None, None, None, None, None
    )
    remapper = StableAscendGDNMetadataRemapper()

    mapped1, plan1 = remapper.prepare(first)
    pointers = remapper.pointers
    mapped2, plan2 = remapper.prepare(second)

    assert remapper.pointers == pointers
    assert mapped1.non_spec_state_indices_tensor.data_ptr() == pointers[0]
    assert mapped2.non_spec_state_indices_tensor.data_ptr() == pointers[0]
    assert torch.equal(plan1.block_ids, torch.tensor([2, 6]))
    assert torch.equal(plan2.block_ids, torch.tensor([4, 7]))
    assert torch.equal(mapped2.non_spec_state_indices_tensor, torch.tensor([0, 1]))


def test_stable_remapper_keeps_separate_shape_variants():
    remapper = StableAscendGDNMetadataRemapper()
    small = Metadata(torch.tensor([6, 2]), None, None, None, None, None)
    large = Metadata(torch.tensor([6, 2, 4]), None, None, None, None, None)

    mapped_small1, _ = remapper.prepare(small)
    small_pointer = remapper.pointers[0]
    mapped_large, _ = remapper.prepare(large)
    large_pointer = remapper.pointers[0]
    mapped_small2, _ = remapper.prepare(small)

    assert small_pointer != large_pointer
    assert mapped_small1.non_spec_state_indices_tensor.data_ptr() == small_pointer
    assert mapped_large.non_spec_state_indices_tensor.data_ptr() == large_pointer
    assert mapped_small2.non_spec_state_indices_tensor.data_ptr() == small_pointer


def test_stable_remapper_targets_request_owned_slots():
    metadata = Metadata(
        torch.tensor([7, 3, -1], dtype=torch.int32),
        None,
        torch.tensor([3], dtype=torch.int32),
        None,
        None,
        None,
    )
    remapper = StableAscendGDNMetadataRemapper()

    # build_active_slot_plan sorts physical blocks as [3, 7].  Request-owned
    # rows need not be contiguous or follow that physical ordering.
    mapped, plan = remapper.prepare(
        metadata, active_slots=torch.tensor([5, 1], dtype=torch.int64)
    )

    assert torch.equal(plan.block_ids, torch.tensor([3, 7], dtype=torch.int32))
    assert torch.equal(
        mapped.non_spec_state_indices_tensor,
        torch.tensor([1, 5, -1], dtype=torch.int32),
    )
    assert torch.equal(
        mapped.prefill_state_indices, torch.tensor([5], dtype=torch.int32)
    )


def test_stable_remapper_rejects_invalid_request_slot_map():
    metadata = Metadata(torch.tensor([7, 3]), None, None, None, None, None)
    remapper = StableAscendGDNMetadataRemapper()
    with pytest.raises(ValueError, match="match discovered"):
        remapper.prepare(metadata, active_slots=torch.tensor([1]))
    with pytest.raises(ValueError, match="unique"):
        remapper.prepare(metadata, active_slots=torch.tensor([1, 1]))
