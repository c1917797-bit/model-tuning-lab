#!/usr/bin/env python3
"""Two synthetic-text, real-model teacher sequences; local fidelity only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import traceback
from urllib.request import Request, urlopen
import uuid

SCHEMA = "gdn-teacher-capture-v1"
MODEL = "/cache/austinov/Qwen3.8-27B"
SERVED_MODEL = "qwen3.8"
RESULT_ROOT = Path("/drrqr-results")
LAYERS = [0, 12, 25, 38, 50, 62]
TP_SIZE, INPUT_TOKENS, DECODE_STEPS, OUTPUT_TOKENS = 4, 128, 8, 9
HEALTH_SECONDS = 900
OLD_CALIBRATION_SHA256 = "81748f94c4eff0ad5e4053eb7c4a30b1a397a82d45676a8b0b42394bd612bd47"
HASH = re.compile(r"^[0-9a-f]{64}$")
PROMPTS = (
    "This is an invented workshop notebook, not an examination. Mira keeps blue "
    "wooden blocks in one box and round copper buttons in another. Each morning "
    "she checks that the labels match the contents, then writes a short note. "
    "Describe a sensible way for Mira to keep this imaginary workspace orderly.",
    "This is an invented travel diary, not an examination. A small ferry crosses "
    "a quiet lake between a garden and a village. The captain watches the wind "
    "and the passengers bring sketchbooks. Describe a calm afternoon on this "
    "imaginary ferry in a few ordinary sentences.",
)
CLAIM = (
    "Synthetic self-written text with actual dense-model tensors, for local algorithm "
    "fidelity calibration only. Distinct complete input token sequences from the old "
    "16 calibration rows do not establish selector-heldout validation or task "
    "generalization. Not final accuracy, performance, or throughput evaluation."
)


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    return digest_bytes(Path(path).read_bytes())


def valid_ids(ids, length=None):
    return (isinstance(ids, list) and bool(ids)
            and (length is None or len(ids) == length)
            and all(type(token) is int and token >= 0 for token in ids))


def validate_layers(value):
    if (not isinstance(value, list) or not 1 <= len(value) <= 48
            or any(type(layer) is not int or not 0 <= layer <= 63 for layer in value)
            or value != sorted(set(value))):
        raise ValueError("layers must be 1..48 sorted unique model layer IDs in [0, 63]")
    return list(value)


def parse_layers(value):
    try:
        layers = [int(item) for item in value.split(",")]
    except (AttributeError, ValueError) as error:
        raise argparse.ArgumentTypeError("layers must be comma-separated integers") from error
    try:
        return validate_layers(layers)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def token_hash(ids):
    if not valid_ids(ids):
        raise ValueError("expected nonempty flat nonnegative integer token IDs")
    return digest_bytes(json.dumps(ids, separators=(",", ":")).encode())


def publish(path, record):
    """Exclusive publication; never overwrite an earlier complete/partial receipt."""
    if path.exists() or path.is_symlink():
        raise FileExistsError("existing receipt: " + str(path))
    partial = path.with_name(path.name + ".partial")
    with partial.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def absolute_path(path, *, below_results=False):
    path = Path(path)
    if not path.is_absolute() or path != path.resolve():
        raise ValueError("absolute non-symlink path required")
    if below_results and RESULT_ROOT.resolve() not in path.parents:
        raise ValueError("service directory must be below /drrqr-results")
    return path


def read_old_calibration(path, expected=OLD_CALIBRATION_SHA256):
    raw = Path(path).read_bytes()
    if digest_bytes(raw) != expected:
        raise ValueError("old calibration SHA256 mismatch")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    if len(rows) != 16:
        raise ValueError("expected the frozen 16 calibration rows")
    hashes = []
    for index, row in enumerate(rows):
        ids = row.get("input_ids")
        if (row.get("schema") != "drrqr-calibration-sample/v2"
                or row.get("index") != index or row.get("token_count") != 2048
                or not valid_ids(ids, 2048)):
            raise ValueError("old calibration row format mismatch")
        actual = token_hash(ids)
        if row.get("input_ids_sha256") != actual or actual in hashes:
            raise ValueError("old calibration token hash/uniqueness mismatch")
        hashes.append(actual)
    return set(hashes)


def make_prompt(tokenizer, text):
    # Never truncate template IDs: each candidate is templated in full, preserving
    # the complete no-thinking assistant/generation suffix.
    for count in range(INPUT_TOKENS + 1):
        content = text + " context" * count
        ids = tokenizer.apply_chat_template(
            [{"role": "user", "content": content}], tokenize=True, return_dict=False,
            add_generation_prompt=True, enable_thinking=False)
        if not valid_ids(ids):
            raise ValueError("tokenizer must return flat integer token IDs")
        if len(ids) == INPUT_TOKENS:
            return content, ids, count
    raise ValueError("bounded user-content padding cannot produce exactly 128 full-template IDs")


def prepare(output_dir, calibration, tokenizer=None, layers=None):
    output = absolute_path(output_dir)
    calibration = absolute_path(calibration)
    output.mkdir(parents=False, exist_ok=False)
    receipt = {"schema": SCHEMA, "status": "failed", "script_sha256": digest(__file__)}
    try:
        old_hashes = read_old_calibration(calibration)
        layers = validate_layers(list(LAYERS) if layers is None else layers)
        if tokenizer is None:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                MODEL, trust_remote_code=True, local_files_only=True)
        sequences = []
        for index, text in enumerate(PROMPTS):
            content, ids, padding_count = make_prompt(tokenizer, text)
            hashed = token_hash(ids)
            if hashed in old_hashes or any(x["input_ids_sha256"] == hashed for x in sequences):
                raise ValueError("teacher input token sequence is not disjoint")
            sequences.append({"id": f"teacher-{index}", "input_ids": ids,
                              "input_ids_sha256": hashed, "synthetic_text": content,
                              "padding_context_repetitions": padding_count})
        manifest = {
            "schema": SCHEMA, "model": MODEL, "served_model": SERVED_MODEL,
            "layers": layers, "tp_size": TP_SIZE, "input_tokens": INPUT_TOKENS,
            "decode_steps": DECODE_STEPS, "output_tokens": OUTPUT_TOKENS,
            "no_thinking": True, "sequences": sequences,
            "chat_template": {"tokenize": True, "return_dict": False,
                              "add_generation_prompt": True, "enable_thinking": False},
            "synthetic_text": True, "claim": CLAIM,
            "old_calibration": {"path": str(calibration), "sha256": OLD_CALIBRATION_SHA256,
                                "rows": 16, "complete_token_sequences_disjoint": True,
                                "selector_holdout_validation": False},
            "tokenizer_class": type(tokenizer).__name__,
            "tokenizer_files_sha256": {
                name: digest(Path(MODEL) / name)
                for name in ("config.json", "tokenizer.json", "tokenizer_config.json",
                             "special_tokens_map.json", "chat_template.jinja")
                if (Path(MODEL) / name).is_file()
            },
            "script_sha256": digest(__file__),
        }
        path = output / "manifest.json"
        publish(path, manifest)
        receipt.update(status="prepared", manifest=str(path), manifest_sha256=digest(path))
        return receipt
    except BaseException as error:
        receipt.update(error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        publish(output / "prepare-receipt.json", receipt)


def load_manifest(path, expected):
    path = absolute_path(path)
    raw = path.read_bytes()
    if not HASH.fullmatch(expected) or digest_bytes(raw) != expected:
        raise ValueError("teacher manifest SHA256 mismatch")
    manifest = json.loads(raw)
    required = {"schema": SCHEMA, "model": MODEL, "served_model": SERVED_MODEL,
                "tp_size": TP_SIZE, "input_tokens": INPUT_TOKENS,
                "decode_steps": DECODE_STEPS, "output_tokens": OUTPUT_TOKENS,
                "no_thinking": True, "synthetic_text": True}
    if (any(manifest.get(key) != value for key, value in required.items())
            or manifest.get("no_thinking") is not True or manifest.get("synthetic_text") is not True):
        raise ValueError("teacher manifest fixed protocol mismatch")
    validate_layers(manifest.get("layers"))
    if manifest.get("chat_template") != {
            "tokenize": True, "return_dict": False, "add_generation_prompt": True,
            "enable_thinking": False}:
        raise ValueError("no-thinking full-template binding missing")
    old = manifest.get("old_calibration", {})
    if (old.get("sha256") != OLD_CALIBRATION_SHA256 or old.get("rows") != 16
            or old.get("complete_token_sequences_disjoint") is not True
            or old.get("selector_holdout_validation") is not False):
        raise ValueError("old calibration disjointness/boundary binding missing")
    sequences = manifest.get("sequences")
    if not isinstance(sequences, list) or len(sequences) != 2:
        raise ValueError("expected exactly two sequences")
    hashes = set()
    for index, sequence in enumerate(sequences):
        ids = sequence.get("input_ids")
        if (sequence.get("id") != f"teacher-{index}" or not valid_ids(ids, INPUT_TOKENS)
                or sequence.get("input_ids_sha256") != token_hash(ids)
                or sequence["input_ids_sha256"] in hashes):
            raise ValueError("teacher sequence identity mismatch")
        hashes.add(sequence["input_ids_sha256"])
    return manifest


def worker_failures(capture):
    failures = [capture / f"rank{rank}.failure.json" for rank in range(TP_SIZE)]
    present = [str(path) for path in failures if path.exists() or path.is_symlink()]
    if present:
        raise RuntimeError("worker failure evidence present: " + ", ".join(present))


def wait_health(service):
    deadline = time.monotonic() + HEALTH_SECONDS
    while True:
        worker_failures(service / "teacher-capture")
        if (service / "service-exit.json").exists() or (service / "stop.request").exists():
            raise RuntimeError("service stopped before requests")
        if (service / "service-manifest.json").is_file():
            try:
                with urlopen("http://127.0.0.1:6666/health", timeout=3) as response:
                    if response.status == 200:
                        return
            except OSError:
                pass
        if time.monotonic() >= deadline:
            raise TimeoutError("900-second health budget expired")
        time.sleep(3)


def bind_service(service, manifest_path, manifest_sha):
    path = service / "service-manifest.json"
    raw = path.read_bytes()
    data = json.loads(raw)
    required = {"schema": "drrqr-gdn-teacher-service/v1", "variant": "dense128",
                "model": MODEL, "shared_hf_head_k_dim": 128, "tensor_parallel_size": 4,
                "calibration_only": True, "enforce_eager": True, "profiler_config": None,
                "capture_manifest": str(manifest_path),
                "capture_manifest_sha256": manifest_sha,
                "capture_manifest_schema": SCHEMA,
                "stop_request_path": str(service / "stop.request")}
    if any(data.get(key) != value for key, value in required.items()):
        raise ValueError("launcher service/teacher manifest binding mismatch")
    observer = data.get("observer_flags", {})
    if (observer.get("DRRQR_GDN_TEACHER_MANIFEST") != str(manifest_path)
            or observer.get("DRRQR_GDN_TEACHER_MANIFEST_SHA256") != manifest_sha
            or observer.get("DRRQR_GDN_TEACHER_DIR") != str(service / "teacher-capture")):
        raise ValueError("worker observer binding mismatch")
    return digest_bytes(raw)


def payload_for(sequence):
    return {"model": SERVED_MODEL, "prompt": sequence["input_ids"], "temperature": 0,
            "seed": 0, "max_tokens": OUTPUT_TOKENS, "ignore_eos": True,
            "return_token_ids": True, "logprobs": 5, "stream": False}


def send_completion(sequence):
    request = Request("http://127.0.0.1:6666/v1/completions",
                      data=json.dumps(payload_for(sequence)).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
    # One attempt only. Health polling is the only retry loop in this collector.
    with urlopen(request, timeout=600) as response:
        raw = response.read(1024 * 1024 + 1)
        if response.status != 200 or len(raw) > 1024 * 1024:
            raise RuntimeError("completion HTTP status/body budget mismatch")
    return json.loads(raw)


def validate_response(result):
    choices = result.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("expected one completion choice")
    choice = choices[0]
    ids = choice.get("token_ids")
    scores = (choice.get("logprobs") or {}).get("token_logprobs")
    if (result.get("usage", {}).get("prompt_tokens") != INPUT_TOKENS
            or result.get("usage", {}).get("completion_tokens") != OUTPUT_TOKENS
            or choice.get("finish_reason") != "length"
            or not valid_ids(ids, OUTPUT_TOKENS)
            or not isinstance(scores, list) or len(scores) != OUTPUT_TOKENS
            or any(type(score) not in (int, float) or not math.isfinite(score) for score in scores)):
        raise ValueError("completion token/logprob/usage coverage mismatch")
    return ids, scores


def verify_workers(capture, sequence, nonce, output_ids, layers=None):
    layers = validate_layers(list(LAYERS) if layers is None else layers)
    layer_count = len(layers)
    record_count = 9 * layer_count
    worker_failures(capture)
    expected_inputs = [sequence["input_ids"]] + [[token] for token in output_ids[:DECODE_STEPS]]
    records = []
    for rank in range(TP_SIZE):
        path = capture / f'{sequence["id"]}.rank{rank}.complete.json'
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("missing regular worker completion receipt: " + str(path))
        raw = path.read_bytes()
        item = json.loads(raw)
        required = {"schema": SCHEMA, "sequence_id": sequence["id"], "rank": rank,
                    "nonce": nonce, "steps": 9, "layers": layer_count,
                    "records": record_count, "layer_ids": layers,
                    "input_ids_per_step": expected_inputs}
        if (any(item.get(key) != value for key, value in required.items())
                or any(type(item.get(key)) is not int for key in ("rank", "steps", "layers", "records"))
                or not isinstance(item.get("input_ids_per_step"), list)
                or any(not valid_ids(ids, INPUT_TOKENS if step == 0 else 1)
                       for step, ids in enumerate(item.get("input_ids_per_step", [])))
                ):
            raise ValueError("worker completion/trajectory mismatch: " + str(path))
        records.append({"path": str(path), "sha256": digest_bytes(raw),
                        "rank": rank, "steps": 9, "layers": layer_count,
                        "records": record_count})
    return records


def clear_owned_arm(capture, arm):
    path = capture / "armed.json"
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("owned arm vanished or is not a regular file")
    actual = json.loads(path.read_bytes())
    if actual != arm:
        raise RuntimeError("arm ownership changed; leave it untouched")
    path.unlink()


def write_stop(service):
    path = service / "stop.request"
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write("teacher collector finished or failed\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("unsafe existing stop request")


def run(service_dir, manifest_path, manifest_sha):
    service = absolute_path(service_dir, below_results=True)
    manifest_path = absolute_path(manifest_path)
    if not service.is_dir():
        raise ValueError("launcher-created service directory is required")
    capture = absolute_path(service / "teacher-capture")
    if not capture.is_dir():
        raise ValueError("launcher-created teacher-capture directory is required")
    report_path = service / "teacher-collector.json"
    if report_path.exists() or report_path.is_symlink():
        raise ValueError("existing collector receipt must not be overwritten")
    # The claim is outside try/finally: a second collector has no authority to
    # stop the active owner, remove its arm, or send any requests.
    publish(service / "teacher-collector.claim.json",
            {"schema": SCHEMA, "pid": os.getpid(), "started_unix_ns": time.time_ns(),
             "manifest_sha256": manifest_sha, "script_sha256": digest(__file__)})
    report = {"schema": SCHEMA, "status": "running", "claim": CLAIM,
              "manifest": str(manifest_path), "manifest_sha256": manifest_sha,
              "script_sha256": digest(__file__), "results": [],
              "protocol": {"requests": 2, "sequential": True, "input_tokens": 128,
                           "output_tokens": 9, "decode_steps": 8, "ignore_eos": True,
                           "no_thinking": True, "health_seconds": 900, "request_retries": 0}}
    arm = None
    original_error = original_traceback = None
    try:
        manifest = load_manifest(manifest_path, manifest_sha)
        wait_health(service)
        report["service_manifest_sha256"] = bind_service(service, manifest_path, manifest_sha)
        for sequence in manifest["sequences"]:
            worker_failures(capture)
            if (service / "service-exit.json").exists() or (service / "stop.request").exists():
                raise RuntimeError("service stopped between teacher sequences")
            arm = {"schema": SCHEMA, "sequence_id": sequence["id"],
                   "nonce": str(uuid.uuid4()), "input_ids_sha256": sequence["input_ids_sha256"]}
            publish(capture / "armed.json", arm)
            response = send_completion(sequence)
            response_record = {"schema": SCHEMA, **arm, "manifest_sha256": manifest_sha,
                               "service_manifest_sha256": report["service_manifest_sha256"],
                               "response": response}
            # Persist the received token IDs in the raw response BEFORE validating
            # coverage, inspecting worker receipts, or canceling this request's arm.
            response_path = capture / f'{sequence["id"]}.response.json'
            publish(response_path, response_record)
            ids, scores = validate_response(response)
            workers = verify_workers(capture, sequence, arm["nonce"], ids, manifest["layers"])
            report["results"].append({
                **arm, "token_ids": ids, "token_ids_sha256": token_hash(ids),
                "selected_logprobs": scores, "response_path": str(response_path),
                "response_sha256": digest(response_path), "worker_reports": workers})
            clear_owned_arm(capture, arm)
            arm = None
        report["status"] = "teacher_capture_complete_local_fidelity_only"
    except BaseException as error:
        original_error, original_traceback = error, error.__traceback__
        report.update(status="failed", error=repr(error), traceback=traceback.format_exc())
    finally:
        cleanup_errors = []
        if arm is not None:
            report["last_arm"] = arm
            try:
                clear_owned_arm(capture, arm)
            except BaseException as error:
                cleanup_errors.append("arm: " + repr(error))
        try:
            write_stop(service)
        except BaseException as error:
            cleanup_errors.append("stop: " + repr(error))
        if cleanup_errors:
            report.update(status="failed", cleanup_errors=cleanup_errors)
        report["completed_unix_ns"] = time.time_ns()
        try:
            publish(report_path, report)
        except BaseException as error:
            if original_error is None:
                original_error, original_traceback = error, error.__traceback__
        if cleanup_errors and original_error is None:
            original_error = RuntimeError("collector cleanup failed: " + "; ".join(cleanup_errors))
    if original_error is not None:
        raise original_error.with_traceback(original_traceback)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--calibration", type=Path, required=True)
    prepare_parser.add_argument("--layers", type=parse_layers,
                                default=list(LAYERS),
                                help="comma-separated frozen model layer IDs")
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--service-dir", type=Path, required=True)
    run_parser.add_argument("--manifest", type=Path, required=True)
    run_parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.output_dir, args.calibration, layers=args.layers)
    else:
        result = run(args.service_dir, args.manifest, args.manifest_sha256)
    print(json.dumps({"status": result["status"], "manifest_sha256": result.get("manifest_sha256")},
                     indent=2), flush=True)
    return result


if __name__ == "__main__":
    main()
