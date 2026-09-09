"""CPU-only structural tests for the distinct captured-reference replay."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
import pytest
import torch


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "tools/replay_gdn_teacher_captured_reference.py"
)
spec = importlib.util.spec_from_file_location("captured_reference_under_test", SOURCE)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return candidate.checksum(path)


def original_fixture():
    return {
        "script_sha256": candidate.ORIGINAL_SCRIPT_SHA256,
        "status": "failed_runtime_evidence",
        "dense_gate_passed": False,
        "candidate_numerical_gate_passed": False,
        "trajectories": [{
            "variant": "dense128", "sequence_id": "teacher-0",
            "rank": 0, "layer": 0,
            "steps": [{"step": 0, "metrics": {
                "full_state_cpu": {"passed": False},
                "output_capture": {"passed": True},
                "full_state_capture": {"passed": True},
                "post_rms_capture": {"passed": True},
            }}],
        }],
    }


def synthetic_fixture():
    return {
        "schema": "drrqr-retained-key-beta-probe/v1",
        "status": "synthetic_retained_key_beta_implementation_pass",
        "raw_sha256": candidate.SYNTHETIC_RAW_SHA256,
        "cases": [
            {"status": "passed", "all_checks_passed": True} for _ in range(4)
        ],
    }


def test_prior_evidence_binds_both_distinct_gates(tmp_path, monkeypatch):
    original = tmp_path / "original.json"
    synthetic = tmp_path / "synthetic.json"
    monkeypatch.setattr(
        candidate, "ORIGINAL_REPORT_SHA256", write_json(original, original_fixture()))
    monkeypatch.setattr(
        candidate, "SYNTHETIC_SUMMARY_SHA256", write_json(synthetic, synthetic_fixture()))
    result = candidate.validate_prior_evidence(original, synthetic)
    assert result["original_failed_replay"]["preserved_failure"].startswith(
        "independent FP32")
    assert result["synthetic_beta_gate"]["raw_sha256"] == candidate.SYNTHETIC_RAW_SHA256


@pytest.mark.parametrize("damage", ("old_failure", "capture", "synthetic"))
def test_prior_evidence_rejects_reclassification(tmp_path, monkeypatch, damage):
    old, synth = original_fixture(), synthetic_fixture()
    if damage == "old_failure":
        old["trajectories"][0]["steps"][0]["metrics"]["full_state_cpu"]["passed"] = True
    elif damage == "capture":
        old["trajectories"][0]["steps"][0]["metrics"]["full_state_capture"]["passed"] = False
    else:
        synth["cases"][3]["all_checks_passed"] = False
    original, synthetic = tmp_path / "original.json", tmp_path / "synthetic.json"
    monkeypatch.setattr(
        candidate, "ORIGINAL_REPORT_SHA256", write_json(original, old))
    monkeypatch.setattr(
        candidate, "SYNTHETIC_SUMMARY_SHA256", write_json(synthetic, synth))
    with pytest.raises(ValueError):
        candidate.validate_prior_evidence(original, synthetic)


def test_finite_bytes_distinguishes_signed_zero_and_nonfinite():
    replay = candidate.load_replay()
    positive = torch.tensor([0.0], dtype=torch.float32)
    negative = torch.tensor([-0.0], dtype=torch.float32)
    assert candidate.finite_bytes(positive, replay)
    assert not replay.exact(positive, negative)
    assert not candidate.finite_bytes(torch.tensor([float("nan")]), replay)


def test_protocol_keeps_old_replay_immutable_and_claim_ceiling():
    replay = candidate.load_replay()
    assert candidate.checksum(candidate.REPLAY_PATH) == candidate.REPLAY_SHA256
    assert replay.VARIANTS == candidate.VARIANTS
    assert "Not an independent dense arithmetic oracle" in candidate.CLAIM
    assert "throughput" in candidate.CLAIM


def test_runtime_library_evidence_requires_native_opapi_mapping():
    valid = [{"path": "/opt/op/libcust_opapi.so", "sha256": "a" * 64}]
    runtime = SimpleNamespace(
        probe=SimpleNamespace(loaded_libraries=lambda: valid))
    assert candidate.validated_runtime_libraries(runtime) == valid
    runtime.probe.loaded_libraries = lambda: []
    with pytest.raises(ValueError, match="empty"):
        candidate.validated_runtime_libraries(runtime)
    runtime.probe.loaded_libraries = lambda: [
        {"path": "/opt/op/libopapi.so", "sha256": "a" * 64}]
    with pytest.raises(ValueError, match="native opapi"):
        candidate.validated_runtime_libraries(runtime)


def test_main_initializes_frozen_runtime_source_hash_mapping():
    source = SOURCE.read_text(encoding="utf-8")
    assert '"source_sha256": {}' in source
