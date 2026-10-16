import copy,unittest
import test_audit_full_quality_cohort as fixtures
from audit_quality_pair import audit_quality_pair
class Tests(unittest.TestCase):
    def fixture(self):
        rows,b,bj=fixtures.Tests().fixture();h=copy.deepcopy(b);hj=copy.deepcopy(bj)
        return rows,b,bj,h,hj
    def score(self,task,text,reference):return text,text==reference
    def audit(self,args):return audit_quality_pair(*args,score=self.score)
    def test_equal(self):
        out=self.audit(self.fixture());self.assertEqual(out["correct_delta"],0)
        self.assertEqual(out["quality_acceptance"],"NOT_DECIDED")
        self.assertEqual(out["rounds"][0]["ties"],127)
    def test_one_fix(self):
        import hashlib
        args=self.fixture();rows,b,bj,h,hj=args
        item=h["results"][0];item.update(response_text="A",response_sha256=hashlib.sha256(b"A").hexdigest(),prediction="A",correct=True);h["correct"]+=1
        next(e for e in hj if e["event"]=="quality-scored-response").update(item)
        out=self.audit(args);self.assertEqual(out["correct_delta"],1)
        self.assertEqual(out["rounds"][0]["wins"],1);self.assertEqual(len(out["changed_cases"]),1)
    def test_one_loss_not_automatic_reject(self):
        import hashlib
        args=self.fixture();rows,b,bj,h,hj=args
        item=h["results"][1];item.update(response_text="B",response_sha256=hashlib.sha256(b"B").hexdigest(),prediction="B",correct=False);h["correct"]-=1
        [e for e in hj if e["event"]=="quality-scored-response"][1].update(item)
        out=self.audit(args);self.assertEqual(out["correct_delta"],-1);self.assertEqual(out["quality_acceptance"],"NOT_DECIDED")
    def test_incomplete_arm(self):
        args=self.fixture();args[3]["results"].pop()
        with self.assertRaises(ValueError):self.audit(args)
    def test_fake_score_rejected(self):
        args=self.fixture();args[3]["results"][0]["correct"]=True
        with self.assertRaises(ValueError):self.audit(args)
    def test_same_request_ids_across_separate_arms_not_invented_gate(self):
        out=self.audit(self.fixture());self.assertTrue(out["complete_paired_cohort"])
if __name__=="__main__":unittest.main()
