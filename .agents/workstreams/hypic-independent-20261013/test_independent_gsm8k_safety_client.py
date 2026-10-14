import unittest
from independent_gsm8k_safety_client import run_gsm8k_safety
class GSMSafetyTests(unittest.TestCase):
    def test_all3957_with_errors_retained(self):
        rows=[{"index":i,"sample_id":str(i),"token_ids":[i+1],"reference":"42"} for i in range(1319)]
        journal=[]
        def send(payload):
            self.assertEqual(payload["stop"],["Question"])
            if payload["prompt"]==[2]:raise RuntimeError("retained")
            return {"id":"fixture","choices":[{"text":"answer:42","finish_reason":"stop"}],
                "usage":{"prompt_tokens":1,"completion_tokens":3}}
        result=run_gsm8k_safety(rows,send=send,score=lambda *x:("42",True),
            guard=lambda:None,record=journal.append)
        self.assertEqual(len(journal),3957);self.assertEqual(result["successful"],3954)
        self.assertEqual(result["requests"],3957)
if __name__=="__main__":unittest.main()
