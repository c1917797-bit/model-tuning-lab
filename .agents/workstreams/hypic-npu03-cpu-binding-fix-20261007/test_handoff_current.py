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
        self.assertEqual(task["latest_attempt"]["result"],
                         "environment_isolation_failure")
        self.assertEqual(task["resource_claim"]["forbidden_npus"],
                         [4, 5, 6, 7])
        subprocess.run(("git", "diff", "--quiet", "HEAD", "--",
                        ".agents/HANDOFF.md"), cwd=REPO, check=True)


if __name__ == "__main__":
    unittest.main()
