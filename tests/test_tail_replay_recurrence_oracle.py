from __future__ import annotations

import json

import pytest
import torch

import tail_replay_ascend.full_group_patch as full_group_patch
from tail_replay_ascend.config import TailReplayConfig, get_config
from tail_replay_ascend.runtime_patch import (
    _CURRENT_LAYER_PREFIX,
    _SEEN_LAYER_PREFIXES,
    _make_chunk_wrapper,
    _state_metrics,
    _tail_tokens,
)
from tail_replay_ascend.full_group_patch import (
    _is_group_end,
    _is_group_start,
    _materialize,
    _tensor_metrics,
)


def _config(evidence_file: str | None = None) -> TailReplayConfig:
    return TailReplayConfig(
        enable=True,
        mode="recurrence-oracle",
        replay_ratios=(0.05, 0.10),
        evidence_file=evidence_file,
        require_runtime_hooks=True,
        min_prefill_tokens=1,
        max_prefill_tokens=4096,
        exact_split_relative_l2_max=0.0,
    )


def test_config_is_disabled_by_default(monkeypatch):
    for name in (
        "MST_TAIL_REPLAY_ENABLE",
        "MST_TAIL_REPLAY_MODE",
        "MST_TAIL_REPLAY_RATIOS",
        "MST_TAIL_REPLAY_EVIDENCE_FILE",
    ):
        monkeypatch.delenv(name, raising=False)
    config = get_config()
    assert config.enable is False
    assert config.mode == "recurrence-oracle"
    assert config.replay_ratios == (0.05, 0.10)


def test_config_rejects_invalid_ratio(monkeypatch):
    monkeypatch.setenv("MST_TAIL_REPLAY_RATIOS", "0,1.1")
    with pytest.raises(ValueError, match="RATIOS"):
        get_config()


def test_config_accepts_group_oracle_mode(monkeypatch):
    monkeypatch.setenv("MST_TAIL_REPLAY_MODE", "group-oracle")
    assert get_config().mode == "group-oracle"


@pytest.mark.parametrize(
    ("layer_idx", "start", "end"),
    [(0, True, False), (1, False, False), (2, False, True), (3, False, False),
     (4, True, False), (62, False, True)],
)
def test_gdn_group_boundaries(layer_idx, start, end):
    assert _is_group_start(layer_idx, "linear_attention") is start
    assert _is_group_end(layer_idx, "linear_attention") is end
    assert _is_group_start(layer_idx, "full_attention") is False
    assert _is_group_end(layer_idx, "full_attention") is False


def test_group_tensor_metrics_and_materialized_state():
    hidden = torch.arange(6, dtype=torch.float32).reshape(2, 3)
    residual = torch.ones_like(hidden)
    materialized = _materialize(hidden, residual)
    assert torch.equal(materialized, hidden + residual)
    metrics = _tensor_metrics(materialized, materialized.clone())
    assert metrics["all_finite"] is True
    assert metrics["relative_l2"] == 0.0
    assert metrics["cosine"] == pytest.approx(1.0)


def test_group_wrapper_keeps_capture_across_three_layer_calls(monkeypatch):
    full_group_patch._SEEN_GROUPS.clear()
    full_group_patch._ACTIVE_CAPTURE.set(None)
    observed = []
    monkeypatch.setattr(
        full_group_patch, "_prefill_metadata", lambda _attention: object()
    )
    monkeypatch.setattr(
        full_group_patch,
        "_run_group_oracle",
        lambda **kwargs: observed.append(kwargs),
    )

    class Attention:
        prefix = "model.layers.fake.linear_attn"

    class Layer:
        def __init__(self, layer_idx):
            self.layer_idx = layer_idx
            self.layer_type = "linear_attention"
            self.linear_attn = Attention()

    def original(_self, hidden_states, residual, *args, **kwargs):
        return hidden_states + 1, residual

    wrapped = full_group_patch._make_decoder_wrapper(
        original, _config()
    )
    hidden = torch.ones((8, 4))
    residual = None
    for layer_idx in range(3):
        hidden, residual = wrapped(Layer(layer_idx), hidden, residual)

    assert torch.equal(hidden, torch.full((8, 4), 4.0))
    assert residual is None
    assert len(observed) == 1
    assert observed[0]["start_layer"] == 0
    assert [layer.layer_idx for layer in observed[0]["layers"]] == [0, 1, 2]
    assert torch.equal(observed[0]["input_hidden"], torch.ones((8, 4)))
    assert full_group_patch._ACTIVE_CAPTURE.get() is None


@pytest.mark.parametrize(
    ("tokens", "ratio", "expected"),
    [(1, 0.05, 1), (20, 0.05, 1), (21, 0.05, 2), (196, 0.10, 20)],
)
def test_tail_token_rounding(tokens, ratio, expected):
    assert _tail_tokens(tokens, ratio) == expected


def test_state_metrics_report_exact_identity():
    reference = torch.arange(24, dtype=torch.float32).reshape(1, 2, 3, 4)
    metrics = _state_metrics(reference, reference.clone())
    assert metrics["all_finite"] is True
    assert metrics["relative_l2"] == 0.0
    assert metrics["cosine"] == pytest.approx(1.0)
    assert metrics["head_relative_l2_max"] == 0.0


def test_recurrence_oracle_preserves_result_and_validates_exact_split(
    tmp_path, monkeypatch
):
    evidence = tmp_path / "oracle.jsonl"
    monkeypatch.setenv("MST_TAIL_REPLAY_EVIDENCE_FILE", str(evidence))
    _SEEN_LAYER_PREFIXES.clear()

    def additive_chunk(
        q,
        k,
        v,
        g,
        beta,
        scale=None,
        initial_state=None,
        output_final_state=False,
        cu_seqlens=None,
        prebuilt_meta=None,
        head_first=False,
        use_qk_l2norm_in_kernel=False,
    ):
        update = v.float().sum(dim=1).unsqueeze(2)
        final_state = initial_state.float() + update
        return v, final_state if output_final_state else None

    wrapped = _make_chunk_wrapper(additive_chunk, _config(str(evidence)))
    q = torch.ones((1, 20, 2, 1), dtype=torch.bfloat16)
    v = torch.arange(120, dtype=torch.float32).reshape(1, 20, 2, 3).to(torch.bfloat16)
    kwargs = {
        "q": q,
        "k": q.clone(),
        "v": v,
        "g": torch.zeros((1, 20, 2), dtype=torch.bfloat16),
        "beta": torch.ones((1, 20, 2), dtype=torch.bfloat16),
        "initial_state": torch.zeros((1, 2, 1, 3), dtype=torch.float32),
        "output_final_state": True,
        "cu_seqlens": torch.tensor([0, 20]),
        "head_first": False,
        "use_qk_l2norm_in_kernel": True,
    }
    token = _CURRENT_LAYER_PREFIX.set("model.layers.0.linear_attn")
    try:
        expected = additive_chunk(**kwargs)
        actual = wrapped(**kwargs)
    finally:
        _CURRENT_LAYER_PREFIX.reset(token)

    assert torch.equal(actual[0], expected[0])
    assert torch.equal(actual[1], expected[1])
    events = [json.loads(line) for line in evidence.read_text().splitlines()]
    results = [event for event in events if event["event"] == "recurrence_oracle_result"]
    assert [event["replay_ratio"] for event in results] == [0.05, 0.10]
    assert all(event["harness_passed"] for event in results)
    assert all(event["exact_split"]["relative_l2"] == 0.0 for event in results)
    assert all(event["zero_tail"]["relative_l2"] > 0.0 for event in results)
