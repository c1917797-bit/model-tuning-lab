from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

from sliminfer_ascend.semantic_prefill import (
    compact_positions,
    compact_gdn_metadata,
    compact_full_attention_metadata,
    compact_gather_indices,
    layer_metadata_key,
    swapped_layer_metadata,
    validate_model_contract,
)


@dataclass
class FakeFullMetadata:
    attn_state: object
    num_actual_tokens_pcp_padded: int
    num_actual_tokens: int
    num_decode_tokens: int
    num_prefills: int
    num_decodes: int
    seq_lens: object
    seq_lens_cpu: object
    seq_lens_list: list[int]
    actual_seq_lengths_q: list[int]
    query_start_loc: object
    max_query_len: int
    slot_mapping: object


def _full_metadata(tokens=192):
    return FakeFullMetadata(
        attn_state=SimpleNamespace(name="PrefillNoCache"),
        num_actual_tokens_pcp_padded=tokens,
        num_actual_tokens=tokens,
        num_decode_tokens=0,
        num_prefills=1,
        num_decodes=0,
        seq_lens=torch.tensor([tokens], dtype=torch.int32),
        seq_lens_cpu=torch.tensor([tokens], dtype=torch.int32),
        seq_lens_list=[tokens],
        actual_seq_lengths_q=[tokens],
        query_start_loc=torch.tensor([0, tokens], dtype=torch.int32),
        max_query_len=tokens,
        slot_mapping=torch.arange(tokens, dtype=torch.int64),
    )


def test_compact_gather_indices_keep_noncontiguous_absolute_blocks():
    assert compact_gather_indices(
        (0, 2, 5), (0, 5), prompt_tokens=6 * 64
    ) == tuple(range(64)) + tuple(range(128, 192))
    with pytest.raises(ValueError, match="subset"):
        compact_gather_indices((0, 2), (0, 3), prompt_tokens=4 * 64)


def test_compact_positions_supports_text_and_qwen_multichannel_rope_layouts():
    index = torch.tensor([0, 3, 5], dtype=torch.long)
    text = torch.arange(6)
    multichannel = torch.arange(18).reshape(3, 6)

    assert compact_positions(text, index, expected_tokens=6).tolist() == [0, 3, 5]
    assert compact_positions(
        multichannel, index, expected_tokens=6
    ).tolist() == multichannel[:, index].tolist()


def test_compact_positions_rejects_unknown_layout_or_wrong_token_count():
    index = torch.tensor([0], dtype=torch.long)
    with pytest.raises(RuntimeError, match="positions shaped"):
        compact_positions(torch.zeros(1, 2, 3), index, expected_tokens=3)
    with pytest.raises(RuntimeError, match="position token count"):
        compact_positions(torch.zeros(3, 5), index, expected_tokens=6)


def test_full_metadata_clone_uses_compact_cache_slots_and_keeps_original_immutable():
    original = _full_metadata()
    compact = compact_full_attention_metadata(original, 128)
    assert compact is not original
    assert compact.num_actual_tokens == 128
    assert compact.seq_lens_list == [128]
    assert compact.actual_seq_lengths_q == [128]
    assert compact.query_start_loc.tolist() == [0, 128]
    assert compact.slot_mapping.tolist() == list(range(128))
    assert original.num_actual_tokens == 192
    assert original.slot_mapping.shape[0] == 192


def test_full_metadata_clone_rejects_non_whole_prefill_contracts():
    metadata = _full_metadata()
    metadata.num_prefills = 2
    with pytest.raises(RuntimeError, match="exactly one"):
        compact_full_attention_metadata(metadata, 128)
    metadata = _full_metadata()
    metadata.attn_state = SimpleNamespace(name="ChunkedPrefill")
    with pytest.raises(RuntimeError, match="PrefillNoCache"):
        compact_full_attention_metadata(metadata, 128)


