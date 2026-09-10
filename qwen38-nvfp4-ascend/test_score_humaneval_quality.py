#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("score_humaneval_quality.py")
SPEC = importlib.util.spec_from_file_location("score_humaneval_quality", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScoreHumanEvalQualityTest(unittest.TestCase):
    def test_pairing_and_gate(self):
        responses = [
            {"id": "HumanEval/0", "error": None, "rendered_prompt_sha256": "a"},
            {"id": "HumanEval/1", "error": None, "rendered_prompt_sha256": "b"},
        ]
        control = [
            {"task_id": "HumanEval/0", "passed": True},
            {"task_id": "HumanEval/1", "passed": False},
        ]
        candidate = [
            {"task_id": "HumanEval/0", "passed": True},
            {"task_id": "HumanEval/1", "passed": True},
        ]
        report = MODULE.compare(responses, responses, control, candidate, expected_count=2)
        self.assertTrue(report["gate_pass"])
        self.assertEqual(report["pass_at_1_delta"], 0.5)
        self.assertEqual(report["outcome_disagreements"], 1)

    def test_prompt_mismatch_fails_gate(self):
        control_response = [{"id": "HumanEval/0", "error": None, "rendered_prompt_sha256": "a"}]
        candidate_response = [{"id": "HumanEval/0", "error": None, "rendered_prompt_sha256": "b"}]
        results = [{"task_id": "HumanEval/0", "passed": True}]
        report = MODULE.compare(control_response, candidate_response, results, results, expected_count=1)
        self.assertFalse(report["gate_pass"])


if __name__ == "__main__":
    unittest.main()
