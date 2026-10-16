import copy,unittest
from audit_catalog_quality_hot import audit_catalog_hot
class Tests(unittest.TestCase):
    def fixture(self,count=2):
        rows=[{"index":i,"segment":{"tokens_sha256":"segA","start":8,"end":24}} for i in range(127)]
        results=[{"ok":True,"request_id":"api-"+str(i),"index":i%127,"segment_sha256":"segA"} for i in range(count)]
        events=[]
        for rank in range(4):
            shared=dict(rank=rank,pid=100+rank,manifest_sha256="m")
            for pool,n,kind in (("linear",48,"compact_public_state_published"),("kv",16,"compact_public_kv_published")):
                for l in range(n):
                    layer=pool+str(l);events.append(dict(shared,event=kind,key=layer,layer=layer,generation=l+1,tokens_sha256="segA",pool=pool))
            for i in range(count):
                rid="api-"+str(i)+"-runtime";step=i+1
                events.append(dict(shared,event="native_request_progress",request_id=rid,step=step,scheduled_tokens=64,computed_tokens=0))
                events.append(dict(shared,event="compact_model_rows_completed",request_ids=[rid],step=step,original_rows=64,retained_rows=56))
                for pool,n,kind,skip in (("linear",48,"compact_gdn_body_composed","skipped_body_tokens"),("kv",16,"compact_c2_queries_completed","skipped_body_queries")):
                    for l in range(n):
                        events.append(dict(shared,event=kind,request_id=rid,step=step,layer=pool+str(l),generation=l+1,retained_rows=56,finite=True,**{skip:8}))
        return events,results,rows
    def run_fixture(self,e,r,rows,count=None):
        return audit_catalog_hot(e,r,rows,manifest_sha256="m",expected_count=len(r) if count is None else count)
    def test_complete(self):
        e,r,rows=self.fixture();out=self.run_fixture(e,r,rows)
        self.assertEqual(out["generation_links"],2*4*64);self.assertEqual(out["denominator"],2)
    def test_full381_cohort(self):
        e,r,rows=self.fixture(381);out=self.run_fixture(e,r,rows)
        self.assertEqual(out["generation_links"],381*4*64)
    def reject(self,mutate):
        e,r,rows=self.fixture();mutate(e,r,rows)
        with self.assertRaises(ValueError):self.run_fixture(e,r,rows)
    def hot(self,e):return next(x for x in e if x["event"]=="compact_gdn_body_composed")
    def test_missing_layer(self):self.reject(lambda e,r,rows:e.remove(self.hot(e)))
    def test_wrong_generation(self):self.reject(lambda e,r,rows:self.hot(e).update(generation=9999))
    def test_wrong_segment(self):self.reject(lambda e,r,rows:e[0].update(tokens_sha256="segB"))
    def test_stale_evicted_generation(self):
        def mutate(e,r,rows):
            e.insert(64,dict(event="compact_public_material_evicted",rank=0,pid=100,manifest_sha256="m",pool="linear",key="linear0",generation=1))
        self.reject(mutate)
    def test_wrong_step(self):self.reject(lambda e,r,rows:self.hot(e).update(step=9999))
    def test_wrong_source(self):self.reject(lambda e,r,rows:self.hot(e).update(manifest_sha256="wrong"))
    def test_wrong_pid(self):self.reject(lambda e,r,rows:self.hot(e).update(pid=9999))
    def test_wrong_skip(self):self.reject(lambda e,r,rows:self.hot(e).update(skipped_body_tokens=7))
    def test_missing_response(self):
        e,r,rows=self.fixture()
        with self.assertRaises(ValueError):self.run_fixture(e,r[:-1],rows,count=2)
    def test_duplicate_api(self):self.reject(lambda e,r,rows:r[1].update(request_id=r[0]["request_id"]))
    def test_duplicate_hot(self):self.reject(lambda e,r,rows:e.append(copy.deepcopy(self.hot(e))))
    def test_wrong_model_pruning(self):
        self.reject(lambda e,r,rows:next(x for x in e if x["event"]=="compact_model_rows_completed").update(retained_rows=55))
if __name__=="__main__":unittest.main()
