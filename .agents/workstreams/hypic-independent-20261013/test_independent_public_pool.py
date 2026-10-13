import unittest
import torch
from independent_public_pool import PublicPool,material_key
class PoolTests(unittest.TestCase):
    def test_oversize_rejected_before_clone(self):
        class Oversize:
            def numel(self):return 100
            def element_size(self):return 4
            def detach(self):raise AssertionError("must reject before allocation")
        with self.assertRaises(ValueError):PublicPool(16).publish('large',{'s':Oversize()})
    def test_exception_releases_pin_and_generation_advances(self):
        p=PublicPool(16);g1=p.publish('a',{'s':torch.ones(4)})
        with self.assertRaises(RuntimeError):
            with p.acquire_private('a'):raise RuntimeError("request abort")
        g2=p.publish('b',{'s':torch.ones(4)})
        self.assertGreater(g2,g1)
        self.assertEqual(list(p.entries),['b'])
    def test_private_and_producer_writes_do_not_change_public(self):
        p=PublicPool(64);x=torch.ones(4);p.publish('a',{'k':x});x.zero_()
        with p.acquire_private('a') as (_,a):a['k'].zero_()
        with p.acquire_private('a') as (_,a):self.assertTrue(torch.equal(a['k'],torch.ones(4)))
    def test_pin_prevents_eviction_and_failure_preserves_pool(self):
        p=PublicPool(16);p.publish('a',{'s':torch.ones(4)})
        with p.acquire_private('a'):
            with self.assertRaises(BufferError):p.publish('b',{'s':torch.ones(4)})
            self.assertEqual(list(p.entries),['a'])
        p.publish('b',{'s':torch.ones(4)});self.assertEqual(list(p.entries),['b'])
    def test_identity_includes_model_code_and_context(self):
        a=material_key('m','v',[1,2],'c')
        self.assertNotEqual(a,material_key('m','v',[1,2],'other'))
        self.assertNotEqual(a,material_key('m','v2',[1,2],'c'))
        self.assertNotEqual(a,material_key('m2','v',[1,2],'c'))
if __name__=='__main__':unittest.main()
