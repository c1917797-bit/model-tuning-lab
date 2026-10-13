"""Negative controls for exact-main replay provenance, not an NPU test."""
import copy
import json
import unittest
import verify_integrated_main_repairs as audit

class IntegratedRepairTests(unittest.TestCase):
    def setUp(self):
        self.row = json.loads((audit.HERE / "MAIN_REPAIR_REPLAY_RECEIPT_20261013.json").read_text())

    def test_retained_receipt(self):
        audit.verify_receipt(self.row)
        audit.verify_git()

    def test_wrong_commit_rejected(self):
        self.row["main_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "commit identity"):
            audit.verify_receipt(self.row)

    def test_failed_replay_rejected(self):
        self.row["fresh_clone"]["exitCode"] = 1
        with self.assertRaisesRegex(ValueError, "replay terminal"):
            audit.verify_receipt(self.row)

    def test_wrong_clone_rejected(self):
        self.row["fresh_clone"]["stdout"] = self.row["fresh_clone"]["stdout"].replace(str(audit.CLONE), "/tmp/not-proof")
        with self.assertRaisesRegex(ValueError, "clone result"):
            audit.verify_receipt(self.row)

    def test_missing_command_rejected(self):
        lines = self.row["fresh_clone"]["stdout"].splitlines()
        self.row["fresh_clone"]["stdout"] = "\n".join(lines[:2] + lines[3:])
        with self.assertRaisesRegex(ValueError, "replay commands"):
            audit.verify_receipt(self.row)

    def test_device_promotion_rejected(self):
        lines = self.row["fresh_clone"]["stdout"].splitlines()
        command = json.loads(lines[1])
        report = json.loads(command["out"])
        report["device_acceptance"] = True
        command["out"] = json.dumps(report)
        lines[1] = json.dumps(command)
        self.row["fresh_clone"]["stdout"] = "\n".join(lines)
        with self.assertRaisesRegex(ValueError, "replay scope"):
            audit.verify_receipt(self.row)

if __name__ == "__main__":
    unittest.main()
