import ast,hashlib,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import clock127r4 as K,audit_transform127r4 as A
class Controls(unittest.TestCase):
 def profile(self):return dict(schema='deltalog.measured-CPU-recovery-profile/v127-repair4',measurement_ref=dict(path='/actual/timing.json',bytes=1,sha256='0'*64),final_fence_reserve_seconds=40.,cleanup_reserve_seconds=90.,predicted_child_seconds=100.,safety_margin_seconds=5.)
 def test_whole720_cap_and_late_admission_rejected(self):
  p=self.profile();self.assertEqual(K.child_cap(720,p,now=0),585.)
  self.assertEqual(K.child_cap(720,p,now=400),185.)
  with self.assertRaises(ValueError):K.child_cap(720,p,now=486)
  with self.assertRaises(ValueError):K.remaining(720,now=720)
 def test_pending_wrong_profile_or_budget_never_admitted(self):
  with self.assertRaises(ValueError):K.profile({})
  for n,v in [('cleanup_reserve_seconds',91),('predicted_child_seconds',586),('final_fence_reserve_seconds',-1),('safety_margin_seconds',float('nan'))]:
   p=self.profile();p[n]=v
   with self.assertRaises(ValueError):K.profile(dict(cpu_budget_profile=p))
 def test_whole_math_inverse_and_all_mixed_gates(self):
  raw=Path(__import__('os').environ['SOURCE127_ORIGINAL']).read_bytes();text=A.transform(raw);self.assertEqual(A.inverse(text),raw)
  for token in ('2*steps+31','2*steps+8',"transition['local_transition_pass']",'ledger[s],_=R.advance',"cross=dict(candidate_vs_independent_cumulative_CPU64",'CPU600s',"metrics=L.mixed(t,R,x)"):
   self.assertIn(token,text)
  self.assertIn('memo.seal_initial',text);self.assertIn('memo.finish()',text)
 def test_completed_initial_inventory_mode_identity_and_no_alias(self):
  counts=[];r=types.SimpleNamespace(advance=object(),restore=object());p=types.SimpleNamespace(evaluate=object(),bits=object());a=types.SimpleNamespace(audit=lambda t,r,p,s,**kw:counts.append(kw)or dict(passed=True,states=[0.]));rr=dict(path='/raw/a.pt',bytes=1,sha256='0'*64)
  m=dict(files={n:dict(path='/code/'+n,bytes=1,sha256='1'*64)for n in('oracle.py','precast.py','sidecar_audit.py','direct_round.py')});q=A.Memo(None,r,p,a,lambda x:None,lambda x:None,m,dict(actual_sidecar_records=[rr]))
  with self.assertRaises(ValueError):q.mixed(rr)
  q.initial(rr,overflow=False);q.seal_initial([rr]);x=q.mixed(rr);x['states'][0]=1;self.assertEqual(q.mixed(rr)['states'],[0.]);self.assertEqual(len(counts),1)
  with self.assertRaises(ValueError):q.mixed(dict(rr,sha256='2'*64))
  a.audit=lambda *args:None
  with self.assertRaises(ValueError):q.mixed(rr)
 def test_actual_cold_pending_profile_frontdoor(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'bind127.py'),'--execute','--template-ref','{}'],capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('pending actual measured complete-workload budget profile',r.stderr)
 def test_actual_GE_cleanup_calls_do_not_reenter_expired_work_profile(self):
  tree=ast.parse((P/'host.py').read_bytes());node=next(n for n in ast.walk(tree)if isinstance(n,ast.ClassDef)and n.name=='GE');clock=[600.];calls=[]
  class Base:
   def run(self,argv,timeout=60):calls.append(('run',argv,timeout));return dict(exit_code=0)
   def call(self,*a,**kw):raise ValueError('old work gate deliberately expired')
   def cleanup(self):calls.append(('cleanup',));self.call(['INDEPENDENT_RELEASE_CHECK'],timeout=90)
  def need(v,m):
   if not v:raise ValueError(m)
  ns=dict(Base=Base,_WHOLE_DEADLINE=720.,budget=dict(final_fence_reserve_seconds=40.),time=types.SimpleNamespace(monotonic=lambda:clock[0]),CLOCK=types.SimpleNamespace(remaining=lambda d:K.remaining(d,now=clock[0])),need=need,json=json)
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-R4-GE>','exec'),ns);ge=ns['GE']();ge.cleanup()
  self.assertEqual(calls,[('cleanup',),('run',['INDEPENDENT_RELEASE_CHECK'],80.)]);self.assertIsNone(ge.cleanup_until)
  clock[0]=680.
  with self.assertRaisesRegex(ValueError,'whole CPU720'):ge.cleanup()
 def test_actual_audit_invocation_roles_do_not_change_math(self):
  import torch
  torch.set_num_threads(1);root=Path(__import__('os').environ['SOURCE127_ORIGINAL']).parent
  def load(n):
   spec=importlib.util.spec_from_file_location('_r4_actual_'+n,root/(n+'.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
  R,PRE,AU=load('oracle'),load('precast'),load('sidecar_audit');sys.path.insert(0,str(root))
  try:
   before=[torch.zeros(1,4,128,dtype=torch.bfloat16),torch.zeros(1,4,128,dtype=torch.bfloat16),torch.zeros(1,12,128,dtype=torch.bfloat16),torch.zeros(1,12),torch.zeros(1,12,dtype=torch.bfloat16),torch.zeros(1,12,128,128),torch.zeros(1,4,7,128,dtype=torch.bfloat16),torch.zeros(1,12,7,128),torch.zeros(1,12,16),torch.zeros(1,12,16),torch.zeros(1,12,16,dtype=torch.int32),torch.tensor([0,1],dtype=torch.int32),torch.tensor([0],dtype=torch.int32)]
   import copy
   z=torch.zeros(1,12,128,dtype=torch.bfloat16);s=dict(before=before,debug_before=copy.deepcopy(before),after=copy.deepcopy(before),debug_after=copy.deepcopy(before),production_output=z,debug_output=z.clone(),actual_precast_FP32=z.float(),pointers_before=[1],pointers_after=[1],debug_pointers_before=[2],debug_pointers_after=[2],sidecar_guards_before=torch.tensor([1]),sidecar_guards_after=torch.tensor([1]))
   rr=dict(path='/software-fixture/raw.pt',bytes=1,sha256='0'*64);m=dict(files={n:dict(path='/source/'+n,bytes=(root/n).stat().st_size,sha256=hashlib.sha256((root/n).read_bytes()).hexdigest())for n in('oracle.py','precast.py','sidecar_audit.py','direct_round.py')})
   memo=A.Memo(torch,R,PRE,AU,lambda r:s,lambda r:None,m,dict(actual_sidecar_records=[rr]));expected=AU.audit(torch,R,PRE,s)
   self.assertEqual(memo.initial(rr,overflow=False),expected);memo.seal_initial([rr]);self.assertEqual(memo.mixed(rr),expected);memo.finish()
   over=A.Memo(torch,R,PRE,AU,lambda r:s,lambda r:None,m,dict(actual_sidecar_records=[rr]));self.assertFalse(over.initial(rr,overflow=True)['passed'])
   with self.assertRaises(ValueError):over.seal_initial([rr])
  finally:sys.path.remove(str(root))
 def test_actual_run_main_and_guest_argv_refs_equal_top_source(self):
  import run_recovery as RUN
  from unittest.mock import patch
  sr=dict(path='/exact/127R4/SOURCE_MANIFEST.json',bytes=123,sha256='a'*64);tr=dict(path='/exact/127R4/SOURCE_TEMPLATE.json',bytes=456,sha256='b'*64);lr=dict(path='/exact/old022.json',bytes=7,sha256='c'*64);captured=[]
  def ref(p):return tr if Path(p).name=='SOURCE_TEMPLATE.json'else sr
  argv=[str(P/'run_recovery.py'),'--execute','--phase','cpu','--template-ref',json.dumps(tr),'--host-cpu','166','--guest-cpu','0']
  with patch.object(sys,'argv',argv),patch.object(RUN.H,'ref',ref),patch.object(RUN.H,'obj',lambda r:dict(lifecycle_source_ref=lr)),patch.object(RUN.subprocess,'call',lambda a:captured.append(a)or 0):self.assertEqual(RUN.main(),0)
  a=captured[0]
  for key in('--owner-ref','--target-source-ref'):self.assertEqual(json.loads(a[a.index(key)+1]),sr)
  tree=ast.parse((P/'host.py').read_bytes());assign=next(n for n in ast.walk(tree)if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='args'for x in n.targets)and "root / 'entry.py'"in ast.unparse(n.value))
  ns=dict(PY='/usr/local/python3.12.13/bin/python3',root=Path('/exact/127R4'),stage='native',sr=sr,ar=RUN.AUTH,lr=lr,a=types.SimpleNamespace(steps=16),childout=Path('/sole/new/result'),json=json)
  guest=eval(compile(ast.Expression(assign.value),'<actual-GE-create-args>','eval'),ns)
  self.assertEqual(json.loads(guest[guest.index('--source-ref')+1]),sr)
  et=ast.parse((P/'entry.py').read_bytes());ea=next(n for n in ast.walk(et)if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='argv'for x in n.targets))
  ps=dict(path='/original/NPU/SOURCE_MANIFEST.json',bytes=99,sha256='d'*64);pr=dict(path='/original/NPU/RESULT.json',bytes=9,sha256='e'*64);st=dict(path='/old/STRICT.json',bytes=8,sha256='f'*64)
  inner=eval(compile(ast.Expression(ea.value),'<actual-entry127-argv>','eval'),dict(sys=sys,P=P,json=json,sr=sr,m=dict(original_source_ref=ps,original_producer_ref=pr,original_strict_ref=st),out=Path('/sole/new/result')))
  self.assertEqual(json.loads(inner[inner.index('--consumer-source-ref')+1]),sr);self.assertEqual(json.loads(inner[inner.index('--producer-source-ref')+1]),ps);self.assertNotEqual(sr,ps)
 def test_previous_reader_failure_never_becomes_success(self):
  import previous_reader127r4 as PR
  ps=dict(path='/old/NPU/source.json',bytes=1,sha256='a'*64)
  docs=dict(owner=dict(schema='deltalog.fresh-bridge-owned-host/v5',source=PR.REFS['source'],target_source=PR.REFS['source'],stage='cpu',NPU=False,result=None,stopped_retained=True,primary="ValueError('new48h authority cutoff/cleanup reserve exhausted')"),child=dict(primary='TimeoutExpired 585.6111058300012'),logs={},cleanup=dict(resource_release_verified=False),source=dict(producer_source=ps))
  def obj(r):return docs[next(k for k,v in PR.REFS.items()if v==r)]
  self.assertTrue(PR.validate(obj,ps)['old_failure_unchanged']);self.assertFalse(docs['cleanup']['resource_release_verified'])
  docs['child']['primary']='different fault'
  with self.assertRaises(ValueError):PR.validate(obj,ps)
if __name__=='__main__':unittest.main()
