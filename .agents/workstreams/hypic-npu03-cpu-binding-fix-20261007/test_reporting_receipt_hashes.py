"""Regression for report-to-raw digest binding; no device or raw writes."""
import unittest
from verify_paper_to_ascend_reporting_case import audit_report_receipt_hashes

class ReportReceiptHashes(unittest.TestCase):
    def setUp(self):
        self.receipts = {"contract": "a" * 64, "capture": "b" * 64,
                         "artifact inventory": "c" * 64}
        self.report = "\n".join(f"{key} `{value}`;"
                                for key, value in self.receipts.items())

    def test_matching_labelled_hashes(self):
        audit_report_receipt_hashes(self.report, self.receipts)

    def test_truncated_digest(self):
        with self.assertRaisesRegex(RuntimeError, "capture"):
            audit_report_receipt_hashes(
                self.report.replace("b" * 64, "b" * 48), self.receipts)

    def test_wrong_full_length_digest(self):
        with self.assertRaisesRegex(RuntimeError, "capture"):
            audit_report_receipt_hashes(
                self.report.replace("b" * 64, "d" * 64), self.receipts)

    def test_swapped_labels(self):
        with self.assertRaises(RuntimeError):
            audit_report_receipt_hashes(
                self.report.replace("contract", "TEMP").replace(
                    "capture", "contract").replace("TEMP", "capture"),
                self.receipts)

    def test_duplicate_receipt(self):
        with self.assertRaisesRegex(RuntimeError, "capture"):
            audit_report_receipt_hashes(
                self.report + "\ncapture `" + "b" * 64 + "`", self.receipts)

    def test_unlabelled_hash_is_not_proof(self):
        with self.assertRaisesRegex(RuntimeError, "capture"):
            audit_report_receipt_hashes(
                self.report.replace("capture ", ""), self.receipts)

if __name__ == "__main__":
    unittest.main()
