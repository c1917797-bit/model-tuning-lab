"""Small CPU/mock tests for DRRQR teacher replay, not NPU or model qualification."""
import copy
import importlib.util
import os
from pathlib import Path

# Importing Torch for CPU fixtures must not discover an NPU backend automatically.
os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
import pytest
import torch

SOURCE = Path(__file__).resolve().parents[1] / "tools/replay_gdn_teacher.py"
_spec = importlib.util.spec_from_file_location("gdn_teacher_replay_under_test", SOURCE)
replay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(replay)
LAYERS = (0, 12, 25, 38, 50, 62)
PLAN_SHA = "b1fcb727d3e58be66cc24148e30a5a1722d3bdc0914784f01cad02f11f741b8c"
STATS_SHA = "8882d60948ed773bb200303a1878d43441bda105bac4090e776b34ad684ceb7b"
CALIBRATION_SHA = "81748f94c4eff0ad5e4053eb7c4a30b1a397a82d45676a8b0b42394bd612bd47"


def frozen_fixture():
    """Nontrivial ordered coordinates; unrelated scalar fields are deliberately different."""
    plan = {
        "schema": "ascend-drrqr-plan/v1",
        "target_model_id": "Qwen/Qwen3.8-27B",
        "old_head_k_dim": 128, "target_head_k_dim": 64,
        "num_key_heads": 16, "num_value_heads": 48, "head_v_dim": 128,
        "selection_objective": "energy-kernel",
        "keep_indices": {
            str(layer): [head * 128 + (2 * index + 1 + 2 * head) % 128
                         for head in range(16) for index in range(63, -1, -1)]
            for layer in LAYERS
        },
    }
    stats = {
        "schema": "drrqr-retained-key-energy-stats/v1",
        "status": "completed_descriptive_only",
        "plan": {"path": "/plans/prune50-energy-kernel-v1.json",
                 "sha256": PLAN_SHA, "objective": "energy-kernel"},
        "calibration": {"sha256": CALIBRATION_SHA,
                        "scalar_train_rows": list(range(12)),
                        "scalar_holdout_rows": [12, 13, 14, 15]},
        "audited_layers": list(LAYERS),
        "head_records": [
            {"layer": layer, "rank": rank, "local_head": head,
             "global_head": rank * 4 + head,
             "train_k_mean": 0.5 + (rank * 4 + head) / 64,
             "heldout_k_mean": 0.99, "k_retained": {"mean": 0.98}}
            for layer in LAYERS for rank in range(4) for head in range(4)
        ],
    }
    return plan, stats


def fidelity_rows(energy=1.0, beta=0.8):
    return [
        {"sequence_id": f"teacher-{sequence}", "rank": rank, "layer": layer,
         "position": position, "energy64_relative_l2": energy,
         "beta64_relative_l2": beta}
        for sequence in range(2) for rank in range(4)
        for layer in LAYERS for position in range(136)
    ]


def test_frozen_source_hashes_are_explicit():
    assert replay.PLAN_SHA256 == PLAN_SHA
    assert replay.STATS_SHA256 == STATS_SHA


@pytest.mark.parametrize("rank", range(4))
def test_coordinate_and_value_head_mapping_uses_train_only(rank):
    plan, stats = frozen_fixture()
    for layer in LAYERS:
        keep, r4, r12 = replay.coefficients(plan, stats, layer, rank)
        assert keep.device.type == r4.device.type == r12.device.type == "cpu"
        assert keep.shape == (4, 64) and keep.dtype == torch.int64
        assert keep.tolist() == [[(2 * i + 1 + 2 * (rank * 4 + head)) % 128
                                  for i in range(63, -1, -1)] for head in range(4)]
        expected = torch.tensor([0.5 + (rank * 4 + h) / 64 for h in range(4)])
        assert r4.dtype == r12.dtype == torch.float32
        torch.testing.assert_close(r4, expected, rtol=0, atol=0)
        torch.testing.assert_close(r12, expected.repeat_interleave(3), rtol=0, atol=0)
    poisoned = copy.deepcopy(stats)
    for row in poisoned["head_records"]:
        row["heldout_k_mean"] = float("nan")
        row["k_retained"]["mean"] = float("inf")
    assert torch.equal(replay.coefficients(plan, poisoned, 0, rank)[1], expected)


