#!/usr/bin/env python3
"""Offline counterexamples for diagnostic-only scored-request coverage."""

import unittest

from diagnose_partial_hotpath_coverage import diagnose
from verify_hotpath_request_coverage import CoverageError


class PartialCoverageTests(unittest.TestCase):
    def test_one_native_fallback_is_not_hidden_by_aggregate_counts(self) -> None:
        workers = {264, 265, 266, 267}
        rows = [{"index": 6, "scores": [
            {"repetition": n, "request_id": f"chatcmpl-api{n}"}
            for n in range(1, 4)
        ]}]
        events = [
            {"event": "explicit_segment_boundary_active",
             "request_id": f"chatcmpl-api{n}-internal"}
            for n in range(1, 4)
        ]
        for n in (1, 2):
            events.extend({
                "event": "worker_hot_request_verified",
                "request_id": f"chatcmpl-api{n}-internal",
                "pid": pid, "skipped_prefix_tokens": 100,
                "complete_hybrid_repair_validated": True,
            } for pid in workers)
        report = diagnose(rows, events, workers)
        self.assertEqual(report["scored_requests"], 3)
        self.assertEqual(report["four_worker_verified_requests"], 2)
        self.assertEqual(report["issue_count"], 1)
        self.assertEqual(report["issues"][0]["repetition"], 3)
        self.assertEqual(report["acceptance"],
                         "not_applicable_to_partial_samples")

    def test_boundary_absence_is_not_a_hot_path_success(self) -> None:
        rows = [{"index": 0, "scores": [
            {"repetition": n, "request_id": f"chatcmpl-api{n}"}
            for n in range(1, 4)
        ]}]
        report = diagnose(rows, [], {1, 2, 3, 4})
        self.assertEqual(report["issue_count"], 3)
        self.assertEqual(report["issues"][0]["reason"],
                         "boundary_join_missing_or_ambiguous")

    def test_duplicate_scored_id_rejected(self) -> None:
        rows = [{"index": 0, "scores": [
            {"repetition": n, "request_id": "chatcmpl-same"}
            for n in range(1, 4)
        ]}]
        with self.assertRaises(CoverageError):
            diagnose(rows, [], {1, 2, 3, 4})


if __name__ == "__main__":
    unittest.main()
