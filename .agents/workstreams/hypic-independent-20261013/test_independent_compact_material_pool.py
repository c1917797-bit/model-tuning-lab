import unittest
import torch
from independent_c1_reference import SegmentAffine
from independent_hybrid_material import MaterialIdentity
from independent_compact_material_pool import CompactLinearBody,CompactLinearMaterialPool
from independent_linear_material_pool import identity_key


class CompactPoolTests(unittest.TestCase):
    def test_cpu_storage_contains_only_compact_state_and_is_private(self):
        i=MaterialIdentity('m','c','layer',0,'a'*64,16384,8)
        t=torch.eye(4).expand(2,4,4).clone();s=torch.ones(2,4,3);c=torch.ones(3,6)
        pool=CompactLinearMaterialPool(1024);m=CompactLinearBody(i,SegmentAffine(t,s),c)
        pool.publish(m);t.zero_()
        self.assertEqual(pool.pool.used,(32+24+18)*4)
        self.assertEqual(set(pool.pool.entries[identity_key(i)]['data']),{'transition','zero_state','conv_tail'})
        with pool.acquire_private(i,device='cpu') as (_,private):private.affine.zero_state.zero_()
        with pool.acquire_private(i,device='cpu') as (_,private):
            self.assertEqual(float(private.affine.zero_state.sum()),24.)
            self.assertEqual(float(private.affine.transition.sum()),8.)
    def test_disabled_hook_does_not_import_device_runtime(self):
        from independent_compact_gdn_hook import install_compact_gdn
        install_compact_gdn(None,enabled=False)()


if __name__=='__main__':unittest.main()
