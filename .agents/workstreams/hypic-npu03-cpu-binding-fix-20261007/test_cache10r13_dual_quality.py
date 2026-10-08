#!/usr/bin/env python3
"""Offline tests for predeclared r13 hot/cold descriptive partition."""

from __future__ import annotations

import unittest

from r13_quality_cohorts import cohort_summary


class DualQualityTests(unittest.TestCase):
    def test_cold_requests_remain_in_all_request_denominator(self) -> None:
        base = []
        candidate = []
        for index in range(127):
            for repetition in range(1, 4):
                base.append({"index": index, "repetition": repetition, "correct": False})
                candidate.append({"index": index, "repetition": repetition,
                                  "correct": index == 0})
        summary = cohort_summary(base, candidate, {(0, 1)})
        self.assertEqual(summary["hot"]["requests"], 380)
        self.assertEqual(summary["cold"]["requests"], 1)
        self.assertEqual(summary["hot"]["candidate_correct"], 2)
        self.assertEqual(summary["cold"]["candidate_correct"], 1)
        self.assertTrue(summary["strata_are_descriptive_not_causal"])

    def test_mismatched_pair_keys_fail_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "cardinality"):
            cohort_summary([], [], set())


if __name__ == "__main__":
    unittest.main()
