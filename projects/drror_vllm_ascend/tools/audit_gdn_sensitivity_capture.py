#!/usr/bin/env python3
"""Independently audit a frozen dense GDN sensitivity capture.

The audit is deliberately CPU-only: it validates immutable runtime identity,
request/receipt bindings, every tensor archive, state continuity, and exact
operator-to-norm handoff.  It does not replay a candidate or make a performance
or task-accuracy claim.
"""

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

import torch


SCHEMA = "gdn-sensitivity-calibration-v1"
REPORT_SCHEMA = "gdn-sensitivity-capture-audit/v1"
LAYERS = [0, 12, 25, 38, 50, 62]
RANKS = range(4)
STEPS = range(9)
SEQUENCES = range(16)
MANIFEST_SHA256 = "6281f7613379daa65af4e70ead89e32fc33290a39124a4bcb7425bb7ff0e38c1"
WORKER_SHA256 = "c408d87bb12122da0e5e64073881208a3830973dfde9344691a008401b8ac69f"
GDN_SOURCE_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
NATIVE_SCHEMA = (
    "_C_ascend::npu_recurrent_gated_delta_rule(Tensor query, Tensor key, "
    "Tensor value, Tensor(a!) state, *, Tensor? beta=None, float? scale=None, "
    "Tensor? actual_seq_lengths=None, Tensor? ssm_state_indices=None, "
    "Tensor? num_accepted_tokens=None, Tensor? g=None, Tensor? gk=None) -> Tensor"
)
HASH = re.compile(r"^[0-9a-f]{64}$")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_json(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"regular JSON required: {path}")
    return json.loads(path.read_bytes())


def exact(left, right):
    return (
        isinstance(left, torch.Tensor)
        and isinstance(right, torch.Tensor)
        and left.dtype == right.dtype
        and left.shape == right.shape
        and torch.equal(
            left.contiguous().view(torch.uint8),
            right.contiguous().view(torch.uint8),
        )
    )


def expected_positions(step):
    value = list(range(128)) if step == 0 else [127 + step]
    return [value, value, value]


def verify_saved_metadata(name, tensor, metadata):
    require(isinstance(tensor, torch.Tensor), f"{name}: tensor required")
    require(
        {
            "shape": list(tensor.shape),
            "stride": list(tensor.stride()),
            "dtype": str(tensor.dtype),
            "numel": tensor.numel(),
            "element_size": tensor.element_size(),
            "contiguous": tensor.is_contiguous(),
        }
        == {key: metadata[key] for key in (
            "shape", "stride", "dtype", "numel", "element_size", "contiguous"
        )},
        f"{name}: saved tensor metadata differs from capture",
    )


def verify_libraries(libraries):
    require(isinstance(libraries, list) and len(libraries) >= 5, "loaded library coverage")
    basenames = {Path(item["path"]).name for item in libraries}
    require(
        {"libopapi.so", "libcust_opapi.so", "libvllm_ascend_kernels.so"}
        <= basenames,
        "native operator libraries missing",
    )
    for item in libraries:
        require(
            isinstance(item.get("path"), str)
            and item["path"].startswith("/")
            and HASH.fullmatch(item.get("sha256", "")),
            "invalid loaded library identity",
        )
    return sorted((item["path"], item["sha256"]) for item in libraries)


