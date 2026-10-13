import copy
import json
import unittest
from verify_hypic_campaign_lessons import BASE, NAME, REPORT, validate

class CampaignLessons(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((BASE / NAME).read_text())

    def test_valid(self):
        self.assertTrue(validate(self.data)["passed"])

    def test_source_and_result_mixing(self):
        for key, bad in (("runtime_source", "c12060c"), ("quality", {"decision": "PASS"}),
                         ("skills", {"total": 29, "bounded_verified": 29, "partial": 0})):
            with self.subTest(key=key):
                data = copy.deepcopy(self.data)
                data["outcomes"][key] = bad
                with self.assertRaises(ValueError):
                    validate(data)

    def test_false_promotion(self):
        for key in ("deployment_allowed", "new_device_work",
                    "historical_verdicts_changed", "whole_branch_main_integration"):
            data = copy.deepcopy(self.data)
            data["outcomes"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(data)

    def test_missing_ingestion_fields(self):
        for key in ("trigger", "different_action", "destination", "verification"):
            data = copy.deepcopy(self.data)
            del data["lessons"][0][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(data)

    def test_source_tampering(self):
        self.data["evidence"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_missing_lesson(self):
        self.data["lessons"].pop()
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_report_numbers_and_boundaries(self):
        report = (BASE / REPORT).read_text()
        for text in ("227/381→219/381", "22.0163%", "134", "REJECT_OR_QUALIFY"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate(self.data, report=report.replace(text, "REMOVED"))

if __name__ == "__main__":
    unittest.main()
