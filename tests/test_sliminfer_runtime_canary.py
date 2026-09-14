from __future__ import annotations

import json
from types import ModuleType

import pytest

from sliminfer_ascend.config import SlimInferConfig, get_config
from sliminfer_ascend.runtime_patch import _apply_model_patch


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
