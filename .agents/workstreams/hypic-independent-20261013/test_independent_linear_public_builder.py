import unittest,torch
from independent_hybrid_material import MaterialIdentity
from independent_linear_public_builder import build_linear_public_body
class PublicBuilderTests(unittest.TestCase):
    def tensors(self):
        return [torch.zeros(1,8,1,2,dtype=torch.bfloat16),
                torch.zeros(1,8,2,3,dtype=torch.bfloat16),
                torch.zeros(1,8,2),torch.zeros(1,8,2),
                torch.ones(1,8,2,3,dtype=torch.bfloat16),
                torch.ones(8,7,dtype=torch.bfloat16)]
    def test_body_only_and_private_storage(self):
        identity=MaterialIdentity('m','c','l',0,'a'*64,8,3);inputs=self.tensors();calls=[]
        def state_runner(q,k,v,g,beta,initial_state,**kw):
            calls.append((k.shape,v.shape))
            return None,initial_state.clone()
        material=build_linear_public_body(identity,*inputs,state_runner=state_runner)
        self.assertEqual(len(calls),2);self.assertEqual(calls[0][0][1],5)
        self.assertEqual(material.core_outputs.shape,(5,2,3))
        inputs[4].zero_();inputs[5].zero_()
        self.assertTrue(material.core_outputs.bool().all())
        self.assertTrue(material.conv_tail.bool().all())
    def test_missing_public_tokens_rejected(self):
        identity=MaterialIdentity('m','c','l',0,'a'*64,8,3);inputs=self.tensors()
        inputs[0]=inputs[0][:,:7]
        with self.assertRaises(ValueError):
            build_linear_public_body(identity,*inputs,state_runner=lambda *a,**k:self.fail())
if __name__=='__main__':unittest.main()