def verify_record(
    record,
    *,
    sequence,
    nonce,
    output_ids,
    rank,
    layer,
    step,
    ready_layer,
    previous_state,
    stable_state_metadata,
):
    phase = "prefill" if step == 0 else "decode"
    expected_ids = sequence["input_ids"] if step == 0 else [output_ids[step - 1]]
    required = {
        "schema": SCHEMA,
        "manifest_sha256": MANIFEST_SHA256,
        "sequence_id": sequence["id"],
        "nonce": nonce,
        "rank": rank,
        "layer": layer,
        "step": step,
        "phase": phase,
        "input_ids": expected_ids,
        "positions": expected_positions(step),
        "input_ids_source": "frozen_runner_input_ids_buffer_with_text_embeddings",
        "operator_calls": 1,
    }
    require(all(record.get(key) == value for key, value in required.items()),
            f"{sequence['id']} rank{rank} layer{layer} step{step}: record binding")
    require(record.get("norm") == ready_layer["norm"], "norm implementation binding")
    require(record.get("scale") == 128 ** -0.5, "dense scale binding")
    indices = record.get("state_indices")
    require(isinstance(indices, list) and len(indices) == 1 and indices[0] >= 0,
            "one nonnegative state slot")
    state_meta = record.get("state_metadata")
    require(
        isinstance(state_meta, dict)
        and state_meta.get("shape", [None])[1:] == [12, 128, 128]
        and state_meta.get("dtype") == "torch.float32"
        and state_meta.get("device") == f"npu:{rank}"
        and state_meta.get("contiguous") is True,
        "dense state geometry/storage metadata",
    )
    if stable_state_metadata is not None:
        require(state_meta == stable_state_metadata, "state storage pointer/metadata changed")

    tensors = record.get("tensors")
    tensor_metadata = record.get("tensor_metadata")
    require(isinstance(tensors, dict) and isinstance(tensor_metadata, dict), "tensor dictionaries")
    prefill_names = {
        "raw_q", "raw_k", "raw_v", "q", "k", "v", "g", "beta",
        "initial_state", "cu_seqlens", "state_initial", "operator_output",
        "chunk_state_final", "state_final", "norm_input", "z",
        "norm_output", "norm_weight",
    }
    decode_names = {
        "raw_q", "raw_k", "raw_v", "query", "key", "value", "g", "beta",
        "actual_seq_lengths", "ssm_state_indices", "state_initial",
        "operator_output", "state_final", "norm_input", "z",
        "norm_output", "norm_weight",
    }
    require(set(tensors) == (prefill_names if step == 0 else decode_names),
            "phase tensor coverage")
    require(set(tensor_metadata) <= set(tensors), "metadata names outside tensors")
    for name, tensor in tensors.items():
        require(isinstance(tensor, torch.Tensor) and tensor.device.type == "cpu",
                f"{name}: CPU snapshot required")
        if tensor.is_floating_point() or tensor.is_complex():
            require(bool(torch.isfinite(tensor).all()), f"{name}: nonfinite tensor")
        if name in tensor_metadata:
            verify_saved_metadata(name, tensor, tensor_metadata[name])

    require(exact(tensors["norm_input"], tensors["operator_output"].reshape(-1, 128)),
            "operator output does not exactly feed post-RMS norm")
    require(tensors["state_initial"].dtype == torch.float32
            and tensors["state_final"].dtype == torch.float32
            and list(tensors["state_initial"].shape) == [1, 12, 128, 128]
            and list(tensors["state_final"].shape) == [1, 12, 128, 128],
            "state snapshot geometry")
    if step == 0:
        require(record.get("has_initial_state") == [False], "prefill reset flag")
        require(int(torch.count_nonzero(tensors["state_initial"])) == 0,
                "prefill state must be exactly zero")
        require(exact(tensors["q"], tensors["raw_q"])
                and exact(tensors["k"], tensors["raw_k"])
                and exact(tensors["v"], tensors["raw_v"]),
                "prefill raw/operator QKV binding")
        require(tensors["cu_seqlens"].tolist() == [0, 128], "prefill boundaries")
        require(exact(
            tensors["state_final"],
            tensors["chunk_state_final"].transpose(-1, -2).contiguous(),
        ), "prefill state layout binding")
    else:
        require(previous_state is not None
                and exact(previous_state, tensors["state_initial"]),
                "byte-exact recurrent state continuity")
        require(exact(tensors["value"], tensors["raw_v"].squeeze(0)),
                "decode raw value binding")
        require(tensors["actual_seq_lengths"].tolist() == [0, 1],
                "decode length ABI")
        require(tensors["ssm_state_indices"].reshape(-1).tolist() == indices,
                "decode state-slot ABI")
    return tensors["state_final"].clone(), state_meta, indices[0], len(tensors)


