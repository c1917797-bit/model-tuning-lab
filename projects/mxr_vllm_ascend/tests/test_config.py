from __future__ import annotations

import pytest

from mxr_vllm_ascend.config import MxrConfig


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MST_MXR_ENABLE", raising=False)
    assert MxrConfig.from_env() == MxrConfig(enabled=False)


def test_enabled_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("MST_MXR_ENABLE", "1")
    monkeypatch.setenv("MST_MXR_BACKEND_MODULE", "candidate")
    monkeypatch.setenv("MST_MXR_EVIDENCE_PATH", str(tmp_path / "evidence.json"))
    monkeypatch.setenv("MST_MXR_EXPECTED_GDN_SHA256", "a" * 64)
    config = MxrConfig.from_env()
    assert config.enabled
    assert config.backend_module == "candidate"
    assert config.expected_gdn_sha256 == "a" * 64


@pytest.mark.parametrize("name", ["MST_MXR_BACKEND_MODULE", "MST_MXR_EVIDENCE_PATH", "MST_MXR_EXPECTED_GDN_SHA256"])
def test_enabled_missing_required_value_fails(monkeypatch, tmp_path, name):
    monkeypatch.setenv("MST_MXR_ENABLE", "1")
    monkeypatch.setenv("MST_MXR_BACKEND_MODULE", "candidate")
    monkeypatch.setenv("MST_MXR_EVIDENCE_PATH", str(tmp_path / "evidence.json"))
    monkeypatch.setenv("MST_MXR_EXPECTED_GDN_SHA256", "a" * 64)
    monkeypatch.delenv(name)
    with pytest.raises(RuntimeError):
        MxrConfig.from_env()
