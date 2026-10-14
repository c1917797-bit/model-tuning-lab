import unittest,torch
from independent_recurrent_boundary import recurrent_boundary
from independent_c1_reference import serial_dense_oracle
class RecurrentBoundaryTests(unittest.TestCase):
    def test_final_against_dense_oracle(self):
        torch.manual_seed(31);q=torch.randn(1,8,1,2,dtype=torch.float64)
        k=torch.randn_like(q);v=torch.randn(1,8,2,3,dtype=torch.float64)
        g=torch.full((1,8,2),-.1,dtype=torch.float64)
        b=torch.full((1,8,2),.3,dtype=torch.float64)
        initial=torch.randn(1,2,2,3,dtype=torch.float64)
        output,state=recurrent_boundary(q,k,v,g,b,initial)
        normalized=k[0]*torch.rsqrt((k[0]*k[0]).sum(-1,keepdim=True)+1e-6)
        expected=serial_dense_oracle(normalized,v[0],b[0],g[0].exp(),initial[0])
        torch.testing.assert_close(state[0],expected,atol=1e-12,rtol=1e-12)
        self.assertEqual(output.shape,(1,8,2,3))
    def test_output_each_step_oracle(self):
        q=torch.ones(1,3,1,2,dtype=torch.float64);v=torch.ones(1,3,1,2,dtype=torch.float64)
        b=torch.full((1,3,1),.2,dtype=torch.float64);g=torch.zeros_like(b)
        output,_=recurrent_boundary(q,q,v,g,b,torch.zeros(1,1,2,2,dtype=torch.float64))
        key=q[0]*torch.rsqrt((q[0]*q[0]).sum(-1,keepdim=True)+1e-6)
        for i in range(3):
            state=serial_dense_oracle(key[:i+1],v[0,:i+1],b[0,:i+1],g[0,:i+1].exp(),torch.zeros(1,2,2,dtype=torch.float64))
            expected=(key[i].unsqueeze(-2)@state).squeeze(-2)/(2**.5)
            torch.testing.assert_close(output[0,i],expected)
if __name__=='__main__':unittest.main()
