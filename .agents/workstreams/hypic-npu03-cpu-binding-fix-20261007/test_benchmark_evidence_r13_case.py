"""Fail-closed unit checks for separate quality and performance verdicts."""

from __future__ import annotations

import unittest

from verify_benchmark_evidence_r13_case import PERFORMANCE_SHA, QUALITY_SHA, validate_summary


def fixture():
    summary = {
        "r13_quality_pair_complete": True,
        "r13_correct": [230, 219],
        "r13_deployment_quality": "REJECT_OR_QUALIFY",
        "r13_strict_hot": [368, 381],
        "r13_strict_hot_decision": "NOT_ACCEPTED_HOT_COVERAGE",
        "r13_performance_all_six_phases_valid": True,
        "r13_performance_strict_hot": [120, 120],
        "r13_performance_weighted_tpot_saved_pct": 21.524278158508903,
        "r13_performance_ttft_p95_saved_s": 40.86937530996511,
    }
    case = {
        "long_term_acceptance": "partial-evidence",
        "observed": {
            "r13_single_dataset_quality_pair_complete": True,
            "r13_fixed_output_six_phase_performance_complete": True,
            "r13_quality_correct_baseline_candidate": [230, 219],
            "r13_quality_decision": "REJECT_OR_QUALIFY",
            "r13_quality_strict_hot": [368, 381],
            "r13_performance_strict_hot": [120, 120],
            "r13_performance_screen_decision": "EFFECT_SCREEN_PASS",
            "full_default_skill_ruler_complete": False,
        },
        "external_raw_receipts": {
            "r13_quality_audit_sha256": QUALITY_SHA,
            "r13_performance_audit_sha256": PERFORMANCE_SHA,
        },
    }
    return summary, case


class BenchmarkEvidenceCaseTests(unittest.TestCase):
    def test_bounded_mixed_verdict(self) -> None:
        validate_summary(*fixture())

    def test_speed_does_not_turn_quality_into_pass(self) -> None:
        summary, case = fixture()
        case["observed"]["r13_quality_decision"] = "PASS"
        with self.assertRaisesRegex(RuntimeError, "conflates"):
            validate_summary(summary, case)

    def test_missing_measured_phase_fails(self) -> None:
        summary, case = fixture()
        summary["r13_performance_all_six_phases_valid"] = False
        with self.assertRaisesRegex(RuntimeError, "matched performance"):
            validate_summary(summary, case)


if __name__ == "__main__":
    unittest.main()
