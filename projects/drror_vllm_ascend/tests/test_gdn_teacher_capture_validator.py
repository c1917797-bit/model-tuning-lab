"""CPU-only integrity tests. Synthetic fixtures are not a captured teacher run."""
import importlib.util
import json
from pathlib import Path

import pytest
import torch

SOURCE = Path(__file__).resolve().parents[1] / "tools/validate_gdn_teacher_capture.py"
spec = importlib.util.spec_from_file_location("teacher_validator_test", SOURCE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

SHA = "a" * 64
NONCE = "fixture-nonce-00000001"
NORM = {"attributes": {"eps": 1e-6, "group_size": None, "norm_before_gate": True},
        "class": {"symbol": "fixture"}, "forward": {"symbol": "fixture"}}


def tensor_meta(tensor, rank=0):
    return {"shape": list(tensor.shape), "stride": list(tensor.stride()),
            "dtype": str(tensor.dtype), "device": f"npu:{rank}", "numel": tensor.numel(),
            "element_size": tensor.element_size(), "data_ptr": tensor.data_ptr(),
            "storage_ptr": tensor.untyped_storage().data_ptr(),
            "storage_offset": tensor.storage_offset(),
            "storage_nbytes": tensor.untyped_storage().nbytes(),
            "contiguous": tensor.is_contiguous()}


def sequence():
    return {"id": "teacher-0", "input_ids": list(range(128)), "output_ids": list(range(70, 79))}


def record_fixture(step=0, *, previous=None, cache=None):
    seq = sequence()
    count = 128 if step == 0 else 1
    bf16 = torch.bfloat16
    initial = torch.zeros(1, 12, 128, 128) if previous is None else previous.clone()
    final = (torch.arange(12 * 128 * 128, dtype=torch.float32).reshape(1, 12, 128, 128) * 1e-6
             if step == 0 else initial + 0.01)
    tensors = {
        "raw_q": torch.ones(1, count, 4, 128, dtype=bf16),
        "raw_k": torch.ones(1, count, 4, 128, dtype=bf16),
        "raw_v": torch.ones(1, count, 12, 128, dtype=bf16),
        "state_initial": initial, "state_final": final,
        "norm_input": torch.ones(count * 12, 128, dtype=bf16),
        "z": torch.ones(count * 12, 128, dtype=bf16),
        "norm_output": torch.ones(count * 12, 128, dtype=bf16),
        "norm_weight": torch.ones(128, dtype=bf16),
    }
    if step == 0:
        tensors.update(q=tensors["raw_q"], k=tensors["raw_k"], v=tensors["raw_v"],
                       g=torch.zeros(1, 128, 12), beta=torch.ones(1, 128, 12, dtype=bf16),
                       initial_state=initial.transpose(-1, -2).contiguous(),
                       chunk_state_final=final.transpose(-1, -2).contiguous(),
                       cu_seqlens=torch.tensor([0, 128], dtype=torch.int32),
                       operator_output=tensors["norm_input"].reshape(1, 128, 12, 128))
    else:
        tensors.update(query=tensors["raw_q"].squeeze(0), key=tensors["raw_k"].squeeze(0),
                       value=tensors["raw_v"].squeeze(0), g=torch.zeros(1, 12),
                       beta=torch.ones(1, 12, dtype=bf16),
                       actual_seq_lengths=torch.tensor([0, 1], dtype=torch.int32),
                       ssm_state_indices=torch.tensor([0], dtype=torch.int32),
                       operator_output=tensors["norm_input"].reshape(1, 12, 128))
    derived = {"state_initial", "state_final"} if step == 0 else set()
    metadata = {key: tensor_meta(value) for key, value in tensors.items() if key not in derived}
    if cache is None:
        cache = tensor_meta(torch.zeros(2, 12, 128, 128))
    if step > 0:
        # CPU snapshots are separate copies; their recorded source metadata must
        # describe the cache's slot-zero view, not those independent CPU allocations.
        for name in ("state_initial", "state_final"):
            metadata[name] = dict(cache, shape=[1, 12, 128, 128],
                                  numel=12 * 128 * 128, contiguous=True)
    return {"schema": audit.SCHEMA, "manifest_sha256": SHA, "sequence_id": seq["id"],
            "nonce": NONCE, "rank": 0, "layer": 0, "step": step,
            "phase": "prefill" if step == 0 else "decode", "operator_calls": 1,
            "scale": 128 ** -0.5, "input_ids": seq["input_ids"] if step == 0 else [seq["output_ids"][step - 1]],
            "positions": list(range(128)) if step == 0 else [127 + step],
            "input_ids_source": "root_input_ids", "norm": NORM,
            "state_indices": [0], "state_metadata": cache,
            "has_initial_state": [False], "tensors": tensors, "tensor_metadata": metadata}


def check(record, previous=None, cache=None, weight=None):
    return audit.check_record(record, sequence(), 0, 0, record["step"], NONCE, SHA, NORM,
                              previous, cache, weight)


def test_valid_prefill_and_decode_trajectory():
    prefill = record_fixture()
    state, cache, weight = check(prefill)
    decode = record_fixture(1, previous=state, cache=cache)
    after, _, _ = check(decode, state, cache, weight)
    assert audit.equal_bytes(after, decode["tensors"]["state_final"])


def test_decode_nonzero_cache_offset_and_selected_slot():
    arena = torch.zeros(5, 12, 128, 128)
    cache_view = arena[1:4]
    state, cache, weight = check(record_fixture(cache=tensor_meta(cache_view)))
    decode = record_fixture(1, previous=state, cache=cache)
    decode["state_indices"] = [1]
    decode["tensors"]["ssm_state_indices"][0] = 1
    selected = cache_view[1:2]
    selected.copy_(state)
    decode["tensor_metadata"]["state_initial"] = tensor_meta(selected)
    selected.copy_(decode["tensors"]["state_final"])
    decode["tensor_metadata"]["state_final"] = tensor_meta(selected)
    check(decode, state, cache, weight)


@pytest.mark.parametrize("name", ("state_initial", "state_final"))
def test_decode_independent_allocation_metadata_is_rejected(name):
    state, cache, weight = check(record_fixture())
    decode = record_fixture(1, previous=state, cache=cache)
    foreign = torch.zeros(1, 12, 128, 128)
    decode["tensor_metadata"][name] = tensor_meta(foreign)
    # This metadata is internally consistent, but does not identify the cache.
    audit.check_metadata(decode["tensors"][name], decode["tensor_metadata"][name], 0)
    with pytest.raises(ValueError, match="selected cache slot view"):
        check(decode, state, cache, weight)


@pytest.mark.parametrize("field", ("storage_ptr", "storage_offset", "data_ptr",
                                    "stride", "storage_nbytes", "dtype", "device"))
def test_decode_cache_view_each_address_component_is_bound(field):
    arena = torch.zeros(5, 12, 128, 128)
    cache = tensor_meta(arena[1:4])
    meta = tensor_meta(arena[2:3])
    audit.check_decode_state_view(meta, cache, 1)
    if field == "stride":
        meta[field] = list(meta[field])
        meta[field][0] += 1
    elif field == "dtype":
        meta[field] = "torch.bfloat16"
    elif field == "device":
        meta[field] = "npu:1"
    else:
        meta[field] += 4
    with pytest.raises(ValueError, match="selected cache slot view"):
        audit.check_decode_state_view(meta, cache, 1)


def test_decode_wrong_slot_view_is_rejected():
    arena = torch.zeros(5, 12, 128, 128)
    cache = tensor_meta(arena[1:4])
    with pytest.raises(ValueError, match="selected cache slot view"):
        audit.check_decode_state_view(tensor_meta(arena[3:4]), cache, 1)


@pytest.mark.parametrize("kind", ["token", "position", "nonce", "layer", "rank", "phase",
                                   "operator_calls", "manifest", "missing_tensor", "extra_tensor"])
def test_record_identity_and_coverage_fail_closed(kind):
    record = record_fixture()
    if kind == "token":
        record["input_ids"][3] = 999
    elif kind == "position":
        record["positions"][3] = 999
    elif kind == "nonce":
        record["nonce"] = "wrong-nonce-000000"
    elif kind == "layer":
        record["layer"] = 12
    elif kind == "rank":
        record["rank"] = 1
    elif kind == "phase":
        record["phase"] = "decode"
    elif kind == "operator_calls":
        record["operator_calls"] = 2
    elif kind == "manifest":
        record["manifest_sha256"] = "b" * 64
    elif kind == "missing_tensor":
        del record["tensors"]["z"]
    else:
        record["tensors"]["extra"] = torch.ones(1)
    with pytest.raises(ValueError):
        check(record)


@pytest.mark.parametrize("kind", ["nan", "dtype", "shape", "metadata", "zero", "transpose",
                                   "norm_input", "norm_attrs"])
def test_tensor_effective_state_and_norm_fail_closed(kind):
    record = record_fixture()
    tensors = record["tensors"]
    if kind == "nan":
        tensors["g"][0, 0, 0] = float("nan")
    elif kind == "dtype":
        tensors["raw_q"] = tensors["raw_q"].float()
    elif kind == "shape":
        tensors["raw_q"] = tensors["raw_q"][:, :-1]
    elif kind == "metadata":
        record["tensor_metadata"]["g"]["device"] = "npu:1"
    elif kind == "zero":
        tensors["state_initial"][0, 0, 0, 0] = 1
        tensors["initial_state"] = tensors["state_initial"].transpose(-1, -2).contiguous()
    elif kind == "transpose":
        tensors["chunk_state_final"] = tensors["state_final"].clone()
    elif kind == "norm_input":
        tensors["norm_input"] = tensors["norm_input"].clone()
        tensors["norm_input"][0, 0] = 0
    else:
        record["norm"] = {"attributes": {"eps": 1e-5}}
    with pytest.raises(ValueError):
        check(record)


@pytest.mark.parametrize("kind", ["state", "weight", "cache", "native_lengths", "native_slot", "raw_value"])
def test_decode_incremental_checks(kind):
    state, cache, weight = check(record_fixture())
    record = record_fixture(1, previous=state, cache=cache)
    if kind == "state":
        record["tensors"]["state_initial"][0, 0, 0, 0] += 1
    elif kind == "weight":
        record["tensors"]["norm_weight"][0] = 2
    elif kind == "cache":
        record["state_metadata"] = dict(cache, storage_nbytes=cache["storage_nbytes"] + 4)
    elif kind == "native_lengths":
        record["tensors"]["actual_seq_lengths"][0] = 1
    elif kind == "native_slot":
        record["tensors"]["ssm_state_indices"][0] = 1
    else:
        record["tensors"]["value"] = record["tensors"]["value"].clone()
        record["tensors"]["value"][0, 0, 0] = 2
    with pytest.raises(ValueError):
        check(record, state, cache, weight)


def test_text_mrope_and_signed_zero():
    audit.check_positions([list(range(128)) for _ in range(3)], 0)
    with pytest.raises(ValueError):
        audit.check_positions([[128], [129], [128]], 1)
    assert not audit.equal_bytes(torch.tensor([0.0]), torch.tensor([-0.0]))
    assert not audit.equal_bytes(torch.tensor([float("inf")]), torch.tensor([float("inf")]))


def test_source_metadata_bounds_and_strided_views():
    base = torch.arange(24, dtype=torch.float32).reshape(4, 6)
    view = base[:, 1::2]
    metadata = tensor_meta(view)
    audit.check_metadata(view.contiguous(), metadata, 0)
    bad = dict(metadata, storage_nbytes=1)
    with pytest.raises(ValueError, match="storage bounds"):
        audit.check_metadata(view.contiguous(), bad, 0)
    bad = dict(metadata, data_ptr=metadata["data_ptr"] + 4)
    with pytest.raises(ValueError, match="pointer"):
        audit.check_metadata(view.contiguous(), bad, 0)


def test_archive_sha_precedes_weights_only_loading(tmp_path, monkeypatch):
    path = tmp_path / "record.pt"
    torch.save({"tensor": torch.tensor([1.0]), "text": "trusted local fixture"}, path)
    sha = audit.file_sha(path)
    original_load = audit.torch.load
    observed = []
    def load(stream, **kwargs):
        observed.append(kwargs)
        return original_load(stream, **kwargs)
    monkeypatch.setattr(audit.torch, "load", load)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        audit.load_record(path, "0" * 64)
    assert observed == []
    result, size = audit.load_record(path, sha)
    assert observed == [{"map_location": "cpu", "weights_only": True}]
    assert result["text"] == "trusted local fixture" and size == path.stat().st_size


def file_list(capture, sid, rank, layers=audit.LAYERS):
    return [{"file": f"{sid}.rank{rank}.layer{layer}.step{step}.pt",
             "path": str(capture / f"{sid}.rank{rank}.layer{layer}.step{step}.pt"), "sha256": SHA}
            for step in range(9) for layer in layers]


def test_exact_432_inventory_and_complete_file_order(tmp_path):
    names = []
    for sid in ("teacher-0", "teacher-1"):
        for rank in range(4):
            files = file_list(tmp_path, sid, rank)
            entries = audit.check_file_list(files, tmp_path, sid, rank)
            assert len(entries) == 54
            for path, _, _, _ in entries:
                path.touch()
                names.append(path.name)
    audit.check_inventory(tmp_path, names)
    with pytest.raises(ValueError):
        audit.check_inventory(tmp_path, names[:-1])
    (tmp_path / "unexpected.pt").touch()
    with pytest.raises(ValueError):
        audit.check_inventory(tmp_path, names)


def test_dynamic_layer_inventory_and_order(tmp_path):
    layers = tuple(range(48))
    assert len(layers) == 48
    names = []
    for sid in ("teacher-0", "teacher-1"):
        for rank in range(4):
            files = file_list(tmp_path, sid, rank, layers)
            entries = audit.check_file_list(files, tmp_path, sid, rank, layers)
            assert len(entries) == 432
            for path, _, _, _ in entries:
                path.touch()
                names.append(path.name)
    audit.check_inventory(tmp_path, names, layers)


@pytest.mark.parametrize("kind", ["duplicate", "path_escape", "hash", "missing", "order"])
def test_complete_files_fail_closed(tmp_path, kind):
    files = file_list(tmp_path, "teacher-0", 0)
    if kind == "duplicate":
        files[1] = files[0]
    elif kind == "path_escape":
        files[0]["path"] = str(tmp_path.parent / files[0]["file"])
    elif kind == "hash":
        files[0]["sha256"] = "bad"
    elif kind == "missing":
        files.pop()
    else:
        files[0], files[1] = files[1], files[0]
    with pytest.raises(ValueError):
        audit.check_file_list(files, tmp_path, "teacher-0", 0)


def test_symlink_archives_are_rejected_before_loading(tmp_path):
    path = tmp_path / "real.pt"
    path.write_bytes(b"not a torch archive")
    link = tmp_path / "link.pt"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="non-symlink"):
        audit.load_record(link, audit.file_sha(path))


