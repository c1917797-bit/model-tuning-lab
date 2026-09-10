#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("score_text_quality.py")
SPEC = importlib.util.spec_from_file_location("score_text_quality", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScoreTextQualityTest(unittest.TestCase):
    def test_mmlu_choice(self):
        self.assertEqual(MODULE.extract_answer("mmlu", "B"), "B")
        self.assertEqual(MODULE.extract_answer("mmlu", "Answer: (c)."), "C")
        self.assertIsNone(MODULE.extract_answer("mmlu", "unknown"))

    def test_gsm8k_strict_final_marker(self):
        self.assertEqual(MODULE.extract_answer("gsm8k", "work\n#### 1,234"), "1234")
        self.assertEqual(MODULE.extract_answer("gsm8k", "#### 18.0"), "18")
        self.assertIsNone(MODULE.extract_answer("gsm8k", "the answer is 18"))


if __name__ == "__main__":
    unittest.main()