@pytest.mark.parametrize("damage", ("duplicate_coordinate", "wrong_global_head",
                                   "missing_head", "duplicate_head", "zero_r", "nan_r"))
def test_coefficient_evidence_fails_closed(damage):
    plan, stats = frozen_fixture()
    if damage == "duplicate_coordinate":
        plan["keep_indices"]["0"][1] = plan["keep_indices"]["0"][0]
    elif damage == "wrong_global_head":
        stats["head_records"][0]["global_head"] = 4
    elif damage == "missing_head":
        stats["head_records"].pop(0)
    elif damage == "duplicate_head":
        stats["head_records"].append(copy.deepcopy(stats["head_records"][0]))
    elif damage == "zero_r":
        stats["head_records"][0]["train_k_mean"] = 0
    else:
        stats["head_records"][0]["train_k_mean"] = float("nan")
    with pytest.raises(ValueError):
        replay.coefficients(plan, stats, 0, 0)


@pytest.mark.parametrize("shape", ((1, 4, 128), (1, 128, 4, 128)))
def test_selection_is_per_head_and_preserves_frozen_order(shape):
    plan, stats = frozen_fixture()
    keep, _, _ = replay.coefficients(plan, stats, 0, 2)
    # Give each head distinct coordinates to detect a broadcast/wrong-axis gather.
    keep = torch.stack([torch.roll(keep[h], h) for h in range(4)])
    raw = torch.arange(torch.tensor(shape).prod().item(), dtype=torch.float32).reshape(shape)
    actual = replay.select_qk(raw, keep)
    expected = torch.stack([raw[..., h, keep[h]] for h in range(4)], dim=-2)
    assert actual.shape == shape[:-1] + (64,)
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)


@pytest.mark.parametrize("shape", ((1, 12), (1, 128, 12)))
def test_beta_is_fp32_product_then_bf16_not_premultiplied_low_precision_r(shape):
    beta = torch.full(shape, 0.8125, dtype=torch.bfloat16)
    r = torch.linspace(0.51111, 0.97777, 12, dtype=torch.float32)
    product, effective = replay.beta_product(beta, r)
    assert product.dtype == torch.float32 and effective.dtype == torch.bfloat16
    assert product.device == effective.device == beta.device
    assert torch.equal(product, beta.float() * r)
    assert torch.equal(effective, (beta.float() * r).to(torch.bfloat16))
    assert not torch.equal(product, beta.float() * r.to(torch.bfloat16).float())
    _, identity = replay.beta_product(beta, torch.ones(12, dtype=torch.float32))
    assert torch.equal(identity.view(torch.uint8), beta.view(torch.uint8))


@pytest.mark.parametrize("damage", ("beta_dtype", "r_dtype", "r_shape", "beta_heads"))
def test_beta_dtype_and_shape_are_not_silently_coerced(damage):
    beta = torch.ones((1, 12), dtype=torch.bfloat16)
    r = torch.ones(12, dtype=torch.float32)
    if damage == "beta_dtype":
        beta = beta.float()
    elif damage == "r_dtype":
        r = r.to(torch.bfloat16)
    elif damage == "r_shape":
        r = r.reshape(1, 12)
    else:
        beta = beta[:, :4]
    with pytest.raises(ValueError):
        replay.beta_product(beta, r)


def test_dense_metrics_preserve_phase_tolerances_and_independent_gates():
    reference = torch.ones(1024)
    actual = reference + 0.012
    assert replay.metrics(actual, reference, "prefill")["passed"]
    decode = replay.metrics(actual, reference, "decode")
    assert decode["allclose"] and decode["finite"]
    assert decode["relative_l2"] > 2 ** -7 and not decode["passed"]
    reference = torch.full((10000,), 0.1)
    actual = reference.clone()
    actual[0] += 0.008
    decode = replay.metrics(actual, reference, "decode")
    assert decode["allclose"] and decode["relative_l2"] < 2 ** -7
    assert decode["normalized_max"] > 2 ** -6 and not decode["passed"]


@pytest.mark.parametrize("value", (float("nan"), float("inf"), -float("inf")))
def test_nonfinite_dense_output_never_qualifies(value):
    x = torch.tensor([value])
    for phase in ("prefill", "decode"):
        result = replay.metrics(x, x, phase)
        assert not result["finite"] and not result["passed"]


