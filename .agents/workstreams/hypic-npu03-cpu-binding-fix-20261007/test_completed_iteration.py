import copy
import unittest
from verify_completed_iteration import audit_plan

class CompletedPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = {"schema": "mst-practice-iteration/v1", "status": "done",
                     "validated_commit": "tested", "changes": [{"files": ["proof.py"]}],
                     "validation_commands": ["python3 -B proof.py"],
                     "lessons_ingested": [{"destination": "proof.py", "severity": "medium",
                                          "classification": 5, "verification": "negative controls"}]}
    def check(self, plan=None, current=b"tested bytes"):
        return audit_plan(plan or self.plan, lambda ref: ref == "tested",
                          lambda ref, path: b"tested bytes", lambda path: current)
    def test_valid(self):
        self.assertEqual(self.check()["files_checked"], 1)
    def test_unrun_checkpoint(self):
        self.plan["validated_commit"] = "future"
        with self.assertRaisesRegex(ValueError, "existing ancestor"):
            self.check()
    def test_stale_file(self):
        with self.assertRaisesRegex(ValueError, "differs"):
            self.check(current=b"new unverified bytes")
    def test_commands_missing(self):
        self.plan["validation_commands"] = []
        with self.assertRaisesRegex(ValueError, "commands"):
            self.check()
    def test_not_done(self):
        self.plan["status"] = "in_progress"
        with self.assertRaisesRegex(ValueError, "completed"):
            self.check()
    def test_lesson_route_missing(self):
        self.plan["lessons_ingested"][0]["destination"] = "elsewhere"
        with self.assertRaisesRegex(ValueError, "routing"):
            self.check()
    def test_duplicate_scope(self):
        self.plan["changes"][0]["files"].append("proof.py")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.check()

if __name__ == "__main__":
    unittest.main()
