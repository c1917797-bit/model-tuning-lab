from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_qwen35_mmar_async_finalize.py"
)
SPEC = importlib.util.spec_from_file_location("qwen35_mmar_benchmark", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize("feature", MODULE.CANDIDATE_FEATURE_ENVS)
def test_accepts_each_supported_candidate_feature(monkeypatch, feature: str) -> None:
    for name in MODULE.CANDIDATE_FEATURE_ENVS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(feature, "1")

    assert MODULE.require_single_candidate_feature() == feature


def test_rejects_missing_candidate_feature(monkeypatch) -> None:
    for name in MODULE.CANDIDATE_FEATURE_ENVS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="exactly one"):
        MODULE.require_single_candidate_feature()


def test_rejects_multiple_candidate_features(monkeypatch) -> None:
    for name in MODULE.CANDIDATE_FEATURE_ENVS:
        monkeypatch.setenv(name, "1")

    with pytest.raises(RuntimeError, match="exactly one"):
        MODULE.require_single_candidate_feature()
