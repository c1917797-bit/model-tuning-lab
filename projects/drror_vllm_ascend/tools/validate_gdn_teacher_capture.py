#!/usr/bin/env python3
"""CPU audit of frozen dense teacher evidence; no candidate gain or NPU execution."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import time
import traceback

import torch

SCHEMA = "gdn-teacher-capture-v1"
AUDIT_SCHEMA = "gdn-teacher-evidence-audit/v1"
ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOT = Path("/drrqr-results")
WORKER = ROOT / "tools/gdn_teacher_capture_worker.py"
COLLECTOR = ROOT / "tools/collect_gdn_teacher.py"
HELPER = ROOT / "tools/layerwise_probe_worker.py"
HELPER_SHA = "678f714458f81a6b73c5dd19fc50a69e11c2e444837908460aa8e4aab9a46feb"
MODEL = "/cache/austinov/Qwen3.8-27B"
LAYERS = (0, 12, 25, 38, 50, 62)
HASH = re.compile(r"^[0-9a-f]{64}$")
OLD_CALIBRATION_SHA = "81748f94c4eff0ad5e4053eb7c4a30b1a397a82d45676a8b0b42394bd612bd47"
CLAIM = ("CPU integrity/trajectory audit of local trusted dense teacher artifacts only. "
         "Not candidate fidelity, task accuracy, timing, throughput or a resolved ACLNN "
         "symbol/device-binary route. Library records establish mapped-file provenance only.")
SOURCE_ROOTS = (ROOT / "tools", Path("/vllm-workspace/vllm"),
                Path("/vllm-workspace/vllm-ascend"))
# Frozen chunk.py:263 uses @torch.compiler.disable. DisableContext.__call__
# in eval_frame.py:1165..1204 calls fn and preserves its symbol via wraps(fn).
# This exact, check_ready(chunk)-only exception does not admit site-packages generally.
CHUNK_DISABLE_WRAPPER = {
    "path": "/usr/local/python3.12.13/lib/python3.12/site-packages/torch/_dynamo/eval_frame.py",
    "sha256": "8f49ecb842a4d50281695e5b8d015fd9afd2a202b0f6c9f3f94c91415ba0d5a4",
    "symbol": "vllm_ascend.ops.triton.fla.chunk.chunk_gated_delta_rule",
    "unwrapped": {
        "path": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/chunk.py",
        "sha256": "6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5",
        "symbol": "vllm_ascend.ops.triton.fla.chunk.chunk_gated_delta_rule",
    },
}
COMMON_TENSORS = {"raw_q", "raw_k", "raw_v", "g", "beta", "state_initial", "state_final",
                  "operator_output", "norm_input", "z", "norm_output", "norm_weight"}
PREFILL_TENSORS = COMMON_TENSORS | {"q", "k", "v", "initial_state", "cu_seqlens",
                                     "chunk_state_final"}
DECODE_TENSORS = COMMON_TENSORS | {"query", "key", "value", "actual_seq_lengths",
                                    "ssm_state_indices"}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def regular(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve() and path.is_file()
            and not path.is_symlink(), "expected an absolute non-symlink regular file: " + str(path))
    return path


def directory(path):
    path = Path(path)
    require(path.is_absolute() and path == path.resolve() and path.is_dir()
            and not path.is_symlink(), "expected an absolute non-symlink directory: " + str(path))
    return path


def bound_bytes(path, expected):
    require(isinstance(expected, str) and HASH.fullmatch(expected) is not None, "invalid SHA256")
    raw = regular(path).read_bytes()
    require(sha_bytes(raw) == expected, "SHA256 mismatch: " + str(path))
    return raw


def bound_json(path, expected):
    value = json.loads(bound_bytes(path, expected))
    require(isinstance(value, dict), "expected JSON object: " + str(path))
    return value


def ids_ok(ids, length):
    return (isinstance(ids, list) and len(ids) == length
            and all(type(value) is int and value >= 0 for value in ids))


def token_hash(ids):
    return sha_bytes(json.dumps(ids, separators=(",", ":")).encode())


def equal_bytes(left, right):
    return (isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor)
            and left.device.type == right.device.type == "cpu"
            and left.shape == right.shape and left.dtype == right.dtype
            and bool(torch.isfinite(left).all() and torch.isfinite(right).all())
            and torch.equal(left.contiguous().reshape(-1).view(torch.uint8),
                            right.contiguous().reshape(-1).view(torch.uint8)))


def check_positions(value, step):
    expected = list(range(128)) if step == 0 else [127 + step]
    if (isinstance(value, list) and len(value) == 3
            and all(isinstance(axis, list) for axis in value)):
        require(value[0] == value[1] == value[2], "non-text MRoPE positions")
        value = value[0]
    require(ids_ok(value, len(expected)) and value == expected, "position trajectory mismatch")


def manifest_layers(doc):
    value = doc.get("layers")
    require(isinstance(value, list) and 1 <= len(value) <= 48, "manifest layers")
    require(all(type(layer) is int and 0 <= layer <= 63 for layer in value),
            "manifest layer IDs")
    require(value == sorted(set(value)), "manifest layers must be sorted and unique")
    return tuple(value)


def check_manifest(doc):
    expected = {"schema": SCHEMA, "model": MODEL, "served_model": "qwen3.8",
                "tp_size": 4, "input_tokens": 128,
                "decode_steps": 8, "output_tokens": 9, "no_thinking": True,
                "synthetic_text": True}
    for key, value in expected.items():
        require(type(doc.get(key)) is type(value) and doc[key] == value, "manifest " + key)
    manifest_layers(doc)
    require(doc.get("chat_template") == {"tokenize": True, "return_dict": False,
            "add_generation_prompt": True, "enable_thinking": False}, "full no-thinking template")
    old = doc.get("old_calibration", {})
    require(old.get("sha256") == OLD_CALIBRATION_SHA and old.get("rows") == 16
            and old.get("complete_token_sequences_disjoint") is True
            and old.get("selector_holdout_validation") is False, "old calibration claim boundary")
    seqs = doc.get("sequences")
    require(isinstance(seqs, list) and len(seqs) == 2, "two manifest sequences")
    for index, sequence in enumerate(seqs):
        require(sequence.get("id") == f"teacher-{index}" and ids_ok(sequence.get("input_ids"), 128),
                "manifest sequence IDs")
        require(sequence.get("input_ids_sha256") == token_hash(sequence["input_ids"]),
                "manifest input token hash")
    require(seqs[0]["input_ids"] != seqs[1]["input_ids"], "duplicate teacher prompts")
    return seqs


def identity(record, identities, *, expected_path=None, expected_sha=None, library=False,
             allow_chunk_wrapper=False):
    require(isinstance(record, dict), "missing file identity")
    path = regular(record.get("path", ""))
    if expected_path is not None:
        require(path == expected_path, "file identity path differs")
    if library:
        require(".so" in path.name, "mapped operator library must name a shared object")
    elif allow_chunk_wrapper and str(path) == CHUNK_DISABLE_WRAPPER["path"]:
        require(record == CHUNK_DISABLE_WRAPPER, "frozen chunk disable wrapper binding")
    else:
        require(any(path.is_relative_to(root) for root in SOURCE_ROOTS), "source outside audited roots")
    expected = record.get("sha256")
    require(isinstance(expected, str) and HASH.fullmatch(expected), "invalid identity hash")
    if expected_sha is not None:
        require(expected == expected_sha, "source identity differs from explicit binding")
    key = str(path)
    if key in identities:
        require(identities[key]["sha256"] == expected, "inconsistent file identity")
    else:
        require(file_sha(path) == expected, "current file differs from recorded identity: " + key)
        identities[key] = {"path": key, "sha256": expected, "size_bytes": path.stat().st_size,
                           "kind": "mapped_library" if library else "source"}
    if "unwrapped" in record:
        identity(record["unwrapped"], identities)
    return record


def check_ready(ready, rank, manifest_sha, worker_sha, identities, layers=LAYERS):
    require(ready.get("schema") == SCHEMA and ready.get("rank") == rank
            and ready.get("local_rank") == rank and ready.get("manifest_sha256") == manifest_sha,
            "rank ready binding")
    identity(ready.get("worker"), identities, expected_path=WORKER, expected_sha=worker_sha)
    identity(ready.get("observer_helper"), identities, expected_path=HELPER, expected_sha=HELPER_SHA)
    protocol = ready.get("protocol", {})
    require(protocol == {"tensor_parallel_size": 4, "pipeline_parallel_size": 1,
            "enable_prefix_caching": False, "speculative_config": None,
            "kv_transfer_config": None, "weight_transfer_config": None,
            "dtype": "torch.bfloat16"}, "worker admission protocol")
    sources = ready.get("runtime_sources")
    require(isinstance(sources, dict) and bool(sources), "runtime source evidence absent")
    for value in sources.values():
        identity(value, identities)
    for key in ("parent_worker", "model_class", "model_forward", "chunk", "l2norm"):
        identity(ready.get(key), identities, allow_chunk_wrapper=(key == "chunk"))
    require("npu_recurrent_gated_delta_rule" in ready.get("native_schema", ""), "native operator schema")
    layer_rows = ready.get("layers")
    require(isinstance(layer_rows, list) and [x.get("layer") for x in layer_rows] == list(layers),
            "ready layer topology")
    for row in layer_rows:
        require(str(row.get("prefix", "")).endswith(f'.layers.{row["layer"]}.linear_attn'),
                "ready layer prefix")
        for key in ("core", "rearrange"):
            identity(row.get(key), identities)
        norm = row.get("norm", {})
        for key in ("class", "forward", "dispatched_forward"):
            require(key in norm, "actual dispatched norm source absent")
            identity(norm[key], identities)
        attrs = norm.get("attributes", {})
        require(attrs.get("eps") == 1e-6 and attrs.get("group_size") is None
                and attrs.get("norm_before_gate") is True, "frozen norm attributes")
    return {row["layer"]: row["norm"] for row in layer_rows}


def check_metadata(tensor, meta, rank, *, state=False):
    require(isinstance(meta, dict), "tensor metadata absent")
    shape = meta.get("shape")
    strides = meta.get("stride")
    require(isinstance(shape, list) and bool(shape) and all(type(x) is int and x > 0 for x in shape),
            "invalid metadata shape")
    require(isinstance(strides, list) and len(strides) == len(shape)
            and all(type(x) is int and x >= 0 for x in strides), "invalid metadata strides")
    if state:
        require(shape[1:] == [12, 128, 128] and meta.get("dtype") == "torch.float32",
                "full cache metadata geometry")
        element = 4
    else:
        require(shape == list(tensor.shape) and meta.get("dtype") == str(tensor.dtype),
                "snapshot differs from source metadata")
        element = tensor.element_size()
    require(meta.get("numel") == math.prod(shape) and meta.get("element_size") == element,
            "metadata element count")
    device = meta.get("device")
    require(device == f"npu:{rank}" or (not state and not tensor.is_floating_point() and device == "cpu"),
            "metadata source device/rank")
    for key in ("data_ptr", "storage_ptr", "storage_offset", "storage_nbytes"):
        require(type(meta.get(key)) is int and meta[key] >= 0, "metadata pointer integer")
    require(meta["data_ptr"] > 0 and meta["storage_ptr"] > 0
            and meta["data_ptr"] == meta["storage_ptr"] + meta["storage_offset"] * element,
            "metadata pointer/offset relation")
    last = meta["storage_offset"] + sum((dim - 1) * stride for dim, stride in zip(shape, strides))
    require((last + 1) * element <= meta["storage_nbytes"], "metadata storage bounds")
    expected_stride = 1
    contiguous = True
    for dim, stride in reversed(list(zip(shape, strides))):
        if dim != 1 and stride != expected_stride:
            contiguous = False
        expected_stride *= dim
    require(type(meta.get("contiguous")) is bool and meta["contiguous"] == contiguous,
            "metadata contiguity flag")


def check_tensor(value, shape, dtypes):
    require(isinstance(value, torch.Tensor) and value.device.type == "cpu"
            and tuple(value.shape) == tuple(shape) and value.dtype in dtypes
            and value.is_contiguous() and bool(torch.isfinite(value).all()),
            "tensor shape/dtype/device/finite/contiguity mismatch")


def check_decode_state_view(meta, cache, slot):
    """Bind a captured decode source view to cache[slot:slot+1], not its CPU copy."""
    expected = {key: cache[key] for key in
                ("stride", "dtype", "device", "element_size", "storage_ptr", "storage_nbytes")}
    expected.update(
        shape=[1] + cache["shape"][1:],
        numel=math.prod(cache["shape"][1:]),
        storage_offset=cache["storage_offset"] + slot * cache["stride"][0],
        data_ptr=cache["data_ptr"] + slot * cache["stride"][0] * cache["element_size"],
    )
    require(all(meta.get(key) == value for key, value in expected.items()),
            "decode state source is not the selected cache slot view")


def check_record(record, sequence, rank, layer, step, nonce, manifest_sha, norm_info,
                 previous_state, previous_cache, previous_norm_weight):
    require(isinstance(record, dict), "capture record must be dict")
    expected = {"schema": SCHEMA, "manifest_sha256": manifest_sha,
                "sequence_id": sequence["id"], "nonce": nonce, "rank": rank,
                "layer": layer, "step": step, "phase": "prefill" if step == 0 else "decode",
                "operator_calls": 1, "scale": 128 ** -0.5}
    for key, value in expected.items():
        require(type(record.get(key)) is type(value) and record[key] == value, "record binding " + key)
    expected_ids = sequence["input_ids"] if step == 0 else [sequence["output_ids"][step - 1]]
    require(ids_ok(record.get("input_ids"), len(expected_ids)) and record["input_ids"] == expected_ids,
            "capture/API token trajectory")
    check_positions(record.get("positions"), step)
    require(record.get("input_ids_source") in
            ("root_input_ids", "frozen_runner_input_ids_buffer_with_text_embeddings"),
            "unrecognized input token provenance")
    require(record.get("norm") == norm_info, "norm source/attributes changed from ready")
    tensors, metas = record.get("tensors"), record.get("tensor_metadata")
    names = PREFILL_TENSORS if step == 0 else DECODE_TENSORS
    require(isinstance(tensors, dict) and set(tensors) == names, "exact capture tensor coverage")
    derived = {"state_initial", "state_final"} if step == 0 else set()
    require(isinstance(metas, dict) and set(metas) == names - derived, "exact source metadata coverage")
    tokens = 128 if step == 0 else 1
    bf16, fp32, integers = (torch.bfloat16,), (torch.float32,), (torch.int32, torch.int64)
    for key in ("raw_q", "raw_k"):
        check_tensor(tensors[key], (1, tokens, 4, 128), bf16)
    check_tensor(tensors["raw_v"], (1, tokens, 12, 128), bf16)
    for key in ("state_initial", "state_final"):
        check_tensor(tensors[key], (1, 12, 128, 128), fp32)
    for key in ("norm_input", "z", "norm_output"):
        check_tensor(tensors[key], (tokens * 12, 128), bf16)
    # Norm parameter dtype is explicitly observed and kept stable; accept the
    # two floating storage types supported by this frozen BF16/FP32 norm path.
    check_tensor(tensors["norm_weight"], (128,), (torch.bfloat16, torch.float32))
    check_metadata(None, record.get("state_metadata"), rank, state=True)
    indices = record.get("state_indices")
    require(ids_ok(indices, 1) and indices[0] < record["state_metadata"]["shape"][0],
            "one valid state slot")
    if previous_cache is not None:
        require(record["state_metadata"] == previous_cache, "cache metadata changed")
    if previous_norm_weight is not None:
        require(equal_bytes(tensors["norm_weight"], previous_norm_weight), "norm weight changed")

    if step == 0:
        initial_flag = record.get("has_initial_state")
        require(isinstance(initial_flag, list) and len(initial_flag) == 1
                and initial_flag[0] is False, "prefill initial-state reset flag")
        for key in ("q", "k"):
            check_tensor(tensors[key], (1, 128, 4, 128), bf16)
            require(equal_bytes(tensors[key], tensors["raw_" + key]), "prefill raw Q/K mismatch")
        check_tensor(tensors["v"], (1, 128, 12, 128), bf16)
        require(equal_bytes(tensors["v"], tensors["raw_v"]), "prefill raw V mismatch")
        check_tensor(tensors["g"], (1, 128, 12), fp32)
        check_tensor(tensors["beta"], (1, 128, 12), bf16)
        check_tensor(tensors["initial_state"], (1, 12, 128, 128), fp32)
        check_tensor(tensors["chunk_state_final"], (1, 12, 128, 128), fp32)
        check_tensor(tensors["cu_seqlens"], (2,), integers)
        require(tensors["cu_seqlens"].tolist() == [0, 128], "prefill cumulative sequence boundary")
        require(equal_bytes(tensors["state_initial"],
                            tensors["initial_state"].transpose(-1, -2).contiguous()),
                "prefill effective initial-state layout")
        require(equal_bytes(tensors["state_initial"], torch.zeros_like(tensors["state_initial"])),
                "prefill effective state is not finite byte-zero")
        require(equal_bytes(tensors["state_final"],
                            tensors["chunk_state_final"].transpose(-1, -2).contiguous()),
                "prefill final-state cache layout")
        check_tensor(tensors["operator_output"], (1, 128, 12, 128), bf16)
    else:
        for key in ("query", "key"):
            check_tensor(tensors[key], (1, 4, 128), bf16)
        check_tensor(tensors["value"], (1, 12, 128), bf16)
        check_tensor(tensors["g"], (1, 12), fp32)
        check_tensor(tensors["beta"], (1, 12), bf16)
        for key in ("actual_seq_lengths", "ssm_state_indices"):
            require(isinstance(tensors[key], torch.Tensor) and tensors[key].dtype in integers,
                    "decode native index dtype")
        check_tensor(tensors["actual_seq_lengths"], (2,), integers)
        require(tensors["actual_seq_lengths"].tolist() == [0, 1], "native sequence-length ABI")
        require(tensors["ssm_state_indices"].reshape(-1).tolist() == indices, "native slot binding")
        require(equal_bytes(tensors["value"], tensors["raw_v"].squeeze(0)), "decode raw V mismatch")
        require(previous_state is not None and equal_bytes(previous_state, tensors["state_initial"]),
                "recurrent state trajectory discontinuity")
        check_tensor(tensors["operator_output"], (1, 12, 128), bf16)
    require(equal_bytes(tensors["norm_input"], tensors["operator_output"].reshape(-1, 128)),
            "operator output/actual norm input byte mismatch")
    for name, meta in metas.items():
        # Index views can have an explicit singleton axis; preserve its recorded
        # shape, while validating dtype, storage and semantic flattened contents.
        if name == "ssm_state_indices":
            require(tensors[name].device.type == "cpu" and tensors[name].is_contiguous()
                    and tensors[name].numel() == 1 and bool(torch.isfinite(tensors[name]).all()),
                    "state-index snapshot")
        check_metadata(tensors[name], meta, rank)
    if step > 0:
        for name in ("state_initial", "state_final"):
            check_decode_state_view(metas[name], record["state_metadata"], indices[0])
    return tensors["state_final"], record["state_metadata"], tensors["norm_weight"]


def check_file_list(files, capture, sid, rank, layers=LAYERS):
    names = [f"{sid}.rank{rank}.layer{layer}.step{step}.pt"
             for step in range(9) for layer in layers]
    require(isinstance(files, list) and len(files) == 9 * len(layers)
            and [x.get("file") for x in files] == names, "file order/name/coverage mismatch")
    result = []
    for entry, filename in zip(files, names):
        path = capture / filename
        require(entry.get("path") == str(path), "archive path mismatch")
        require(isinstance(entry.get("sha256"), str) and HASH.fullmatch(entry["sha256"]),
                "archive SHA256 format")
        result.append((path, entry["sha256"],
                       int(filename.split(".layer")[1].split(".")[0]),
                       int(filename.split(".step")[1].split(".")[0])))
    return result


def check_inventory(capture, names, layers=LAYERS):
    expected_count = 2 * 4 * 9 * len(layers)
    require(len(names) == expected_count and len(set(names)) == expected_count
            and set(names) == {path.name for path in capture.glob("*.pt")},
            "exact archive inventory")


def load_record(path, expected):
    raw = bound_bytes(path, expected)  # Verify archive bytes before the safe unpickler sees them.
    record = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
    return record, len(raw)


def audit(service_dir, manifest_path, manifest_sha, collector_receipt_sha, collector_sha, worker_sha):
    service = directory(service_dir)
    require(RESULT_ROOT.resolve() in service.parents, "service must be below /drrqr-results")
    capture = directory(service / "teacher-capture")
    for path in capture.iterdir():
        require(path.is_file() and not path.is_symlink(), "capture directory must be flat and non-symlink")
        require(not path.name.endswith(".partial") and not path.name.endswith(".failure.json")
                and path.name != "armed.json", "unfinished/failed/armed capture evidence")
    manifest_path = regular(manifest_path)
    manifest = bound_json(manifest_path, manifest_sha)
    layers = manifest_layers(manifest)
    sequences = check_manifest(manifest)
    receipt_path = service / "teacher-collector.json"
    receipt = bound_json(receipt_path, collector_receipt_sha)
    require(receipt.get("schema") == SCHEMA
            and receipt.get("status") == "teacher_capture_complete_local_fidelity_only"
            and receipt.get("manifest") == str(manifest_path)
            and receipt.get("manifest_sha256") == manifest_sha
            and receipt.get("script_sha256") == collector_sha, "collector receipt binding/status")
    require(receipt.get("protocol") == {"requests": 2, "sequential": True, "input_tokens": 128,
            "output_tokens": 9, "decode_steps": 8, "ignore_eos": True, "no_thinking": True,
            "health_seconds": 900, "request_retries": 0}, "collector fixed protocol")
    identities = {}
    identity({"path": str(COLLECTOR), "sha256": collector_sha}, identities, expected_path=COLLECTOR)
    identity({"path": str(WORKER), "sha256": worker_sha}, identities, expected_path=WORKER)
    service_path = service / "service-manifest.json"
    service_sha = receipt.get("service_manifest_sha256")
    service_doc = bound_json(service_path, service_sha)
    require(service_doc.get("schema") == "drrqr-gdn-teacher-service/v1"
            and service_doc.get("capture_manifest") == str(manifest_path)
            and service_doc.get("capture_manifest_sha256") == manifest_sha
            and service_doc.get("capture_manifest_schema") == SCHEMA
            and service_doc.get("worker") == str(WORKER)
            and service_doc.get("worker_sha256") == worker_sha
            and service_doc.get("variant") == "dense128"
            and service_doc.get("model") == MODEL
            and service_doc.get("tensor_parallel_size") == 4
            and service_doc.get("shared_hf_head_k_dim") == 128
            and service_doc.get("calibration_only") is True
            and service_doc.get("enforce_eager") is True
            and service_doc.get("profiler_config") is None, "service source/protocol binding")
    observer = service_doc.get("observer_flags", {})
    require(observer.get("DRRQR_GDN_TEACHER_MANIFEST") == str(manifest_path)
            and observer.get("DRRQR_GDN_TEACHER_MANIFEST_SHA256") == manifest_sha
            and observer.get("DRRQR_GDN_TEACHER_DIR") == str(capture), "observer environment binding")
    regular(service / "stop.request")
    # Launcher source itself is checked through its recorded source identity.
    identity({"path": str(ROOT / "tools/run_gdn_teacher_capture.py"),
              "sha256": service_doc.get("wrapper_sha256")}, identities)
    identity({"path": str(ROOT / "tools/run_layerwise_service.py"),
              "sha256": service_doc.get("shared_helper_sha256")}, identities)
    ready, ready_hashes, native_schemas = {}, [], []
    for rank in range(4):
        path = regular(capture / f"rank{rank}.ready.json")
        raw = path.read_bytes()
        doc = json.loads(raw)
        ready[rank] = check_ready(doc, rank, manifest_sha, worker_sha, identities, layers)
        native_schemas.append(doc["native_schema"])
        ready_hashes.append({"path": str(path), "sha256": sha_bytes(raw)})
    require(len(set(native_schemas)) == 1, "native operator schema differs between ranks")
    results = receipt.get("results")
    require(isinstance(results, list) and len(results) == 2, "two collector results")
    archives, complete_evidence, expected_files = [], [], set()
    for sequence, result in zip(sequences, results):
        sid = sequence["id"]
        nonce = result.get("nonce")
        require(result.get("schema") == SCHEMA and result.get("sequence_id") == sid
                and result.get("input_ids_sha256") == sequence["input_ids_sha256"]
                and isinstance(nonce, str) and re.fullmatch(r"[a-zA-Z0-9-]{16,64}", nonce),
                "collector arm/result identity")
        ids = result.get("token_ids")
        require(ids_ok(ids, 9) and result.get("token_ids_sha256") == token_hash(ids),
                "completion output token identity")
        sequence = dict(sequence, output_ids=ids)
        response_path = capture / f"{sid}.response.json"
        require(result.get("response_path") == str(response_path), "response receipt path")
        response = bound_json(response_path, result.get("response_sha256"))
        require(response.get("schema") == SCHEMA and response.get("sequence_id") == sid
                and response.get("nonce") == nonce
                and response.get("input_ids_sha256") == sequence["input_ids_sha256"]
                and response.get("manifest_sha256") == manifest_sha
                and response.get("service_manifest_sha256") == service_sha, "raw API response binding")
        api = response.get("response", {})
        choices = api.get("choices")
        require(isinstance(choices, list) and len(choices) == 1, "single raw completion")
        scores = (choices[0].get("logprobs") or {}).get("token_logprobs")
        require(choices[0].get("token_ids") == ids and choices[0].get("finish_reason") == "length"
                and api.get("usage", {}).get("prompt_tokens") == 128
                and api.get("usage", {}).get("completion_tokens") == 9
                and isinstance(scores, list) and len(scores) == 9
                and all(type(x) in (float, int) and math.isfinite(x) for x in scores)
                and result.get("selected_logprobs") == scores, "API response coverage")
        worker_rows = result.get("worker_reports")
        require(isinstance(worker_rows, list) and [x.get("rank") for x in worker_rows] == list(range(4)),
                "collector four-rank coverage")
        for rank, worker_result in enumerate(worker_rows):
            complete_path = capture / f"{sid}.rank{rank}.complete.json"
            require(worker_result.get("path") == str(complete_path)
                    and all(worker_result.get(key) == value
                            for key, value in (("steps", 9), ("layers", len(layers)),
                                               ("records", 9 * len(layers)))),
                    "collector worker completion coverage")
            complete = bound_json(complete_path, worker_result.get("sha256"))
            expected = {"schema": SCHEMA, "sequence_id": sid, "nonce": nonce, "rank": rank,
                        "steps": 9, "layers": len(layers), "records": 9 * len(layers),
                        "layer_ids": list(layers),
                        "manifest_sha256": manifest_sha,
                        "input_ids_per_step": [sequence["input_ids"]] + [[x] for x in ids[:8]]}
            require(all(complete.get(key) == value for key, value in expected.items()),
                    "complete manifest/trajectory/count binding")
            libraries = complete.get("loaded_libraries")
            require(isinstance(libraries, list) and bool(libraries), "mapped library evidence absent")
            require(any("libcust_opapi" in Path(x.get("path", "")).name for x in libraries),
                    "native custom opapi mapping/hash absent")
            for entry in libraries:
                identity(entry, identities, library=True)
            files = complete.get("files")
            require(isinstance(files, list) and len(files) == 9 * len(layers),
                    "files per sequence/rank")
            for path, checksum, layer, step in check_file_list(
                    files, capture, sid, rank, layers):
                require(path.name not in expected_files, "duplicate archive across completions")
                expected_files.add(path.name)
                archives.append((path, checksum, sequence, rank, layer, step, nonce))
            complete_evidence.append({"path": str(complete_path), "sha256": worker_result["sha256"],
                                      "records": 9 * len(layers)})
    check_inventory(capture, [row[0].name for row in archives], layers)
    require(results[0]["nonce"] != results[1]["nonce"], "two sequences reuse nonce")
    previous_states, cache_metadata, norm_weights = {}, {}, {}
    file_reports = []
    for path, checksum, sequence, rank, layer, step, nonce in archives:
        record, size = load_record(path, checksum)
        key = (sequence["id"], rank, layer)
        shared_key = (rank, layer)
        previous, cache, weight = check_record(
            record, sequence, rank, layer, step, nonce, manifest_sha, ready[rank][layer],
            previous_states.get(key), cache_metadata.get(shared_key), norm_weights.get(shared_key))
        previous_states[key], cache_metadata[shared_key], norm_weights[shared_key] = previous, cache, weight
        file_reports.append({"file": path.name, "sha256": checksum, "size_bytes": size,
                             "sequence_id": sequence["id"], "rank": rank, "layer": layer, "step": step,
                             "norm_weight_dtype": str(weight.dtype)})
    return {
        "schema": AUDIT_SCHEMA, "status": "dense_teacher_evidence_validated_local_only", "claim": CLAIM,
        "manifest": {"path": str(manifest_path), "sha256": manifest_sha},
        "collector_receipt": {"path": str(receipt_path), "sha256": collector_receipt_sha},
        "service_manifest": {"path": str(service_path), "sha256": service_sha},
        "ready_reports": ready_hashes, "complete_reports": complete_evidence,
        "archive_count": len(archives), "files": file_reports,
        "identities": list(identities.values()),
        "native_schema": native_schemas[0],
        "checks": {"full_coverage": True, "token_trajectory": True,
                   "state_continuity_bytes": True, "effective_prefill_byte_zero": True,
                   "decode_selected_cache_view_binding": True,
                   "operator_to_norm_input_bytes": True, "norm_source_attrs_weight_stable": True,
                   "shapes_dtypes_finite": True},
        "limits": [
            "Ready report hashes are collected here; they were not individually pinned by the collector.",
            "Captured pass-through cache-write equality is a worker assertion; archives independently "
            "prove final-state layout and continuity, not an additional cache-after snapshot.",
            "No recomputation of Q/K normalization, recurrent math or gated RMS output is performed.",
            "No claim that the loaded same-name ACLNN symbol or device binary was resolved.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("service-dir", "manifest", "output-dir"):
        parser.add_argument("--" + flag, type=Path, required=True)
    for flag in ("manifest-sha256", "collector-receipt-sha256", "collector-sha256", "worker-sha256"):
        parser.add_argument("--" + flag, required=True)
    args = parser.parse_args(argv)
    output = args.output_dir
    require(output.is_absolute() and output == output.resolve() and not output.exists()
            and RESULT_ROOT.resolve() in output.parents, "fresh output below /drrqr-results required")
    require(not output.is_relative_to(args.service_dir.resolve()), "keep original capture directory immutable")
    output.mkdir(parents=False, exist_ok=False)
    report = {"schema": AUDIT_SCHEMA, "status": "failed", "claim": CLAIM}
    try:
        report = audit(args.service_dir, args.manifest, args.manifest_sha256,
                       args.collector_receipt_sha256, args.collector_sha256, args.worker_sha256)
    except BaseException as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        report["auditor_sha256"] = file_sha(__file__)
        report["completed_unix_ns"] = time.time_ns()
        with (output / "report.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps({"status": report["status"], "report": str(output / "report.json")}), flush=True)
    return report


if __name__ == "__main__":
    main()
