"""Software-only sensitivity capture tests; no model, service, or NPU."""

import hashlib
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType
from unittest import mock

import pytest
import torch

from tools import collect_gdn_sensitivity_calibration as collector
from tools import run_gdn_teacher_capture as launcher


def token_hash(ids):
    return hashlib.sha256(
        json.dumps(ids, separators=(",", ":")).encode()
    ).hexdigest()


def write_calibration(path):
    rows = []
    for index in range(16):
        ids = [index + 1] + list(range(1, 2048))
        rows.append(
            {
                "schema": "drrqr-calibration-sample/v2",
                "index": index,
                "token_count": 2048,
                "input_ids": ids,
                "input_ids_sha256": token_hash(ids),
            }
        )
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return hashlib.sha256(path.read_bytes()).hexdigest(), rows


def test_manifest_uses_exact_unique_raw_prefixes_and_frozen_split(tmp_path):
    calibration = tmp_path / "calibration.jsonl"
    digest, rows = write_calibration(calibration)
    output = tmp_path / "prepared"
    with mock.patch.object(collector, "CALIBRATION_SHA256", digest):
        receipt = collector.prepare(output, calibration)
        manifest = collector.load_manifest(
            output / "manifest.json", receipt["manifest_sha256"]
        )
    assert manifest["raw_token_prompts"] is True
    assert manifest["add_special_tokens"] is False
    assert len(manifest["sequences"]) == 16
    assert manifest["sequences"][7]["input_ids"] == rows[7]["input_ids"][:128]
    assert manifest["source_calibration"]["selector_train_indices"] == list(range(12))
    assert manifest["source_calibration"]["selector_heldout_indices"] == list(range(12, 16))
    payload = collector.payload_for(manifest["sequences"][0])
    assert payload["prompt"] == rows[0]["input_ids"][:128]
    assert payload["add_special_tokens"] is False
    assert payload["max_tokens"] == 9
    assert payload["ignore_eos"] is True


@pytest.fixture
def sensitivity_worker(monkeypatch):
    stub = ModuleType("vllm_ascend.worker.worker")
    stub.NPUWorker = type("FakeNPUWorker", (), {})
    monkeypatch.setitem(sys.modules, "vllm_ascend.worker.worker", stub)
    root = Path(__file__).resolve().parents[1]
    for name, filename in (
        ("layerwise_probe_worker", "layerwise_probe_worker.py"),
        ("gdn_teacher_capture_worker", "gdn_teacher_capture_worker.py"),
        ("gdn_sensitivity_capture_worker", "gdn_sensitivity_capture_worker.py"),
    ):
        spec = importlib.util.spec_from_file_location(
            name, root / "tools" / filename
        )
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
    return module


def test_worker_manifest_and_sequence_order_are_fail_closed(
    sensitivity_worker, tmp_path
):
    module = sensitivity_worker
    sequences = []
    for index in range(16):
        ids = [index + 1] + list(range(1, 128))
        sequences.append(
            {
                "id": f"calibration-{index:02d}",
                "source_index": index,
                "input_ids": ids,
                "input_ids_sha256": module.base.ids_sha256(ids),
                "source_input_ids_sha256": f"{index:064x}",
            }
        )
    manifest = {
        "schema": module.SCHEMA,
        "model": module.base.MODEL,
        "tp_size": 4,
        "input_tokens": 128,
        "decode_steps": 8,
        "output_tokens": 9,
        "no_thinking": True,
        "raw_token_prompts": True,
        "add_special_tokens": False,
        "layers": [0, 12],
        "source_calibration": {"rows": 16, "sha256": "a" * 64},
        "sequences": sequences,
    }
    assert module.validate_manifest(manifest) is manifest
    bad = json.loads(json.dumps(manifest))
    bad["add_special_tokens"] = True
    with pytest.raises(RuntimeError, match="add_special_tokens"):
        module.validate_manifest(bad)

    worker = module.GdnSensitivityCaptureWorker()
    worker._manifest = manifest
    worker._teacher_dir = Path("/nonexistent")
    worker._frame = worker._current = None
    worker._pending = {}
    worker._nonces = {}
    worker._steps = {}
    worker._teacher_dir = tmp_path / "sensitivity-order"
    worker._teacher_dir.mkdir()
    with pytest.raises(RuntimeError, match="ordering"):
        sequence = sequences[1]
        (worker._teacher_dir / "armed.json").write_text(
            json.dumps(
                {
                    "schema": module.SCHEMA,
                    "sequence_id": sequence["id"],
                    "input_ids_sha256": sequence["input_ids_sha256"],
                    "nonce": "0123456789abcdef",
                }
            )
        )
        worker._model_before(
            None,
            (),
            {
                "input_ids": torch.tensor(sequence["input_ids"]),
                "positions": torch.arange(128),
            },
        )


def test_launcher_accepts_only_explicit_repo_worker_path(tmp_path):
    repo = tmp_path / "repo"
    tools = repo / "tools"
    tools.mkdir(parents=True)
    worker = tools / "gdn_sensitivity_capture_worker.py"
    worker.write_text("# sensitivity worker\n")
    capture = tmp_path / "capture.json"
    capture.write_text("{}\n")
    build = tmp_path / "build.json"
    build.write_text("{}\n")
    output = tmp_path / "output"
    arguments = [
        "--build-manifest", str(build),
        "--build-manifest-sha256", launcher.shared.digest(build),
        "--reference-manifest-sha256", "a" * 64,
        "--worker-sha256", launcher.shared.digest(worker),
        "--worker-path", str(worker),
        "--worker-class", collector.WORKER_CLASS,
        "--capture-manifest", str(capture),
        "--capture-manifest-sha256", launcher.shared.digest(capture),
        "--output-dir", str(output),
    ]
    with mock.patch.object(launcher, "ROOT", repo):
        args = launcher.parse_args(arguments)[1]
        command = launcher.service_command(worker_class=args.worker_class)
    assert command[command.index("--worker-cls") + 1] == collector.WORKER_CLASS
