#!/usr/bin/env python3
"""Pure regression checks for the r13 producer-kind evidence join."""

import unittest

from verify_r13_strict_mode_path import materialization_producers


class StrictModePathTests(unittest.TestCase):
    def test_only_materialization_candidates_are_counted(self) -> None:
        rows = [
            {"event": "position_independent_materialization_candidate",
             "producer_kind": "zero_start"},
            {"event": "materialization_ready", "producer_kind": "ignored"},
            {"event": "position_independent_materialization_candidate",
             "producer_kind": "combined_prefill_approximation"},
        ]
        self.assertEqual(materialization_producers(rows),
                         {"zero_start": 1, "combined_prefill_approximation": 1})

    def test_missing_kind_fails_closed(self) -> None:
        with self.assertRaises(KeyError):
            materialization_producers([
                {"event": "position_independent_materialization_candidate"}])


if __name__ == "__main__":
    unittest.main()