def test_global_mean_requires_ten_percent_reduction():
    assert replay.fidelity_screen(fidelity_rows(beta=0.8))["passed"]
    assert not replay.fidelity_screen(fidelity_rows(beta=0.901))["passed"]


@pytest.mark.parametrize("positions", (range(136), range(64, 128), range(132, 136)))
def test_worst_group_and_both_late_windows_cannot_hide_in_global_mean(positions):
    rows = fidelity_rows(beta=0.8)
    selected = set(positions)
    for row in rows:
        if (row["sequence_id"], row["rank"], row["layer"]) == ("teacher-0", 0, 0):
            if row["position"] in selected:
                row["beta64_relative_l2"] = 1.051
    # All three counterexamples still exceed 10% improvement globally.
    assert sum(x["beta64_relative_l2"] for x in rows) / len(rows) < 0.9
    assert not replay.fidelity_screen(rows)["passed"]


@pytest.mark.parametrize("damage", ("missing", "duplicate", "wrong_position", "wrong_layer",
                                   "nan", "negative"))
def test_fidelity_coverage_and_metric_values_fail_closed(damage):
    rows = fidelity_rows()
    if damage == "missing":
        rows.pop()
    elif damage == "duplicate":
        rows[-1] = dict(rows[0])
    elif damage == "wrong_position":
        rows[0]["position"] = 136
    elif damage == "wrong_layer":
        rows[0]["layer"] = 1
    elif damage == "nan":
        rows[0]["beta64_relative_l2"] = float("nan")
    else:
        rows[0]["energy64_relative_l2"] = -0.1
    with pytest.raises(ValueError):
        replay.fidelity_screen(rows)


@pytest.mark.parametrize("field,value", (
    ("scalar_train_rows", list(range(16))),
    ("scalar_holdout_rows", [12, 13, 14]),
))
def test_scalar_training_split_is_frozen(field, value):
    plan, stats = frozen_fixture()
    stats["calibration"][field] = value
    with pytest.raises(ValueError, match="scalar training split"):
        replay.coefficients(plan, stats, 0, 0)


def main_args(tmp_path, receipt_sha):
    return [
        "--audit-report", str(tmp_path / "audit.json"), "--audit-sha256", receipt_sha,
        "--manifest", str(tmp_path / "manifest.json"), "--manifest-sha256", "a" * 64,
        "--energy-plan", str(tmp_path / "plan.json"),
        "--retained-stats", str(tmp_path / "stats.json"),
        "--output-dir", str(tmp_path / "result"),
    ]


@pytest.mark.parametrize("damage", ("status", "checksum"))
def test_bad_receipt_stops_before_runtime_and_saves_admission_failure(tmp_path, monkeypatch, damage):
    import json
    monkeypatch.setenv("ASCEND_RT_VISIBLE_DEVICES", "0,1,2,3")
    monkeypatch.setattr(replay, "RESULT_ROOT", tmp_path)
    path = tmp_path / "audit.json"
    path.write_text(json.dumps({"schema": "gdn-teacher-evidence-audit/v1",
                               "status": "failed", "auditor_sha256": replay.AUDITOR_SHA256}))
    expected = replay.checksum(path) if damage == "status" else "0" * 64
    calls = []
    monkeypatch.setattr(replay, "init_runtime", lambda *args: calls.append("runtime"))
    assert replay.main(main_args(tmp_path, expected)) == 1
    receipt = json.loads((tmp_path / "result/report.json").read_text())
    assert receipt["status"] == "failed_admission"
    assert not receipt["dense_gate_passed"] and not calls
    assert receipt["trajectories"] == []
    assert ("validator receipt" if damage == "status" else "SHA256 mismatch") in receipt["error"]
    previous = (tmp_path / "result/report.json").read_bytes()
    with pytest.raises(ValueError, match="fresh canonical output"):
        replay.main(main_args(tmp_path, expected))
    assert (tmp_path / "result/report.json").read_bytes() == previous


def mock_bound():
    from types import SimpleNamespace
    plan, stats = frozen_fixture()
    entries = {
        (f"teacher-{s}", rank, layer, step): {"file": str(step), "sha256": "c" * 64}
        for s in range(2) for rank in range(4) for layer in LAYERS for step in range(9)
    }
    library = {"path": "/mock/libcust_opapi.so", "sha256": "d" * 64}
    return SimpleNamespace(
        binding={"mock": True}, plan=plan, stats=stats, capture=Path("/mock"),
        entries=entries, audit=SimpleNamespace(load_record=lambda path, sha: (int(path.name), 0)),
        receipt={"native_schema": "mock-native",
                 "identities": [dict(library, kind="mapped_library")]}), library


