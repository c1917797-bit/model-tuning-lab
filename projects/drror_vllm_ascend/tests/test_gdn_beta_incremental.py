"""CPU mocks only: no NPU initialization, model execution, or qualification claim."""
import copy
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
import pytest
import torch

SOURCE = Path(__file__).resolve().parents[1] / "tools/probe_gdn_beta_incremental.py"
spec = importlib.util.spec_from_file_location("beta_incremental_under_test", SOURCE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
replay = probe.load_replay()


def record(step):
    tokens = 128 if step == 0 else 1
    beta_shape = (1, 128, 12) if step == 0 else (1, 12)
    return {
        "sequence_id": "teacher-0", "rank": 0, "layer": 0, "step": step,
        "tensors": {
            "raw_q": torch.full((1, tokens, 4, 128), step + 1, dtype=torch.bfloat16),
            "raw_k": torch.full((1, tokens, 4, 128), step + 2, dtype=torch.bfloat16),
            "raw_v": torch.full((1, tokens, 12, 128), step, dtype=torch.bfloat16),
            "g": torch.zeros(beta_shape), "beta": torch.full(beta_shape, 0.8125, dtype=torch.bfloat16),
            "z": torch.zeros((tokens * 12, 128), dtype=torch.bfloat16),
            "norm_weight": torch.ones(128, dtype=torch.bfloat16),
            "state_initial": torch.full((1, 12, 128, 128), 999.0),
            "state_final": torch.full((1, 12, 128, 128), 999.0),
        },
    }


def selection():
    return torch.arange(64).repeat(4, 1), torch.tensor([0.5, 0.75, 0.875, 1.0]).repeat_interleave(3)


def test_protocol_and_frozen_helpers_are_explicit():
    assert probe.GROUP == ("teacher-0", 0, 0)
    assert probe.LANES == ("A_eager", "B_eager", "A_graph", "B_graph")
    assert (probe.SLOTS, probe.DK, probe.DECODE_STEPS) == (4, 64, 8)
    assert probe.REPLAY_SHA256 == "56e0d2de14df9c177d607f785d856b00434384bb364ca598972d5457a042c8dd"
    assert probe.ORIGINAL_REPLAY_SHA256 == "eb6aa7e8af0234554951b01a808da566fda02994317519a500357b3d586ba79b"
    assert "Original FP32-reference qualification failed" in probe.CLAIM
    assert "No performance admission" in probe.CLAIM


@pytest.mark.parametrize("step", (0, 1))
def test_cpu_A_beta_and_original_B_beta_wiring(step):
    keep, r12 = selection()
    source = record(step)
    original_beta = source["tensors"]["beta"].clone()
    expected = (original_beta.float() * r12).bfloat16()
    for lane in probe.LANES:
        inputs, actual_expected = probe.lane_inputs(source, keep, r12, lane, replay)
        assert inputs["r"].dtype == torch.float32
        assert replay.exact(actual_expected, expected)
        assert replay.exact(inputs["beta"], expected if lane.startswith("A_") else original_beta)
        assert inputs["beta"].data_ptr() != source["tensors"]["beta"].data_ptr()
        assert inputs["q"].shape[-2:] == (4, 64)
        assert "state_initial" not in inputs and "state_final" not in inputs
    assert replay.exact(source["tensors"]["beta"], original_beta)


def test_private_state_slot_carry_has_independent_expected_trajectory():
    state = torch.zeros(4, 12, 128, 64)
    state[0].fill_(1)
    for step in range(1, 9):
        assert probe.slot_for_step(step) == ((step - 1) % 4, step % 4)
        selected = probe.migrate_own_state(state, step)
        assert state[selected, 0, 0, 0].item() == step
        state[selected].add_(1)
    assert state[:, 0, 0, 0].tolist() == [9, 6, 7, 8]


@pytest.mark.parametrize("bad", (0, 9, True, -1))
def test_out_of_budget_step_is_rejected(bad):
    with pytest.raises(ValueError):
        probe.slot_for_step(bad)


def failure_fixture():
    binding = {name: {"path": "/frozen/" + name, "sha256": "a" * 64}
               for name in ("audit", "manifest", "energy_plan", "retained_stats")}
    doc = {
        "bindings": copy.deepcopy(binding), "script_sha256": probe.ORIGINAL_SCRIPT_SHA256,
        "dense_gate_passed": False, "candidate_numerical_gate_passed": False,
        "status": "failed_runtime_evidence",
        "trajectories": [{"sequence_id": "teacher-0", "rank": 0, "layer": 0,
                          "variant": "dense128", "passed": False,
                          "steps": [{"step": 0, "phase": "prefill",
                                     "metrics": {"full_state_cpu": {"passed": False}}}]}],
    }
    observed = []

    def bound_json(path, sha):
        observed.append((path, sha))
        return doc

    return SimpleNamespace(binding=binding, audit=SimpleNamespace(bound_json=bound_json)), doc, observed


def test_original_failed_gate_is_pinned_and_not_promoted():
    bound, _, observed = failure_fixture()
    result = probe.original_failure(bound, replay)
    assert observed == [(probe.ORIGINAL_REPLAY, probe.ORIGINAL_REPLAY_SHA256)]
    assert result["qualification_passed"] is False
    assert result["failed_check"] == "dense128.step0.full_state_cpu"


@pytest.mark.parametrize("damage", ("gate", "source", "other_capture"))
def test_original_failure_or_capture_binding_cannot_be_replaced(damage):
    bound, doc, _ = failure_fixture()
    if damage == "gate":
        doc["trajectories"][0]["steps"][0]["metrics"]["full_state_cpu"]["passed"] = True
    elif damage == "source":
        doc["script_sha256"] = "f" * 64
    else:
        doc["bindings"]["audit"]["sha256"] = "f" * 64
    with pytest.raises(ValueError):
        probe.original_failure(bound, replay)


@pytest.mark.parametrize("stale_graph_indices", (False, True))
def test_four_lane_actual_control_and_common_stale_graph_counterexample(
        tmp_path, monkeypatch, stale_graph_indices):
    from contextlib import contextmanager
    original_to, original_zeros = torch.Tensor.to, torch.zeros

    def cpu_to(tensor, *args, **kwargs):
        if args and args[0] == "npu:0":
            args = ("cpu",) + args[1:]
        return original_to(tensor, *args, **kwargs)

    def cpu_zeros(*args, **kwargs):
        if kwargs.get("device") == "npu:0":
            kwargs["device"] = "cpu"
        return original_zeros(*args, **kwargs)

    monkeypatch.setattr(torch.Tensor, "to", cpu_to)
    monkeypatch.setattr(torch, "zeros", cpu_zeros)
    active, created, prefix_states, archived, phases = {"graph": None}, [], [], [], []

    def output(data, state, selected, compensated):
        product, beta = (replay.beta_product(data["beta"], data["r"]) if compensated
                         else (data["beta"], data["beta"]))
        count = data["q"].shape[1]
        value = float(state[selected, 0, 0, 0])
        return {"beta": beta, "product": product,
                "output": torch.full((count, 12, 128), value, dtype=torch.bfloat16),
                "norm": torch.full((count, 12, 128), value * 2, dtype=torch.bfloat16)}

    def operation(data, state, dk, compensated, runtime, fixed_index=None):
        selected = int(data["indices"][0]) if fixed_index is None else fixed_index
        state[selected].add_(1)
        result = output(data, state, selected, compensated)
        if active["graph"] is not None:
            active["graph"].args = (data, state, dk, compensated, runtime)
            active["graph"].result = result
        return result

    class Graph:
        def __init__(self):
            created.append(self)
            self.reset_called = False

        def replay(self):
            values = operation(*self.args, fixed_index=1 if stale_graph_indices else None)
            for key in self.result:
                self.result[key].copy_(values[key])

        def reset(self):
            self.reset_called = True

    @contextmanager
    def graph_context(graph):
        active["graph"] = graph
        try:
            yield
        finally:
            active["graph"] = None

    monkeypatch.setattr(torch, "npu", SimpleNamespace(
        synchronize=lambda: None, NPUGraph=Graph, graph=graph_context), raising=False)

    def prefill(data, dk, compensated, runtime):
        state = torch.ones((1, 12, 128, dk))
        prefix_states.append(state)
        return output(data, state, 0, compensated), state

    def metadata(tensor):
        return {"ptr": tensor.data_ptr(), "shape": list(tensor.shape),
                "stride": list(tensor.stride()), "dtype": str(tensor.dtype)}

    def unchanged(before, after, indices):
        slots = [index for index in range(4) if index not in indices.tolist()]
        return replay.exact(before[slots], after[slots])

    def archive(path, payload):
        archived.append({"step": payload["step"], "passed": payload["passed"], "checks": payload["checks"],
                         "state_values": {lane: row["state"][:, 0, 0, 0].tolist()
                                          for lane, row in payload["lanes"].items()}})
        return {"path": str(path), "sha256": "e" * 64, "size_bytes": 0}

    monkeypatch.setattr(replay, "prefill", prefill)
    monkeypatch.setattr(replay, "operation", operation)
    monkeypatch.setattr(replay, "archive", archive)
    runtime = SimpleNamespace(probe=SimpleNamespace(metadata=metadata, unselected_unchanged=unchanged))
    keep, r12 = selection()
    report = {"steps": [], "incremental_numerical_passed": False}
    args = ([record(step) for step in range(9)], keep, r12, runtime, replay,
            tmp_path, report, lambda: None, lambda name, **details: phases.append((name, details)))
    if stale_graph_indices:
        with pytest.raises(ValueError, match="bytewise"):
            probe.run_incremental(*args)
        assert report["steps"][-1]["step"] == 2 and report["steps"][-1]["passed"] is False
        assert not report["incremental_numerical_passed"]
        assert not report["steps"][-1]["checks"]["A_graph"]["unselected_slots_unchanged"]
        assert not report["steps"][-1]["checks"]["B_graph"]["unselected_slots_unchanged"]
    else:
        probe.run_incremental(*args)
        assert report["incremental_numerical_passed"]
        assert [row["step"] for row in archived] == list(range(9))
        assert all(values == [9, 6, 7, 8] for values in archived[-1]["state_values"].values())
        decode = [details for name, details in phases if name == "decode"]
        assert [(row["step"], row["lane"]) for row in decode] == [
            (step, lane) for step in range(1, 9) for lane in probe.LANES]
    assert len(prefix_states) == 4 and len({state.data_ptr() for state in prefix_states}) == 4
    assert len(created) == 2 and all(graph.reset_called for graph in created)
    assert [graph.args[3] for graph in created] == [False, True]
    assert report["graph_prefill_reset_bytes"] is True


def test_helper_hash_failure_before_runtime_and_fresh_receipt(tmp_path, monkeypatch):
    monkeypatch.setenv("ASCEND_RT_VISIBLE_DEVICES", "0,1,2,3")
    monkeypatch.setattr(probe, "RESULT_ROOT", tmp_path)
    bad_source = tmp_path / "replay.py"
    bad_source.write_text("raise AssertionError('must not execute changed helper')")
    monkeypatch.setattr(probe, "REPLAY_SOURCE", bad_source)
    old_report = tmp_path / "immutable-original.json"
    old_report.write_text("original failed evidence fixture")
    monkeypatch.setattr(probe, "ORIGINAL_REPLAY", old_report)
    monkeypatch.setattr(probe, "ORIGINAL_REPLAY_SHA256", replay.checksum(old_report))
    out = tmp_path / "result"
    argv = [
        "--audit-report", str(tmp_path / "audit.json"), "--audit-sha256", "a" * 64,
        "--manifest", str(tmp_path / "manifest.json"), "--manifest-sha256", "a" * 64,
        "--energy-plan", str(tmp_path / "plan.json"), "--retained-stats", str(tmp_path / "stats.json"),
        "--output-dir", str(out),
    ]
    assert probe.main(argv) == 1
    result = json.loads((out / "report.json").read_text())
    assert result["status"] == "failed_admission" and "helper source changed" in result["error"]
    assert not result["performance_admitted"] and not result["original_qualification_passed"]
    assert result["steps"] == [] and len(result["script_sha256"]) == 64
    assert result["original_report_check"]["unchanged"] is True
    before = (out / "report.json").read_bytes()
    with pytest.raises(ValueError, match="fresh canonical"):
        probe.main(argv)
    assert (out / "report.json").read_bytes() == before


@pytest.mark.parametrize("bad_lane", ("B_eager", "B_graph"))
def test_fp32_product_drift_is_rejected_even_when_bf16_beta_agrees(tmp_path, monkeypatch, bad_lane):
    expected_product = torch.tensor([0.5], dtype=torch.float32)
    expected_beta = expected_product.bfloat16()
    branches = {}
    for lane in probe.LANES:
        branches[lane] = {"state": torch.ones(1), "result": {
            "beta": expected_beta.clone(), "output": expected_beta.clone(),
            "norm": expected_beta.clone(),
            "product": expected_product.clone() if lane.startswith("B_") else expected_beta.clone()}}
    branches[bad_lane]["result"]["product"] += 2 ** -24
    assert replay.exact(branches[bad_lane]["result"]["product"].bfloat16(), expected_beta)
    archived = []
    monkeypatch.setattr(replay, "archive", lambda path, payload: archived.append(payload) or {"path": str(path)})
    report = {"steps": []}
    with pytest.raises(ValueError, match="bytewise"):
        probe.compare_step(0, branches, expected_beta, expected_product, {}, None,
                           replay, tmp_path, report, lambda: None)
    assert report["steps"][-1]["checks"][bad_lane]["beta_A_eager_bytes"] is True
    assert report["steps"][-1]["checks"][bad_lane]["beta_product_fp32_cpu_bytes"] is False
    assert archived[-1]["lanes"][bad_lane]["beta_product_fp32"].dtype == torch.float32
    assert replay.exact(archived[-1]["expected_beta_product_fp32"], expected_product)


def test_original_report_postcheck_retains_identity_failure(tmp_path, monkeypatch):
    original = tmp_path / "original.json"
    original.write_text("immutable failure fixture")
    expected = replay.checksum(original)
    monkeypatch.setattr(probe, "ORIGINAL_REPLAY", original)
    monkeypatch.setattr(probe, "ORIGINAL_REPLAY_SHA256", expected)
    report = {}
    probe.check_original_unchanged(report)
    assert report["original_report_check"]["unchanged"] is True
    original.write_text("changed fixture")
    with pytest.raises(ValueError, match="original replay report identity changed"):
        probe.check_original_unchanged(report)
    assert report["original_report_check"]["unchanged"] is False
    assert report["original_report_check"]["expected_sha256"] == expected
    assert report["original_report_check"]["sha256"] == replay.checksum(original)
