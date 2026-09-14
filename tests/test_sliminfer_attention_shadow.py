from __future__ import annotations

import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

from sliminfer_ascend import attention_shadow
from sliminfer_ascend.attention_shadow import (
    _apply_attention_patch,
    _layer_index,
    _tp_reduce_sum,
    _whole_prompt_start_locs,
    selection_forward_scope,
)
from sliminfer_ascend.config import SlimInferConfig


def _config(evidence):
    return SlimInferConfig(
        enable=True,
        mode="selection-shadow",
        evidence_file=str(evidence),
        require_runtime_hooks=True,
    )


def _metadata(lengths, *, state="PrefillNoCache", decode_tokens=0):
    starts = [0]
    for length in lengths:
        starts.append(starts[-1] + length)
    return SimpleNamespace(
        num_prefills=len(lengths),
        num_decode_tokens=decode_tokens,
        attn_state=SimpleNamespace(name=state),
        query_start_loc=starts,
        num_actual_tokens=sum(lengths),
    )


def test_layer_index_comes_from_live_attention_name():
    assert _layer_index("language_model.model.layers.19.self_attn.attn") == 19
    with pytest.raises(ValueError, match="cannot extract"):
        _layer_index("language_model.attention")


def test_tp_score_sum_is_canonicalized_from_rank_zero(monkeypatch):
    calls = []

    class FakeGroup:
        def all_reduce(self, value):
            calls.append(("all_reduce", value))
            return value + 1

        def broadcast(self, value, src):
            calls.append(("broadcast", value, src))
            return value + 2

    module = ModuleType("vllm.distributed.parallel_state")
    module.get_tp_group = lambda: FakeGroup()
    monkeypatch.setitem(sys.modules, module.__name__, module)
    value = torch.tensor([3.0])

    result = _tp_reduce_sum(value)

    assert torch.equal(result, torch.tensor([6.0]))
    assert calls[0][0] == "all_reduce"
    assert calls[1][0] == "broadcast"
    assert calls[1][2] == 0


def test_whole_prompt_contract_skips_decode_and_rejects_partial_rows():
    assert _whole_prompt_start_locs(_metadata((2, 3)), 5) == (0, 2, 5)
    assert _whole_prompt_start_locs(SimpleNamespace(num_prefills=0), 1) is None
    with pytest.raises(RuntimeError, match="prefill-only"):
        _whole_prompt_start_locs(_metadata((2,), decode_tokens=1), 2)
    with pytest.raises(RuntimeError, match="PrefillNoCache"):
        _whole_prompt_start_locs(_metadata((2,), state="ChunkedPrefill"), 2)
    with pytest.raises(RuntimeError, match="padded or partial"):
        _whole_prompt_start_locs(_metadata((2,)), 3)


def test_attention_shadow_preserves_original_forward_and_emits_selection(
    tmp_path, monkeypatch
):
    evidence = tmp_path / "selection.jsonl"
    monkeypatch.setenv("MST_SLIMINFER_EVIDENCE_FILE", str(evidence))

    class Qwen3NextAttention:
        def forward(self, positions, output, hidden_states):
            output.copy_(hidden_states)
            return "original-result"

    Qwen3NextAttention.__module__ = "vllm_ascend.patch.worker.patch_qwen3_5"
    module = ModuleType(Qwen3NextAttention.__module__)
    module.Qwen3NextAttention = Qwen3NextAttention
    _apply_attention_patch(module, _config(evidence))

    instance = Qwen3NextAttention()
    instance.attn = SimpleNamespace(
        layer_name="language_model.model.layers.19.self_attn.attn"
    )
    instance.num_heads = 1
    instance.num_kv_heads = 1
    instance.total_num_heads = 1
    hidden = torch.arange(4, dtype=torch.float32).reshape(4, 1)
    output = torch.empty_like(hidden)
    q = torch.ones((4, 1, 1), dtype=torch.float32)
    k = torch.arange(4, dtype=torch.float32).reshape(4, 1, 1)
    monkeypatch.setattr(attention_shadow, "_compute_live_qk", lambda *args: (q, k))
    monkeypatch.setattr(
        attention_shadow, "_attention_metadata", lambda name: _metadata((4,))
    )
    monkeypatch.setattr(attention_shadow, "_tp_reduce_sum", lambda value: value)

    with selection_forward_scope():
        result = instance.forward(torch.arange(4), output, hidden)

    assert result == "original-result"
    assert torch.equal(output, hidden)
    events = [json.loads(line) for line in evidence.read_text().splitlines()]
    assert [event["event"] for event in events] == [
        "selection_shadow_patch_installed",
        "selection_shadow_layer",
    ]
    selection = events[1]
    assert selection["layer_index"] == 19
    assert selection["selected_blocks"] == [0]
    assert selection["runtime_mutation"] is False
    assert selection["duplicate_projection_for_diagnostics"] is True


def test_non_boundary_layer_calls_original_without_scoring(tmp_path, monkeypatch):
    evidence = tmp_path / "selection.jsonl"
    monkeypatch.setenv("MST_SLIMINFER_EVIDENCE_FILE", str(evidence))

    class Qwen3NextAttention:
        def forward(self, positions, output, hidden_states):
            return "untouched"

    module = ModuleType("vllm_ascend.patch.worker.patch_qwen3_5")
    module.Qwen3NextAttention = Qwen3NextAttention
    _apply_attention_patch(module, _config(evidence))
    instance = Qwen3NextAttention()
    instance.attn = SimpleNamespace(
        layer_name="language_model.model.layers.23.self_attn.attn"
    )
    monkeypatch.setattr(
        attention_shadow,
        "_compute_live_qk",
        lambda *args: (_ for _ in ()).throw(AssertionError("must not score")),
    )
    assert instance.forward(None, None, None) == "untouched"


def test_boundary_layer_skips_dummy_forward_without_metadata(tmp_path, monkeypatch):
    evidence = tmp_path / "selection.jsonl"
    monkeypatch.setenv("MST_SLIMINFER_EVIDENCE_FILE", str(evidence))

    class Qwen3NextAttention:
        def forward(self, positions, output, hidden_states):
            return "dummy-forward"

    module = ModuleType("vllm_ascend.patch.worker.patch_qwen3_5")
    module.Qwen3NextAttention = Qwen3NextAttention
    _apply_attention_patch(module, _config(evidence))
    instance = Qwen3NextAttention()
    instance.attn = SimpleNamespace(
        layer_name="language_model.model.layers.19.self_attn.attn"
    )
    monkeypatch.setattr(attention_shadow, "_attention_metadata", lambda name: None)
    monkeypatch.setattr(
        attention_shadow,
        "_compute_live_qk",
        lambda *args: (_ for _ in ()).throw(AssertionError("must not score")),
    )

    with selection_forward_scope():
        result = instance.forward(None, None, torch.ones((4, 1)))

    assert result == "dummy-forward"
    events = [json.loads(line) for line in evidence.read_text().splitlines()]
    assert [event["event"] for event in events] == [
        "selection_shadow_patch_installed",
        "selection_shadow_metadata_unavailable",
    ]
    assert events[1]["reason"] == "forward-context-attn-metadata-is-none"
    assert events[1]["runtime_mutation"] is False


def test_missing_attention_target_fails_closed(tmp_path):
    with pytest.raises(RuntimeError, match="was not found"):
        _apply_attention_patch(ModuleType("empty"), _config(tmp_path / "events"))
