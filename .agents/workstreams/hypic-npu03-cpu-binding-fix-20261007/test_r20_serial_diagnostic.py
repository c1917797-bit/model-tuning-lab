"""Host-only regression checks for the bounded r20 diagnostic contract."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

import r20_serial_diagnostic_audit as audit


class R20SerialDiagnosticTests(unittest.TestCase):
    def test_frozen_selection_and_new_roots(self) -> None:
        items, _ = audit.CONTROLLER.cases()
        self.assertEqual([item["index"] for item in items], [59, 82, 126])
        self.assertEqual(audit.CONTROLLER.CONCURRENCY, 1)
        self.assertEqual(audit.CONTROLLER.REPETITIONS, 3)
        self.assertEqual(audit.CONTROLLER.MAX_OUTPUT, 2048)
        self.assertNotEqual(audit.BASE, audit.CAND)
        self.assertFalse(audit.BASE.exists())
        self.assertFalse(audit.CAND.exists())
        self.assertTrue(audit.one_switch_seam()["binds_equal"])

    def test_payload_bytes_replay_existing_frozen_rows(self) -> None:
        old = Path(
            "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
            "quality-context-41984-hotpath-cache10r19-c32-full-baseline/samples")
        for item in audit.CONTROLLER.cases()[0]:
            with self.subTest(index=item["index"]):
                row = json.loads(
                    (old / f"{item['index']:03d}.json").read_text(encoding="utf-8"))
                self.assertEqual(row["prompt_sha256"], item["prompt_sha256"])
                self.assertTrue(all(
                    warm["request_sha256"] == audit.payload_hash(item, 1)
                    for warm in row["warm"]))
                self.assertTrue(all(
                    score["request_sha256"] == audit.payload_hash(item, 2048)
                    for score in row["scores"]))

    def test_prefix_and_selection_boundary(self) -> None:
        self.assertEqual(audit.common_prefix("abc", "abx"), 2)
        self.assertEqual(audit.common_prefix("abc", "abc"), 3)
        self.assertEqual(audit.common_prefix("abc", "ab"), 2)
        self.assertIn("Diagnostic only", audit.PREREG["decision_rule"])


if __name__ == "__main__":
    unittest.main()