def audit(service_dir, manifest_path):
    service = Path(service_dir).resolve()
    manifest_path = Path(manifest_path).resolve()
    require(service.is_dir() and not service.is_symlink(), "capture service directory")
    require(digest(manifest_path) == MANIFEST_SHA256, "manifest SHA256")
    manifest = read_json(manifest_path)
    require(
        manifest.get("schema") == SCHEMA
        and manifest.get("layers") == LAYERS
        and manifest.get("tp_size") == 4
        and manifest.get("input_tokens") == 128
        and manifest.get("output_tokens") == 9
        and manifest.get("decode_steps") == 8
        and manifest.get("no_thinking") is True
        and manifest.get("raw_token_prompts") is True
        and manifest.get("add_special_tokens") is False,
        "manifest protocol",
    )
    sequences = manifest.get("sequences")
    require(isinstance(sequences, list) and len(sequences) == 16, "manifest sequences")
    require(
        manifest.get("source_calibration", {}).get("selector_train_indices") == list(range(12))
        and manifest.get("source_calibration", {}).get("selector_heldout_indices") == list(range(12, 16))
        and manifest.get("source_calibration", {}).get("evaluation_overlap") is False,
        "train/held-out/non-evaluation split",
    )

    service_manifest_path = service / "service-manifest.json"
    service_manifest = read_json(service_manifest_path)
    require(
        service_manifest.get("schema") == "drrqr-gdn-teacher-service/v1"
        and service_manifest.get("variant") == "dense128"
        and service_manifest.get("worker_sha256") == WORKER_SHA256
        and service_manifest.get("capture_manifest_sha256") == MANIFEST_SHA256
        and service_manifest.get("worker_class")
            == "gdn_sensitivity_capture_worker.GdnSensitivityCaptureWorker"
        and service_manifest.get("physical_npu_contract") == [4, 5, 6, 7]
        and service_manifest.get("container_npu_namespace") == [0, 1, 2, 3]
        and service_manifest.get("enforce_eager") is True
        and service_manifest.get("profiler_config") is None,
        "service protocol/identity",
    )
    require(
        service_manifest.get("source_sha256", {}).get(
            "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"
        ) == GDN_SOURCE_SHA256,
        "Ascend GDN source identity",
    )
    require(
        all(value == "0" for value in
            service_manifest.get("disabled_optimization_flags", {}).values()),
        "dense capture optimization isolation",
    )
    exit_doc = read_json(service / "service-exit.json")
    require(
        exit_doc.get("exit_code") == 0
        and exit_doc.get("stop_reason") == "stop_request"
        and exit_doc.get("group_remaining") is False,
        "clean service exit",
    )

    collector = read_json(service / "sensitivity-collector.json")
    require(
        collector.get("schema") == SCHEMA
        and collector.get("status") == "sensitivity_capture_complete_local_fidelity_only"
        and collector.get("manifest_sha256") == MANIFEST_SHA256
        and collector.get("service_manifest_sha256") == digest(service_manifest_path)
        and len(collector.get("results", [])) == 16,
        "collector completion/binding",
    )
    protocol = collector.get("protocol", {})
    require(
        protocol == {
            "requests": 16, "sequential": True, "input_tokens": 128,
            "output_tokens": 9, "decode_steps": 8, "ignore_eos": True,
            "add_special_tokens": False, "request_retries": 0,
        },
        "collector protocol",
    )

    capture = service / "teacher-capture"
    require(capture.is_dir() and not capture.is_symlink(), "teacher capture directory")
    expected_archives = {
        f"calibration-{sequence:02d}.rank{rank}.layer{layer}.step{step}.pt"
        for sequence in SEQUENCES for rank in RANKS for layer in LAYERS for step in STEPS
    }
    actual_archives = {path.name for path in capture.glob("*.pt")}
    require(actual_archives == expected_archives, "exact 3456 archive coverage")
    require(not list(capture.glob("*.failure.json"))
            and not list(capture.glob("*.partial")), "no worker failure/partial files")

    ready = {}
    wrappers = {}
    for rank in RANKS:
        ready[rank] = read_json(capture / f"rank{rank}.ready.json")
        wrappers[rank] = read_json(capture / f"rank{rank}.sensitivity-wrapper.json")
        require(
            ready[rank].get("schema") == SCHEMA
            and ready[rank].get("rank") == rank
            and ready[rank].get("local_rank") == rank
            and ready[rank].get("manifest_sha256") == MANIFEST_SHA256
            and ready[rank].get("native_schema") == NATIVE_SCHEMA
            and wrappers[rank].get("schema") == SCHEMA
            and wrappers[rank].get("rank") == rank
            and wrappers[rank].get("manifest_sha256") == MANIFEST_SHA256
            and wrappers[rank].get("adapter", {}).get("sha256") == WORKER_SHA256,
            f"rank{rank}: worker/source identity",
        )
        layer_map = {item["layer"]: item for item in ready[rank].get("layers", [])}
        require(sorted(layer_map) == LAYERS, f"rank{rank}: ready layer coverage")
        require(all(
            item.get("core", {}).get("sha256") == GDN_SOURCE_SHA256
            for item in layer_map.values()
        ), f"rank{rank}: actual Ascend GDN dispatch")
        ready[rank]["layer_map"] = layer_map

    total_tensors = 0
    total_tensor_bytes = 0
    library_identity = None
    state_slots = {}
    stable_metadata = {}
    archive_hashes = {}
    for sequence_index, sequence in enumerate(sequences):
        sequence_id = f"calibration-{sequence_index:02d}"
        require(sequence.get("id") == sequence_id, "sequence ordering")
        result = collector["results"][sequence_index]
        require(
            result.get("sequence_id") == sequence_id
            and result.get("input_ids_sha256") == sequence.get("input_ids_sha256")
            and len(result.get("token_ids", [])) == 9
            and all(type(token) is int and token >= 0 for token in result["token_ids"]),
            f"{sequence_id}: collector result binding",
        )
        nonce = result.get("nonce")
        output_ids = result["token_ids"]
        response = capture / f"{sequence_id}.response.json"
        require(
            digest(response) == result.get("response_sha256")
            and Path(result.get("response_path", "")).name == response.name,
            f"{sequence_id}: response identity",
        )
        reports = {item["rank"]: item for item in result.get("worker_reports", [])}
        require(sorted(reports) == list(RANKS), f"{sequence_id}: worker reports")
        for rank in RANKS:
            wrapper_path = capture / f"rank{rank}.sensitivity-wrapper.json"
            completion_path = capture / f"{sequence_id}.rank{rank}.complete.json"
            report = reports[rank]
            require(
                digest(wrapper_path) == report.get("wrapper_sha256")
                and digest(completion_path) == report.get("completion_sha256")
                and report.get("records") == 54,
                f"{sequence_id} rank{rank}: collector receipt hashes",
            )
            completion = read_json(completion_path)
            require(
                completion.get("schema") == SCHEMA
                and completion.get("sequence_id") == sequence_id
                and completion.get("nonce") == nonce
                and completion.get("rank") == rank
                and completion.get("steps") == 9
                and completion.get("layer_ids") == LAYERS
                and completion.get("records") == 54,
                f"{sequence_id} rank{rank}: completion binding",
            )
            libraries = verify_libraries(completion.get("loaded_libraries"))
            if library_identity is None:
                library_identity = libraries
            else:
                require(libraries == library_identity, "loaded library identity changed")
            receipts = {item["file"]: item for item in completion.get("files", [])}
            expected_rank_files = {
                f"{sequence_id}.rank{rank}.layer{layer}.step{step}.pt"
                for step in STEPS for layer in LAYERS
            }
            require(set(receipts) == expected_rank_files, "completion archive coverage")
            for layer in LAYERS:
                previous_state = None
                first_metadata = stable_metadata.get((rank, layer))
                slot = None
                for step in STEPS:
                    filename = f"{sequence_id}.rank{rank}.layer{layer}.step{step}.pt"
                    path = capture / filename
                    checksum = digest(path)
                    require(
                        receipts[filename].get("sha256") == checksum
                        and Path(receipts[filename].get("path", "")).name == filename,
                        f"{filename}: completion hash/path",
                    )
                    archive_hashes[filename] = checksum
                    record = torch.load(path, map_location="cpu", weights_only=True)
                    previous_state, metadata, current_slot, tensor_count = verify_record(
                        record,
                        sequence=sequence,
                        nonce=nonce,
                        output_ids=output_ids,
                        rank=rank,
                        layer=layer,
                        step=step,
                        ready_layer=ready[rank]["layer_map"][layer],
                        previous_state=previous_state,
                        stable_state_metadata=first_metadata,
                    )
                    if first_metadata is None:
                        first_metadata = metadata
                        stable_metadata[(rank, layer)] = metadata
                    if slot is None:
                        slot = current_slot
                    require(slot == current_slot, "state slot changed within sequence")
                    total_tensors += tensor_count
                    total_tensor_bytes += sum(
                        tensor.numel() * tensor.element_size()
                        for tensor in record["tensors"].values()
                    )
                state_slots[f"{sequence_id}.rank{rank}.layer{layer}"] = slot

    return {
        "schema": REPORT_SCHEMA,
        "status": "passed",
        "claim": (
            "The dense Ascend GDN sensitivity corpus passed archive identity, "
            "runtime/source/library binding, finite-tensor, exact state-continuity, "
            "and operator-to-post-RMS handoff checks. This is selector input only, "
            "not a DRRQR candidate, performance, accuracy, or portability result."
        ),
        "service_dir": str(service),
        "manifest": str(manifest_path),
        "manifest_sha256": MANIFEST_SHA256,
        "service_manifest_sha256": digest(service_manifest_path),
        "collector_sha256": digest(service / "sensitivity-collector.json"),
        "service_exit_sha256": digest(service / "service-exit.json"),
        "archive_count": len(archive_hashes),
        "archive_set_sha256": hashlib.sha256(
            json.dumps(archive_hashes, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "tensor_count": total_tensors,
        "logical_tensor_bytes_checked": total_tensor_bytes,
        "sequence_count": 16,
        "rank_count": 4,
        "layer_count": 6,
        "steps_per_sequence": 9,
        "state_trajectory_count": 16 * 4 * 6,
        "state_transition_count": 16 * 4 * 6 * 8,
        "stable_state_storage_groups": len(stable_metadata),
        "state_slots": state_slots,
        "loaded_libraries": [
            {"path": path, "sha256": checksum}
            for path, checksum in (library_identity or [])
        ],
        "selector_split": {
            "fit_indices": list(range(12)),
            "untouched_admission_indices": list(range(12, 16)),
        },
        "auditor": {
            "path": str(Path(__file__).resolve()),
            "sha256": digest(__file__),
            "python": sys.version,
            "torch": torch.__version__,
        },
        "completed_unix_ns": time.time_ns(),
    }


def publish(path, value):
    path = Path(path)
    require(path.is_absolute() and not path.exists() and not path.is_symlink(),
            "fresh absolute audit output required")
    partial = path.with_name(path.name + ".partial")
    require(not partial.exists() and not partial.is_symlink(), "fresh partial output required")
    with partial.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = audit(args.service_dir, args.manifest)
    publish(args.output, report)
    print(json.dumps({
        "status": report["status"],
        "archive_count": report["archive_count"],
        "state_transition_count": report["state_transition_count"],
        "output": str(args.output),
        "output_sha256": digest(args.output),
    }, indent=2))
    return report


if __name__ == "__main__":
    main()
