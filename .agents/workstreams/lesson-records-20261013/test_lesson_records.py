import copy
import unittest
import verify_lesson_records as v

class LessonRecordsTests(unittest.TestCase):
    def setUp(self):
        self.old, self.current, self.review = v.inputs()
    def test_positive(self):
        self.assertEqual(v.check(self.old, self.current, self.review)["complete_records"], 3)
    def test_missing_fields(self):
        for item in self.current["proposals"][:2]:
            for field in v.FIELDS:
                d=copy.deepcopy(self.current)
                next(p for p in d["proposals"] if p["id"] == item["id"]).pop(field)
                with self.subTest(id=item["id"], field=field), self.assertRaises(AssertionError):
                    v.check(self.old,d,self.review)
    def test_historical_decision_cannot_change(self):
        d=copy.deepcopy(self.current);d["proposals"][0]["decision"]="rejected"
        with self.assertRaises(AssertionError):v.check(self.old,d,self.review)
    def test_existing_complete_record_cannot_change(self):
        d=copy.deepcopy(self.current);d["proposals"][2]["different_action"]="skip exact command"
        with self.assertRaises(AssertionError):v.check(self.old,d,self.review)
    def test_wrong_classification(self):
        d=copy.deepcopy(self.current);d["proposals"][1]["classification"]=2
        with self.assertRaises(AssertionError):v.check(self.old,d,self.review)
    def test_missing_or_extra_lesson(self):
        for change in ("missing","extra"):
            d=copy.deepcopy(self.current)
            if change=="missing":d["proposals"].pop()
            else:d["proposals"].append(copy.deepcopy(d["proposals"][0]))
            with self.subTest(change=change),self.assertRaises(AssertionError):
                v.check(self.old,d,self.review)
    def test_no_full_acceptance_claim(self):
        r=copy.deepcopy(self.review);r["claim_boundary"]["full_skill_acceptance"]=True
        with self.assertRaises(AssertionError):v.check(self.old,self.current,r)

if __name__ == "__main__":unittest.main()
