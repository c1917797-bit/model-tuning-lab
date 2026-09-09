"""CPU-only contract tests for the aligned captured-teacher width curve."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path

os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
import pytest
import torch


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "tools/replay_gdn_teacher_width_curve.py"
)
spec = importlib.util.spec_from_file_location("width_curve_under_test", SOURCE)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)

LAYERS = (0, 12, 25, 38, 50, 62)


def plan_fixture(dk):
    layer_types = [
        "full_attention" if (layer + 1) % 4 == 0 else "linear_attention"
        for layer in range(64)
    ]
    keep_indices = {}
    for layer, kind in enumerate(layer_types):
        if kind != "linear_attention":
            continue
        keep_indices[str(layer)] = [
            head * 128 + coordinate
            for head in range(16)
            for coordinate in range(dk)
        ]
    return {
        "schema": "ascend-drrqr-plan/v1",
        "target_model_id": "Qwen/Qwen3.8-27B",
        "source_config_sha256": "a" * 64,
        "source_index_sha256": "b" * 64,
        "old_head_k_dim": 128,
        "target_head_k_dim": dk,
        "selection_objective": "energy-kernel",
        "pruning_ratio": 1.0 - dk / 128.0,
        "num_key_heads": 16,
        "num_value_heads": 48,
        "head_v_dim": 128,
        "conv_kernel_dim": 4,
        "hidden_size": 5120,
        "layer_types": layer_types,
        "model_type": "qwen3_5_text",
        "keep_indices": keep_indices,
        "provenance": {
            "method": "Experimental joint normalized Q/K energy top-k selector",
            "paper_exact_selection": False,
            "calibration_sha256": "c" * 64,
            "selection": {
                "schema": "drrqr-selection/v1",
                "selection_objective": "energy-kernel",
                "capture_file_count": 3072,
                "capture_manifest_sha256": "d" * 64,
            },
        },
    }


def fidelity_rows(e48=0.40, e64=0.30, e80=0.24):
    return [
        {
            "sequence_id": f"teacher-{sequence}",
            "rank": rank,
            "layer": layer,
            "position": position,
            "energy48_relative_l2": e48,
            "energy64_relative_l2": e64,
            "energy80_relative_l2": e80,
        }
        for sequence in range(2)
        for rank in range(4)
        for layer in LAYERS
        for position in range(136)
    ]


@pytest.mark.parametrize("dk", (48, 64, 80))
def test_width_plan_contract_accepts_aligned_energy_plans(dk):
    baseline = plan_fixture(64)
    plan = plan_fixture(dk)
    assert candidate.validate_width_plan_doc(plan, dk, baseline) is plan
    keep = candidate.keep_for(plan, layer=0, rank=3, dk=dk)
    assert tuple(keep.shape) == (4, dk)
    assert keep[0].tolist() == list(range(dk))


def test_width_plan_contract_rejects_provenance_or_coordinate_drift():
    baseline = plan_fixture(64)
    changed = plan_fixture(80)
    changed["provenance"]["selection"]["capture_manifest_sha256"] = "e" * 64
    with pytest.raises(ValueError, match="selection provenance differs"):
        candidate.validate_width_plan_doc(changed, 80, baseline)

    changed = plan_fixture(48)
    changed["keep_indices"]["0"][1] = changed["keep_indices"]["0"][0]
    with pytest.raises(ValueError, match="cross/duplicate"):
        candidate.validate_width_plan_doc(changed, 48, baseline)


@pytest.mark.parametrize("dk", (48, 80))
def test_data_from_selects_exact_head_local_width(dk):
    keep = candidate.keep_for(plan_fixture(dk), layer=0, rank=0, dk=dk)
    record = {
        "tensors": {
            "raw_q": torch.arange(128 * 4 * 128).reshape(128, 4, 128),
            "raw_k": torch.arange(128 * 4 * 128).reshape(128, 4, 128) + 1,
            "raw_v": torch.zeros(128, 12, 128),
            "g": torch.zeros(128, 12),
            "beta": torch.zeros(128, 12, dtype=torch.bfloat16),
            "z": torch.zeros(128, 12, 128),
            "norm_weight": torch.ones(128),
        }
    }
    data = candidate.data_from(record, keep, dk)
    assert tuple(data["q"].shape) == (128, 4, dk)
    assert tuple(data["k"].shape) == (128, 4, dk)
    assert data["q"][0, 0].tolist() == list(range(dk))
    assert data["r"].tolist() == [1.0] * 12


def test_fidelity_gate_accepts_predeclared_monotonic_width_curve():
    result = candidate.fidelity_screen(fidelity_rows(), LAYERS)
    assert result["passed"] is True
    assert result["aggregate_monotonic_48_64_80"] is True
    assert result["overall"]["energy80_over_energy64_with_floor"] == pytest.approx(
        0.8
    )
    assert len(result["groups"]) == 2 * 4 * len(LAYERS) * 3


def test_fidelity_gate_rejects_local_energy80_regression():
    rows = fidelity_rows()
    for row in rows:
        if (
            row["sequence_id"] == "teacher-1"
            and row["rank"] == 2
            and row["layer"] == 62
            and 132 <= row["position"] <= 135
        ):
            row["energy80_relative_l2"] = 0.40
    result = candidate.fidelity_screen(rows, LAYERS)
    assert result["passed"] is False
    failed = [item for item in result["groups"] if not item["passed"]]
    assert any(
        item["sequence_id"] == "teacher-1"
        and item["rank"] == 2
        and item["layer"] == 62
        and item["window"] == "decode_late"
        for item in failed
    )


def test_fidelity_gate_rejects_nonmonotonic_lower_cost_side():
    result = candidate.fidelity_screen(
        fidelity_rows(e48=0.20, e64=0.30, e80=0.24), LAYERS
    )
    assert result["passed"] is False
    assert result["aggregate_monotonic_48_64_80"] is False


def test_fidelity_gate_requires_complete_coordinates():
    with pytest.raises(ValueError, match="complete"):
        candidate.fidelity_screen(fidelity_rows()[:-1], LAYERS)


def test_frozen_helpers_and_claim_ceiling_are_explicit():
    captured = candidate.load_captured_reference()
    replay = captured.load_replay()
    assert candidate.checksum(candidate.CAPTURED_PATH) == candidate.CAPTURED_SHA256
    assert candidate.checksum(captured.REPLAY_PATH) == captured.REPLAY_SHA256
    assert replay.LAYERS == LAYERS
    assert "throughput" in candidate.CLAIM
    assert "Not exact StrongRRQR" in candidate.CLAIM
    source = SOURCE.read_text(encoding="utf-8")
    assert '"width_shard_pass"' in source


def test_budget_and_interrupt_are_inconclusive_not_numerical_failures():
    assert candidate.run_error_status(
        TimeoutError("budget"), "energy48"
    ) == "inconclusive_budget_exhausted"
    assert candidate.run_error_status(
        InterruptedError("signal"), "energy64"
    ) == "inconclusive_interrupted"
    assert candidate.run_error_status(
        ValueError("gate"), "energy80"
    ) == "failed_candidate_numerical"


def test_completed_trajectory_requires_all_nine_passing_steps():
    row = {"passed": True, "steps": [{"passed": True}] * 9}
    assert candidate.completed_trajectory(row) is True
    assert candidate.completed_trajectory({**row, "steps": row["steps"][:-1]}) is False
    assert candidate.completed_trajectory({**row, "passed": None}) is False


def test_prior_dense_report_requires_complete_passing_group_matrix():
    group = ("teacher-0", 0, 0)
    bindings = {"manifest": {"sha256": "a" * 64}}
    row = {
        "sequence_id": group[0],
        "rank": group[1],
        "layer": group[2],
        "variant": "dense128",
        "passed": True,
        "steps": [{"passed": True}] * 9,
    }
    document = {
        "schema": "drrqr-captured-teacher-width-curve/v1",
        "status": "inconclusive_budget_exhausted",
        "captured_reference_helper_sha256": candidate.CAPTURED_SHA256,
        "dense_capture_gate_passed": True,
        "bindings": bindings,
        "trajectories": [row],
        "script_sha256": "b" * 64,
    }
    result = candidate.validate_prior_dense_report(
        document, "c" * 64, bindings, [group]
    )
    assert result["trajectory_count"] == 1
    changed = copy.deepcopy(document)
    changed["trajectories"][0]["steps"].pop()
    with pytest.raises(ValueError, match="complete passing dense"):
        candidate.validate_prior_dense_report(
            changed, "c" * 64, bindings, [group]
        )
