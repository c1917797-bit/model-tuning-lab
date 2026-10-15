import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import precast as P
class Empirical(unittest.TestCase):
 def test_all_negative_controls(self):
  import torch
  from direct_round import round_bf16
  t=torch.tensor([[1.,2.,4.],[8.,16.,32.]],dtype=torch.float64);y=t.float();z=round_bf16(torch,y.double())
  self.assertTrue(P.evaluate(torch,y,z,t)['passed'])
  for bad in(y*2,y.flip(0),y.roll(1,1),y*1.001):self.assertFalse(P.evaluate(torch,bad,round_bf16(torch,bad.double()),t)['passed'])
  self.assertFalse(P.evaluate(torch,y,z.flip(0),t)['passed'])
  self.assertFalse(P.evaluate(torch,torch.full_like(y,float('nan')),z,t)['passed'])
  self.assertFalse(P.evaluate(torch,torch.ones(1),torch.ones(1,dtype=torch.bfloat16),torch.ones(1,dtype=torch.float64)*2)['passed'])
 def test_signed_zero_and_zero_truth(self):
  import torch
  self.assertFalse(P.evaluate(torch,torch.tensor([-0.]),torch.tensor([0.],dtype=torch.bfloat16),torch.tensor([0.],dtype=torch.float64))['passed'])
  self.assertFalse(P.evaluate(torch,torch.tensor([1e-30]),torch.tensor([0.],dtype=torch.bfloat16),torch.tensor([0.],dtype=torch.float64))['passed'])
 def test_bad_shape_and_broadA(self):
  import torch
  with self.assertRaises(ValueError):P.evaluate(torch,torch.ones(2),torch.ones(1,dtype=torch.bfloat16),torch.ones(1,dtype=torch.float64))
  self.assertFalse(P.evaluate(torch,torch.tensor([2.]),torch.tensor([2.],dtype=torch.bfloat16),torch.tensor([1.],dtype=torch.float64))['passed'])
 def test_actual_loader_does_not_require_numerical_manifest(self):
  import io_contract as C
  p=pathlib.Path(__file__).resolve().parent/'precast.py'
  self.assertEqual(C.load(C.ref(p),'_actual016_load_control').L2,2**-13)
 def test_large_request_cannot_mask_small_request(self):
  import torch
  from direct_round import round_bf16
  t=torch.tensor([[1e6,2e6],[1.,2.]],dtype=torch.float64);y=t.float();y[1]*=1.01;r=P.evaluate(torch,y,round_bf16(torch,y.double()),t)
  self.assertTrue(r['whole_batch_diagnostic']['passed']);self.assertTrue(r['requests'][0]['passed']);self.assertFalse(r['requests'][1]['passed']);self.assertFalse(r['passed'])
if __name__=='__main__':unittest.main()
