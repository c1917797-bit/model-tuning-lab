import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import direct_round as D
class Round(unittest.TestCase):
 def test_all_direct_round_controls(self):
  import torch
  self.assertTrue(D.controls(torch)['direct_RNE'])
 def test_wrong_scale_head_slot_and_mockcast(self):
  import torch
  t=torch.tensor([[1.,2.,4.],[8.,16.,32.]],dtype=torch.float64)
  for wrong in[D.round_bf16(torch,t*2),D.round_bf16(torch,t.flip(0)),D.round_bf16(torch,t.roll(1,1))]:self.assertGreater(D.peer_error(torch,wrong,t)[0],.00303)
  boundary=torch.tensor([1+2**-8+2**-30],dtype=torch.float64)
  self.assertGreater(D.peer_error(torch,boundary.float().bfloat16(),boundary)[0],.00303)
 def test_bad_metadata_and_state_rejected(self):
  import torch,oracle
  self.assertTrue(all(oracle.boundary_tests(torch).values()));self.assertTrue(all(oracle.sequence_tests(torch).values()))
  with self.assertRaises(ValueError):D.peer_error(torch,torch.ones(2,dtype=torch.bfloat16),torch.ones(1,dtype=torch.float64))
  with self.assertRaises(ValueError):D.peer_error(torch,torch.tensor([float('nan')],dtype=torch.bfloat16),torch.ones(1,dtype=torch.float64))
