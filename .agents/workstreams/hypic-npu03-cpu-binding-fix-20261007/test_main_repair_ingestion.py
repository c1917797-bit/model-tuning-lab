import copy
import unittest
import verify_main_repair_ingestion as audit

class IngestionReviewTests(unittest.TestCase):
    def setUp(self):
        self.review, self.source, self.selected, self.missing = audit.load_and_check()

    def test_existing_source_gaps_and_supplement(self):
        self.assertEqual(set(self.missing), {"planning-schema", "runtime-template"})
        self.assertEqual(len(audit.missing_explicit(self.review["lessons"])), 0)

    def test_each_required_question_is_fail_closed(self):
        for field in audit.FIELDS:
            row = copy.deepcopy(self.review)
            row["lessons"][0].pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "four-question"):
                audit.validate(row, self.source, self.selected)

    def test_classification_rejected(self):
        self.review["lessons"][0]["classification"] = 11
        with self.assertRaisesRegex(ValueError, "classification"):
            audit.validate(self.review, self.source, self.selected)

    def test_wrong_commit_rejected(self):
        self.review["main_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source binding"):
            audit.validate(self.review, self.source, self.selected)

    def test_changed_destination_rejected(self):
        self.review["lessons"][0]["destination"] = "somewhere-else"
        with self.assertRaisesRegex(ValueError, "destination drift"):
            audit.validate(self.review, self.source, self.selected)

    def test_scope_promotion_rejected(self):
        self.review["claim_boundary"]["full_skill_acceptance"] = True
        with self.assertRaisesRegex(ValueError, "scope overclaim"):
            audit.validate(self.review, self.source, self.selected)

    def test_unrelated_files_rejected(self):
        self.review["lessons"][0]["files_changed"].append("foreign.py")
        with self.assertRaisesRegex(ValueError, "validation/files"):
            audit.validate(self.review, self.source, self.selected)

if __name__ == "__main__":
    unittest.main()