def test_source_and_library_identity_hashes(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "SOURCE_ROOTS", (tmp_path,))
    path = tmp_path / "source.py"
    path.write_text("source fixture")
    row = {"path": str(path), "sha256": audit.file_sha(path)}
    verified = {}
    audit.identity(row, verified, expected_path=path)
    assert verified[str(path)]["size_bytes"] == path.stat().st_size
    path.write_text("changed source")
    with pytest.raises(ValueError, match="recorded identity"):
        audit.identity(row, {}, expected_path=path)
    with pytest.raises(ValueError, match="shared object"):
        audit.identity(row, {}, library=True)


def test_main_failure_receipt_and_fresh_output_only(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "RESULT_ROOT", tmp_path)
    source = tmp_path / "service"
    source.mkdir()
    def fail(*args):
        raise ValueError("intentional incomplete capture")
    monkeypatch.setattr(audit, "audit", fail)
    output = tmp_path / "audit-result"
    argv = ["--service-dir", str(source), "--manifest", str(tmp_path / "manifest.json"),
            "--manifest-sha256", SHA, "--collector-receipt-sha256", SHA,
            "--collector-sha256", SHA, "--worker-sha256", SHA, "--output-dir", str(output)]
    with pytest.raises(ValueError, match="incomplete"):
        audit.main(argv)
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "failed"
    assert "Not candidate fidelity" in report["claim"]
    before = (output / "report.json").read_bytes()
    with pytest.raises(ValueError, match="fresh output"):
        audit.main(argv)
    assert (output / "report.json").read_bytes() == before


