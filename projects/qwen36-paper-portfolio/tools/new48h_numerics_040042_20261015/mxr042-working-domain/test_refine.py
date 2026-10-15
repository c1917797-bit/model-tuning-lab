"""Independent CPU64 inverse controls; software only, not a hardware PASS."""
import importlib.util,unittest,os
from pathlib import Path
import torch
P=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('new027',P/'refine.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R);torch.set_num_threads(1)
def make(boundaries):
 t=boundaries[-1];A=torch.zeros((1,t,12,64));X=torch.zeros_like(A);ref=torch.zeros_like(A,dtype=torch.float64);g=torch.Generator().manual_seed(271510)
 for bos,eos in zip(boundaries,boundaries[1:]):
  for start in range(bos,eos,64):
   n=min(64,eos-start);a=torch.tril(torch.randn((12,n,n),generator=g)*.035,-1);eye=torch.eye(n,dtype=torch.float64).expand(12,n,n)
   a16=a.half().float();x16=torch.linalg.solve_triangular(eye+a16.double(),eye,upper=False,unitriangular=True).float();oracle=torch.linalg.solve_triangular(eye+a.double(),eye,upper=False,unitriangular=True)
   A[0,start:start+n,:,:n]=a.permute(1,0,2);X[0,start:start+n,:,:n]=x16.permute(1,0,2);ref[0,start:start+n,:,:n]=oracle.permute(1,0,2)
 return A,X,ref
class Tests(unittest.TestCase):
 def test_shared_actual_fourarm_cardinality(self):
  z=importlib.util.spec_from_file_location('counts027',P/'probe_contract.py');G=importlib.util.module_from_spec(z);z.loader.exec_module(G);v=dict(source='source',primary=None,raws=[{'path':str(i)}for i in range(G.REPEATS*G.FRAMES)],candidate_hits=G.CANDIDATE_HITS,teardown=[{'pass_release':True} for _ in range(3)])
  self.assertTrue(G.ready(v,'source'))
  for n in(0,3,5,7):self.assertFalse(G.ready(dict(v,candidate_hits=n),'source'))
  self.assertFalse(G.ready(dict(v,raws=v['raws']*2),'source'))
  self.assertFalse(G.ready(v,'other'))
 def test_originalA_recovers_conversion_loss_and_inputs_unchanged(self):
  A,X,oracle=make([0,129]);beforeA=A.clone();beforeX=X.clone();ap,xp,rows=R.pack(torch,A,X,[0,129]);y,d=R.correction(torch,ap,xp);full=R.scatter(torch,y,rows,A.shape)
  old=float((X.double()-oracle).norm());new=float((full.double()-oracle).norm());self.assertLess(new,old*.005)
  self.assertTrue(torch.equal(A,beforeA));self.assertTrue(torch.equal(X,beforeX));self.assertEqual(rows,[(0,0,64),(0,64,64),(0,128,1)])
 def test_varlen_tail_and_head_isolation(self):
  for cu in([0,1],[0,63],[0,64],[0,65],[0,0,1,65,129],[0,2,66,129]):
   A,X,ref=make(cu);ap,xp,rows=R.pack(torch,A,X,cu);y,_=R.correction(torch,ap,xp);out=R.scatter(torch,y,rows,A.shape);self.assertLess(float((out.double()-ref).abs().max()),4e-7)
   for _,start,n in rows:self.assertEqual(int(torch.count_nonzero(out[0,start:start+n,:,n:])),0)
 def test_no_recovering_originalA_from_half_and_sign_negative(self):
  A,X,oracle=make([0,129]);ap,xp,rows=R.pack(torch,A,X,[0,129]);good,_=R.correction(torch,ap,xp);half,_=R.correction(torch,ap.half().float(),xp);bad,_=R.correction(torch,-ap,xp)
  e=lambda y:float((R.scatter(torch,y,rows,A.shape).double()-oracle).norm())
  self.assertLess(e(good),e(half)*.005);self.assertGreater(e(bad),e(good)*100)
 def test_missing_wrong_cpu_domain_and_budget(self):
  for cu,t in(([1,129],129),([0,130],129),([0,True],1),([0,193],193),([0,1,2,3,4,5],5)):
   with self.assertRaises(ValueError):R.plan(cu,t)
  A,X,_=make([0,1])
  with self.assertRaises(ValueError):R.pack(torch,A.half(),X,[0,1])
 def test_defaultoff_precision_unknown_rejects_before_launch(self):
  old=os.environ.pop(R.ENABLE,None)
  try:
   with self.assertRaises(RuntimeError):R.precision_policy(torch)
   os.environ[R.ENABLE]='1'
   with self.assertRaises(RuntimeError):R.precision_policy(torch)
  finally:
   os.environ.pop(R.ENABLE,None)
   if old is not None:os.environ[R.ENABLE]=old
if __name__=='__main__':unittest.main()