def test_transactional_mapping_restores_shared_metadata_even_on_error():
    original = object()
    replacement = object()
    mapping = {"layer": original}
    with pytest.raises(RuntimeError, match="boom"):
        with swapped_layer_metadata(mapping, "layer", replacement):
            assert mapping["layer"] is replacement
            raise RuntimeError("boom")
    assert mapping["layer"] is original


def test_layer_metadata_key_is_resolved_from_live_layer_objects():
    full = SimpleNamespace(
        layer_type="full_attention",
        self_attn=SimpleNamespace(attn=SimpleNamespace(layer_name="layers.3.attn")),
    )
    linear = SimpleNamespace(
        layer_type="linear_attention",
        linear_attn=SimpleNamespace(prefix="layers.4.linear_attn"),
    )
    assert layer_metadata_key(full) == "layers.3.attn"
    assert layer_metadata_key(linear) == "layers.4.linear_attn"


def test_model_contract_rejects_partial_layers_and_auxiliary_hidden_states():
    valid = SimpleNamespace(
        layers=[object(), object()],
        start_layer=0,
        end_layer=2,
        aux_hidden_state_layers=(),
    )
    validate_model_contract(valid)

    partial = SimpleNamespace(
        layers=[object(), object()],
        start_layer=1,
        end_layer=2,
        aux_hidden_state_layers=(),
    )
    with pytest.raises(RuntimeError, match="complete decoder layer range"):
        validate_model_contract(partial)

    auxiliary = SimpleNamespace(
        layers=[object(), object()],
        start_layer=0,
        end_layer=2,
        aux_hidden_state_layers=(1,),
    )
    with pytest.raises(RuntimeError, match="auxiliary hidden-state"):
        validate_model_contract(auxiliary)


def test_real_ascend_gdn_metadata_clone_rebuilds_compact_chunk_contract():
    gdn = pytest.importorskip("vllm.v1.attention.backends.gdn_attn")
    builder_module = pytest.importorskip("vllm_ascend.ops.gdn_attn_builder")
    fake_builder = SimpleNamespace(
        vllm_config=SimpleNamespace(
            model_config=SimpleNamespace(
                hf_text_config=SimpleNamespace(linear_num_value_heads=48)
            ),
            parallel_config=SimpleNamespace(tensor_parallel_size=4),
        )
    )
    start = torch.tensor([0, 192], dtype=torch.int32)
    chunk = builder_module._build_non_spec_chunked_prefill_metadata(
        fake_builder, start, torch.device("cpu")
    )
    causal = builder_module.GDNCausalConv1dMetadata(
        query_start_loc=start,
        cache_indices=torch.tensor([7], dtype=torch.int32),
        initial_state_mode=torch.tensor([0], dtype=torch.int32),
    )
    metadata = gdn.GDNAttentionMetadata(
        num_prefills=1,
        num_prefill_tokens=192,
        num_decodes=0,
        num_decode_tokens=0,
        num_spec_decodes=0,
        num_spec_decode_tokens=0,
        num_actual_tokens=192,
        non_spec_query_start_loc=start,
        non_spec_state_indices_tensor=torch.tensor([7], dtype=torch.int32),
        chunk_indices=chunk.chunk_indices_chunk64,
        chunk_offsets=chunk.chunk_offsets_chunk64,
        prefill_query_start_loc=start,
        prefill_state_indices=torch.tensor([7], dtype=torch.int32),
        prefill_has_initial_state=torch.tensor([False]),
    )
    metadata.non_spec_prefill_metadata = builder_module.GDNPrefillMetadata(
        causal_conv1d=causal, chunk=chunk
    )

    compact = compact_gdn_metadata(
        metadata,
        128,
        linear_num_value_heads=48,
        tp_size=4,
    )

    assert compact is not metadata
    assert compact.num_actual_tokens == 128
    assert compact.num_prefill_tokens == 128
    assert compact.non_spec_query_start_loc.tolist() == [0, 128]
    assert compact.prefill_query_start_loc.tolist() == [0, 128]
    assert (
        compact.non_spec_prefill_metadata.chunk.cu_seqlens_host
        == (0, 128)
    )
    assert metadata.num_actual_tokens == 192
