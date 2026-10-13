import unittest,torch
from dataclasses import replace
from independent_hybrid_material import MaterialIdentity,materialize_linear_body,materialize_attention_body
from independent_c1_reference import SegmentAffine
class MaterialTests(unittest.TestCase):
    def setUp(self):self.identity=MaterialIdentity('model','code','layer',0,'a'*64,12,8)
    def test_linear_consumes_live_boundary_state(self):
        s=SegmentAffine(torch.eye(2)[None]*.5,torch.ones(1,2,2))
        out=materialize_linear_body(self.identity,self.identity,s,torch.ones(1,2,2)*4)
        torch.testing.assert_close(out,torch.ones(1,2,2)*3)
    def test_wrong_rank_or_boundary_rejected(self):
        for bad in [replace(self.identity,rank=1),replace(self.identity,boundary_tokens=3)]:
            with self.assertRaises(ValueError):materialize_linear_body(bad,self.identity,None,None)
    def test_attention_returns_private_body(self):
        k=torch.ones(4,1,8);v=k.clone();pos=torch.arange(4)
        pk,pv=materialize_attention_body(self.identity,self.identity,k,v,pos,pos+10,torch.tensor([1.,.1]))
        self.assertNotEqual(pk.data_ptr(),k.data_ptr());self.assertNotEqual(pv.data_ptr(),v.data_ptr())
        self.assertTrue(torch.equal(k,torch.ones_like(k)))
if __name__=='__main__':unittest.main()
