import unittest
import torch
from independent_c1_official_bridge import official_segment_affine
from independent_c1_reference import accumulate_segment
class BridgeTests(unittest.TestCase):
    def test_dual_invocation_math_and_grouping(self):
        torch.manual_seed(41)
        k=torch.randn(1,17,2,8,dtype=torch.bfloat16)
        v=torch.randn(1,17,4,8,dtype=torch.bfloat16)
        g=-torch.rand(1,17,4)*.1;beta=torch.rand(1,17,4)
        calls=[]
        def runner(q,k,v,g,beta,initial_state,**kw):
            self.assertEqual(k.shape[2],v.shape[2])
            calls.append(kw)
            kn=torch.nn.functional.normalize(k[0].float(),dim=-1)
            ref=accumulate_segment(kn,v[0].float(),beta[0],g[0].exp())
            return None,(ref.transition@initial_state[0]+ref.zero_state)[None]
        got=official_segment_affine(runner,k,v,g,beta)
        ref=accumulate_segment(torch.nn.functional.normalize(k[0].float(),dim=-1),v[0].float(),beta[0],g[0].exp())
        torch.testing.assert_close(got.transition,ref.transition)
        torch.testing.assert_close(got.zero_state,ref.zero_state)
        self.assertEqual(len(calls),2)
        self.assertTrue(all(x['use_qk_l2norm_in_kernel'] for x in calls))
    def test_float32_data_rejected(self):
        k=torch.zeros(1,4,1,8);v=k.clone();g=torch.zeros(1,4,1)
        with self.assertRaises(ValueError):official_segment_affine(None,k,v,g,g)
if __name__=='__main__':unittest.main()
