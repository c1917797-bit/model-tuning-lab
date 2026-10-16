import copy,unittest
from audit_catalog_rebuild_chain import audit_rebuild_chain
import test_audit_catalog_quality_hot as hot_fixtures
class Tests(unittest.TestCase):
    def fixture(self):
        e,r,rows=hot_fixtures.Tests().fixture(2);out=[]
        for rank in range(4):
            part=[x for x in e if x["rank"]==rank]
            at=next(i for i,x in enumerate(part) if x.get("request_id")=="api-1-runtime")
            # Model completion precedes rebuilt layer receipts but does not affect this chain.
            old=next(x for x in part if x["event"]=="compact_public_kv_published")
            eviction=dict(old,event="compact_public_material_evicted")
            fresh=dict(old,generation=1000)
            part[at:at]=[eviction,fresh]
            for x in part:
                if x.get("request_id")=="api-1-runtime" and x["event"]=="compact_c2_queries_completed" and x["layer"]==old["layer"]:x["generation"]=1000
            out.extend(part)
        return out
    def audit(self,e):
        return audit_rebuild_chain(e,manifest_sha256="m",initial_api="api-0",rebuild_api="api-1",tokens_sha256="segA")
    def test_complete(self):self.assertEqual(len(self.audit(self.fixture())["transitions"]),4)
    def reject(self,fn):
        e=self.fixture();fn(e)
        with self.assertRaises(ValueError):self.audit(e)
    def test_no_eviction(self):self.reject(lambda e:e.__setitem__(slice(None),[x for x in e if x["event"]!="compact_public_material_evicted"]))
    def test_one_rank_not_evicted(self):self.reject(lambda e:e.remove(next(x for x in e if x["event"]=="compact_public_material_evicted")))
    def test_old_generation_reused(self):self.reject(lambda e:next(x for x in e if x.get("request_id")=="api-1-runtime" and x["event"]=="compact_c2_queries_completed").update(generation=1))
    def test_new_producer_missing(self):self.reject(lambda e:e.remove(next(x for x in e if x["event"]=="compact_public_kv_published" and x["generation"]==1000)))
    def test_initial_hot_missing(self):self.reject(lambda e:e.remove(next(x for x in e if x.get("request_id")=="api-0-runtime" and x["event"]=="compact_c2_queries_completed")))
    def test_worker_drift(self):self.reject(lambda e:next(x for x in e if x["event"]=="compact_public_kv_published" and x["generation"]==1000).update(pid=999))
    def test_source_drift(self):self.reject(lambda e:e[0].update(manifest_sha256="wrong"))
    def test_other_segment(self):self.reject(lambda e:next(x for x in e if x["event"]=="compact_public_kv_published" and x["generation"]==1000).update(tokens_sha256="other"))
if __name__=="__main__":unittest.main()
