import importlib.util,json,time,unittest,torch
from pathlib import Path
P=Path(__file__).resolve().parent
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fast=load(P/'independent_block_reference.py','_fast008').recurrence
slow=load(P/'independent_reference.py','_slow008').recurrence
class Oracle(unittest.TestCase):
 def case(self,T=71,heads=2,group=2,cu=None):
  gen=torch.Generator().manual_seed(2815+T);q=torch.randn(1,T,heads,4,generator=gen);k=torch.randn(q.shape,generator=gen)
  return dict(q=q/k.new_tensor(2),k=k/k.new_tensor(3),v=torch.randn(1,T,heads*group,3,generator=gen),g=-torch.rand(1,T,heads*group,generator=gen),beta=torch.rand(1,T,heads*group,generator=gen),initial_state=torch.randn(len(cu or [0,T])-1,heads*group,4,3,generator=gen),cu_seqlens=torch.tensor(cu or [0,T]),scale=.5,already_normalized=True)
 def same(self,x,block=64):
  a,s=fast(torch,x,block);b,t=slow(torch,x);torch.testing.assert_close(a,b,rtol=1e-11,atol=1e-11);torch.testing.assert_close(s,t,rtol=1e-11,atol=1e-11)
 def test_nonmultiple(self):self.same(self.case())
 def test_segments(self):self.same(self.case(cu=[0,1,36,71]))
 def test_nonzero_state(self):self.same(self.case(T=2,heads=1,group=1),1)
 def test_invalid_no_normalized(self):
  x=self.case();x.pop('already_normalized')
  with self.assertRaises(ValueError):fast(torch,x)
if __name__=='__main__':torch.set_num_threads(1);unittest.main()