def test_validator_does_not_import_worker_or_start_device():
    code = SOURCE.read_text()
    assert "from vllm" not in code and "import torch_npu" not in code
    assert "torch.npu" not in code and "subprocess" not in code


def frozen_wrapper_fixture(tmp_path, monkeypatch):
    import copy
    wrapper = tmp_path / "site-packages/torch/_dynamo/eval_frame.py"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text("mock disable wrapper; no execution")
    source_root = tmp_path / "vllm-ascend"
    source_root.mkdir()
    chunk = source_root / "chunk.py"
    chunk.write_text("mock wrapped chunk; no execution")
    record = copy.deepcopy(audit.CHUNK_DISABLE_WRAPPER)
    record["path"], record["sha256"] = str(wrapper), audit.file_sha(wrapper)
    record["unwrapped"]["path"] = str(chunk)
    record["unwrapped"]["sha256"] = audit.file_sha(chunk)
    monkeypatch.setattr(audit, "SOURCE_ROOTS", (source_root,))
    monkeypatch.setattr(audit, "CHUNK_DISABLE_WRAPPER", copy.deepcopy(record))
    return record


def test_chunk_wrapper_binding_is_exact_frozen_path_hash_and_symbol():
    row = audit.CHUNK_DISABLE_WRAPPER
    assert row["path"] == "/usr/local/python3.12.13/lib/python3.12/site-packages/torch/_dynamo/eval_frame.py"
    assert row["sha256"] == "8f49ecb842a4d50281695e5b8d015fd9afd2a202b0f6c9f3f94c91415ba0d5a4"
    assert row["unwrapped"]["path"] == "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/chunk.py"
    assert row["unwrapped"]["sha256"] == "6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5"
    assert row["symbol"] == row["unwrapped"]["symbol"] == (
        "vllm_ascend.ops.triton.fla.chunk.chunk_gated_delta_rule")


