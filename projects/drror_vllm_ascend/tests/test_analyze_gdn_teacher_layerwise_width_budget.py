"""Tests for the captured-teacher equal-cost layer-width solver."""
from __future__ import annotations

from tools.analyze_gdn_teacher_layerwise_width_budget import analyze


def rows(values):
    result = []
    for sequence in range(2):
        for rank in range(4):
            for layer, widths in enumerate(values):
                for position in range(136):
                    result.append({
                        "sequence_id": f"teacher-{sequence}",
                        "rank": rank,
                        "layer": layer,
                        "position": position,
                        "energy48_relative_l2": widths[0],
                        "energy64_relative_l2": widths[1],
                        "energy80_relative_l2": widths[2],
                    })
    return result


def test_solver_accepts_balanced_safe_48_80_pair():
    values = [
        (0.31, 0.30, 0.10),
        (0.31, 0.30, 0.10),
    ]
    report = analyze(rows(values), [0, 1])
    assert report["passed"] is True
    assert report["assignment_counts"] == {"48": 1, "64": 0, "80": 1}
    assert report["selected_budget"] == 128


def test_solver_rejects_when_no_layer_can_safely_reduce_width():
    values = [
        (0.40, 0.30, 0.20),
        (0.40, 0.30, 0.20),
    ]
    report = analyze(rows(values), [0, 1])
    assert report["passed"] is False
    assert report["safe_layer_counts"]["48"] == 0
    assert report["assignment_counts"] == {"48": 0, "64": 2, "80": 0}
    assert report["selected_improvement_fraction"] == 0.0
