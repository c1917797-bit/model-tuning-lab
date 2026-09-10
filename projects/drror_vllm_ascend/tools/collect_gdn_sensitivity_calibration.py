#!/usr/bin/env python3
"""Prepare and collect a bounded dense GDN sensitivity calibration corpus."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import time
import traceback
from urllib.request import Request, urlopen
import uuid

try:
    import collect_gdn_teacher as shared
except ModuleNotFoundError:  # Imported as tools.* by the software test suite.
    from tools import collect_gdn_teacher as shared


SCHEMA = "gdn-sensitivity-calibration-v1"
CALIBRATION_SHA256 = "81748f94c4eff0ad5e4053eb7c4a30b1a397a82d45676a8b0b42394bd612bd47"
LAYERS = [0, 12, 25, 38, 50, 62]
INPUT_TOKENS = 128
OUTPUT_TOKENS = 9
DECODE_STEPS = 8
SEQUENCE_COUNT = 16
WORKER_CLASS = "gdn_sensitivity_capture_worker.GdnSensitivityCaptureWorker"
CLAIM = (
    "Dense pass-through state/post-RMS calibration on existing non-evaluation "
    "raw token IDs. Not a DRRQR candidate, NPU speedup, task accuracy, or "
    "portability result."
)


def read_calibration(path: Path, expected_sha256=None):
    expected_sha256 = CALIBRATION_SHA256 if expected_sha256 is None else expected_sha256
    raw = path.read_bytes()
    if shared.digest_bytes(raw) != expected_sha256:
        raise ValueError("sensitivity calibration SHA256 mismatch")
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    if len(rows) != SEQUENCE_COUNT:
        raise ValueError("expected sixteen calibration rows")
    for index, row in enumerate(rows):
        ids = row.get("input_ids")
        if (
            row.get("schema") != "drrqr-calibration-sample/v2"
            or row.get("index") != index
            or row.get("token_count") != 2048
            or not shared.valid_ids(ids, 2048)
            or row.get("input_ids_sha256") != shared.token_hash(ids)
        ):
            raise ValueError("invalid sensitivity calibration row")
    return rows


def prepare(output_dir: Path, calibration: Path, layers=None):
    output = shared.absolute_path(output_dir)
    calibration = shared.absolute_path(calibration)
    output.mkdir(parents=False, exist_ok=False)
    receipt = {"schema": SCHEMA, "status": "failed", "script_sha256": shared.digest(__file__)}
    try:
        rows = read_calibration(calibration)
        layers = shared.validate_layers(list(LAYERS) if layers is None else layers)
        sequences = []
        hashes = set()
        for index, row in enumerate(rows):
            ids = row["input_ids"][:INPUT_TOKENS]
            hashed = shared.token_hash(ids)
            if hashed in hashes:
                raise ValueError("duplicate 128-token calibration prefix")
            hashes.add(hashed)
            sequences.append(
                {
                    "id": f"calibration-{index:02d}",
                    "source_index": index,
                    "input_ids": ids,
                    "input_ids_sha256": hashed,
                    "source_input_ids_sha256": row["input_ids_sha256"],
                }
            )
        manifest = {
            "schema": SCHEMA,
            "model": shared.MODEL,
            "served_model": shared.SERVED_MODEL,
            "layers": layers,
            "tp_size": 4,
            "input_tokens": INPUT_TOKENS,
            "decode_steps": DECODE_STEPS,
            "output_tokens": OUTPUT_TOKENS,
            "no_thinking": True,
            "raw_token_prompts": True,
            "add_special_tokens": False,
            "sequences": sequences,
            "source_calibration": {
                "path": str(calibration),
                "sha256": CALIBRATION_SHA256,
                "rows": SEQUENCE_COUNT,
                "source_token_count": 2048,
                "prefix_token_count": INPUT_TOKENS,
                "evaluation_overlap": False,
                "selector_train_indices": list(range(12)),
                "selector_heldout_indices": list(range(12, 16)),
            },
            "claim": CLAIM,
            "script_sha256": shared.digest(__file__),
        }
        path = output / "manifest.json"
        shared.publish(path, manifest)
        receipt.update(status="prepared", manifest=str(path), manifest_sha256=shared.digest(path))
        return receipt
    except BaseException as error:
        receipt.update(error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        shared.publish(output / "prepare-receipt.json", receipt)


def load_manifest(path: Path, expected: str):
    path = shared.absolute_path(path)
    raw = path.read_bytes()
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or shared.digest_bytes(raw) != expected:
        raise ValueError("sensitivity manifest SHA256 mismatch")
    document = json.loads(raw)
    required = {
        "schema": SCHEMA,
        "model": shared.MODEL,
        "served_model": shared.SERVED_MODEL,
        "tp_size": 4,
        "input_tokens": INPUT_TOKENS,
        "decode_steps": DECODE_STEPS,
        "output_tokens": OUTPUT_TOKENS,
        "no_thinking": True,
        "raw_token_prompts": True,
        "add_special_tokens": False,
    }
    if any(document.get(name) != value for name, value in required.items()):
        raise ValueError("sensitivity manifest protocol mismatch")
    shared.validate_layers(document.get("layers"))
    source = document.get("source_calibration", {})
    calibration = shared.absolute_path(Path(source.get("path", "")))
    if (
        source.get("sha256") != CALIBRATION_SHA256
        or source.get("rows") != SEQUENCE_COUNT
        or source.get("selector_train_indices") != list(range(12))
        or source.get("selector_heldout_indices") != list(range(12, 16))
    ):
        raise ValueError("sensitivity source/split binding mismatch")
    rows = read_calibration(calibration)
    sequences = document.get("sequences")
    if not isinstance(sequences, list) or len(sequences) != SEQUENCE_COUNT:
        raise ValueError("sensitivity sequence coverage mismatch")
    for index, (sequence, row) in enumerate(zip(sequences, rows, strict=True)):
        ids = row["input_ids"][:INPUT_TOKENS]
        if (
            sequence.get("id") != f"calibration-{index:02d}"
            or sequence.get("source_index") != index
            or sequence.get("input_ids") != ids
            or sequence.get("input_ids_sha256") != shared.token_hash(ids)
            or sequence.get("source_input_ids_sha256") != row["input_ids_sha256"]
        ):
            raise ValueError("sensitivity sequence/source mismatch")
    return document


def bind_service(service: Path, manifest_path: Path, manifest_sha: str):
    path = service / "service-manifest.json"
    raw = path.read_bytes()
    document = json.loads(raw)
    required = {
        "schema": "drrqr-gdn-teacher-service/v1",
        "variant": "dense128",
        "model": shared.MODEL,
        "shared_hf_head_k_dim": 128,
        "tensor_parallel_size": 4,
        "calibration_only": True,
        "enforce_eager": True,
        "profiler_config": None,
        "capture_manifest": str(manifest_path),
        "capture_manifest_sha256": manifest_sha,
        "capture_manifest_schema": SCHEMA,
        "worker_class": WORKER_CLASS,
        "stop_request_path": str(service / "stop.request"),
    }
    if any(document.get(name) != value for name, value in required.items()):
        raise ValueError("launcher/sensitivity manifest binding mismatch")
    observer = document.get("observer_flags", {})
    if (
        observer.get("DRRQR_GDN_TEACHER_MANIFEST") != str(manifest_path)
        or observer.get("DRRQR_GDN_TEACHER_MANIFEST_SHA256") != manifest_sha
        or observer.get("DRRQR_GDN_TEACHER_DIR") != str(service / "teacher-capture")
    ):
        raise ValueError("sensitivity worker observer binding mismatch")
    return shared.digest_bytes(raw)


def payload_for(sequence):
    return {
        "model": shared.SERVED_MODEL,
        "prompt": sequence["input_ids"],
        "add_special_tokens": False,
        "temperature": 0,
        "seed": 0,
        "max_tokens": OUTPUT_TOKENS,
        "ignore_eos": True,
        "return_token_ids": True,
        "logprobs": 5,
        "stream": False,
    }


def send_completion(sequence):
    request = Request(
        "http://127.0.0.1:6666/v1/completions",
        data=json.dumps(payload_for(sequence)).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=600) as response:
        raw = response.read(1024 * 1024 + 1)
        if response.status != 200 or len(raw) > 1024 * 1024:
            raise RuntimeError("completion HTTP status/body budget mismatch")
    return json.loads(raw)


def verify_workers(capture, sequence, nonce, output_ids, layers):
    layers = shared.validate_layers(layers)
    expected_inputs = [sequence["input_ids"]] + [[token] for token in output_ids[:DECODE_STEPS]]
    result = []
    shared.worker_failures(capture)
    for rank in range(4):
        wrapper = capture / f"rank{rank}.sensitivity-wrapper.json"
        path = capture / f'{sequence["id"]}.rank{rank}.complete.json'
        if not wrapper.is_file() or wrapper.is_symlink() or not path.is_file() or path.is_symlink():
            raise RuntimeError("missing sensitivity wrapper/completion receipt")
        wrapper_doc = json.loads(wrapper.read_bytes())
        item = json.loads(path.read_bytes())
        required = {
            "schema": SCHEMA,
            "sequence_id": sequence["id"],
            "rank": rank,
            "nonce": nonce,
            "steps": 9,
            "layers": len(layers),
            "records": 9 * len(layers),
            "layer_ids": layers,
            "input_ids_per_step": expected_inputs,
        }
        if (
            wrapper_doc.get("schema") != SCHEMA
            or wrapper_doc.get("rank") != rank
            or any(item.get(name) != value for name, value in required.items())
        ):
            raise ValueError("sensitivity worker trajectory mismatch")
        result.append(
            {
                "rank": rank,
                "wrapper_sha256": shared.digest(wrapper),
                "completion_sha256": shared.digest(path),
                "records": 9 * len(layers),
            }
        )
    return result


def run(service_dir: Path, manifest_path: Path, manifest_sha: str):
    service = shared.absolute_path(service_dir, below_results=True)
    manifest_path = shared.absolute_path(manifest_path)
    capture = shared.absolute_path(service / "teacher-capture")
    if not service.is_dir() or not capture.is_dir():
        raise ValueError("launcher-created service/capture directory required")
    report_path = service / "sensitivity-collector.json"
    if report_path.exists() or report_path.is_symlink():
        raise ValueError("existing sensitivity collector receipt")
    manifest = load_manifest(manifest_path, manifest_sha)
    shared.publish(
        service / "sensitivity-collector.claim.json",
        {
            "schema": SCHEMA,
            "pid": os.getpid(),
            "started_unix_ns": time.time_ns(),
            "manifest_sha256": manifest_sha,
            "script_sha256": shared.digest(__file__),
        },
    )
    report = {
        "schema": SCHEMA,
        "status": "running",
        "claim": CLAIM,
        "manifest": str(manifest_path),
        "manifest_sha256": manifest_sha,
        "script_sha256": shared.digest(__file__),
        "results": [],
        "protocol": {
            "requests": SEQUENCE_COUNT,
            "sequential": True,
            "input_tokens": INPUT_TOKENS,
            "output_tokens": OUTPUT_TOKENS,
            "decode_steps": DECODE_STEPS,
            "ignore_eos": True,
            "add_special_tokens": False,
            "request_retries": 0,
        },
    }
    arm = None
    original_error = original_traceback = None
    try:
        shared.wait_health(service)
        report["service_manifest_sha256"] = bind_service(service, manifest_path, manifest_sha)
        for sequence in manifest["sequences"]:
            shared.worker_failures(capture)
            if (service / "service-exit.json").exists() or (service / "stop.request").exists():
                raise RuntimeError("service stopped between sensitivity sequences")
            arm = {
                "schema": SCHEMA,
                "sequence_id": sequence["id"],
                "nonce": str(uuid.uuid4()),
                "input_ids_sha256": sequence["input_ids_sha256"],
            }
            shared.publish(capture / "armed.json", arm)
            response = send_completion(sequence)
            response_path = capture / f'{sequence["id"]}.response.json'
            shared.publish(
                response_path,
                {
                    "schema": SCHEMA,
                    **arm,
                    "manifest_sha256": manifest_sha,
                    "service_manifest_sha256": report["service_manifest_sha256"],
                    "response": response,
                },
            )
            output_ids, scores = shared.validate_response(response)
            workers = verify_workers(
                capture, sequence, arm["nonce"], output_ids, manifest["layers"]
            )
            report["results"].append(
                {
                    **arm,
                    "token_ids": output_ids,
                    "token_ids_sha256": shared.token_hash(output_ids),
                    "selected_logprobs": scores,
                    "response_path": str(response_path),
                    "response_sha256": shared.digest(response_path),
                    "worker_reports": workers,
                }
            )
            shared.clear_owned_arm(capture, arm)
            arm = None
        report["status"] = "sensitivity_capture_complete_local_fidelity_only"
    except BaseException as error:
        original_error, original_traceback = error, error.__traceback__
        report.update(status="failed", error=repr(error), traceback=traceback.format_exc())
    finally:
        cleanup_errors = []
        if arm is not None:
            report["last_arm"] = arm
            try:
                shared.clear_owned_arm(capture, arm)
            except BaseException as error:
                cleanup_errors.append("arm: " + repr(error))
        try:
            shared.write_stop(service)
        except BaseException as error:
            cleanup_errors.append("stop: " + repr(error))
        if cleanup_errors:
            report.update(status="failed", cleanup_errors=cleanup_errors)
        report["completed_unix_ns"] = time.time_ns()
        try:
            shared.publish(report_path, report)
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
    prepare_parser.add_argument(
        "--layers", type=shared.parse_layers, default=list(LAYERS)
    )
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--service-dir", type=Path, required=True)
    run_parser.add_argument("--manifest", type=Path, required=True)
    run_parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args(argv)
    result = (
        prepare(args.output_dir, args.calibration, args.layers)
        if args.command == "prepare"
        else run(args.service_dir, args.manifest, args.manifest_sha256)
    )
    print(json.dumps({"status": result["status"], "manifest_sha256": result.get("manifest_sha256")}, indent=2))
    return result


if __name__ == "__main__":
    main()