def test_wrapper_exception_is_explicit_and_both_files_are_hashed(tmp_path, monkeypatch):
    record = frozen_wrapper_fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="outside audited roots"):
        audit.identity(record, {})
    observed = {}
    audit.identity(record, observed, allow_chunk_wrapper=True)
    assert set(observed) == {record["path"], record["unwrapped"]["path"]}
    Path(record["unwrapped"]["path"]).write_text("changed chunk")
    with pytest.raises(ValueError, match="recorded identity"):
        audit.identity(record, {}, allow_chunk_wrapper=True)


@pytest.mark.parametrize("damage", ("wrapper_path", "wrapper_sha", "wrapper_symbol",
                                   "unwrapped_path", "unwrapped_sha", "unwrapped_symbol",
                                   "missing_unwrapped", "extra_unwrapped"))
def test_chunk_wrapper_near_matches_are_not_whitelisted(tmp_path, monkeypatch, damage):
    record = frozen_wrapper_fixture(tmp_path, monkeypatch)
    if damage == "wrapper_path":
        other = Path(record["path"]).with_name("other.py")
        other.write_text("other wrapper")
        record["path"], record["sha256"] = str(other), audit.file_sha(other)
    elif damage == "wrapper_sha":
        record["sha256"] = "0" * 64
    elif damage == "wrapper_symbol":
        record["symbol"] += "_other"
    elif damage == "unwrapped_path":
        other = Path(record["unwrapped"]["path"]).with_name("other_chunk.py")
        other.write_text("other chunk under otherwise allowed root")
        record["unwrapped"]["path"] = str(other)
        record["unwrapped"]["sha256"] = audit.file_sha(other)
    elif damage == "unwrapped_sha":
        record["unwrapped"]["sha256"] = "0" * 64
    elif damage == "unwrapped_symbol":
        record["unwrapped"]["symbol"] += "_other"
    elif damage == "missing_unwrapped":
        del record["unwrapped"]
    else:
        record["unwrapped"]["unwrapped"] = dict(record["unwrapped"])
    with pytest.raises(ValueError):
        audit.identity(record, {}, allow_chunk_wrapper=True)


def test_actual_wrapper_bytes_are_still_checked(tmp_path, monkeypatch):
    record = frozen_wrapper_fixture(tmp_path, monkeypatch)
    Path(record["path"]).write_text("changed wrapper")
    with pytest.raises(ValueError, match="recorded identity"):
        audit.identity(record, {}, allow_chunk_wrapper=True)