@pytest.mark.parametrize("dense_failure", (True, False))
def test_main_dense_gate_order_and_failure_attribution(tmp_path, monkeypatch, dense_failure):
    import json
    from types import SimpleNamespace
    monkeypatch.setenv("ASCEND_RT_VISIBLE_DEVICES", "0,1,2,3")
    monkeypatch.setattr(replay, "RESULT_ROOT", tmp_path)
    bound, library = mock_bound()
    monkeypatch.setattr(replay, "bind_inputs", lambda args: bound)

    def initialize(report, phase):
        report["operator_schema"] = "mock-native"
        return SimpleNamespace(probe=SimpleNamespace(loaded_libraries=lambda: [library]))

    calls = []

    def trajectory(records, variant, keep, r12, runtime, group, out, report, save, phase):
        assert records == list(range(9))
        calls.append((variant, group))
        if dense_failure:
            assert variant == "dense128"
            raise ValueError("mock dense output/state gate failed")
        report["trajectories"].append({"variant": variant, "passed": True})
        value = {"dense128": 0.0, "energy64": 0.5, "beta64": 0.4}[variant]
        return [{"position": position, "relative_l2": value} for position in range(136)]

    monkeypatch.setattr(replay, "init_runtime", initialize)
    monkeypatch.setattr(replay, "run_trajectory", trajectory)
    status = replay.main(main_args(tmp_path, "a" * 64))
    result = json.loads((tmp_path / "result/report.json").read_text())
    if dense_failure:
        assert status == 1 and result["status"] == "blocked_dense_replay"
        assert calls == [("dense128", ("teacher-0", 0, 0))]
        assert not result["dense_gate_passed"] and not result["candidate_numerical_gate_passed"]
        assert "fidelity" not in result
    else:
        assert status == 0 and result["status"] == "local_fidelity_screen_pass"
        assert [x[0] for x in calls] == ["dense128"] * 48 + ["energy64"] * 48 + ["beta64"] * 48
        assert result["dense_gate_passed"] and result["candidate_numerical_gate_passed"]
        assert result["fidelity"]["passed"]
        assert "not" in result["claim"].lower() and "throughput" in result["claim"].lower()


