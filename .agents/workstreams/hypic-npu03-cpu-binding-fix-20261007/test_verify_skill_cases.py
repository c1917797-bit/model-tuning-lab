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
        self.assertEqual(report["cases_with_verified_provenance"], 17)
        self.assertEqual(report["skills_without_case"], 12)
        self.assertEqual(report["case_acceptance"],
                         {"partial-evidence": 15, "verified": 2})

    def test_architecture_fit_retrospective_is_not_prospective_pass(self) -> None:
        path = cases.CASES / "ascend-architecture-fit.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"ascend-architecture-fit"})
        self.assertEqual(skill, "ascend-architecture-fit")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertEqual(item["observed"]["c1_c2_single_instance_configured_fit"],
                         "fits-now")
        self.assertEqual(item["observed"]["c3_current_single_replica_fit"],
                         "does-not-fit")
        self.assertFalse(item["observed"]["historical_preimplementation_git_decision_gate_met"])

    def test_paper_ingestion_preserves_source_and_c3_boundary(self) -> None:
        path = cases.CASES / "paper-ingestion.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"paper-ingestion"})
        self.assertEqual(skill, "paper-ingestion")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertTrue(item["observed"]["branch_skill_differs_from_exact_main"])
        self.assertFalse(item["observed"]["exact_author_git_commit_pinned"])
        self.assertFalse(item["observed"]["paper_c3_multi_replica_present"])
        self.assertFalse(item["observed"]["paper_ingestion_final_acceptance"])

    def test_reporting_case_does_not_promote_progress_to_final(self) -> None:
        path = cases.CASES / "paper-to-ascend-reporting.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"paper-to-ascend-reporting"})
        self.assertEqual(skill, "paper-to-ascend-reporting")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertEqual(item["observed"]["r12_four_worker_hot_responses"], 52)
        self.assertFalse(item["observed"]["current_same_identity_no_cache_control_complete"])
        self.assertFalse(item["observed"]["final_colleague_style_report_ready"])

    def test_reproduction_case_preserves_failed_hotpath_gate(self) -> None:
        path = cases.CASES / "paper-to-ascend-reproduction.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"paper-to-ascend-reproduction"})
        self.assertEqual(skill, "paper-to-ascend-reproduction")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertTrue(item["observed"]["branch_skill_differs_from_exact_main"])
        self.assertEqual(item["observed"]["clean2_distinct_worker_hot_pids"], 0)
        self.assertFalse(item["observed"]["clean2_formal_hotpath_gate_passed"])
        self.assertFalse(item["observed"]["reproduction_skill_completion_gate_passed"])

    def test_paper_to_ascend_real_task_is_partial_not_paper_success(self) -> None:
        path = cases.CASES / "paper-to-ascend.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"paper-to-ascend"})
        self.assertEqual(skill, "paper-to-ascend")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertTrue(item["observed"]["historical_six_unit_performance_audit_passed"])
        self.assertFalse(item["observed"]["paper_c3_multi_replica_complete"])
        self.assertFalse(item["observed"]["full_explicit_2048_quality_pair_complete"])
        self.assertFalse(item["observed"]["whole_paper_reproduction_accepted"])

    def test_runtime_delivery_case_is_not_promotion(self) -> None:
        path = cases.CASES / "runtime-monkeypatch-delivery.json"
        skill, state = cases.check_case(
            path, self.main_commit, {"runtime-monkeypatch-delivery"})
        self.assertEqual(skill, "runtime-monkeypatch-delivery")
        self.assertEqual(state, "partial-evidence")
        item = json.loads(path.read_text())
        self.assertTrue(item["observed"]["main_documented_validator_absent"])
        self.assertFalse(item["observed"]["plugin_manifest_package_present"])
        self.assertFalse(item["observed"]["package_promotion_ready"])

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
        self.assertEqual(item["observed"]["r12_four_worker_verified_scored_requests"], 52)
        self.assertEqual(item["observed"]["r12_cold_ready_cache_partial_chunk"], 1)
        self.assertEqual(item["observed"]["r12_cold_scored_producer_rematerialization"], 4)
        self.assertFalse(item["observed"]["r12_exact_cache_eviction_causality_proven"])

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
