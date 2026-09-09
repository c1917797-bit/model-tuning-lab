"""Software-control tests only: no Ascend runtime, model, NPU, or fidelity claim."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest
import torch


@pytest.fixture
def teacher(monkeypatch):
    stub = ModuleType("vllm_ascend.worker.worker")
    stub.NPUWorker = type("FakeNPUWorker", (), {})
    monkeypatch.setitem(sys.modules, "vllm_ascend.worker.worker", stub)
    root = Path(__file__).resolve().parents[1]
    for name, filename in (
        ("layerwise_probe_worker", "layerwise_probe_worker.py"),
        ("isolated_gdn_teacher_worker", "gdn_teacher_capture_worker.py"),
    ):
        spec = importlib.util.spec_from_file_location(name, root / "tools" / filename)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
    return module


def manifest(teacher):
    return {
        "schema": teacher.SCHEMA, "model": teacher.MODEL, "tp_size": 4,
        "input_tokens": 128, "decode_steps": 8, "output_tokens": 9,
        "no_thinking": True, "layers": list(teacher.LAYERS),
        "sequences": [
            {"id": f"teacher-{i}", "input_ids": list(range(i, i + 128)),
             "input_ids_sha256": teacher.ids_sha256(list(range(i, i + 128)))}
            for i in range(2)
        ],
    }


@pytest.fixture
def worker(teacher, tmp_path, monkeypatch):
    obj = teacher.GdnTeacherCaptureWorker()
    obj.rank = obj.local_rank = 0
    obj._teacher_dir = tmp_path
    obj._manifest = manifest(teacher)
    obj._layers = list(obj._manifest["layers"])
    obj._manifest_hash = "a" * 64
    obj._frame = obj._current = obj._libraries = None
    for name in ("_pending", "_last_state", "_steps", "_nonces", "_tokens",
                 "_receipts", "_norm_info"):
        setattr(obj, name, {})
    monkeypatch.setattr(teacher, "loaded_libraries", lambda: [{"scope": "mock-only"}])
    return obj


def arm(worker, sid="teacher-0", nonce="0123456789abcdef"):
    seq = worker._manifest["sequences"][int(sid[-1])]
    path = worker._teacher_dir / "armed.json"
    path.write_text(json.dumps({
        "schema": worker._manifest["schema"], "sequence_id": sid,
        "input_ids_sha256": seq["input_ids_sha256"], "nonce": nonce,
    }))
    return seq


def begin(worker, step=0, sid="teacher-0"):
    seq = arm(worker, sid)
    ids = seq["input_ids"] if step == 0 else [1000 + step]
    positions = list(range(128)) if step == 0 else [127 + step]
    kwargs = {"input_ids": torch.tensor(ids), "positions": torch.tensor(positions)}
    assert worker._model_before(None, (), kwargs) is None
    return kwargs


def frame_record(worker, phase="decode", layer=0, slot=1):
    return {
        "schema": worker._manifest["schema"], "sequence_id": "teacher-0",
        "nonce": "0123456789abcdef", "rank": 0, "layer": layer,
        "phase": phase, "step": 0 if phase == "prefill" else 1,
        "state_indices": [slot], "tensors": ({"raw_v": torch.ones(1, 1, 12, 128, dtype=torch.bfloat16)}
                                              if phase == "decode" else {}),
        "tensor_metadata": {},
    }


def decode_kwargs(state, slot=1):
    return {
        "query": torch.ones(1, 4, 128, dtype=torch.bfloat16),
        "key": torch.ones(1, 4, 128, dtype=torch.bfloat16),
        "value": torch.ones(1, 12, 128, dtype=torch.bfloat16),
        "g": torch.ones(1, 12), "beta": torch.ones(1, 12),
        "actual_seq_lengths": torch.tensor([0, 1], dtype=torch.int32),
        "ssm_state_indices": torch.tensor([slot], dtype=torch.int32),
        "state": state, "scale": 128 ** -0.5,
    }


def chunk_kwargs(initial=None):
    return {
        "q": torch.ones(1, 128, 4, 128, dtype=torch.bfloat16),
        "k": torch.ones(1, 128, 4, 128, dtype=torch.bfloat16),
        "v": torch.ones(1, 128, 12, 128, dtype=torch.bfloat16),
        "g": torch.ones(1, 128, 12), "beta": torch.ones(1, 128, 12),
        "initial_state": (torch.zeros(1, 12, 128, 128) if initial is None else initial),
        "cu_seqlens": torch.tensor([0, 128], dtype=torch.int32),
        "use_qk_l2norm_in_kernel": True, "head_first": False,
        "output_final_state": True,
    }


def install_context(monkeypatch, module, metadata):
    context = ModuleType("vllm.forward_context")
    context.get_forward_context = lambda: SimpleNamespace(attn_metadata={module.prefix: metadata})
    monkeypatch.setitem(sys.modules, "vllm.forward_context", context)


def core_fixture(worker, teacher, monkeypatch, step=0):
    worker._steps["teacher-0"] = step
    begin(worker, step)
    state = torch.full((3, 12, 128, 128), 17.0)
    module = SimpleNamespace(prefix="model.layers.0.linear_attn", kv_cache=[None, state])
    metadata = SimpleNamespace(
        spec_sequence_masks=None, num_prefills=int(step == 0),
        num_decodes=int(step != 0), num_actual_tokens=128 if step == 0 else 1,
        prefill_state_indices=torch.tensor([1], dtype=torch.int32),
        non_spec_state_indices_tensor=torch.tensor([1], dtype=torch.int32),
        prefill_has_initial_state=torch.tensor([False]),
    )
    worker._norm_info[0] = {"scope": "mock-only"}
    install_context(monkeypatch, module, metadata)
    return module, metadata


def test_manifest_accepts_exact_bounded_protocol(teacher):
    doc = manifest(teacher)
    assert teacher.validate_manifest(doc) is doc


@pytest.mark.parametrize("key,value", [
    ("tp_size", True), ("input_tokens", 127), ("decode_steps", 9),
    ("output_tokens", 8), ("no_thinking", 1), ("layers", [0, 0]),
    ("model", "/another/model"), ("schema", "other"),
])
def test_manifest_rejects_protocol_drift(teacher, key, value):
    doc = manifest(teacher)
    doc[key] = value
    with pytest.raises(RuntimeError, match="manifest"):
        teacher.validate_manifest(doc)


def test_manifest_accepts_frozen_dynamic_layer_set(teacher):
    doc = manifest(teacher)
    doc["layers"] = list(range(48))
    assert len(doc["layers"]) == 48
    assert teacher.validate_manifest(doc)["layers"] == doc["layers"]


@pytest.mark.parametrize("mutation", ["hash", "boolean_token", "duplicate", "count"])
def test_manifest_rejects_bad_token_identity(teacher, mutation):
    doc = manifest(teacher)
    if mutation == "hash":
        doc["sequences"][0]["input_ids_sha256"] = "b" * 64
    elif mutation == "boolean_token":
        doc["sequences"][0]["input_ids"][0] = True
    elif mutation == "duplicate":
        doc["sequences"][1] = copy.deepcopy(doc["sequences"][0])
        doc["sequences"][1]["id"] = "teacher-1"
    else:
        doc["sequences"].pop()
    with pytest.raises(RuntimeError):
        teacher.validate_manifest(doc)


def test_step_tokens_and_text_mrope_positions_bound(teacher):
    seq = manifest(teacher)["sequences"][0]
    assert teacher.validate_step(seq, 0, seq["input_ids"], [list(range(128))] * 3) is None
    for step in range(1, 9):
        teacher.validate_step(seq, step, [555], [127 + step])
    with pytest.raises(RuntimeError, match="non-text MRoPE"):
        teacher.validate_step(seq, 1, [555], [[128], [128], [129]])
    with pytest.raises(RuntimeError, match="prompt"):
        teacher.validate_step(seq, 0, list(range(1, 129)), list(range(128)))
    with pytest.raises(RuntimeError, match="positions/chunked"):
        teacher.validate_step(seq, 0, seq["input_ids"][:64], list(range(64)))
    with pytest.raises(RuntimeError, match="outside fixed budget"):
        teacher.validate_step(seq, 9, [555], [136])


def test_unarmed_warmup_all_wrappers_passthrough_without_capture(worker):
    sentinel = object()
    calls = []
    def original(*args, **kwargs):
        calls.append((args, kwargs))
        return sentinel
    token = torch.tensor([7])
    assert worker._model_before(None, (), {"input_ids": token}) is None
    assert worker._core_wrapper(0, None, original)(token, same=token) is sentinel
    assert worker._rearrange_wrapper(0, original)(token) is sentinel
    assert worker._chunk_wrapper(original)(token) is sentinel
    worker._native = original
    assert worker._decode(token) is sentinel
    assert worker._norm_hook(0)(None, (), sentinel) is None
    assert worker._model_after(None, (), {}, sentinel) is None
    assert len(calls) == 4 and calls[0][0][0] is token
    assert calls[0][1]["same"] is token
    assert worker._frame is None and not worker._steps
    assert list(worker._teacher_dir.iterdir()) == []


def test_two_sequences_nine_steps_six_layers_admission(worker, teacher):
    # Exercise frame accounting only. Synthetic receipts are not tensor evidence.
    for sid in ("teacher-0", "teacher-1"):
        for step in range(9):
            kwargs = begin(worker, step, sid)
            assert worker._frame["step"] == step
            worker._frame["layers"] = list(teacher.LAYERS)
            worker._frame["records"] = [
                {"file": f"mock-{sid}-{step}-{layer}"} for layer in teacher.LAYERS
            ]
            output = object()
            assert worker._model_after(None, (), kwargs, output) is None
        data = json.loads((worker._teacher_dir / f"{sid}.rank0.complete.json").read_text())
        assert data["steps"] == 9 and data["layers"] == 6 and data["records"] == 54
        assert len(data["files"]) == 54 and len(data["input_ids_per_step"]) == 9
        assert data["input_ids_per_step"][0] == worker._manifest["sequences"][int(sid[-1])]["input_ids"]
        assert data["input_ids_per_step"][1:] == [[1000 + step] for step in range(1, 9)]
        assert data["manifest_sha256"] == worker._manifest_hash
    assert sum(map(len, worker._receipts.values())) == 108
    with pytest.raises(RuntimeError, match="outside fixed budget"):
        begin(worker, 9, "teacher-1")


def test_model_sequence_order_nonce_and_prompt_binding(worker):
    with pytest.raises(RuntimeError, match="sequence ordering"):
        begin(worker, 0, "teacher-1")
    seq = arm(worker)
    kwargs = {"input_ids": torch.tensor(seq["input_ids"]), "positions": torch.arange(128)}
    bad = dict(kwargs, input_ids=torch.arange(1, 129))
    with pytest.raises(RuntimeError, match="prompt/decode"):
        worker._model_before(None, (), bad)
    arm(worker, nonce="fedcba9876543210")
    with pytest.raises(RuntimeError, match="nonce changed"):
        worker._model_before(None, (), kwargs)


@pytest.mark.parametrize("layers,records,pending", [
    ([0, 12, 25, 38, 50], 5, False),
    ([0, 12, 25, 38, 50, 50], 6, False),
    ([0, 12, 25, 38, 50, 62], 5, False),
    ([0, 12, 25, 38, 50, 62], 6, True),
])
def test_model_after_rejects_missing_duplicate_or_pending_layers(worker, layers, records, pending):
    begin(worker)
    worker._frame["layers"] = layers
    worker._frame["records"] = [{} for _ in range(records)]
    if pending:
        worker._pending[0] = {}
    with pytest.raises(RuntimeError, match="unfinished|incomplete/duplicate"):
        worker._model_after(None, (), {}, object())
    assert not worker._steps
    assert not list(worker._teacher_dir.glob("*.complete.json"))


@pytest.mark.parametrize("change,reason", [
    ({"spec_sequence_masks": torch.tensor([True])}, "speculation"),
    ({"num_prefills": 1, "num_decodes": 1}, "mixed/chunked"),
    ({"num_actual_tokens": 64}, "mixed/chunked"),
    ({"prefill_has_initial_state": torch.tensor([True])}, "reset state"),
    ({"prefill_state_indices": torch.tensor([-1])}, "valid slot"),
    ({"prefill_state_indices": torch.tensor([0, 1])}, "valid slot"),
])
def test_core_rejects_spec_mixed_chunked_or_invalid_initial_state(
        worker, teacher, monkeypatch, change, reason):
    module, meta = core_fixture(worker, teacher, monkeypatch)
    for key, value in change.items():
        setattr(meta, key, value)
    called = []
    with pytest.raises(RuntimeError, match=reason):
        worker._core_wrapper(0, module, lambda: called.append(True))()
    assert not called


def test_core_rejects_wrong_layer_or_non_fp32_state(worker, teacher, monkeypatch):
    module, _ = core_fixture(worker, teacher, monkeypatch)
    with pytest.raises(RuntimeError, match="selected layer order"):
        worker._core_wrapper(12, module, lambda: None)()
    module.kv_cache[1] = module.kv_cache[1].to(torch.bfloat16)
    with pytest.raises(RuntimeError, match="FP32 state geometry"):
        worker._core_wrapper(0, module, lambda: None)()


def test_prefill_effective_zero_with_dirty_reused_slot_and_readonly_norm_hook(
        worker, teacher, monkeypatch):
    module, _ = core_fixture(worker, teacher, monkeypatch)
    state = module.kv_cache[1]
    untouched = state[[0, 2]].clone()
    metadata_before = teacher.tensor_metadata(state)
    inputs = chunk_kwargs()
    out = torch.ones(1, 128, 12, 128, dtype=torch.bfloat16)
    last = torch.full((1, 12, 128, 128), 2.0)
    core_result = object()
    raw = (inputs["q"], inputs["k"], inputs["v"])
    def chunk(**kwargs):
        assert kwargs["initial_state"] is inputs["initial_state"]
        return out, last
    def original_core():
        observed = worker._rearrange_wrapper(0, lambda: raw)()
        assert observed is raw
        actual_out, actual_last = worker._chunk_wrapper(chunk)(**inputs)
        assert actual_out is out and actual_last is last
        state[1:2].copy_(last.transpose(-1, -2))
        return core_result
    assert worker._core_wrapper(0, module, original_core)() is core_result
    assert teacher.byte_equal(state[[0, 2]], untouched)
    assert teacher.tensor_metadata(state) == metadata_before
    record = worker._pending[0]
    assert not torch.count_nonzero(record["tensors"]["state_initial"])
    assert teacher.byte_equal(worker._last_state[("teacher-0", 0)], state[1:2])
    norm_input = out.reshape(-1, 128)
    z = torch.ones_like(norm_input)
    norm_output = norm_input + 1
    norm = SimpleNamespace(weight=torch.ones(128))
    before = norm_output.clone()
    assert worker._norm_hook(0)(norm, (norm_input, z), norm_output) is None
    assert teacher.byte_equal(norm_output, before)
    assert not worker._pending and worker._frame["layers"] == [0]
    saved = worker._teacher_dir / "teacher-0.rank0.layer0.step0.pt"
    assert saved.is_file() and len(worker._frame["records"]) == 1
    assert worker._frame["records"][0]["sha256"] == hashlib.sha256(saved.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match="selected layer order"):
        worker._core_wrapper(0, module, original_core)()


@pytest.mark.parametrize("mutation,reason", [
    ("nonzero", "effective prefill"),
    ("bf16", "effective prefill"),
    ("boundaries", "prefill boundaries"),
    ("normalization", "normalization/state flags"),
])
def test_chunk_rejects_nonzero_or_wrong_effective_initial_contract(worker, mutation, reason):
    worker._current = frame_record(worker, phase="prefill")
    kwargs = chunk_kwargs()
    for name in ("q", "k", "v"):
        worker._current["tensors"]["raw_" + name] = kwargs[name].clone()
    if mutation == "nonzero":
        kwargs["initial_state"][0, 0, 0, 0] = 1
    elif mutation == "bf16":
        kwargs["initial_state"] = kwargs["initial_state"].to(torch.bfloat16)
    elif mutation == "boundaries":
        kwargs["cu_seqlens"] = torch.tensor([0, 64, 128])
    else:
        kwargs["use_qk_l2norm_in_kernel"] = False
    called = []
    with pytest.raises(RuntimeError, match=reason):
        worker._chunk_wrapper(lambda **kw: called.append(True))(**kwargs)
    assert not called


def test_decode_preserves_argument_identity_and_tracks_fp32_state(worker, teacher):
    state = torch.zeros(3, 12, 128, 128)
    state[1].fill_(4)
    worker._last_state[("teacher-0", 0)] = state[1:2].clone()
    worker._current = frame_record(worker)
    kwargs = decode_kwargs(state)
    out = torch.ones(1, 12, 128, dtype=torch.bfloat16)
    untouched = state[[0, 2]].clone()
    def native(**actual):
        assert actual.keys() == kwargs.keys()
        assert all(actual[key] is value for key, value in kwargs.items())
        actual["state"][1].add_(1)
        return out
    worker._native = native
    assert worker._decode(**kwargs) is out
    record = worker._current
    assert record["operator_calls"] == 1
    assert torch.all(record["tensors"]["state_initial"] == 4)
    assert torch.all(record["tensors"]["state_final"] == 5)
    assert teacher.byte_equal(state[[0, 2]], untouched)
    assert record["tensors"]["state_initial"].dtype == torch.float32


@pytest.mark.parametrize("mutation,reason", [
    ("length", "length ABI"), ("slot", "slot binding"), ("scale", "dense scale"),
    ("discontinuity", "trajectory discontinuity"), ("signed_zero", "trajectory discontinuity"),
    ("missing_previous", "trajectory discontinuity"),
])
def test_decode_rejects_misbinding_or_discontinuous_state_before_native(worker, mutation, reason):
    state = torch.zeros(3, 12, 128, 128)
    worker._last_state[("teacher-0", 0)] = state[1:2].clone()
    worker._current = frame_record(worker)
    kwargs = decode_kwargs(state)
    if mutation == "length":
        kwargs["actual_seq_lengths"] = torch.tensor([1], dtype=torch.int32)
    elif mutation == "slot":
        kwargs["ssm_state_indices"] = torch.tensor([2], dtype=torch.int32)
    elif mutation == "scale":
        kwargs["scale"] = 1.0
    elif mutation == "discontinuity":
        state[1, 0, 0, 0] = 1
    elif mutation == "signed_zero":
        state[1, 0, 0, 0] = -0.0
    else:
        worker._last_state.clear()
    called = []
    worker._native = lambda **kw: called.append(True)
    with pytest.raises(RuntimeError, match=reason):
        worker._decode(**kwargs)
    assert not called


def test_norm_hook_uses_none_return_and_exclusive_output(worker, teacher):
    begin(worker)
    output = torch.ones(12, 128, dtype=torch.bfloat16)
    record = frame_record(worker, phase="prefill")
    record["tensors"]["operator_output"] = output.reshape(1, 1, 12, 128)
    worker._pending[0] = record
    path = worker._teacher_dir / "teacher-0.rank0.layer0.step0.pt"
    path.write_bytes(b"prior evidence")
    norm = SimpleNamespace(weight=torch.ones(128))
    with pytest.raises(FileExistsError):
        worker._norm_hook(0)(norm, (output, output), output)
    assert path.read_bytes() == b"prior evidence"


def test_json_exclusive_preserves_old_public_and_new_partial(worker, teacher):
    path = worker._teacher_dir / "result.json"
    teacher.write_json(path, {"generation": 1})
    prior = path.read_bytes()
    with pytest.raises(FileExistsError):
        teacher.write_json(path, {"generation": 2})
    assert path.read_bytes() == prior
    assert json.loads(path.with_name("result.json.partial").read_text()) == {"generation": 2}


def test_guard_retains_first_failure_and_partial_frame(worker):
    begin(worker)
    first = ValueError("intentional observer failure")
    def fail():
        raise first
    with pytest.raises(ValueError) as info:
        worker._guard(fail)()
    assert info.value is first
    path = worker._teacher_dir / "rank0.failure.json"
    prior = path.read_bytes()
    report = json.loads(prior)
    assert report["frame"]["step"] == 0
    assert "intentional observer failure" in report["traceback"]
    worker._failure(RuntimeError("second failure"))
    assert path.read_bytes() == prior


@pytest.mark.parametrize("dtype", [torch.bfloat16, torch.float32])
def test_snapshot_detached_copy_preserves_source_and_raw_bytes(teacher, dtype):
    source = torch.arange(24, dtype=dtype).reshape(4, 6).t()
    before = teacher.tensor_metadata(source)
    result = teacher.snapshot(source)
    assert result.is_contiguous() and result.data_ptr() != source.data_ptr()
    assert teacher.tensor_metadata(source) == before and teacher.byte_equal(source, result)
    result[0, 0] = 100
    assert source[0, 0].item() == 0
    assert not teacher.byte_equal(torch.tensor([0.0], dtype=dtype),
                                  torch.tensor([-0.0], dtype=dtype))
    with pytest.raises(RuntimeError, match="nonfinite"):
        teacher.snapshot(torch.tensor([float("nan")], dtype=dtype))


@pytest.mark.parametrize("mrope", [False, True])
def test_embedding_branch_binds_exact_runner_token_buffer(worker, mrope):
    seq = arm(worker)
    buffer = torch.tensor(seq["input_ids"] + [999] * 8)
    worker.model_runner = SimpleNamespace(input_ids=SimpleNamespace(gpu=buffer))
    positions = torch.arange(128)
    if mrope:
        positions = positions.expand(3, 128)
    kwargs = {"input_ids": None, "positions": positions, "inputs_embeds": torch.ones(128, 2)}
    before = buffer.clone()
    assert worker._model_before(None, (), kwargs) is None
    assert worker._frame["input_ids"] == seq["input_ids"]
    assert worker._frame["input_ids_source"] == "frozen_runner_input_ids_buffer_with_text_embeddings"
    assert torch.equal(buffer, before)


@pytest.mark.parametrize("mutation,reason", [
    ("missing_embedding", "embedding token interface"),
    ("embedding_length", "embedding token interface"),
    ("buffer_token", "prompt/decode token mismatch"),
    ("positions", "positions/chunked"),
])
def test_embedding_branch_does_not_relax_input_identity(worker, mutation, reason):
    seq = arm(worker)
    buffer = torch.tensor(seq["input_ids"] + [999] * 8)
    worker.model_runner = SimpleNamespace(input_ids=SimpleNamespace(gpu=buffer))
    kwargs = {"input_ids": None, "positions": torch.arange(128), "inputs_embeds": torch.ones(128, 2)}
    if mutation == "missing_embedding":
        kwargs["inputs_embeds"] = None
    elif mutation == "embedding_length":
        kwargs["inputs_embeds"] = torch.ones(127, 2)
    elif mutation == "buffer_token":
        buffer[0] += 1
    else:
        kwargs["positions"] = torch.arange(1, 129)
    with pytest.raises(RuntimeError, match=reason):
        worker._model_before(None, (), kwargs)
    assert worker._frame is None


def test_torch_root_hooks_do_not_replace_model_output(worker, teacher):
    seq = arm(worker)
    output = torch.ones(2, 3)
    class Model(torch.nn.Module):
        def forward(self, input_ids, positions):
            worker._frame["layers"] = list(teacher.LAYERS)
            worker._frame["records"] = [{"mock_layer": layer} for layer in teacher.LAYERS]
            return output
    model = Model()
    model.register_forward_pre_hook(worker._guard(worker._model_before), with_kwargs=True)
    model.register_forward_hook(worker._guard(worker._model_after), with_kwargs=True)
    result = model(input_ids=torch.tensor(seq["input_ids"]), positions=torch.arange(128))
    assert result is output and torch.equal(output, torch.ones(2, 3))
    assert worker._steps == {"teacher-0": 1}


def test_torch_norm_hook_does_not_replace_output_or_mutate_inputs(worker, teacher):
    begin(worker)
    x = torch.ones(12, 128, dtype=torch.bfloat16)
    z = torch.full_like(x, 2)
    output = x * z
    record = frame_record(worker, phase="prefill")
    record["tensors"]["operator_output"] = x.reshape(1, 1, 12, 128).clone()
    worker._pending[0] = record
    class Norm(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.weight = torch.nn.Parameter(torch.ones(128), requires_grad=False)
        def forward(self, actual_x, actual_z):
            assert actual_x is x and actual_z is z
            return output
    norm = Norm()
    norm.register_forward_hook(worker._guard(worker._norm_hook(0)))
    result = norm(x, z)
    assert result is output
    assert torch.equal(x, torch.ones_like(x)) and torch.equal(z, torch.full_like(z, 2))


@pytest.mark.parametrize("phase", ["prefill", "decode"])
def test_raw_operator_input_identity_mismatch_fails_before_operator(worker, phase):
    record = frame_record(worker, phase=phase)
    worker._current = record
    called = []
    if phase == "prefill":
        kwargs = chunk_kwargs()
        for name in ("q", "k", "v"):
            record["tensors"]["raw_" + name] = kwargs[name].clone()
        record["tensors"]["raw_k"][0, 0, 0, 0] = 2
        call = worker._chunk_wrapper(lambda **kw: called.append(True))
        message = "prefill raw input mismatch"
    else:
        kwargs = decode_kwargs(torch.zeros(3, 12, 128, 128))
        record["tensors"]["raw_v"][0, 0, 0, 0] = 2
        worker._native = lambda **kw: called.append(True)
        call = worker._decode
        message = "decode value input mismatch"
    with pytest.raises(RuntimeError, match=message):
        call(**kwargs)
    assert not called


def test_json_serialization_failure_retains_partial_file(worker, teacher):
    path = worker._teacher_dir / "serialization.json"
    with pytest.raises(ValueError):
        teacher.write_json(path, {"value": float("nan")})
    assert not path.exists()
    assert path.with_name("serialization.json.partial").is_file()
