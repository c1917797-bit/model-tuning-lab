#!/usr/bin/env python3
"""Offline regression for the branch-local concise maintainer handoff."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


class HandoffTests(unittest.TestCase):
    def test_current_shape_and_history_retention(self) -> None:
        current = (HERE / "HANDOFF.md").read_text(encoding="utf-8")
        history = (HERE / "HANDOFF_HISTORY.md").read_text(encoding="utf-8")
        headings = re.findall(r"^## ([0-8])\. ", current, re.M)
        self.assertEqual(headings, list("012345678"))
        self.assertLessEqual(len(current.splitlines()), 150)
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
        self.assertEqual(task["latest_attempt"]["campaign"], "cache10r12")
        self.assertEqual(task["latest_attempt"]["controller_operation"],
                         "exec-00000000000018b4")
        self.assertEqual(task["r13_candidate_attempt"]["campaign"], "cache10r13")
        self.assertEqual(task["r13_candidate_attempt"]["controller_operation"],
                         "exec-0000000000001bb1")
        self.assertEqual(task["r13_quality_audit"]["sha256"],
                         "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b")
        self.assertIsNone(task["active_attempt"])
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
        self.assertIn("127x3", task["goal_horizons"]["short_term"])
        self.assertIn("all 29", task["goal_horizons"]["long_term"])
        self.assertIn("exec-000000000000004b", task["next_action"])
        self.assertIn("53/57", task["prior_stress_attempt"]["request_hot_path_gate"])
        self.assertIn("52/57", task["latest_attempt"]["status"])
        self.assertIn("c12060c", task["diagnostic_plugin"]["local_commit"])
        self.assertTrue((HERE / task["previous_attempt"]["evidence"]).is_file())
        self.assertTrue((HERE / task["prior_stress_attempt"]["coverage_report"]).is_file())
        self.assertTrue((HERE / task["latest_attempt"]["coverage_report"]).is_file())
        self.assertEqual(task["resource_claim"]["forbidden_npus"],
                         [4, 5, 6, 7])
        subprocess.run(("git", "diff", "--quiet", "HEAD", "--",
                        ".agents/HANDOFF.md"), cwd=REPO, check=True)


if __name__ == "__main__":
    unittest.main()
