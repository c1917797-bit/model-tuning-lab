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
        self.assertEqual(report["cases_with_verified_provenance"], 1)
        self.assertEqual(report["skills_without_case"], 28)
        self.assertEqual(report["case_acceptance"], {"partial-evidence": 1})

    def test_wrong_evidence_bytes_fail_closed(self) -> None:
        with patch.object(cases, "evidence_path", return_value=Path(__file__)):
            with self.assertRaisesRegex(RuntimeError, "evidence SHA256 drift"):
                cases.check_case(
                    self.case_path, self.main_commit, {"mst-repo-onboarding"})


if __name__ == "__main__":
    unittest.main()
