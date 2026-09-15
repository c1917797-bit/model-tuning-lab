#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("run_physical_canary.py")
SPEC = importlib.util.spec_from_file_location("run_physical_canary_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def activation_rows(
    physical_pids: range,
    geometry_pids: range,
    dispatch_pids: range,
) -> list[dict]:
    rows: list[dict] = [{"event": "heterogeneous_cache_grouped", "pid": 99}]
    for pid in physical_pids:
        rows.append(
            {
                "event": "physical_cache_bound",
                "pid": pid,
                "compact_page_bytes": 64,
                "dense_page_bytes": 128,
                "num_blocks": 1,
            }
        )
    rows.extend({"event": "tp_geometry_aligned", "pid": pid} for pid in geometry_pids)
    rows.extend(
        {"event": "worker_dispatch_verified", "pid": pid}
        for pid in dispatch_pids
    )
    return rows


class PhysicalCanaryGateTest(unittest.TestCase):
    def test_activation_requires_one_exact_four_worker_cohort(self) -> None:
        summary = MODULE.activation_summary(
            activation_rows(range(1, 5), range(1, 5), range(1, 5)),
            [],
        )
        self.assertTrue(summary["ok"])
        self.assertTrue(summary["worker_cohort_aligned"])

    def test_activation_rejects_disjoint_four_worker_cohorts(self) -> None:
        summary = MODULE.activation_summary(
            activation_rows(range(1, 5), range(5, 9), range(9, 13)),
            [],
        )
        self.assertFalse(summary["ok"])
        self.assertFalse(summary["worker_cohort_aligned"])

    def test_activation_rejects_extra_worker(self) -> None:
        summary = MODULE.activation_summary(
            activation_rows(range(1, 6), range(1, 6), range(1, 6)),
            [],
        )
        self.assertFalse(summary["ok"])
        self.assertFalse(summary["worker_cohort_aligned"])

    def test_exact_output_rejects_whitespace_or_length_finish(self) -> None:
        self.assertTrue(
            MODULE.exact_stopped({"content": "OK", "finish_reason": "stop"}, "OK")
        )
        self.assertFalse(
            MODULE.exact_stopped({"content": " OK", "finish_reason": "stop"}, "OK")
        )
        self.assertFalse(
            MODULE.exact_stopped({"content": "OK", "finish_reason": "length"}, "OK")
        )


if __name__ == "__main__":
    unittest.main()
