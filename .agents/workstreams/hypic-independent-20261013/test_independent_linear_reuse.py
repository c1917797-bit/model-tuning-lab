import unittest,torch
from independent_c1_reference import accumulate_segment,serial_dense_oracle
from independent_hybrid_material import MaterialIdentity
from independent_linear_reuse import LinearPublicBody,reuse_linear_segment
class LinearReuseTests(unittest.TestCase):
    def test_live_boundary_then_body_final_state(self):
        torch.manual_seed(10)
        k=torch.randn(8,1,2,dtype=torch.float64)*.1
        v=torch.randn(8,1,3,dtype=torch.float64)
        b=torch.full((8,1),.3,dtype=torch.float64)
        g=torch.full((8,1),.9,dtype=torch.float64)
        identity=MaterialIdentity('m','c','l',0,'a'*64,8,3)
        initial=torch.randn(1,2,3,dtype=torch.float64)
        core=torch.randn(5,1,3,dtype=torch.float64);tail=torch.randn(3,7)
        original=core.clone(); initial_copy=initial.clone()
        material=LinearPublicBody(identity,accumulate_segment(k[3:],v[3:],b[3:],g[3:]),core,tail)
        calls=[]
        def boundary(state):
            calls.append(state)
            return torch.ones(3,1,3,dtype=torch.float64),serial_dense_oracle(k[:3],v[:3],b[:3],g[:3],state)
        output,final,conv=reuse_linear_segment(material,identity,initial,boundary)
        expected=serial_dense_oracle(k,v,b,g,initial)
        torch.testing.assert_close(final,expected,atol=1e-12,rtol=1e-12)
        torch.testing.assert_close(output[3:],core)
        self.assertEqual(len(calls),1)
        self.assertTrue(torch.equal(core,original));self.assertTrue(torch.equal(initial,initial_copy))
        self.assertNotEqual(conv.data_ptr(),tail.data_ptr())
    def test_bad_body_fails_before_boundary(self):
        identity=MaterialIdentity('m','c','l',0,'a'*64,8,3)
        material=LinearPublicBody(identity,None,torch.zeros(4,1,3),torch.zeros(3,7))
        with self.assertRaises(ValueError):
            reuse_linear_segment(material,identity,torch.zeros(1,2,3),lambda s:self.fail('must not run'))
if __name__=='__main__':unittest.main()
