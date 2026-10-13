#!/usr/bin/env python3
"""Offline regression for the branch-local concise maintainer handoff."""

from __future__ import annotations

import json
import hashlib
import re
import subprocess
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def verify_publication(task: dict, receipt: dict) -> None:
    """Check recorded branch publication, without claiming current remote freshness."""
    state = task["remote_publication_20261013"]
    branch = receipt["published_branch"]
    commit = state["code_checkpoint"]
    assert branch == "work/hypic-npu03-cpu-binding-fix-20261007"
    assert receipt["published_code_commit"] == commit
    assert state["main_updated"] is False and receipt["main_updated"] is False
    record = receipt["push_and_remote_verification"]
    assert record["state"] == "completed" and record["exitCode"] == 0
    rows = [json.loads(line) for line in record["stdout"].splitlines()]
    pushed, verified = rows
    assert pushed["push_exit"] == 0 and pushed["expected_commit"] == commit
    assert pushed["branch"] == branch
    assert verified["verification_exit"] == 0
    assert verified["remote_refs"]["refs/heads/" + branch] == commit
    assert verified["remote_refs"]["refs/heads/main"] == state["remote_main"]
    assert state["work_branch_remote_equal"] is True
    assert verified["work_branch_equal"] is True and verified["main_unchanged"] is True


