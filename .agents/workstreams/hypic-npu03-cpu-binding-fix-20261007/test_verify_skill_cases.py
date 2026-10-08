#!/usr/bin/env python3
"""Offline regression for case provenance and fail-closed hash checking."""

import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_skill_cases as cases


class SkillCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.main_commit = cases.git("rev-parse", "origin/main")
        self.case_path = cases.CASES / "mst-repo-onboarding.json"

    def test_historical_case_is_partial_not_long_term_verified(self) -> None:
        skill, state = cases.check_case(
            self.case_path, self.main_commit, {"mst-repo-onboarding"})
        self.assertEqual(skill, "mst-repo-onboarding")
        self.assertEqual(state, "partial-evidence")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cases.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["registered_skills"], 29)
        self.assertEqual(report["cases_with_verified_provenance"], 11)
        self.assertEqual(report["skills_without_case"], 18)
        self.assertEqual(report["case_acceptance"],
                         {"partial-evidence": 9, "verified": 2})

    def test_performance_optimization_case_stays_partial(self) -> None:
        path = cases.CASES / "ascend-performance-optimization.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"ascend-performance-optimization"})
        self.assertEqual(skill, "ascend-performance-optimization")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertEqual(item["observed"]["candidate_class"],
                         "supported_upstream_configuration")
        self.assertFalse(item["observed"]["optimization_accepted"])
        self.assertFalse(item["observed"]["full_2048_token_paired_quality_complete"])

    def test_inference_tuning_loop_replay_stays_bounded(self) -> None:
        path = cases.CASES / "ascend-inference-tuning-loop.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"ascend-inference-tuning-loop"})
        self.assertEqual(skill, "ascend-inference-tuning-loop")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertEqual(item["observed"]["raw_performance_runs_hash_verified"], 6)
        self.assertFalse(item["observed"]["full_2048_token_paired_quality_complete"])
        self.assertFalse(item["observed"]["hypic_paper_effect_verified"])

    def test_benchmark_baseline_reuse_case_stays_partial(self) -> None:
        path = cases.CASES / "ascend-benchmark-evidence.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"ascend-benchmark-evidence"})
        self.assertEqual(skill, "ascend-benchmark-evidence")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertTrue(item["observed"]["old_control_complete"])
        self.assertFalse(item["observed"]["old_control_reusable_for_r9"])
        self.assertFalse(item["observed"]["new_control_run_authorized_by_this_case"])

    def test_quality_request_coverage_case_stays_partial(self) -> None:
        path = cases.CASES / "ascend-model-quality-evaluation.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"ascend-model-quality-evaluation"})
        self.assertEqual(skill, "ascend-model-quality-evaluation")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertEqual(item["observed"]["strict_request_level_gate"],
                         "UNVERIFIED 162/162")
        self.assertFalse(item["observed"]["terminal_quality_pair_complete"])
        self.assertFalse(item["observed"]["main_skill_integrated"])

    def test_practice_iteration_main_contract_defect_stays_partial(self) -> None:
        path = cases.CASES / "mst-practice-iteration-planning.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"mst-practice-iteration-planning"})
        self.assertEqual(skill, "mst-practice-iteration-planning")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertEqual(item["observed"]["first_validator_exit"], 1)
        self.assertFalse(item["observed"]["main_skill_integrated"])

    def test_experience_ingestion_case_keeps_main_gap_partial(self) -> None:
        path = cases.CASES / "mst-experience-ingestion.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"mst-experience-ingestion"})
        self.assertEqual(skill, "mst-experience-ingestion")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertTrue(item["observed"]["main_host_skill_lacks_continuous_reentry_guard"])
        self.assertEqual(item["observed"]["scored_samples_per_attempt"], 0)

    def test_environment_orientation_case_is_partial_not_quality_success(self) -> None:
        path = cases.CASES / "ascend-npu-environment-orientation.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"ascend-npu-environment-orientation"})
        self.assertEqual(skill, "ascend-npu-environment-orientation")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertEqual(item["observed"]["scored_rows"], 0)
        self.assertFalse(item["observed"]["current_cache10r5_canary_completed"])

    def test_handoff_case_is_bounded_verified(self) -> None:
        path = cases.CASES / "mst-maintainer-handoff.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"mst-maintainer-handoff"})
        self.assertEqual(skill, "mst-maintainer-handoff")
        self.assertEqual(state, "verified")
        self.assertIn("branch-local",
                      json.loads(path.read_text())["boundary"])

    def test_git_checkpoint_case_is_bounded_verified(self) -> None:
        path = cases.CASES / "mst-git-checkpoint-policy.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"mst-git-checkpoint-policy"})
        self.assertEqual(skill, "mst-git-checkpoint-policy")
        self.assertEqual(state, "verified")
        self.assertIn("named-workstream checkpoint",
                      json.loads(path.read_text())["boundary"])

    def test_host_isolation_case_is_bounded_not_algorithm_success(self) -> None:
        path = cases.CASES / "chicaihong01-host-maintenance.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"chicaihong01-host-maintenance"})
        self.assertEqual(skill, "chicaihong01-host-maintenance")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertEqual(item["observed"]["scored_requests_before_abort"], 0)
        self.assertFalse(item["replayable_regression_recorded"])

    def test_wrong_evidence_bytes_fail_closed(self) -> None:
        with patch.object(cases, "evidence_path", return_value=Path(__file__)):
            with self.assertRaisesRegex(RuntimeError, "evidence SHA256 drift"):
                cases.check_case(
                    self.case_path, self.main_commit, {"mst-repo-onboarding"})


if __name__ == "__main__":
    unittest.main()
