#!/usr/bin/env python3
"""CPU-only coverage counterexamples for measured performance requests."""

import unittest

from performance_request_coverage import diagnose_request_coverage


def fixture(cold_index=None):
    measured = [{"index": i, "request_id": f"cmpl-{i:03d}"} for i in range(40)]
    events = []
    for i in range(40):
        internal = f"cmpl-{i:03d}-0-private"
        events.append({"event": "explicit_segment_boundary_active",
                       "request_id": internal})
        for pid in (1, 2, 3, 4):
            if i == cold_index and pid == 4:
                continue
            events.append({"event": "worker_hot_request_verified",
                           "request_id": internal, "pid": pid,
                           "skipped_prefix_tokens": 16384,
                           "complete_hybrid_repair_validated": True})
    return measured, events


class PerformanceCoverageTests(unittest.TestCase):
    def test_all_40_join_four_workers(self):
        measured, events = fixture()
        report = diagnose_request_coverage(measured, events, {1, 2, 3, 4})
        self.assertEqual(report["four_worker_verified_requests"], 40)
        self.assertEqual(report["issue_count"], 0)

    def test_one_cold_request_is_retained_as_negative(self):
        measured, events = fixture(cold_index=17)
        report = diagnose_request_coverage(measured, events, {1, 2, 3, 4})
        self.assertEqual(report["four_worker_verified_requests"], 39)
        self.assertEqual(report["issues"][0]["index"], 17)
        self.assertEqual(report["issues"][0]["observed_worker_pids"], [1, 2, 3])

    def test_duplicate_api_id_is_invalid(self):
        measured, events = fixture()
        measured[1]["request_id"] = measured[0]["request_id"]
        with self.assertRaisesRegex(RuntimeError, "duplicated"):
            diagnose_request_coverage(measured, events, {1, 2, 3, 4})

    def test_missing_boundary_is_not_hot(self):
        measured, events = fixture()
        events = [row for row in events if not (
            row["event"] == "explicit_segment_boundary_active"
            and row["request_id"].startswith("cmpl-005-"))]
        report = diagnose_request_coverage(measured, events, {1, 2, 3, 4})
        self.assertEqual(report["issues"][0]["index"], 5)
        self.assertEqual(report["issues"][0]["reason"],
                         "missing-or-ambiguous-boundary")


if __name__ == "__main__":
    unittest.main()
