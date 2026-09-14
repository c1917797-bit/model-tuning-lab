from __future__ import annotations

import pytest

from sliminfer_ascend.stream_contract import (
    RequestPruningState,
    build_whole_prompt_layout,
    decode_full_attention_slots,
    full_attention_physical_slot,
    prefill_full_attention_slots,
)


def test_request_state_separates_absolute_position_from_compact_cache():
    state = RequestPruningState(prompt_tokens=130, active_blocks=(0, 2))
    assert state.active_prompt_tokens == 66
    assert state.active_prompt_token_ids[:2] == (0, 1)
    assert state.active_prompt_token_ids[-2:] == (128, 129)
    assert state.next_decode_absolute_position == 130
    assert state.next_decode_compact_cache_position == 66

    advanced = state.advance_decode()
    assert advanced.next_decode_absolute_position == 131
    assert advanced.next_decode_compact_cache_position == 67


def test_whole_prompt_batch_layout_preserves_request_and_position_identity():
    states = (
        RequestPruningState(prompt_tokens=130, active_blocks=(0, 2)),
        RequestPruningState(prompt_tokens=70, active_blocks=(0, 1)),
    )
    layout = build_whole_prompt_layout(states, (0, 130, 200), (0, 0))

    assert layout.query_start_loc == (0, 66, 136)
    assert layout.gather_indices[:2] == (0, 1)
    assert layout.gather_indices[64:66] == (128, 129)
    assert layout.gather_indices[66:68] == (130, 131)
    assert layout.absolute_positions[64:68] == (128, 129, 0, 1)
    assert layout.request_indices[:66] == (0,) * 66
    assert layout.request_indices[66:] == (1,) * 70
    assert layout.compact_cache_positions[64:68] == (64, 65, 0, 1)


def test_whole_prompt_layout_rejects_chunked_or_resumed_prefill():
    state = RequestPruningState(prompt_tokens=130, active_blocks=(0, 2))
    with pytest.raises(RuntimeError, match="partial or resumed"):
        build_whole_prompt_layout((state,), (0, 64), (0,))
    with pytest.raises(RuntimeError, match="partial or resumed"):
        build_whole_prompt_layout((state,), (0, 130), (64,))


def test_full_attention_slots_use_compact_order_not_absolute_positions():
    states = (
        RequestPruningState(prompt_tokens=130, active_blocks=(0, 2)),
        RequestPruningState(prompt_tokens=70, active_blocks=(0, 1)),
    )
    block_tables = ((10, 20), (30, 31))
    prefill_slots = prefill_full_attention_slots(
        states, block_tables, kv_block_size=64
    )

    assert prefill_slots[:2] == (640, 641)
    assert prefill_slots[63:66] == (703, 1280, 1281)
    assert prefill_slots[66:68] == (1920, 1921)
    assert decode_full_attention_slots(
        states, block_tables, kv_block_size=64
    ) == (1282, 1990)


def test_contract_rejects_invalid_active_sets_and_cache_capacity():
    with pytest.raises(ValueError, match="sink"):
        RequestPruningState(prompt_tokens=130, active_blocks=(1, 2))
    # SlimInfer forces only the first sink block. Generated response tokens are
    # retained separately and must not be confused with the latest prompt block.
    without_recent_prompt = RequestPruningState(
        prompt_tokens=130, active_blocks=(0, 1)
    )
    assert without_recent_prompt.active_prompt_tokens == 128
    with pytest.raises(ValueError, match="sorted and unique"):
        RequestPruningState(prompt_tokens=130, active_blocks=(2, 0))
    with pytest.raises(ValueError, match="too short"):
        full_attention_physical_slot(
            (10,), kv_block_size=64, compact_cache_position=64
        )
