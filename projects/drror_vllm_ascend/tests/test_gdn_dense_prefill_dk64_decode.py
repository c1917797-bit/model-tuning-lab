import pytest
import torch

from tools.probe_gdn_dense_prefill_dk64_decode import (
    TARGET,
    VALUE_HEADS_PER_KEY_HEAD,
    WIDTH,
    _advance,
    initialize_decode_state,
)


def _record(step, state_initial, state_final):
    token_count = 128 if step == 0 else 1
    zeros_q = torch.zeros((token_count, 4, WIDTH), dtype=torch.bfloat16)
    zeros_v = torch.zeros((token_count, 12, WIDTH), dtype=torch.bfloat16)
    return {
        "step": step,
        "tensors": {
            "raw_q": zeros_q,
            "raw_k": zeros_q.clone(),
            "raw_v": zeros_v,
            "g": torch.zeros((token_count, 12), dtype=torch.float32),
            "beta": torch.zeros((token_count, 12), dtype=torch.float32),
            "operator_output": zeros_v.clone(),
            "z": zeros_v.clone(),
            "norm_output": zeros_v.clone(),
            "norm_weight": torch.ones(WIDTH, dtype=torch.bfloat16),
            "state_initial": state_initial.clone().unsqueeze(0),
            "state_final": state_final.clone().unsqueeze(0),
        },
    }


def _records():
    initial = torch.zeros((12, WIDTH, WIDTH), dtype=torch.float32)
    prefill_final = torch.arange(
        12 * WIDTH * WIDTH, dtype=torch.float32
    ).reshape(12, WIDTH, WIDTH)
    records = [_record(0, initial, prefill_final)]
    current = prefill_final
    for step in range(1, 9):
        records.append(_record(step, current, current))
    return records, prefill_final


def test_dense_prefill_transition_is_exact_selected_state():
    records, prefill_final = _records()
    selected = torch.arange(TARGET)
    state = initialize_decode_state(records, 0, selected, dense_prefill=True)
    assert torch.equal(
        state,
        prefill_final[:VALUE_HEADS_PER_KEY_HEAD].index_select(-1, selected),
    )


def test_transition_rejects_nonidentical_prefill_decode_state():
    records, _ = _records()
    records[1]["tensors"]["state_initial"] += 1
    with pytest.raises(ValueError, match="transition identity"):
        initialize_decode_state(records, 0, torch.arange(TARGET), True)


def test_advance_never_expands_dk64_state():
    records, _ = _records()
    selected = torch.arange(TARGET)
    item = {
        name: value
        for name, value in __import__(
            "tools.analyze_gdn_recurrent_transition_selector",
            fromlist=["head_tensors"],
        ).head_tensors(records[1], 0).items()
    }
    state = torch.zeros(
        VALUE_HEADS_PER_KEY_HEAD, WIDTH, TARGET, dtype=torch.float32
    )
    updated, output = _advance(state, item, selected)
    assert updated.shape == (VALUE_HEADS_PER_KEY_HEAD, WIDTH, TARGET)
    assert output.shape == (1, VALUE_HEADS_PER_KEY_HEAD, WIDTH)
