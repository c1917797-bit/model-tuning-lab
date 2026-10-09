"""Focused non-acceptance tests for material-event ordering diagnosis."""

from __future__ import annotations

import unittest

from diagnose_material_eviction_sequence import classify_issue


class MaterialEvictionSequenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.issue = {"index": 7, "repetition": 3, "internal_request_id": "rid"}
        self.plan = {
            "event": "position_independent_prefill_plan_unavailable",
            "request_id": "rid", "time_ns": 30,
            "reason": "computed_prefix_not_reusable_boundary",
            "computed_tokens": 16384, "candidate_hashes": ["hash"],
            "ready_hashes": [],
        }
        self.ready = {"event": "materialization_report", "time_ns": 10,
                      "ready_hashes": ["hash"], "evicted_hashes": []}
        self.evicted = {"event": "materialization_report", "time_ns": 20,
                        "ready_hashes": [], "evicted_hashes": ["hash"]}

    def test_ready_then_evicted_before_reject(self) -> None:
        result = classify_issue(self.issue, [self.ready, self.evicted, self.plan])
        self.assertEqual(result["classification"],
                         "evicted_before_partial_prefill_rejection")
        self.assertEqual(result["transitions"][0]["last_prior"]["time_ns"], 20)

    def test_ready_after_eviction_is_not_misclassified(self) -> None:
        later = dict(self.ready, time_ns=25)
        result = classify_issue(self.issue, [self.ready, self.evicted, later,
                                             self.plan])
        self.assertEqual(result["classification"], "unresolved")

    def test_no_prior_ready_is_not_misclassified(self) -> None:
        result = classify_issue(self.issue, [self.evicted, self.plan])
        self.assertEqual(result["classification"], "unresolved")

    def test_missing_plan_is_not_misclassified(self) -> None:
        result = classify_issue(self.issue, [self.ready, self.evicted])
        self.assertEqual(result["reason"], "missing_or_ambiguous_plan_event")


if __name__ == "__main__":
    unittest.main()
