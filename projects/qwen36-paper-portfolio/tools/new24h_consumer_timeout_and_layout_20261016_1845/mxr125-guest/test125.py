"""Actual FP32 loop/bit-cast controls, not backend qualification."""
import importlib.util,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location(n,P/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NewControls(unittest.TestCase):
 def test_third_round_actual_FP32_trace(self):
  import torch
  torch.set_num_threads(1);V=load('third_residual125')
  A=torch.zeros((1,64,12,64),dtype=torch.float32);X=torch.eye(64).view(64,1,64).expand(64,12,64).unsqueeze(0).contiguous()*.75
  _,groups=V.plan([0,64],64);trace=[];out=V._correct_blocks(torch,A,X,groups,torch.empty_like(A,dtype=torch.bfloat16),V.allocate(torch,A),trace)
  t=trace[0];self.assertEqual(set(t),{'rows','A32','X0','X1','R1','X2','R2','X3','R3'})
  self.assertEqual(t['X3'].dtype,torch.float32);self.assertTrue(torch.equal(t['X3'],t['X2']+torch.bmm(t['X2'],torch.eye(64).expand_as(t['X2'])-t['X2'])))
  self.assertFalse(torch.equal(t['X2'],t['X3']));self.assertEqual(V.budget([0,64],64)['FP32_bmm_launches'],6)
 def test_direct_RNE_boundaries(self):
  import torch,math
  D=load('direct_rne');x=torch.tensor([1+2**-8-2**-30,1+2**-8,1+2**-8+2**-30,-1-2**-8-2**-30,-1-2**-8,-1-2**-8+2**-30,0.,-0.,2**-134,3*2**-134,2**-133,math.inf,-math.inf,2**128],dtype=torch.float64)
  expected=[0x3f80,0x3f80,0x3f81,0xbf81,0xbf80,0xbf80,0,0x8000,0,2,1,0x7f80,0xff80,0x7f80]
  self.assertEqual([int(v)&65535 for v in D.round_bf16(torch,x).view(torch.int16)],expected)
 def test_wrong_scale_head_slot_and_order_rejected_at_anchor(self):
  import torch
  G=load('guest_core');x=torch.arange(24,dtype=torch.float32).reshape(2,3,4);saved=dict(output=x,final_state=x.clone())
  for bad in(x*2,x.flip(1),x.flip(0),x.flip(2)):
   with self.assertRaisesRegex(ValueError,'bitwise anchor'):G.anchored_arms(torch,saved,lambda arm:dict(output=bad,state=x))
if __name__=='__main__':unittest.main()
