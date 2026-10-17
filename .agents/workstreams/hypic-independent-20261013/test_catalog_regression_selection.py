import unittest
from independent_catalog_quality_canary import catalog_canary_plan
class RegressionSelectionTests(unittest.TestCase):
    def rows(self):
        return [dict(index=i,sample_id=str(i),token_ids=list(range(32)),
                     segment=dict(start=4,end=24,tokens_sha256=format(i,"064x")))for i in range(127)]
    def test_first_failed_batch_preserved_then_distinct_next(self):
        r=self.rows();r[8]["segment"]["tokens_sha256"]=r[0]["segment"]["tokens_sha256"]
        p=catalog_canary_plan(r,selection="first_batch_regression")
        self.assertEqual(p["batches"][0],tuple(range(8)))
        self.assertEqual(p["batches"][1],tuple(range(9,17)))
        self.assertEqual(p["private_requests"],17)
        self.assertEqual(p["rebuild_candidates"],tuple(range(8)))
    def test_default_capacity_unchanged(self):
        r=self.rows();self.assertEqual(catalog_canary_plan(r),catalog_canary_plan(r,selection="capacity"))
    def test_unknown_selection_and_duplicate_first_batch_rejected(self):
        for value in (None,True,"random"):
            with self.assertRaises(ValueError):catalog_canary_plan(self.rows(),selection=value)
        r=self.rows();r[1]["segment"]["tokens_sha256"]=r[0]["segment"]["tokens_sha256"]
        with self.assertRaises(ValueError):catalog_canary_plan(r,selection="first_batch_regression")
if __name__=="__main__":unittest.main()
