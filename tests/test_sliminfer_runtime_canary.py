from __future__ import annotations

import json
import sys
from types import ModuleType

import pytest

from sliminfer_ascend.config import SlimInferConfig, get_config
from sliminfer_ascend import runtime_patch
from sliminfer_ascend.runtime_patch import (
    _apply_model_patch,
    _group_layer_mapping,
    _safe_summary,
)


def test_config_is_disabled_by_default(monkeypatch):
    for name in (
        "MST_SLIMINFER_ENABLE",
        "MST_SLIMINFER_MODE",
        "MST_SLIMINFER_EVIDENCE_FILE",
        "MST_SLIMINFER_REQUIRE_RUNTIME_HOOKS",
    ):
        monkeypatch.delenv(name, raising=False)
    config = get_config()
    assert config.enable is False
    assert config.mode == "identity-canary"
    assert config.evidence_file is None
    assert config.require_runtime_hooks is True


def test_config_rejects_unknown_mode(monkeypatch):
    monkeypatch.setenv("MST_SLIMINFER_MODE", "prune-without-proof")
    with pytest.raises(ValueError, match="MST_SLIMINFER_MODE"):
        get_config()


def test_config_accepts_metadata_canary(monkeypatch):
    monkeypatch.setenv("MST_SLIMINFER_MODE", "metadata-canary")
    assert get_config().mode == "metadata-canary"


def test_config_accepts_selection_shadow(monkeypatch):
    monkeypatch.setenv("MST_SLIMINFER_MODE", "selection-shadow")
    assert get_config().mode == "selection-shadow"


def test_config_accepts_semantic_prefill(monkeypatch):
    monkeypatch.setenv("MST_SLIMINFER_MODE", "semantic-prefill")
    assert get_config().mode == "semantic-prefill"


def test_identity_canary_preserves_forward_and_emits_once(tmp_path, monkeypatch):
    evidence = tmp_path / "runtime.jsonl"
    monkeypatch.setenv("MST_SLIMINFER_EVIDENCE_FILE", str(evidence))
    config = SlimInferConfig(
        enable=True,
        mode="identity-canary",
        evidence_file=str(evidence),
        require_runtime_hooks=True,
    )

    class Qwen3_5Model:
        def forward(self, input_ids=None, positions=None, **kwargs):
            return input_ids, positions, kwargs

    module = ModuleType("vllm.model_executor.models.qwen3_5")
    Qwen3_5Model.__module__ = module.__name__
    module.Qwen3_5Model = Qwen3_5Model

    _apply_model_patch(module, config)
    model = Qwen3_5Model()
    assert model.forward(input_ids="ids", positions="pos", marker=7) == (
        "ids",
        "pos",
        {"marker": 7},
    )
    assert model.forward(input_ids="ids2", positions="pos2") == (
        "ids2",
        "pos2",
        {},
    )

    events = [json.loads(line) for line in evidence.read_text().splitlines()]
    assert [item["event"] for item in events] == [
        "model_patch_installed",
        "model_forward_enter",
    ]
    assert events[1]["target_class"] == "Qwen3_5Model"
    assert events[1]["call_index"] == 0
    assert events[1]["forward_context"] is None


def test_safe_summary_never_reads_tensor_values():
    class TensorLike:
        shape = (2, 3)
        dtype = "float16"
        device = "npu:0"

        def is_contiguous(self):
            return True

        def tolist(self):
            raise AssertionError("tensor values must not be read")

    assert _safe_summary(TensorLike()) == {
        "kind": "tensor",
        "type": (
            "test_sliminfer_runtime_canary."
            "test_safe_summary_never_reads_tensor_values.<locals>.TensorLike"
        ),
        "shape": [2, 3],
        "dtype": "float16",
        "device": "npu:0",
        "is_contiguous": True,
    }


def test_layer_mapping_groups_shared_metadata_objects():
    shared = object()
    other = object()
    summary = _group_layer_mapping(
        {"layers.0.attn": shared, "layers.1.attn": shared, "layers.2.attn": other}
    )
    assert summary["layer_count"] == 3
    assert summary["group_count"] == 2
    assert summary["groups"][0]["layer_names"] == [
        "layers.0.attn",
        "layers.1.attn",
    ]


def test_metadata_canary_preserves_forward_and_captures_each_call(
    tmp_path, monkeypatch
):
    evidence = tmp_path / "runtime.jsonl"
    monkeypatch.setenv("MST_SLIMINFER_EVIDENCE_FILE", str(evidence))
    monkeypatch.setattr(
        runtime_patch,
        "_capture_forward_context",
        lambda: {"available": True, "marker": "context"},
    )
    config = SlimInferConfig(
        enable=True,
        mode="metadata-canary",
        evidence_file=str(evidence),
        require_runtime_hooks=True,
    )

    class Qwen3_5Model:
        def forward(self, input_ids=None, positions=None, **kwargs):
            return input_ids, positions, kwargs

    module = ModuleType("vllm.model_executor.models.qwen3_5")
    Qwen3_5Model.__module__ = module.__name__
    module.Qwen3_5Model = Qwen3_5Model

    _apply_model_patch(module, config)
    model = Qwen3_5Model()
    assert model.forward(input_ids="a", positions="p") == ("a", "p", {})
    assert model.forward(input_ids="b", positions="q") == ("b", "q", {})

    events = [json.loads(line) for line in evidence.read_text().splitlines()]
    forward_events = [item for item in events if item["event"] == "model_forward_enter"]
    assert [item["call_index"] for item in forward_events] == [0, 1]
    assert all(
        item["forward_context"] == {"available": True, "marker": "context"}
        for item in forward_events
    )


def test_missing_target_fails_closed():
    module = ModuleType("vllm.model_executor.models.qwen3_5")
    config = SlimInferConfig(
        enable=True,
        mode="identity-canary",
        evidence_file=None,
        require_runtime_hooks=True,
    )
    with pytest.raises(RuntimeError, match="was not found"):
        _apply_model_patch(module, config)


def test_semantic_prefill_allows_only_startup_without_attention_metadata(
    tmp_path, monkeypatch
):
    evidence = tmp_path / "runtime.jsonl"
    monkeypatch.setenv("MST_SLIMINFER_EVIDENCE_FILE", str(evidence))
    config = SlimInferConfig(
        enable=True,
        mode="semantic-prefill",
        evidence_file=str(evidence),
        require_runtime_hooks=True,
    )

    class ForwardContext:
        attn_metadata = None

    forward_context_module = ModuleType("vllm.forward_context")
    forward_context_module.get_forward_context = lambda: ForwardContext()
    monkeypatch.setitem(sys.modules, "vllm.forward_context", forward_context_module)

    class Qwen3_5Model:
        def forward(self, input_ids=None, positions=None, **kwargs):
            return input_ids, positions, kwargs

    module = ModuleType("vllm.model_executor.models.qwen3_5")
    Qwen3_5Model.__module__ = module.__name__
    module.Qwen3_5Model = Qwen3_5Model

    _apply_model_patch(module, config)
    model = Qwen3_5Model()
    assert model.forward(input_ids="dummy", positions="dummy-pos") == (
        "dummy",
        "dummy-pos",
        {},
    )

    events = [json.loads(line) for line in evidence.read_text().splitlines()]
    unavailable = [
        item
        for item in events
        if item["event"] == "semantic_prefill_metadata_unavailable"
    ]
    assert len(unavailable) == 1
    assert unavailable[0]["runtime_mutation"] is False
    assert unavailable[0]["reason"] == "forward-context-attn-metadata-is-none"
