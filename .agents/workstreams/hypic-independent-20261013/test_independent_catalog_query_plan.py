import unittest
from independent_request_map import RequestSlice
from independent_segment_catalog import SegmentCatalog
from independent_catalog_query_plan import plan_catalog_batch
from independent_mixed_query_plan import NativeQueryPlan
class CatalogQueryPlanTests(unittest.TestCase):
    def test_distinct_lengths_and_cold_material_in_same_batch(self):
        a=tuple(range(16));b=tuple(range(100,124));catalog=SegmentCatalog([a,b])
        requests=[RequestSlice("a",0,1,0,20,0,0,20),
                  RequestSlice("b",0,1,0,28,1,20,48)]
        prompts={"a":(999,)+a+(999,)*3,"b":(999,)+b+(999,)*3}
        plans=plan_catalog_batch(requests,prompts,catalog,catalog.entries)
        self.assertEqual([p.skipped_tokens for p in plans],[8,16])
        self.assertNotEqual(plans[0].tokens_sha256,plans[1].tokens_sha256)
        plans=plan_catalog_batch(requests,prompts,catalog,[plans[0].tokens_sha256])
        self.assertIsInstance(plans[1],NativeQueryPlan)
        self.assertEqual(plans[1].reason,"cold-material")
    def test_unknown_material_digest_rejected(self):
        with self.assertRaises(ValueError):
            plan_catalog_batch([],{},SegmentCatalog([range(16)]),["unknown"])
    def test_canonical_prefix_remains_native_producer(self):
        catalog=SegmentCatalog([range(16)])
        req=RequestSlice("r",0,1,0,20,0,0,20)
        p=plan_catalog_batch([req],{"r":tuple(range(16))+(999,)*4},catalog,catalog.entries)[0]
        self.assertIsInstance(p,NativeQueryPlan);self.assertEqual(p.reason,"public-producer")
if __name__=="__main__":unittest.main()
