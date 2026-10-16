import copy,hashlib,unittest
from independent_quality_schedule import quality_schedule
from audit_full_quality_cohort import audit_full_quality_cohort
class Tests(unittest.TestCase):
    def fixture(self):
        rows=[dict(index=i,sample_id=str(i),reference="A",segment=dict(tokens_sha256=str(i),start=8,end=24))for i in range(127)]
        results=[];journal=[]
        for block in quality_schedule(rows,batch_samples=8):
            rep=block["repetition"];batch=block["batch"]
            for digest in block["producer_digests"]:
                journal.append(dict(event="quality-public-producer",scored=False,repetition=rep,batch=batch,segment_sha256=digest,
                    response=dict(id=f"producer-{rep}-{digest}",usage=dict(prompt_tokens=16,completion_tokens=1),choices=[dict(finish_reason="stop")])))
            for index in block["sample_indexes"]:
                text="A"if index%2 else "B"
                r=dict(index=index,repetition=rep,sample_id=str(index),segment_sha256=str(index),attempts=1,retries=0,ok=True,
                    request_id=f"private-{rep}-{index}",response_text=text,response_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    prediction=text,correct=text=="A",completion_tokens=1,finish_reason="stop",truncated=False)
                results.append(r);journal.append(dict(r,event="quality-scored-response",scored=True))
        return rows,dict(requests=381,successful=381,retries=0,concurrency_bound=8,correct=sum(r["correct"]for r in results),results=results),journal
    def score(self,dataset,text,reference):return text,text==reference
    def audit(self,*a):return audit_full_quality_cohort(*a,score=self.score)
    def test_full381(self):
        out=self.audit(*self.fixture());self.assertEqual(out["requests"],381);self.assertEqual(out["correct"],189)
    def reject(self,fn):
        rows,u,j=self.fixture();fn(rows,u,j)
        with self.assertRaises(ValueError):self.audit(rows,u,j)
    def test_missing_sample(self):self.reject(lambda rows,u,j:u["results"].pop())
    def test_duplicate_round(self):self.reject(lambda rows,u,j:u["results"][-1].update(repetition=1))
    def test_fake_score(self):self.reject(lambda rows,u,j:u["results"][0].update(correct=True))
    def test_fake_prediction(self):self.reject(lambda rows,u,j:u["results"][0].update(prediction="A"))
    def test_hidden_retry(self):self.reject(lambda rows,u,j:u["results"][0].update(retries=1))
    def test_duplicate_api(self):self.reject(lambda rows,u,j:u["results"][1].update(request_id=u["results"][0]["request_id"]))
    def test_missing_producer(self):self.reject(lambda rows,u,j:j.pop(0))
    def test_scored_producer(self):self.reject(lambda rows,u,j:j[0].update(scored=True))
    def test_journal_output_drift(self):self.reject(lambda rows,u,j:next(e for e in j if e["event"]=="quality-scored-response").update(response_text="changed"))
    def test_output_hash(self):self.reject(lambda rows,u,j:u["results"][0].update(response_sha256="wrong"))
    def test_aggregate(self):self.reject(lambda rows,u,j:u.update(correct=381))
    def test_truncation_not_hidden(self):
        rows,u,j=self.fixture();r=u["results"][0];r.update(finish_reason="length",completion_tokens=1024,truncated=True)
        next(e for e in j if e["event"]=="quality-scored-response").update(r)
        self.assertEqual(self.audit(rows,u,j)["truncated"],1)
    def test_order(self):self.reject(lambda rows,u,j:j.reverse())
if __name__=="__main__":unittest.main()