def test_real_trajectory_control_uses_private_zero_state_and_eight_ordered_steps(tmp_path, monkeypatch):
    """Mock only device/operators/graph; execute the tool's actual trajectory orchestration."""
    from contextlib import contextmanager
    from types import SimpleNamespace
    original_to = torch.Tensor.to

    def cpu_only_to(tensor, *args, **kwargs):
        if args and args[0] == "npu:0":
            args = ("cpu",) + args[1:]
        if kwargs.get("device") == "npu:0":
            kwargs["device"] = "cpu"
        return original_to(tensor, *args, **kwargs)

    monkeypatch.setattr(torch.Tensor, "to", cpu_only_to)
    active = {"graph": None}
    eager_allocations, observed_reference_inputs, archives = [], [], []

    def result_for(data, state, compensated):
        value = float(state.flatten()[0])
        tokens = data["q"].shape[1]
        product, beta = (replay.beta_product(data["beta"], data["r"]) if compensated
                         else (data["beta"], data["beta"]))
        return {"output": torch.full((tokens, 12, 128), value, dtype=torch.bfloat16),
                "norm": torch.full((tokens, 12, 128), value, dtype=torch.bfloat16),
                "q": data["q"].squeeze(0), "k": data["k"].squeeze(0),
                "product": product, "beta": beta}

    def fake_operation(data, state, dk, compensated, runtime):
        state.add_(1)
        result = result_for(data, state, compensated)
        if active["graph"] is not None:
            active["graph"].operation = (data, state, dk, compensated, runtime)
            active["graph"].result = result
        return result

    class Graph:
        def replay(self):
            computed = fake_operation(*self.operation)
            for key, tensor in self.result.items():
                tensor.copy_(computed[key])

        def reset(self):
            pass

    @contextmanager
    def graph_context(graph):
        active["graph"] = graph
        try:
            yield
        finally:
            active["graph"] = None

    monkeypatch.setattr(torch, "npu", SimpleNamespace(
        synchronize=lambda: None, NPUGraph=Graph, graph=graph_context), raising=False)

    def reference(data, state, dk, compensated, golden):
        assert float(data["v"].flatten()[0]) == len(observed_reference_inputs) % 9
        observed_reference_inputs.append(float(state.flatten()[0]))
        updated = state + 1
        return result_for(data, updated, compensated)["output"], updated

    def fake_prefill(data, dk, compensated, runtime):
        state = torch.ones((1, 12, 128, dk), dtype=torch.float32)
        eager_allocations.append(state)
        return result_for(data, state, compensated), state

    def metadata(tensor):
        return {"shape": list(tensor.shape), "stride": list(tensor.stride()),
                "dtype": str(tensor.dtype), "data_ptr": tensor.data_ptr()}

    def save_archive(path, payload):
        archives.append((payload["variant"], payload["step"], payload["passed"],
                         float(payload["state"].flatten()[0])))
        return {"path": str(path), "sha256": "e" * 64, "size_bytes": 0}

    monkeypatch.setattr(replay, "cpu_reference", reference)
    monkeypatch.setattr(replay, "prefill", fake_prefill)
    monkeypatch.setattr(replay, "operation", fake_operation)
    monkeypatch.setattr(replay, "archive", save_archive)
    runtime = SimpleNamespace(golden=None, probe=SimpleNamespace(metadata=metadata))
    records = []
    for step in range(9):
        tokens = 128 if step == 0 else 1
        qk = torch.zeros((1, tokens, 4, 128), dtype=torch.bfloat16)
        value = torch.full((1, tokens, 12, 128), step, dtype=torch.bfloat16)
        records.append({"tensors": {
            "raw_q": qk, "raw_k": qk.clone(), "raw_v": value,
            "g": torch.zeros((1, tokens, 12) if step == 0 else (1, 12)),
            "beta": torch.ones((1, tokens, 12) if step == 0 else (1, 12), dtype=torch.bfloat16),
            "z": torch.zeros((tokens * 12, 128), dtype=torch.bfloat16),
            "norm_weight": torch.ones(128, dtype=torch.bfloat16),
            "operator_output": torch.full((tokens, 12, 128), step + 1, dtype=torch.bfloat16),
            "norm_output": torch.full((tokens * 12, 128), step + 1, dtype=torch.bfloat16),
            "state_final": torch.full((1, 12, 128, 128), step + 1, dtype=torch.float32),
            "query": qk.squeeze(0), "key": qk.squeeze(0),
        }})
    plan, stats = frozen_fixture()
    keep, _, r12 = replay.coefficients(plan, stats, 0, 0)
    report = {"trajectories": []}
    for variant in replay.VARIANTS:
        steps = []
        rows = replay.run_trajectory(
            records, variant, keep, r12, runtime, ("teacher-0", 0, 0), tmp_path,
            report, lambda: None,
            lambda phase, **details: steps.append(details["step"]) if "step" in details else None)
        assert steps == list(range(1, 9))
        assert [row["position"] for row in rows] == list(range(136))
    assert len({state.data_ptr() for state in eager_allocations}) == 3
    assert observed_reference_inputs == list(map(float, range(9))) * 3
    assert [tuple(state.shape) for state in eager_allocations] == [
        (1, 12, 128, 128), (1, 12, 128, 64), (1, 12, 128, 64)]
    assert all(torch.equal(state, torch.full_like(state, 9)) for state in eager_allocations)
    assert len(archives) == 27 and all(passed and value == step + 1
                                      for _, step, passed, value in archives)
    assert all(row["passed"] for row in report["trajectories"])


def dispatch_data(tokens):
    return {
        "q": torch.ones((1, tokens, 4, 64), dtype=torch.bfloat16),
        "k": torch.full((1, tokens, 4, 64), 2, dtype=torch.bfloat16),
        "v": torch.ones((1, tokens, 12, 128), dtype=torch.bfloat16),
        "g": torch.zeros((1, 12) if tokens == 1 else (1, tokens, 12)),
        "beta": torch.full((1, 12) if tokens == 1 else (1, tokens, 12), 0.75,
                           dtype=torch.bfloat16),
        "r": torch.linspace(0.51, 0.99, 12),
        "weight": torch.ones(128, dtype=torch.bfloat16),
        "z": torch.zeros((tokens * 12, 128), dtype=torch.bfloat16),
        "lengths": torch.tensor([0, 1], dtype=torch.int32),
        "indices": torch.zeros(1, dtype=torch.int32),
    }


