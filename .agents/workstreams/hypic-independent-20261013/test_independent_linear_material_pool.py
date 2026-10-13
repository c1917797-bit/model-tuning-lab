import unittest,torch
from dataclasses import replace
from independent_linear_material_pool import LinearMaterialPool
from independent_linear_reuse import LinearPublicBody
from independent_hybrid_material import MaterialIdentity
from independent_c1_reference import SegmentAffine
class LinearPoolTests(unittest.TestCase):
    def material(self):
        i=MaterialIdentity('m','c','l',0,'a'*64,8,3)
        return LinearPublicBody(i,SegmentAffine(torch.eye(2)[None],torch.zeros(1,2,3)),
                                torch.ones(5,1,3),torch.ones(3,7))
    def test_private_mutation_does_not_change_public(self):
        m=self.material();p=LinearMaterialPool(1024);g=p.publish(m)
        m.core_outputs.zero_()
        with p.acquire_private(m.identity) as (actual,copy):
            self.assertEqual(actual,g);self.assertTrue(copy.core_outputs.bool().all())
            copy.core_outputs.zero_()
        with p.acquire_private(m.identity) as (_,copy):
            self.assertTrue(copy.core_outputs.bool().all())
    def test_wrong_code_cannot_acquire(self):
        m=self.material();p=LinearMaterialPool(1024);p.publish(m)
        with self.assertRaises(KeyError):
            with p.acquire_private(replace(m.identity,code='other')):pass
if __name__=='__main__':unittest.main()
