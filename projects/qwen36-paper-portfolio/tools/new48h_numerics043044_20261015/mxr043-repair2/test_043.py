"""Actual aggregate/admission/callsite controls, no Torch or device import."""
import ast,copy,functools,importlib.util,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location('_043test'+n,P/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def valid():
 A=load('admit042');sr=A.SOURCE042;pr={'path':'probe'}
 owner=dict(schema='mxr.saved-frame-owned/v042',source=sr,primary=None,secondary=[],cpu_preflight=False,released=True,source_hashes_before={'a':'b'},source_hashes_after={'a':'b'},phase_seconds=2400,elapsed_seconds=100,probe=pr)
 rows=[dict(role=role,repeat=r,working_domain_gate_pass=True,arms={'x':{'inputs_unchanged':True}})for role in('nontrivial_heldout_layer16','nontrivial_heldout_layer40','initial_state_rounding_witness')for r in range(3)]
 consumer=dict(schema='mxr.three-arm-solve-chain-independent/v042',source=sr,probe=pr,complete=True,working_domain_heldout_pass=True,actual_native_initial_state_calibration_pass=True,numerical_qualification_granted=False,original_failures_unchanged=True,rows=rows)
 probe=dict(source=sr,primary=None,raws=[{'path':str(i)}for i in range(9)],candidate_hits=18,teardown=[{'pass_release':True}for _ in range(3)])
 return A,owner,consumer,probe,[dict(stopped=True,retained=True,errors=[])for _ in range(2)]
class Tests(unittest.TestCase):
 def test_pending_refuses_before_IO(self):
  with self.assertRaises(ValueError):load('admit042').gate(None)
 def test_actual_admission_controls(self):
  A,o,c,p,k=valid();self.assertFalse(A.validate(o,c,p,k)['model_ready'])
  for what in('ownerfail','heldoutfail','calibrationfail','cleanupfail','missingrow','source_drift'):
   oo,cc,pp,kk=copy.deepcopy((o,c,p,k))
   if what=='ownerfail':oo['primary']='original failure'
   if what=='heldoutfail':cc['rows'][1]['working_domain_gate_pass']=False
   if what=='calibrationfail':cc['actual_native_initial_state_calibration_pass']=False
   if what=='cleanupfail':kk[1]['errors']=['unreleased']
   if what=='missingrow':cc['rows'].pop()
   if what=='source_drift':oo['source']=dict(o['source'],sha256='0'*64)
   with self.assertRaises(ValueError,msg=what):A.validate(oo,cc,pp,kk)
 def test_actual_all4_48_aggregate(self):
  H=load('host_ticket');values={};reports=[];bindings=[]
  for i in range(4):
   key=str(i);reports.append(dict(rank=i,result=key));bindings.append(dict(rank=i,namespace_pid=100+i,worker_root='/w/'+key));values[key]=dict(pid=100+i,worker_root='/w/'+key,gdn_frame_gate_pass=True,layer_prefixes=['layer%d'%j for j in range(48)])
  c=types.SimpleNamespace(obj=lambda key:values[key]);self.assertTrue(H.all4_layers(c,reports,bindings)['passed'])
  with self.assertRaises(ValueError):H.all4_layers(c,reports[:3],bindings)
  values['2']['layer_prefixes'][-1]='foreign'
  with self.assertRaises(ValueError):H.all4_layers(c,reports,bindings)
 def test_actual_observed_refiner_callsite(self):
  tree=ast.parse((P/'worker.py').read_text());node=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='observed');node.decorator_list=[]
  class T:
   def detach(self):return self
   def cpu(self):return self
   def clone(self):return self
   def tolist(self):return [0,129]
  frame={};seen=[];tensor=T()
  def eager(*args,**kw):seen.append((args,kw));kw['trace']['X1_FP32']=tensor;return tensor
  ns=dict(scope=types.SimpleNamespace(get=lambda:frame),original_eager=lambda *a:None,refiner=types.SimpleNamespace(eager=eager),torch=types.SimpleNamespace(npu=types.SimpleNamespace(synchronize=lambda:None)),precision={'allow_hf32':False},fingerprint=lambda *a:None,need=lambda v,m:None if v else (_ for _ in()).throw(ValueError(m)))
  exec(compile(ast.Module(body=[node],type_ignores=[]),'actual043-observed','exec'),ns);self.assertIs(ns['observed']('solver',tensor,tensor,3,'BF16','pool','backend'),tensor)
  self.assertEqual(seen[0][0][-1],[0,129]);self.assertIn('refinement',frame);self.assertIs(frame['solve']['output'],tensor)
if __name__=='__main__':unittest.main()
