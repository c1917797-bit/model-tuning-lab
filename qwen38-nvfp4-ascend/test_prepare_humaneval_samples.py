#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("prepare_humaneval_samples.py")
SPEC = importlib.util.spec_from_file_location("prepare_humaneval_samples", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareHumanEvalSamplesTest(unittest.TestCase):
    def test_population_and_order(self):
        requests = [
            {"id": "HumanEval/1", "suite": "humaneval"},
            {"id": "HumanEval/0", "suite": "humaneval"},
        ]
        responses = [
            {"id": "HumanEval/0", "text": " zero", "error": None, "rendered_prompt_sha256": "a"},
            {"id": "HumanEval/1", "text": " one", "error": None, "rendered_prompt_sha256": "b"},
        ]
        self.assertEqual(
            MODULE.prepare(requests, responses),
            [
                {"task_id": "HumanEval/0", "completion": " zero"},
                {"task_id": "HumanEval/1", "completion": " one"},
            ],
        )

    def test_error_fails_closed(self):
        with self.assertRaises(ValueError):
            MODULE.prepare(
                [{"id": "HumanEval/0", "suite": "humaneval"}],
                [{"id": "HumanEval/0", "text": "", "error": "failed", "rendered_prompt_sha256": "x"}],
            )


if __name__ == "__main__":
    unittest.main()
