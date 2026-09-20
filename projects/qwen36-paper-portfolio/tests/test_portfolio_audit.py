import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from portfolio_audit import (
    amdahl_speedup,
    build_report,
    disjoint_speedup,
    local_speedup_required,
)


def test_overlap_aware_components_stay_below_ten_percent():
    report = build_report()
    combined = report["best_non_overlapping_observed_components"]["combined"]
    perfect = report["best_non_overlapping_observed_components"][
        "perfect_elimination_upper_bound"
    ]
    assert combined["gain_pct"] < 5
    assert perfect["gain_pct"] < 10


def test_six_stage_candidate_needs_more_than_six_x_local():
    required = local_speedup_required(0.1087, 1.10)
    assert required is not None
    assert required > 6
    assert amdahl_speedup(0.1087, 1.087) < 1.01


def test_disjoint_math_does_not_multiply_overlapping_implementations():
    expected = 1 / (1 - 0.2 * 0.5 - 0.1 * 0.75)
    assert math.isclose(disjoint_speedup([(0.2, 2), (0.1, 4)]), expected)
