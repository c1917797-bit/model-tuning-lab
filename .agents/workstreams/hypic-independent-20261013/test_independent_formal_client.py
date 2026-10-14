import unittest
from independent_formal_client import run_full40

class FormalClientTests(unittest.TestCase):
    def cases(self):return [{"index":i,"token_ids":[i]*32768} for i in range(40)]
    def test_full_denominator_failure_not_dropped(self):
        journal=[]
        def send(p):
            self.assertEqual(p["max_tokens"],1024)
            if p["prompt"][0]==8:raise RuntimeError("injected")
            return {"completion_tokens":1024}
        r=run_full40(self.cases(),send=send,guard=lambda:None,record=journal.append)
        self.assertFalse(r["valid"]);self.assertEqual(len(journal),40)
        self.assertEqual(sum(not x["ok"] for x in r["results"]),1)
        self.assertEqual(r["results"][8]["error"]["message"],"injected")
    def test_partial_denominator_rejected_before_send(self):
        with self.assertRaises(ValueError):
            run_full40(self.cases()[:-1],send=lambda p:self.fail("send"),
                       guard=lambda:None,record=lambda x:None)
    def test_guard_failure_before_admission(self):
        def fail():raise RuntimeError("foreign")
        with self.assertRaises(RuntimeError):
            run_full40(self.cases(),send=lambda p:self.fail("send"),guard=fail,record=lambda x:None)

if __name__=="__main__":unittest.main()
