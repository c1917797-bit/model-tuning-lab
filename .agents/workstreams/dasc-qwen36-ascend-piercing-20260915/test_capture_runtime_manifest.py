import hashlib

import pytest

from capture_runtime_manifest import build


def test_builds_deterministic_labeled_manifest(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.write_bytes(b"model-index")
    second.write_bytes(b"driver")
    result = build([f"model_index={first}", f"driver={second}"])
    assert result["schema"] == "dasc-formal-runtime-manifest/v1"
    assert result["files"]["model_index"]["size"] == 11
    assert result["files"]["model_index"]["sha256"] == hashlib.sha256(
        b"model-index"
    ).hexdigest()


def test_rejects_missing_file(tmp_path):
    with pytest.raises(ValueError, match="missing regular file"):
        build([f"missing={tmp_path / 'absent'}"])


def test_rejects_duplicate_label(tmp_path):
    value = tmp_path / "value"
    value.write_text("x")
    with pytest.raises(ValueError, match="duplicate"):
        build([f"same={value}", f"same={value}"])
