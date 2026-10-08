#!/usr/bin/env python3
"""Offline regression for in-flight shared-NPU isolation failure."""

import os
import threading
import unittest
from unittest.mock import patch

os.environ["HYPIC_HOTPATH_QUALITY_ARM"] = "hypic-only"
os.environ["HYPIC_HOTPATH_QUALITY_MODE"] = "stress"
os.environ["HYPIC_HOTPATH_QUALITY_CAMPAIGN"] = "cache10"

import hotpath_quality_full as hotpath


class Guard:
    def __init__(self, fail: bool) -> None:
        self.fail = fail
        self.checks = 0

    def assert_clean(self) -> None:
        self.checks += 1
        if self.fail:
            raise RuntimeError("foreign physical NPU process")


class HotpathFailfastTests(unittest.TestCase):
    def test_foreign_process_stops_only_exact_owned_service_while_request_runs(self) -> None:
        release = threading.Event()
        entered = threading.Event()
        accepted = []

        def slow_sample(item: dict, _evaluator: object) -> dict:
            entered.set()
            if not release.wait(5):
                raise RuntimeError("request was not unblocked")
            return item

        def timeout_with_pending(futures: set, **_kwargs: object) -> tuple[set, set]:
            self.assertTrue(entered.wait(1))
            return set(), futures

        def stop_owned(arm: str, container_id: str) -> None:
            self.assertEqual((arm, container_id), ("hypic-only", "exact-owned-id"))
            release.set()

        guard = Guard(True)
        with patch.object(hotpath, "run_sample", side_effect=slow_sample), \
                patch.object(hotpath.concurrent.futures, "wait",
                             side_effect=timeout_with_pending), \
                patch.object(hotpath.quality, "stop_owned_for_abort",
                             side_effect=stop_owned) as stop:
            with self.assertRaisesRegex(RuntimeError, "foreign physical NPU process"):
                hotpath.monitored_samples([{"index": 0}], object(), guard,
                                          "exact-owned-id", accepted.append)
        self.assertTrue(entered.is_set())
        self.assertEqual(guard.checks, 1)
        self.assertEqual(accepted, [])
        stop.assert_called_once_with("hypic-only", "exact-owned-id")

    def test_clean_sample_is_accepted_without_stopping_service(self) -> None:
        accepted = []
        guard = Guard(False)
        with patch.object(hotpath, "run_sample", side_effect=lambda item, _: item), \
                patch.object(hotpath.quality, "stop_owned_for_abort") as stop:
            hotpath.monitored_samples([{"index": 0}], object(), guard,
                                      "exact-owned-id", accepted.append)
        self.assertEqual(accepted, [{"index": 0}])
        self.assertGreaterEqual(guard.checks, 1)
        stop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
