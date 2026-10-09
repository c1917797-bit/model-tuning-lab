#!/usr/bin/env python3
"""Offline unit tests for descriptive HYPIC response-variability arithmetic."""

import unittest

from analyze_r13_response_variability import bucket_summary, common_prefix_chars


class ResponseVariabilityTests(unittest.TestCase):
    def test_common_prefix_stops_at_first_difference_or_shorter_text(self) -> None:
        self.assertEqual(common_prefix_chars("abcdef", "abcZef"), 3)
        self.assertEqual(common_prefix_chars("abc", "abcdef"), 3)
        self.assertEqual(common_prefix_chars("", "abcdef"), 0)

    def test_bucket_preserves_text_answer_and_score_as_separate_facts(self) -> None:
        left = {"response_text": "A" * 128 + "x", "response_sha256": "a",
                "prediction": "A", "correct": True}
        right = {"response_text": "A" * 128 + "y", "response_sha256": "b",
                 "prediction": "A", "correct": True}
        result = bucket_summary([(left, right)])
        self.assertEqual(result["pairs"], 1)
        self.assertEqual(result["exact_text"], 0)
        self.assertEqual(result["same_prediction"], 1)
        self.assertEqual(result["same_correctness"], 1)
        self.assertEqual(result["common_first_128_chars"], 1)
        self.assertEqual(result["common_first_512_chars"], 0)


if __name__ == "__main__":
    unittest.main()
