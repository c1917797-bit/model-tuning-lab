import hashlib,unittest
from audit_quality_pair import audit_pair,audit_arm
class PairAuditTests(unittest.TestCase):
    def fixtures(self):
        inputs=[{"index":i,"sample_id":str(i),"reference":"A","segment":{"tokens_sha256":str(i)}} for i in range(127)]
        rows=[{"index":i,"repetition":r,"sample_id":str(i),"segment_sha256":str(i),
            "attempts":1,"retries":0,"ok":True,"correct":True,"request_id":str((r,i)),
            "response_text":"A","response_sha256":hashlib.sha256(b"A").hexdigest(),
            "prediction":"A","finish_reason":"stop","completion_tokens":1,"truncated":False}
            for r in range(1,4) for i in range(127)]
        return inputs,rows
    def test_replay_and_all_request_denominator(self):
        inputs,rows=self.fixtures();candidate=[dict(x) for x in rows]
        candidate[0].update(ok=False,correct=False,error={"type":"failure"})
        result=audit_pair(rows,candidate,inputs,lambda *x:("A",True))
        self.assertEqual(result["candidate"]["correct"],380)
        self.assertEqual(result["candidate"]["failed"],1)
        self.assertLess(result["delta_pp"],0)
    def test_duplicate_missing_score_and_hash_rejected(self):
        for mutation in ({"request_id":str((1,0))},{"correct":False},{"response_sha256":"bad"}):
            inputs,rows=self.fixtures();rows[-1].update(mutation)
            with self.assertRaises(ValueError):audit_arm(rows,inputs,lambda *x:("A",True))
        inputs,rows=self.fixtures()
        with self.assertRaises(ValueError):audit_arm(rows[:-1],inputs,lambda *x:("A",True))
if __name__=="__main__":unittest.main()
