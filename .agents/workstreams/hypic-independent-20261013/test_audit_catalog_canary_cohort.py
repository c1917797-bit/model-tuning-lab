import copy,hashlib,unittest
from audit_catalog_canary_cohort import audit_canary_cohort
from independent_catalog_quality_canary import catalog_canary_plan
class Tests(unittest.TestCase):
    def fixture(self):
        rows=[dict(index=i,sample_id=str(i),token_ids=[i]*32,segment=dict(start=8,end=24,tokens_sha256=str(i)))for i in range(127)]
        p=catalog_canary_plan(rows);selected=p["initial_indexes"][0];batches=[*p["batches"],(selected,)];journal=[];results=[]
        for phase,indexes in enumerate(batches):
            if phase==2:journal.append(dict(event="catalog-canary-rebuild-selected",scored=False,index=selected,segment_sha256=str(selected)))
            journal.append(dict(event="catalog-canary-phase-start",scored=False,phase=phase,indexes=list(indexes)))
            for i in indexes:journal.append(dict(event="catalog-canary-producer",scored=False,phase=phase,index=i,segment_sha256=str(i),
                response=dict(id=f"producer-{phase}-{i}",usage=dict(prompt_tokens=16,completion_tokens=1),choices=[dict(finish_reason="stop")])))
            for i in indexes:
                r=dict(index=i,phase=phase,sample_id=str(i),segment_sha256=str(i),attempts=1,retries=0,ok=True,
                    request_id=f"private-{phase}-{i}",response_text="",response_sha256=hashlib.sha256(b"").hexdigest(),completion_tokens=1,finish_reason="stop",correct=False)
                results.append(r);journal.append(dict(r,event="catalog-canary-response",scored=False))
        return dict(requests=17,successful=17,full_quality=False,initial_indexes=list(p["initial_indexes"]),results=results),journal,rows
    def test_complete(self):self.assertEqual(audit_canary_cohort(*self.fixture())["private_responses"],17)
    def reject(self,fn):
        u,j,r=self.fixture();fn(u,j,r)
        with self.assertRaises(ValueError):audit_canary_cohort(u,j,r)
    def test_full_quality_false_required(self):self.reject(lambda u,j,r:u.update(full_quality=True))
    def test_missing_response(self):self.reject(lambda u,j,r:u["results"].pop())
    def test_journal_drift(self):self.reject(lambda u,j,r:next(x for x in j if x["event"]=="catalog-canary-response").update(completion_tokens=2))
    def test_extra_scoring(self):self.reject(lambda u,j,r:j[0].update(scored=True))
    def test_wrong_order(self):self.reject(lambda u,j,r:j.reverse())
    def test_hidden_retry(self):self.reject(lambda u,j,r:u["results"][0].update(retries=1))
    def test_hash_drift(self):self.reject(lambda u,j,r:u["results"][0].update(response_sha256="wrong"))
    def test_producer_missing(self):self.reject(lambda u,j,r:j.remove(next(x for x in j if x["event"]=="catalog-canary-producer")))
    def test_duplicate_api(self):self.reject(lambda u,j,r:u["results"][1].update(request_id=u["results"][0]["request_id"]))
if __name__=="__main__":unittest.main()