def test_decode_operation_uses_bound_decode_l2_not_ascend_chunk():
    from types import SimpleNamespace
    data = dispatch_data(1)
    state = torch.zeros((1, 12, 128, 64))
    calls, observed = [], {}

    def decode_l2(tensor):
        calls.append(tensor)
        return tensor + 3

    def forbidden(*args, **kwargs):
        raise AssertionError("decode must not dispatch Ascend chunk L2")

    def native(**kwargs):
        observed.update(kwargs)
        return torch.ones((1, 12, 128), dtype=torch.bfloat16)

    runtime = SimpleNamespace(
        decode_l2norm=decode_l2, chunk=SimpleNamespace(l2norm_fwd=forbidden),
        native=native, norm=SimpleNamespace(apply=lambda tensor, *args: tensor * 2))
    result = replay.operation(data, state, 64, True, runtime)
    assert len(calls) == 2
    assert calls[0] is data["q"] and calls[1] is data["k"]
    assert calls[0].shape == calls[1].shape == (1, 1, 4, 64)
    assert observed["query"] is result["q"] and observed["key"] is result["k"]
    assert observed["query"].shape == observed["key"].shape == (1, 4, 64)
    assert torch.equal(observed["query"], data["q"].squeeze(0) + 3)
    assert observed["state"] is state and observed["scale"] == 64 ** -0.5
    assert observed["beta"] is result["beta"]
    assert torch.equal(result["beta"], (data["beta"].float() * data["r"]).bfloat16())
    assert torch.equal(result["norm"], torch.full_like(result["norm"], 2))


def test_prefill_keeps_chunk_internal_qk_norm_and_zero_initial_state(monkeypatch):
    from types import SimpleNamespace
    original_to, original_device, original_zeros = torch.Tensor.to, torch.device, torch.zeros

    def cpu_only_to(tensor, *args, **kwargs):
        if args and args[0] == "npu:0":
            args = ("cpu",) + args[1:]
        return original_to(tensor, *args, **kwargs)

    def cpu_only_zeros(*args, **kwargs):
        if kwargs.get("device") == "npu:0":
            kwargs["device"] = "cpu"
        return original_zeros(*args, **kwargs)

    monkeypatch.setattr(torch.Tensor, "to", cpu_only_to)
    monkeypatch.setattr(torch, "device", lambda value: original_device("cpu" if value == "npu:0" else value))
    monkeypatch.setattr(torch, "zeros", cpu_only_zeros)
    data, observed = dispatch_data(128), {}
    chunk_state = torch.arange(12 * 64 * 128, dtype=torch.float32).reshape(1, 12, 64, 128)

    def forbidden(*args, **kwargs):
        raise AssertionError("prefill must delegate normalization to the Ascend chunk")

    def chunk_call(**kwargs):
        observed.update(kwargs)
        return torch.ones((1, 128, 12, 128), dtype=torch.bfloat16), chunk_state

    runtime = SimpleNamespace(
        decode_l2norm=forbidden,
        chunk=SimpleNamespace(get_forward_context=lambda: None, get_pcp_group=lambda: None,
                              chunk_gated_delta_rule=chunk_call, l2norm_fwd=forbidden),
        golden=SimpleNamespace(_build_prefill_metadata=lambda device, cu: {"mock": True}),
        norm=SimpleNamespace(apply=lambda tensor, *args: tensor))
    result, final = replay.prefill(data, 64, True, runtime)
    assert observed["q"] is data["q"] and observed["k"] is data["k"]
    assert observed["use_qk_l2norm_in_kernel"] is True and observed["head_first"] is False
    assert observed["output_final_state"] is True and observed["scale"] == 64 ** -0.5
    assert observed["initial_state"].shape == (1, 12, 64, 128)
    assert torch.count_nonzero(observed["initial_state"]) == 0
    assert observed["initial_state"].dtype == torch.float32
    assert observed["cu_seqlens"].tolist() == [0, 128]
    assert observed["beta"] is result["beta"]
    assert torch.equal(final, chunk_state.transpose(-1, -2).contiguous())
