"""Software contract tests only; no compiled Meta or NPU claim."""
import ast,copy,hashlib,importlib.util,json,subprocess,sys,unittest,types,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import split_build052 as S
def module(n):
 s=importlib.util.spec_from_file_location('_052_'+n,P/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Tests(unittest.TestCase):
 def build(self):
  libs=[dict(path='/prod',bytes=1,sha256='a'*64),dict(path='/debug',bytes=2,sha256='b'*64)]
  r=dict(path='/build',bytes=3,sha256='c'*64);src=dict(path='/kernel',bytes=4,sha256='d'*64)
  v=dict(schema='deltalog-split-scale-actual-build/v051',primary=None,source_manifest=src,Devices=[],NPU=False,numeric_qualified=False,model_ready=False,commands=[dict(exit_code=0,error=None)],artifacts=[dict(arm=a,library=b)for a,b in zip(S.ARMS,libs)])
  m=dict(split_build_ref=r,reviewed_split_build_ref=r,split_kernel_source_ref=src,library_ref=libs[0],debug_library=libs[1],debug_build_ref=r)
  return m,v,libs
 def test_build_schema_and_artifacts(self):
  m,v,libs=self.build();self.assertEqual(S.admit(m,lambda r:v,lambda p:next(x for x in libs if x['path']==p)),v)
  for key,val in [('primary','failed'),('Devices',[0]),('NPU',True),('model_ready',True),('source_manifest',{})]:
   bad=copy.deepcopy(v);bad[key]=val
   with self.assertRaises(ValueError):S.admit(m,lambda r:bad,lambda p:next(x for x in libs if x['path']==p))
 def test_missing_future_rejected(self):
  m,v,l=self.build();m['split_build_ref']=None
  with self.assertRaises(ValueError):S.admit(m,lambda r:v,lambda p:l[0])
 def test_actual_meta_callable_13_14_software_ABI_only(self):
  import torch
  from unittest.mock import patch
  M=module('meta051');m,v,libs=self.build();calls=[];loaded=[]
  class Op:
   default=types.SimpleNamespace(_schema='SOFTWARE-FIXTURE-NOT-COMPILED-META')
   def __init__(self,n):self.n=n
   def __call__(self,*args):
    self_outer.assertEqual(len(args),self.n);calls.append((self.n,args[0].shape[0]));return torch.empty((args[0].shape[0],12,128),dtype=torch.bfloat16,device='meta')
  self_outer=self
  ops=types.SimpleNamespace(load_library=lambda p:loaded.append(p),qwen36_deltalog_split_scale_v051=types.SimpleNamespace(decode=Op(13)),qwen36_deltalog_split_scale_sidecar_v051=types.SimpleNamespace(decode=Op(14)))
  T=types.SimpleNamespace(ops=ops,bfloat16=torch.bfloat16,float32=torch.float32,int32=torch.int32,empty=torch.empty,_C=types.SimpleNamespace(_dispatch_has_kernel_for_dispatch_key=lambda n,k:True))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'build.json';p.write_text(json.dumps(v));r=dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
   with patch.object(M,'checked',side_effect=lambda ref: p if ref==r else Path(ref['path'])):
    z=M.run(T,r,m['split_kernel_source_ref'])
  self.assertEqual(calls,[(13,1),(13,16),(14,1),(14,16)]);self.assertEqual(loaded,[str(Path('/prod')),str(Path('/debug'))]);self.assertFalse(z['NPU']);self.assertFalse(z['numeric_qualified'])
 def test_actual_failure_persisted_before_aggregate(self):
  import torch,sidecar_receipt052,oracle,precast
  from unittest.mock import patch
  rr=dict(path='/software-only/corrupt-actual-schema.pt',bytes=1,sha256='e'*64)
  with tempfile.TemporaryDirectory()as d,patch.object(torch,'load',return_value={}):
   row=sidecar_receipt052.one(torch,oracle,precast,rr,{'software-source':1},{'software-producer':1},{},str(Path(d)/'DOMAIN.json'),0,set(),set(),[],lambda r:r['path'])
   self.assertFalse(row['passed']);self.assertIn('KeyError',row['primary'])
   receipt=json.loads(Path(row['receipt']['path']).read_bytes());self.assertEqual(receipt['raw'],rr);self.assertFalse(receipt['passed']);self.assertEqual(receipt['source'],{'software-source':1})
 def test_original_regression_before_bytes_independently_joined(self):
  import torch,regression052
  from unittest.mock import patch
  rr=dict(path='/software-only/raw',bytes=1,sha256='f'*64);args=[torch.tensor([0.,-0.])for _ in range(13)];control=dict(case='original-B16-step80',original_raw=rr,old_failure_preserved=True);side={'before':[x.clone()for x in args]}
  with patch.object(regression052,'inputs',return_value=(rr,args)):
   self.assertTrue(regression052.audit(torch,{},None,control,side));side['before'][0][1]=0.
   with self.assertRaises(ValueError):regression052.audit(torch,{},None,control,side)
 def test_real_host_PLAN_to_entry_to_producer_cold(self):
  import builtins
  from unittest.mock import patch
  E=module('entry');G=module('producer');gate=module('preregister')
  from qwen36_deltalog_fresh import provider
  sr={'software-source':1};ar={'software-authority':1};lr={'software-lifecycle':1}
  owner=dict(schema='deltalog.diagnostic-owned-host/v035',target_source=sr,stage='numeric',steps=16,stopped_retained=True,primary=None,secondary=[],bridge_primitive_gate_pass=False,model_ready=False,result='result',independent_consumer='consumer')
  consumed=dict(schema='deltalog.diagnostic-consumption/v043',source=sr,actual_result='result',validation_contract={'schema':'deltalog.actual-FP32-precast-per-request-empirical/v043'},diagnostic_capture_complete=True,domain_checks_pass=True,complete_proof=False,original_strict_result_preserved={'pass_gate':False})
  m=dict(allowed_steps=[16,160],debug_library='software-debug',files={'preregister.py':'gate','producer.py':'producer'})
  cpu=dict(source=sr,lifecycle=lr,pass_gate=True,NPU=False,actual_precast_meta=dict(pass_gate=True,debug_library='software-debug'),actual_collection_contract_controls='collection',actual_terminal_process_controls='terminal')
  tree=ast.parse((P/'host.py').read_bytes());expression=next(n.args[1]for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='write'and len(n.args)==2 and isinstance(n.args[0],ast.Name)and n.args[0].id=='plan')
  class BeforeTorch(Exception):pass
  imported=builtins.__import__;seen=[]
  def stop(name,*args,**kwargs):
   if name in('torch','torch_npu'):seen.append(name);raise BeforeTorch()
   return imported(name,*args,**kwargs)
  with tempfile.TemporaryDirectory()as d:
   out=Path(d)/'numeric';plan=eval(compile(ast.Expression(expression),'actual-host-PLAN','eval'),dict(sr=sr,ar=ar,lr=lr,a=types.SimpleNamespace(steps=160,physical_device=5),smoke='owner',cpur='cpu',childout=out))
   values={'plan':plan,'owner':owner,'consumer':consumed,'cpu':cpu,'collection':dict(source=sr,software_contracts_pass=True,NPU=False),'terminal':{'software_controls_pass':True}}
   def load(r,n):return {'gate':gate,'producer':G}[r]
   argv=[str(P/'entry.py'),'--execute','--stage','numeric','--source-ref',json.dumps(sr),'--authority-ref',json.dumps(ar),'--lifecycle-ref',json.dumps(lr),'--plan-ref',json.dumps('plan'),'--cpu-preflight-ref',json.dumps('cpu'),'--output',str(out),'--steps','160']
   with patch.object(E.C,'source',return_value=m),patch.object(E.C,'window'),patch.object(E.C,'obj',side_effect=lambda r:values[r]),patch.object(E.C,'load',side_effect=load),patch.object(provider,'source_admission',return_value=(m,{})),patch.object(sys,'argv',argv),patch('builtins.__import__',side_effect=stop):
    with self.assertRaises(BeforeTorch):E.main()
   self.assertEqual(seen,['torch']);self.assertTrue(out.is_dir())
 def test_cold_defaultoff(self):
  for name in('run052.py','bind052.py'):
   z=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True);self.assertEqual(z.returncode,0,z.stderr);self.assertEqual(z.stdout.strip(),'disabled')
 def test_actual_entry_and_provider_namespaces(self):
  p=(P/'qwen36_deltalog_fresh/provider.py').read_text();s=(P/'sidecar_capture.py').read_text();m=(P/'meta051.py').read_text()
  self.assertIn("state_predecessor_library_ref",p);self.assertIn('admit(m,_obj,_ref)',p);self.assertIn('split_scale_sidecar_v051',s);self.assertIn("'split_scale_v051','split_scale_sidecar_v051'",m)
 def test_math_reference_unchanged(self):
  b=P.parent/'deltalog-mixed-precast-new48h-20261015-043-repair3'
  for n in('oracle.py','precast.py','direct_round.py','sidecar_audit.py','per_request_increment.py'):
   self.assertEqual((P/n).read_bytes(),(b/n).read_bytes(),n)
 def test_seed_both_independent_sides(self):
  for n in('domain_consumer.py','qwen36_deltalog_fresh/native_fixture.py'):
   s=(P/n).read_text();self.assertIn('2610165101',s);self.assertNotIn('2610154301',s)
 def test_control_counts_and_regression(self):
  c=module('npu_controls');self.assertEqual(len(c.CASES),11);self.assertIn('finite-final-normalized-query',c.CASES)
  s=(P/'collection_policy.py').read_text();self.assertIn('2*steps+31',s);self.assertIn('original-B16-step80',s);self.assertIn('original-B16-step137',s)
  t=ast.parse((P/'producer.py').read_bytes());calls=[ast.unparse(x)for x in ast.walk(t)if isinstance(x,ast.Call)]
  self.assertTrue(any('replay_firstfault(torch, sidecar, m, C)'==x for x in calls))
 def test_whole_source_lf_hash(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
  for n,r in m['files'].items():
   b=(P/n).read_bytes();self.assertNotIn(b'\r',b,n);self.assertEqual(len(b),r['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),r['sha256'])
if __name__=='__main__':unittest.main()
