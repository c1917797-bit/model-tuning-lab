import unittest
import torch
from independent_hybrid_material import MaterialIdentity
from independent_linear_public_builder import build_compact_linear_public_body


class CompactPublicBuilderTests(unittest.TestCase):
    def test_only_body_transitions_and_conv_tail_are_retained(self):
        i=MaterialIdentity('m','c','l',0,'a'*64,8,3)
        keys=torch.zeros(1,8,1,2,dtype=torch.bfloat16)
        values=torch.zeros(1,8,2,3,dtype=torch.bfloat16)
        gates=torch.zeros(1,8,2);projected=torch.ones(8,7,dtype=torch.bfloat16)
        calls=[]
        def runner(q,k,v,g,beta,initial_state,**kwargs):
            calls.append((k.shape[1],v.shape[-1],initial_state.shape))
            return None,initial_state.clone()
        material=build_compact_linear_public_body(i,keys,values,gates,gates,
                                                 projected,state_runner=runner)
        self.assertFalse(hasattr(material,'core_outputs'))
        self.assertEqual([c[0] for c in calls],[5,5])
        self.assertEqual(material.affine.zero_state.shape,(2,2,3))
        self.assertEqual(material.affine.transition.shape,(2,2,2))
        projected.zero_();self.assertTrue(material.conv_tail.bool().all())


if __name__=='__main__':unittest.main()
