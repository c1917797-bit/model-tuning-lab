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
        self.assertEqual(
            report["issues"][0]["request_local_diagnostics"]["event_counts"],
            {})
        self.assertEqual(report["acceptance"],
                         "not_applicable_to_partial_samples")

    def test_new_request_local_reason_is_joined_without_causal_claim(self) -> None:
        workers = {264, 265, 266, 267}
        rows = [{"index": 18, "scores": [
            {"repetition": n, "request_id": f"chatcmpl-api{n}"}
            for n in range(1, 4)
        ]}]
        events = [{"event": "explicit_segment_boundary_active",
                   "request_id": f"chatcmpl-api{n}-internal"}
                  for n in range(1, 4)]
        events += [{
            "event": "position_independent_prefill_plan_unavailable",
            "request_id": "chatcmpl-api3-internal",
            "reason": "no_ready_public_material",
            "computed_tokens": None,
            "candidate_hashes": ["aabb"],
            "ready_hashes": [],
        }]
        for n in (1, 2):
            events.extend({
                "event": "worker_hot_request_verified",
                "request_id": f"chatcmpl-api{n}-internal",
                "pid": pid, "skipped_prefix_tokens": 100,
                "complete_hybrid_repair_validated": True,
            } for pid in workers)
        issue = diagnose(rows, events, workers)["issues"][0]
        diagnostic = issue["request_local_diagnostics"]
        self.assertEqual(diagnostic["observed_reasons"],
                         ["no_ready_public_material"])
        self.assertIsNone(diagnostic["first_event"]["computed_tokens"])
        self.assertEqual(diagnostic["causal_status"],
                         "unresolved_without_matched_state_audit")

    def test_prefill_filter_miss_is_not_mislabeled_as_plan_rejection(self) -> None:
        rows = [{"index": 0, "scores": [
            {"repetition": n, "request_id": f"chatcmpl-api{n}"}
            for n in range(1, 4)
        ]}]
        events = [{"event": "explicit_segment_boundary_active",
                   "request_id": f"chatcmpl-api{n}-internal"}
                  for n in range(1, 4)]
        events.append({
            "event": "position_independent_prefill_filter_miss",
            "request_id": "chatcmpl-api1-internal",
            "reason": "segmented_first_schedule_classified_as_decode",
            "request_in_pre_schedule_snapshot": False,
            "native_prefix_cache_enabled": False,
        })
        issue = diagnose(rows, events, {1, 2, 3, 4})["issues"][0]
        diagnostic = issue["request_local_diagnostics"]
        self.assertEqual(diagnostic["event_counts"],
                         {"position_independent_prefill_filter_miss": 1})
        self.assertFalse(diagnostic["first_event"]["native_prefix_cache_enabled"])

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
