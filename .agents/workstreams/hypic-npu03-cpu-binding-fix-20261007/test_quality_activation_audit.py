#!/usr/bin/env python3
"""Offline proof that quality activation requires four distinct hot workers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_binding_off_quality import audit_activation_events


class QualityActivationAuditTests(unittest.TestCase):
    def check(self, worker_pids: list[int], include_scheduler: bool = True) -> dict:
        events = [{"event": "plugin_build_active", "pid": 1}]
        events.extend({"event": "worker_hot_path", "pid": pid} for pid in worker_pids)
        if include_scheduler:
            events.append({"event": "runtime_scheduler_active", "pid": 2})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.jsonl"
            path.write_text("".join(json.dumps(event) + "\n" for event in events))
            return audit_activation_events(path)

    def test_four_distinct_workers_pass(self) -> None:
        result = self.check([265, 266, 267, 268])
        self.assertEqual(result["distinct_worker_hot_pids"], [265, 266, 267, 268])

    def test_four_repeats_from_one_worker_fail(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "distinct_worker_hot_pids"):
            self.check([265, 265, 265, 265])

    def test_missing_scheduler_fails(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "runtime activation insufficient"):
            self.check([265, 266, 267, 268], include_scheduler=False)


if __name__ == "__main__":
    unittest.main()