class HandoffTests(unittest.TestCase):
    def test_current_shape_and_history_retention(self) -> None:
        current = (HERE / "HANDOFF.md").read_text(encoding="utf-8")
        history = (HERE / "HANDOFF_HISTORY.md").read_text(encoding="utf-8")
        headings = re.findall(r"^## ([0-8])\. ", current, re.M)
        self.assertEqual(headings, list("012345678"))
        self.assertLessEqual(len(current.splitlines()), 160)
        self.assertGreaterEqual(len(history.splitlines()), 380)
        self.assertIn("cache10r3 terminal decision", history)
        self.assertIn("HANDOFF_HISTORY.md", current)
        self.assertIn("NPU4–7", current)
        self.assertIn("mapping alone", current.lower())
        self.assertIn("original full single-service", current)
        self.assertIn("unapproved", current)
        for name in ("task.json", "HOTPATH_CACHE10R3_RESOURCE_CONFLICT.md",
                     "MAIN_SKILL_ACCEPTANCE_GAP_AUDIT_20261008.md"):
            self.assertTrue((HERE / name).is_file(), name)

    def test_task_and_global_boundary(self) -> None:
        task = json.loads((HERE / "task.json").read_text(encoding="utf-8"))
        self.assertEqual(task["execution_state"], "in-progress")
        self.assertEqual(task["integration_state"], "not-ready")
        self.assertEqual(task["previous_attempt"]["campaign"], "cache10r10")
        self.assertIn("366/381", task["previous_attempt"]["result"])
        self.assertEqual(task["prior_stress_attempt"]["campaign"], "cache10r11")
        self.assertEqual(task["prior_stress_attempt"]["controller_operation"],
                         "exec-0000000000001830")
        self.assertEqual(task["latest_attempt"]["campaign"], "cache10r13-performance")
        self.assertEqual(task["latest_attempt"]["arm"], "hypic-only")
        self.assertEqual(task["latest_attempt"]["mode"], "repeat3")
        self.assertEqual(task["latest_attempt"]["attempt_number"], 21)
        self.assertEqual(task["latest_attempt"]["controller_operation"],
                         "exec-00000000000003a4")
        self.assertTrue(task["latest_attempt"]["root"].endswith("repeat3-retry21"))
        self.assertIn("valid HYPIC-only repeat3",
                      task["latest_attempt"]["classification"])
        self.assertIn("40/40 four-worker hot proof",
                      task["latest_attempt"]["status"])
        self.assertTrue((HERE / task["latest_attempt"]["preregistration"]).is_file())
        self.assertEqual(task["r13_candidate_attempt"]["campaign"], "cache10r13")
        self.assertEqual(task["r13_candidate_attempt"]["controller_operation"],
                         "exec-0000000000001bb1")
        self.assertEqual(task["r13_quality_audit"]["sha256"],
                         "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b")
        self.assertIsNone(task["active_attempt"])
        cp = task["current_source_performance_checkpoint"]
        self.assertEqual(cp["state"], "six-phases-audited-performance-complete")
        self.assertEqual(cp["completed_phases"], 6)
        self.assertIsNone(cp["controller_operation"])
        self.assertEqual(cp["quality_decision"], "REJECT_OR_QUALIFY")
        self.assertFalse(cp["deployment_allowed"])
        self.assertEqual(cp["aggregate"]["sha256"],
                         "67ba6cf14fc9bed993acbdf421eb438f22d56957f3e56baad170a4bb871e53fe")
        r18 = task["r18_candidate_terminal"]
        self.assertEqual(r18["controller_operation"], "exec-0000000000000247")
        self.assertIn("terminal runtime failure", r18["state"])
        self.assertTrue((HERE / r18["terminal_audit"]).is_file())
        self.assertEqual(task["r17_cap_isolation_design"]["quality_decision"],
                         "REJECT_OR_QUALIFY")
        self.assertEqual(task["r13_baseline_attempt"]["arm"], "no-cache")
        self.assertEqual(task["r13_baseline_attempt"]["controller_operation"],
                         "exec-0000000000001a76")
        self.assertEqual(task["performance_baseline_screen"]["arm"], "no-cache")
        self.assertEqual(task["performance_baseline_screen"]["controller_operation"],
                         "exec-0000000000001c05")
        self.assertTrue((HERE / task["performance_baseline_screen"]["audit"]).is_file())
        self.assertEqual(task["performance_candidate_screen"]["controller_operation"],
                         "exec-0000000000001c22")
        self.assertTrue((HERE / task["performance_candidate_screen"]["audit"]).is_file())
        self.assertEqual(task["performance_candidate_repeat2"]["arm"], "hypic-only")
        self.assertTrue((HERE / task["performance_candidate_repeat2"]["audit"]).is_file())
        self.assertIn("40/40", task["performance_candidate_repeat2"]["status"])
        self.assertEqual(task["performance_baseline_repeat2"]["arm"], "no-cache")
        self.assertTrue((HERE / task["performance_baseline_repeat2"]["audit"]).is_file())
        self.assertEqual(task["performance_baseline_repeat3"]["arm"], "no-cache")
        self.assertTrue((HERE / task["performance_baseline_repeat3"]["audit"]).is_file())
        failure = task["performance_candidate_repeat3_environmental_failure"]
        self.assertEqual(failure["arm"], "hypic-only")
        self.assertEqual(failure["controller_operation"],
                         "exec-000000000000004b")
        self.assertIn("before service health", failure["status"])
        self.assertIn("max2048", task["goal_horizons"]["short_term"])
        self.assertEqual(task["r19_repaired_longbench_candidate_terminal"]["scored_responses"], 381)
        self.assertIn("all 29", task["goal_horizons"]["long_term"])
        self.assertIn("No further device stages", task["next_action"])
        self.assertIn("remaining exact-main obligations offline", task["next_action"])
        self.assertEqual(task["timeboxed_milestone_plan"]["deadline_utc"],
                         "2026-10-09T17:21:24Z")
        self.assertEqual(len(task["timeboxed_milestone_plan"]["milestones"]), 6)
        self.assertEqual(task["performance_candidate_repeat3_retry14_environmental_failure"]["scored_requests"], 0)
        self.assertIn("53/57", task["prior_stress_attempt"]["request_hot_path_gate"])
        self.assertIn("c12060c", task["diagnostic_plugin"]["local_commit"])
        self.assertTrue((HERE / task["previous_attempt"]["evidence"]).is_file())
        self.assertTrue((HERE / task["prior_stress_attempt"]["coverage_report"]).is_file())
        self.assertTrue((HERE / task["latest_attempt"]["coverage_report"]).is_file())
        self.assertTrue((HERE / "HOTPATH_CACHE10PERF_RETRY19_PREREGISTRATION_20261009.md").is_file())
        self.assertEqual(task["resource_claim"]["forbidden_npus"],
                         [4, 5, 6, 7])
        subprocess.run(("git", "diff", "--quiet", "HEAD", "--",
                        ".agents/HANDOFF.md"), cwd=REPO, check=True)


    def test_latest_snapshot_and_terminal_active_receipt(self) -> None:
        snapshot = HERE / "HANDOFF_SNAPSHOT_20261013_0802.md"
        self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                         "a79dfa7aa634a1f69575c24d56fb0dc03efeecc9a15ef1dee07cfa1d336311cd")
        self.assertGreater(len(snapshot.read_text().splitlines()), 160)
        task = json.loads((HERE / "task.json").read_text())
        retired = task["retired_active_attempt_20261013"]
        old = retired["original_entry"]
        self.assertEqual(old["campaign"], "cache10r19-c32-gsm8k")
        raw = (Path(old["root"]) / "arm-result.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), retired["arm_result_sha256"])
        result = json.loads(raw)
        self.assertEqual(result["completed_units"], 3)
        self.assertIsNone(result["error"])
        for key in ("container_removed", "owned_npus_released", "port_released"):
            self.assertTrue(result["service_stop"][key])
        self.assertEqual(result["service_stop"]["at_utc"],
                         "2026-10-10T17:11:41.241053+00:00")
        statuses = [json.loads(p.read_text())["long_term_acceptance"]
                    for p in (HERE / "skill-cases").glob("*.json")]
        self.assertEqual(len(statuses), 29)
        verified = statuses.count("verified")
        partial = statuses.count("partial-evidence")
        self.assertEqual(verified + partial, 29)
        self.assertEqual(task["skill_case_inventory"]["bounded_verified"], verified)
        self.assertEqual(task["skill_case_inventory"]["partial_evidence"], partial)
        self.assertIn(f"29 cases:{verified} bounded verified,{partial} partial,0 missing.",
                      (HERE / "HANDOFF.md").read_text())

    def test_current_page_does_not_resume_old_controller(self) -> None:
        text = (HERE / "HANDOFF.md").read_text()
        self.assertNotIn("exec-00000000000004a3", text)
        self.assertNotIn("exec-00000000000002d6", text)
        self.assertIn("No additional quality,observer,GDN,profiling or performance run", text)
        self.assertIn("fresh-agent orient/validate/push", text)
        self.assertIn("Selective repairs integrated into main23ec33d7", text)
        self.assertEqual(json.loads((HERE / "task.json").read_text())["integrated_main_repairs_20261013"]["main_commit"],
                         "23ec33d7d692bb77d17fb5b81aabacf57adad5c7")
        task = json.loads((HERE / "task.json").read_text())
        receipt = json.loads((HERE / task["remote_publication_20261013"]["receipt"]).read_text())
        verify_publication(task, receipt)
        subprocess.run(("git", "merge-base", "--is-ancestor",
                        receipt["published_code_commit"], "HEAD"), cwd=REPO, check=True)

    def test_publication_false_claims_rejected(self) -> None:
        task = json.loads((HERE / "task.json").read_text())
        original = json.loads((HERE / task["remote_publication_20261013"]["receipt"]).read_text())
        for failure in ("commit", "exit", "remote-ref", "main-claim"):
            receipt = json.loads(json.dumps(original))
            if failure == "commit":
                receipt["published_code_commit"] = "0" * 40
            elif failure == "exit":
                receipt["push_and_remote_verification"]["exitCode"] = 1
            elif failure == "main-claim":
                receipt["main_updated"] = True
            else:
                record = receipt["push_and_remote_verification"]
                rows = [json.loads(line) for line in record["stdout"].splitlines()]
                rows[1]["remote_refs"]["refs/heads/" + receipt["published_branch"]] = "0" * 40
                record["stdout"] = "\n".join(json.dumps(row) for row in rows)
            with self.subTest(failure=failure):
                with self.assertRaises(AssertionError):
                    verify_publication(task, receipt)


if __name__ == "__main__":
    unittest.main()
