#!/usr/bin/env python3
"""Offline regression for current main/work-branch Skill attribution."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPECTED_CHANGED_V = {
    "ascend-benchmark-evidence",
    "chicaihong01-host-maintenance",
}


class MainVersionBoundaryTests(unittest.TestCase):
    def test_changed_v_cannot_be_silently_attributed_to_main(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(HERE / "verify_skill_matrix.py")],
            cwd=HERE.parents[2], text=True, capture_output=True, check=True,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["skills"], 29)
        self.assertEqual(report["current_status"], {"V": 11, "P": 14, "N": 4})
        self.assertEqual(set(report["branch_modified_bounded_v"]),
                         EXPECTED_CHANGED_V)
        self.assertEqual(len(report["branch_modified_main_skill_bodies"]), 7)
        self.assertTrue(report["branch_registry_differs_from_main"])


if __name__ == "__main__":
    unittest.main()
