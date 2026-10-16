import unittest
from independent_catalog_rebuild_selection import choose_evicted_rebuild
class Tests(unittest.TestCase):
    def pub(self,rank=0,digest="a",key="k",generation=1):
        return dict(event="compact_public_kv_published",manifest_sha256="m",rank=rank,pid=rank+100,
                    pool="kv",key=key,generation=generation,tokens_sha256=digest,layer="l")
    def evict(self,p):return dict(p,event="compact_public_material_evicted")
    def test_real_prior_eviction_selected(self):
        p=self.pub();self.assertEqual(choose_evicted_rebuild([p,self.evict(p)],"m",[dict(index=48,tokens_sha256="a")]),48)
    def test_missing_material_not_eviction(self):
        with self.assertRaises(ValueError):choose_evicted_rebuild([],"m",[dict(index=48,tokens_sha256="a")])
    def test_wrong_generation(self):
        p=self.pub()
        with self.assertRaises(ValueError):choose_evicted_rebuild([p,dict(self.evict(p),generation=2)],"m",[dict(index=48,tokens_sha256="a")])
    def test_wrong_worker(self):
        p=self.pub()
        with self.assertRaises(ValueError):choose_evicted_rebuild([p,dict(self.evict(p),pid=999)],"m",[dict(index=48,tokens_sha256="a")])
    def test_wrong_manifest(self):
        p=self.pub()
        with self.assertRaises(ValueError):choose_evicted_rebuild([p,self.evict(p)],"other",[dict(index=48,tokens_sha256="a")])
    def test_other_segment_eviction_not_selected(self):
        p=self.pub(digest="b")
        with self.assertRaises(ValueError):choose_evicted_rebuild([p,self.evict(p)],"m",[dict(index=48,tokens_sha256="a")])
    def test_frozen_order(self):
        p=self.pub();q=self.pub(digest="b",key="q",generation=2)
        self.assertEqual(choose_evicted_rebuild([p,q,self.evict(q),self.evict(p)],"m",
            [dict(index=48,tokens_sha256="a"),dict(index=0,tokens_sha256="b")]),48)
    def test_rebuilt_complete_material_not_selected(self):
        p=self.pub();events=[p,self.evict(p)]
        for rank in range(4):
            for pool,n in (("linear",48),("kv",16)):
                for i in range(n):
                    x=self.pub(rank,key=pool+str(i),generation=i+2)
                    x.update(pool=pool,layer=pool+str(i),event="compact_public_state_published" if pool=="linear" else "compact_public_kv_published")
                    events.append(x)
        with self.assertRaises(ValueError):choose_evicted_rebuild(events,"m",[dict(index=48,tokens_sha256="a")])
if __name__=="__main__":unittest.main()
