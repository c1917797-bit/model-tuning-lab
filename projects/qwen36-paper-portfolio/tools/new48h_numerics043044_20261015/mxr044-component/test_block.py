import importlib.util,os,unittest
from pathlib import Path
import torch
P=Path(__file__).resolve().parent
def load(name):
 s=importlib.util.spec_from_file_location('_044'+name,P/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('block_refine');torch.set_num_threads(1)
def input_pair(cu):
 T=cu[-1];A=torch.zeros((1,T,12,64));X=torch.zeros_like(A);g=torch.Generator().manual_seed(2610154401)
 for _,start,n in M.plan(cu,T)[0]:
  ix=torch.arange(n);X[0,start+ix,:,ix]=1
  if n>1:
   A[0,start+1,:,0]=torch.randn((12,),generator=g)*.1;X[0,start+1,:,0]=-A[0,start+1,:,0].half().float()
 return A,X
class Block(unittest.TestCase):
 def test_registered_numeric_tail_coverage(self):
  Q=load('qualification_probe');cases=Q.recipes();self.assertEqual(len(cases),9);self.assertEqual({(b-a)%64 for _,cu in cases[5:]for a,b in zip(cu,cu[1:])},set(range(64)))
 def test_real_backing_storage_counted(self):
  storage=torch.zeros((1,100,12,64));A=storage[:,:1];cu_storage=torch.tensor([0,1,2,3],dtype=torch.int32);cu=cu_storage[:2];b=M.budget([0,1],1)
  self.assertEqual(M.storage_budget(A,cu,b)-b['keepalive_bytes'],storage.numel()*4-A.numel()*4+8)
 def test_exact_budget_32k_and_max_varlen(self):
  a=M.budget([0,32768],32768);self.assertEqual(a['groups'],8);self.assertEqual(a['FP32_bmm_launches'],16);self.assertEqual(a['official037_launches'],1);self.assertGreater(a['keepalive_bytes'],32*1024**2)
  lengths=[2049]*15+[10225];cu=[0]
  for n in lengths:cu.append(cu[-1]+n)
  b=M.budget(cu,40960);self.assertEqual(b['chunks'],655);self.assertEqual(b['groups'],19);self.assertTrue(b['formal_one_live_fit']);self.assertFalse(b['formal_two_live_fit'])
  A=torch.empty((1,1,12,64));scratch=M.allocate(torch,A);self.assertEqual(sum(v.numel()*v.element_size()for v in scratch.values()),b['scratch_bytes'])
 def test_full_longest_real_geometry_and_mixed_tails(self):
  for cu in ([0,32768],[0,32768,40960],[0]+[2049*i for i in range(1,16)]+[40960]):
   A,X=input_pair(cu);before=A.clone();out=M.cpu_with_X0(torch,A,X,cu)
   # Independent nilpotent strict-lower A has A^2=0: inverse is I-A.
   expected=torch.zeros_like(out)
   for _,start,n in M.plan(cu,cu[-1])[0]:
    ix=torch.arange(n);expected[0,start+ix,:,ix]=1
    if n>1:expected[0,start+1,:,0]=-A[0,start+1,:,0].bfloat16()
   self.assertTrue(torch.equal(before,A));self.assertTrue(torch.equal(out,expected))
 def test_small_case_monolithic_same_math(self):
  A,X=input_pair([0,129]);out=M.cpu_with_X0(torch,A,X,[0,129]);rows,_=M.plan([0,129],129);ap=torch.zeros((36,64,64));xp=torch.eye(64).expand(36,64,64).clone()
  for i,(_,start,n)in enumerate(rows):ap[i*12:(i+1)*12,:n]=A[0,start:start+n].permute(1,0,2);xp[i*12:(i+1)*12,:n,:n]=X[0,start:start+n,:,:n].permute(1,0,2)
  eye=torch.eye(64);R=eye-torch.bmm(eye+ap,xp);X1=xp+torch.bmm(xp,R);expected=torch.zeros_like(out)
  for i,(_,start,n)in enumerate(rows):expected[0,start:start+n,:,:n]=X1[i*12:(i+1)*12,:n,:n].permute(1,0,2).bfloat16()
  self.assertTrue(torch.equal(out,expected))
 def test_metadata_and_empty_domain_rejected(self):
  for cu in ([0,0],[0,40961],[0,2,1],[0,1.0],list(range(18))):
   with self.assertRaises(ValueError):M.plan(cu,cu[-1])
 def test_no_device_work_defaultoff(self):
  old=os.environ.pop(M.ENABLE,None)
  try:
   with self.assertRaises(RuntimeError):M.eager(None,None,None,None,None,None,None,None)
  finally:
   if old is not None:os.environ[M.ENABLE]=old
if __name__=='__main__':unittest.main()
