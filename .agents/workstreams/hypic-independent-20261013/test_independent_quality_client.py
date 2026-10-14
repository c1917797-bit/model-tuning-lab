import unittest
from independent_quality_client import run_quality
class QualityClientTests(unittest.TestCase):
    def test_full381_failures_and_truncation_retained(self):
        rows=[{"index":i,"sample_id":str(i),"segment":{"tokens_sha256":str(i)},
            "token_ids":[i+1]*16,"reference":"A"} for i in range(127)]
        journal=[];prepared=[]
        def send(payload):
            if payload["prompt"][0]==2:raise RuntimeError("retained failure")
            return {"id":"r"+str(payload["prompt"][0]),"choices":[{"text":"A","finish_reason":"length"}],
                "usage":{"prompt_tokens":16,"completion_tokens":1024}}
        result=run_quality(rows,send=send,prepare=prepared.append,
            score=lambda *a:("A",True),guard=lambda:None,record=journal.append)
        self.assertEqual(result["requests"],381)
        self.assertEqual(len(journal),381)
        self.assertEqual(result["successful"],378)
        self.assertEqual(sum(x.get("truncated",False) for x in journal),378)
        self.assertEqual(len(prepared),39)
if __name__=="__main__":unittest.main()
