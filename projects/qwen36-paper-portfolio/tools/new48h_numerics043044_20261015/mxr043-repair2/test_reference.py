import unittest,torch
import importlib.util
from pathlib import Path
_s=importlib.util.spec_from_file_location('_independent007',Path(__file__).resolve().parent/'independent_reference.py');_m=importlib.util.module_from_spec(_s);_s.loader.exec_module(_m);recurrence=_m.recurrence
class Tests(unittest.TestCase):
 def data(self):
  return dict(q=torch.ones(1,2,1,1),k=torch.ones(1,2,1,1),v=torch.full((1,2,1,1),4.),g=torch.zeros(1,2,1),beta=torch.full((1,2,1),.5),initial_state=torch.full((1,1,1,1),3.),cu_seqlens=torch.tensor([0,2]),scale=1.)
 def test_two_step_state(self):
  o,s=recurrence(torch,self.data());self.assertTrue(torch.equal(o,torch.tensor([[[[3.5]],[[3.75]]]],dtype=torch.float64)));self.assertEqual(s.item(),3.75)
 def test_gqa(self):
  x=self.data();x['v']=x['v'].repeat(1,1,2,1);x['g']=x['g'].repeat(1,1,2);x['beta']=x['beta'].repeat(1,1,2);x['initial_state']=x['initial_state'].repeat(1,2,1,1)
  o,s=recurrence(torch,x);self.assertEqual(tuple(s.shape),(1,2,1,1));self.assertTrue(torch.equal(s,torch.full_like(s,3.75)))
 def test_bad_boundary(self):
  x=self.data();x['cu_seqlens']=torch.tensor([1,2])
  with self.assertRaises(ValueError):recurrence(torch,x)
if __name__=='__main__':unittest.main()
