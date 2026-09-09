"""CPU-only teacher collector protocol tests; no model/service/NPU execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

SOURCE = Path(__file__).resolve().parents[1] / "tools/collect_gdn_teacher.py"
spec = importlib.util.spec_from_file_location("teacher_collector_test", SOURCE)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def write_json(path, value):
    path.write_text(json.dumps(value))


def manifest_data():
    return {
        "schema": collector.SCHEMA, "model": collector.MODEL,
        "served_model": collector.SERVED_MODEL, "layers": collector.LAYERS,
        "tp_size": 4, "input_tokens": 128, "decode_steps": 8, "output_tokens": 9,
        "no_thinking": True, "synthetic_text": True,
        "chat_template": {"tokenize": True, "return_dict": False,
                          "add_generation_prompt": True, "enable_thinking": False},
        "old_calibration": {"sha256": collector.OLD_CALIBRATION_SHA256, "rows": 16,
                            "complete_token_sequences_disjoint": True,
                            "selector_holdout_validation": False},
        "sequences": [
            {"id": f"teacher-{index}", "input_ids": list(range(1000 * index, 1000 * index + 128)),
             "input_ids_sha256": collector.token_hash(list(range(1000 * index, 1000 * index + 128)))}
            for index in range(2)],
    }


def fixture_files(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "RESULT_ROOT", tmp_path)
    service = tmp_path / "service"
    service.mkdir()
    capture = service / "teacher-capture"
    capture.mkdir()
    manifest = tmp_path / "manifest.json"
    write_json(manifest, manifest_data())
    sha = collector.digest(manifest)
    service_data = {
        "schema": "drrqr-gdn-teacher-service/v1", "variant": "dense128",
        "model": collector.MODEL, "shared_hf_head_k_dim": 128,
        "tensor_parallel_size": 4, "calibration_only": True, "enforce_eager": True,
        "profiler_config": None, "capture_manifest": str(manifest),
        "capture_manifest_sha256": sha, "capture_manifest_schema": collector.SCHEMA,
        "stop_request_path": str(service / "stop.request"),
        "observer_flags": {
            "DRRQR_GDN_TEACHER_MANIFEST": str(manifest),
            "DRRQR_GDN_TEACHER_MANIFEST_SHA256": sha,
            "DRRQR_GDN_TEACHER_DIR": str(capture)},
    }
    write_json(service / "service-manifest.json", service_data)
    return service, capture, manifest, sha


def response_data():
    return {"choices": [{"token_ids": list(range(70, 79)), "finish_reason": "length",
                         "logprobs": {"token_logprobs": [-0.1] * 9}}],
            "usage": {"prompt_tokens": 128, "completion_tokens": 9}}


def worker_completions(capture, sequence, ids, *, layers=None, bad_rank=None, missing_rank=None):
    layers = list(collector.LAYERS if layers is None else layers)
    arm = json.loads((capture / "armed.json").read_text())
    for rank in range(4):
        if rank == missing_rank:
            continue
        data = {"schema": collector.SCHEMA, "sequence_id": sequence["id"], "rank": rank,
                "nonce": arm["nonce"], "steps": 9, "layers": len(layers),
                "records": 9 * len(layers), "layer_ids": layers,
                "input_ids_per_step": [sequence["input_ids"]] + [[x] for x in ids[:8]]}
        if rank == bad_rank:
            data["input_ids_per_step"][-1] = [999]
        write_json(capture / f'{sequence["id"]}.rank{rank}.complete.json', data)


class FakeTokenizer:
    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        text = messages[0]["content"]
        padding = text.count(" context")
        offset = 1000 if "ferry" in text else 0
        return [5001] + list(range(offset, offset + 50 + padding)) + [5002, 5003, 5004]


def test_prepare_exact_full_template_and_disjointness(tmp_path, monkeypatch):
    calibration = tmp_path / "old.jsonl"
    calibration.write_text("fixture")
    monkeypatch.setattr(collector, "read_old_calibration", lambda path: set())
    tokenizer = FakeTokenizer()
    output = tmp_path / "prepared"
    receipt = collector.prepare(output, calibration, tokenizer)
    manifest = collector.load_manifest(output / "manifest.json", receipt["manifest_sha256"])
    assert len(manifest["sequences"]) == 2
    for sequence in manifest["sequences"]:
        assert len(sequence["input_ids"]) == 128
        assert sequence["input_ids"][-3:] == [5002, 5003, 5004]
        assert sequence["input_ids_sha256"] == collector.token_hash(sequence["input_ids"])
    assert manifest["no_thinking"] is True
    assert manifest["old_calibration"]["selector_holdout_validation"] is False
    assert "Synthetic self-written text" in manifest["claim"]
    assert all(kwargs == {"tokenize": True, "return_dict": False,
                          "add_generation_prompt": True, "enable_thinking": False}
               for _, kwargs in tokenizer.calls)
    before = (output / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        collector.prepare(output, calibration, tokenizer)
    assert (output / "manifest.json").read_bytes() == before


def test_prepare_preserves_failure_when_disjointness_fails(tmp_path, monkeypatch):
    tokenizer = FakeTokenizer()
    _, ids, _ = collector.make_prompt(tokenizer, collector.PROMPTS[0])
    calibration = tmp_path / "old.jsonl"
    calibration.write_text("fixture")
    monkeypatch.setattr(collector, "read_old_calibration", lambda path: {collector.token_hash(ids)})
    output = tmp_path / "failed"
    with pytest.raises(ValueError, match="disjoint"):
        collector.prepare(output, calibration, tokenizer)
    assert not (output / "manifest.json").exists()
    assert json.loads((output / "prepare-receipt.json").read_text())["status"] == "failed"


def test_canonical_token_hash_and_strict_ids():
    ids = [1, 2, 3]
    assert collector.token_hash(ids) == hashlib.sha256(b"[1,2,3]").hexdigest()
    for invalid in ([], [True], [-1], [[1]], [1.0]):
        with pytest.raises(ValueError):
            collector.token_hash(invalid)


def test_old_calibration_format_hash_and_internal_ids(tmp_path):
    rows = []
    for index in range(16):
        ids = [index] * 2048
        rows.append({"schema": "drrqr-calibration-sample/v2", "index": index,
                     "token_count": 2048, "input_ids": ids,
                     "input_ids_sha256": collector.token_hash(ids)})
    path = tmp_path / "old.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    assert len(collector.read_old_calibration(path, collector.digest(path))) == 16
    with pytest.raises(ValueError, match="SHA256"):
        collector.read_old_calibration(path, "0" * 64)
    rows[4]["input_ids_sha256"] = "0" * 64
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    with pytest.raises(ValueError, match="token hash"):
        collector.read_old_calibration(path, collector.digest(path))


@pytest.mark.parametrize("field,value", [
    ("decode_steps", 9), ("output_tokens", 8), ("no_thinking", False), ("no_thinking", 1),
    ("layers", [0, 0]), ("tp_size", 1), ("model", "/other")])
def test_manifest_protocol_fails_closed(tmp_path, field, value):
    data = manifest_data()
    data[field] = value
    path = tmp_path / "manifest.json"
    write_json(path, data)
    with pytest.raises(ValueError):
        collector.load_manifest(path, collector.digest(path))


def test_manifest_accepts_frozen_dynamic_layer_set(tmp_path):
    data = manifest_data()
    data["layers"] = list(range(48))
    path = tmp_path / "manifest.json"
    write_json(path, data)
    assert collector.load_manifest(path, collector.digest(path))["layers"] == data["layers"]


def test_manifest_sequence_hash_and_duplicate_fail_closed(tmp_path):
    data = manifest_data()
    data["sequences"][1]["input_ids"] = data["sequences"][0]["input_ids"]
    data["sequences"][1]["input_ids_sha256"] = data["sequences"][0]["input_ids_sha256"]
    path = tmp_path / "manifest.json"
    write_json(path, data)
    with pytest.raises(ValueError, match="identity"):
        collector.load_manifest(path, collector.digest(path))


def test_payload_uses_verified_raw_token_endpoint_and_nine_outputs():
    sequence = manifest_data()["sequences"][0]
    payload = collector.payload_for(sequence)
    assert payload["prompt"] == sequence["input_ids"]
    assert payload["return_token_ids"] is True and payload["logprobs"] == 5
    assert payload["max_tokens"] == 9 and payload["ignore_eos"] is True
    assert payload["stream"] is False and payload["temperature"] == payload["seed"] == 0


def test_run_sequential_responses_and_four_worker_trajectory_gates(tmp_path, monkeypatch):
    service, capture, manifest, sha = fixture_files(tmp_path, monkeypatch)
    monkeypatch.setattr(collector, "wait_health", lambda service: None)
    calls = []

    def send(sequence):
        if calls:
            assert (capture / "teacher-0.response.json").is_file()
        calls.append(sequence["id"])
        assert len(calls) <= 2
        result = response_data()
        worker_completions(capture, sequence, result["choices"][0]["token_ids"])
        return result

    monkeypatch.setattr(collector, "send_completion", send)
    result = collector.run(service, manifest, sha)
    assert calls == ["teacher-0", "teacher-1"]
    assert result["status"] == "teacher_capture_complete_local_fidelity_only"
    assert len(result["results"]) == 2
    assert all(len(item["worker_reports"]) == 4 for item in result["results"])
    assert not (capture / "armed.json").exists()
    assert (service / "stop.request").is_file()
    assert (service / "teacher-collector.json").is_file()


@pytest.mark.parametrize("failure", ("missing_rank", "wrong_token", "worker_error", "bad_response"))
def test_failure_saves_response_stops_and_never_sends_second(tmp_path, monkeypatch, failure):
    service, capture, manifest, sha = fixture_files(tmp_path, monkeypatch)
    monkeypatch.setattr(collector, "wait_health", lambda service: None)
    calls = []

    def send(sequence):
        calls.append(sequence["id"])
        result = response_data()
        worker_completions(capture, sequence, result["choices"][0]["token_ids"],
                           bad_rank=2 if failure == "wrong_token" else None,
                           missing_rank=3 if failure == "missing_rank" else None)
        if failure == "worker_error":
            write_json(capture / "rank1.failure.json", {"error": "intentional failure"})
        if failure == "bad_response":
            result["choices"][0]["token_ids"] = [1]
        return result

    monkeypatch.setattr(collector, "send_completion", send)
    with pytest.raises((ValueError, RuntimeError)):
        collector.run(service, manifest, sha)
    assert calls == ["teacher-0"]
    assert (capture / "teacher-0.response.json").exists()
    assert not (capture / "teacher-1.response.json").exists()
    assert not (capture / "armed.json").exists()
    assert (service / "stop.request").exists()
    report = json.loads((service / "teacher-collector.json").read_text())
    assert report["status"] == "failed" and report["last_arm"]["sequence_id"] == "teacher-0"


def test_request_exception_no_retry_and_failed_receipt(tmp_path, monkeypatch):
    service, capture, manifest, sha = fixture_files(tmp_path, monkeypatch)
    monkeypatch.setattr(collector, "wait_health", lambda service: None)
    calls = []
    def send(sequence):
        calls.append(sequence["id"])
        raise TimeoutError("intentional request timeout")
    monkeypatch.setattr(collector, "send_completion", send)
    with pytest.raises(TimeoutError, match="intentional"):
        collector.run(service, manifest, sha)
    assert calls == ["teacher-0"] and (service / "stop.request").exists()
    assert json.loads((service / "teacher-collector.json").read_text())["status"] == "failed"


def test_duplicate_collector_cannot_stop_owner_or_send_requests(tmp_path, monkeypatch):
    service, capture, manifest, sha = fixture_files(tmp_path, monkeypatch)
    collector.publish(service / "teacher-collector.claim.json", {"owner": "first"})
    def unexpected(*args):
        raise AssertionError("duplicate collector performed an action")
    monkeypatch.setattr(collector, "wait_health", unexpected)
    monkeypatch.setattr(collector, "send_completion", unexpected)
    with pytest.raises(FileExistsError):
        collector.run(service, manifest, sha)
    assert not (service / "stop.request").exists()
    assert not (service / "teacher-collector.json").exists()


def test_launcher_binding_mismatch_stops_before_request(tmp_path, monkeypatch):
    service, capture, manifest, sha = fixture_files(tmp_path, monkeypatch)
    monkeypatch.setattr(collector, "wait_health", lambda service: None)
    data = json.loads((service / "service-manifest.json").read_text())
    data["capture_manifest_sha256"] = "0" * 64
    write_json(service / "service-manifest.json", data)
    monkeypatch.setattr(collector, "send_completion",
                        lambda sequence: pytest.fail("must not request mismatched service"))
    with pytest.raises(ValueError, match="binding"):
        collector.run(service, manifest, sha)
    assert (service / "stop.request").exists()
    assert not (capture / "armed.json").exists()


def test_health_timeout_is_bounded_and_worker_failure_is_immediate(tmp_path, monkeypatch):
    service, capture, manifest, sha = fixture_files(tmp_path, monkeypatch)
    times = iter((0.0, 901.0))
    monkeypatch.setattr(collector.time, "monotonic", lambda: next(times))
    def unavailable(*args, **kwargs):
        raise OSError("not up")
    monkeypatch.setattr(collector, "urlopen", unavailable)
    monkeypatch.setattr(collector.time, "sleep", lambda seconds: pytest.fail("budget expired"))
    with pytest.raises(TimeoutError, match="900"):
        collector.wait_health(service)
    monkeypatch.setattr(collector.time, "monotonic", lambda: 0.0)
    write_json(capture / "rank0.failure.json", {"error": "failed"})
    with pytest.raises(RuntimeError, match="worker failure"):
        collector.wait_health(service)


def test_owned_arm_cannot_remove_different_nonce(tmp_path):
    arm = {"schema": collector.SCHEMA, "sequence_id": "teacher-0", "nonce": "owner"}
    write_json(tmp_path / "armed.json", {**arm, "nonce": "someone-else"})
    with pytest.raises(RuntimeError, match="ownership"):
        collector.clear_owned_arm(tmp_path, arm)
    assert (tmp_path / "armed.json").is_file()


def test_absolute_paths_reject_symlinks(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError):
        collector.absolute_path(alias)
