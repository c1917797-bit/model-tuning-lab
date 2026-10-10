"""No-device regression checks for the prospective r17 cap-only diagnostic."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from r17_cap1024_offline_adapter import check_preregistration
from hotpath_quality_audit import audit_arm, frozen_cases, payload_hash


class R17Cap1024ContractTest(unittest.TestCase):
    def test_preregistered_files_match_frozen_hashes(self):
        prereg = check_preregistration()
        self.assertEqual(prereg["arm_order"], ["no-cache", "hypic-only"])
        self.assertFalse(prereg["historical_1024_c32_acceptance"])
        self.assertFalse(prereg["current_2048_skill_acceptance"])

    def test_only_scored_cap_changes_and_roots_are_distinct(self):
        rows = []
        script = Path(__file__).with_name("r17_cap1024_offline_adapter.py")
        for arm in ("no-cache", "hypic-only"):
            env = dict(os.environ, HYPIC_R17_ARM=arm)
            result = subprocess.run([sys.executable, "-B", str(script), "--check"],
                                    env=env, capture_output=True, text=True,
                                    check=True)
            rows.append(json.loads(result.stdout))
        self.assertEqual([row["arm"] for row in rows], ["no-cache", "hypic-only"])
        self.assertTrue(all(row["max_output_tokens"] == 1024
                            and row["concurrency"] == 8
                            and row["sample_count"] == 127
                            and not row["device_run_started"] for row in rows))
        self.assertNotEqual(rows[0]["root"], rows[1]["root"])
        self.assertTrue(all(not Path(row["root"]).exists() for row in rows))

    def test_1024_payload_is_not_2048_payload(self):
        cases, _ = frozen_cases()
        self.assertEqual(len(cases), 127)
        self.assertNotEqual(payload_hash(cases[0], 1024),
                            payload_hash(cases[0], 2048))

    def test_old_2048_root_cannot_pass_1024_auditor(self):
        cases, evaluator = frozen_cases()
        r16_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/") / (
            "quality-context-41984-hotpath-cache10r16-full-baseline")
        with self.assertRaisesRegex(RuntimeError, "generation contract drift"):
            audit_arm(r16_root, "no-cache", cases, evaluator,
                      scored_cap=1024)


if __name__ == "__main__":
    unittest.main()
