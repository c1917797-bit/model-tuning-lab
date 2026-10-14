import unittest
from types import SimpleNamespace
from independent_segment_catalog import SegmentCatalog
from independent_plan_material_identity import identity_for_plan
class PlanMaterialIdentityTests(unittest.TestCase):
    def test_exact_digest_and_length_not_first_catalog_entry(self):
        c=SegmentCatalog([range(16),range(100,124)])
        digests=list(c.entries)
        stage=SimpleNamespace(catalog=c,model="model",code="code",boundary=8)
        a=identity_for_plan(stage,"layer",SimpleNamespace(rank=1,tokens_sha256=digests[0]))
        b=identity_for_plan(stage,"layer",SimpleNamespace(rank=1,tokens_sha256=digests[1]))
        self.assertEqual((a.length,b.length),(16,24));self.assertNotEqual(a.tokens_sha256,b.tokens_sha256)
        with self.assertRaises(ValueError):
            identity_for_plan(stage,"layer",SimpleNamespace(rank=1,tokens_sha256="unknown"))
    def test_single_segment_route_preserved(self):
        marker=object();stage=SimpleNamespace(identity=lambda layer,rank:marker)
        self.assertIs(identity_for_plan(stage,"layer",SimpleNamespace(rank=0)),marker)
if __name__=="__main__":unittest.main()
