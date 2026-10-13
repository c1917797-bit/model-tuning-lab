"""Round1/2 source-bound fault injection, NEVER a controller/admission entry.
Actual original function bodies run over explicitly synthetic SMI/proc/inspect
observations. No Docker, Torch, NPU, resource admission or hardware PASS.
"""
import ast,copy,hashlib,importlib.util,json,os,sys,time,types,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path

TEMP=Path('C:/Users/Huawei/AppData/Local/Temp')
DONOR=TEMP/'kivi-direct-fp32-graph-owner-20261012-002/actual-donors/host_once.py'
H8=TEMP/'R118_h8_host_run.py'
CURRENT=TEMP/'kivi-continuous-prefix-r156-20261013-002'
OBSERVER=TEMP/'r162-protected-observer-20261013-001/observer.py'

def need(v,m):
 if not v:raise ValueError(m)
def exact(p,size,digest):
 b=p.read_bytes();need(len(b)==size and hashlib.sha256(b).hexdigest()==digest,'whole original source '+str(p));return b
def load(p,size,digest,name):
 exact(p,size,digest);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
RAW=exact(DONOR,29763,'6414c912b216f3896a21e7b321717b604c4be7db21220ed034a798da460a0be8')
POLICY=load(CURRENT/'cohort_policy.py',10024,'3b11b2eee79b2da97cc9f2204826a3cb4a1b349b29ed2a8e86d6ea0786c43476','_round2_actual_policy')
RUNTIME=load(CURRENT/'cohort_runtime.py',9836,'f7df120d3cf8e6cfc9faa406ea091bb0efbba8b1afa5cf1a9b620bce4649adbb','_round2_actual_shared')
OBS=load(OBSERVER,6275,'fafdb2685481d3e1c77dad977156cf3ed4838e515d6c3a4a4d4042751f0c216f','_round2_main_observer')

def scope_tree():
 """Three isolated scope deltas ONLY; not installed into an executable owner."""
 original=ast.parse(RAW);tree=copy.deepcopy(original);changes=[]
 joint=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Joint')
 observe=next(n for n in joint.body if isinstance(n,ast.FunctionDef)and n.name=='observe')
 loop=next(n for n in observe.body if isinstance(n,ast.For)and ast.unparse(n.target)=='card')
 old=copy.deepcopy(loop);need(ast.unparse(loop.iter)=='(4, 5, 6, 7)','exact all4 loop')
 loop.body.insert(1,ast.parse('if card != ctl.card:\n self.cohort.observe_other(ctl,card,live,record)\n continue').body[0]);changes.append((old,copy.deepcopy(loop)))
 fd=next(n for n in observe.body if isinstance(n,ast.For)and ast.unparse(n.target)=='fd')
 old=copy.deepcopy(fd);need('real foreign device FD/UDA'in ast.unparse(fd),'exact originalFD guard');fd.body=[ast.parse('self.cohort.fd(ctl,fd,record)').body[0]];changes.append((old,copy.deepcopy(fd)))
 factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='controller')
 owned=next(n for n in factory.body if isinstance(n,ast.ClassDef)and n.name=='Owned')
 cleanup=next(n for n in owned.body if isinstance(n,ast.FunctionDef)and n.name=='cleanup')
 tried=next(n for n in cleanup.body if isinstance(n,ast.Try))
 idle=next(n for n in tried.body if isinstance(n,ast.For)and ast.unparse(n.target)=='card')
 old=copy.deepcopy(idle);need(ast.unparse(idle.iter)=='(4, 5, 6, 7)','exact cleanup all4 idle');idle.iter=ast.parse('((self.card,) if self.card is not None else ())',mode='eval').body;changes.append((old,copy.deepcopy(idle)))
 class Undo(ast.NodeTransformer):
  def visit_For(self,n):
   for old,new in changes:
    if ast.dump(n,include_attributes=False)==ast.dump(new,include_attributes=False):return copy.deepcopy(old)
   return self.generic_visit(n)
 need(ast.dump(Undo().visit(copy.deepcopy(tree)),include_attributes=False)==ast.dump(original,include_attributes=False),'WHOLE inverse AST, all other code unchanged')
 return ast.fix_missing_locations(tree)

def view(scoped,rows,fds=()):
 publications=[];idle=[]
 def publish(p,value):publications.append(value);return dict(path=str(p),bytes=1,sha256='0'*64)
 C=types.SimpleNamespace(need=need,write=publish,HOST=512*1024**2,CLEANUP=90,CUTOFF=1792002456)
 L=types.SimpleNamespace(proc_snapshot=lambda pid:{'pid':pid},proc_frames=lambda unused:[],child_association=lambda ctl:{'synthetic':True},holders=lambda cards:[d for d in fds if d['physical']in cards])
 H=types.SimpleNamespace(Controller=object,SMI='/source-fixture-only/npu-smi',started=lambda value:value)
 def no_proof(pid):raise FileNotFoundError('synthetic unavailable proof')
 def idle_one(text,card):
  idle.append(card);need(not any(x[0]==card for x in rows),'synthetic actual busy card')
 frozen=types.SimpleNamespace(protected=lambda text:[],legacy=lambda:types.SimpleNamespace(process_rows=lambda text:rows),idle_one=idle_one,gate_process=no_proof)
 H.started=lambda value:value
 tree=scope_tree()if scoped else ast.parse(RAW)
 nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in('utc','Joint','controller')]
 ns=dict(C=C,L=L,Path=Path,json=json,os=os,time=time,datetime=datetime,timedelta=timedelta,timezone=timezone,math=__import__('math'),resource=types.SimpleNamespace())
 exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(DONOR),'exec'),ns)
 co=ns['Joint'].__new__(ns['Joint']);co.out=Path('/fixture-only');co.protected_check=lambda rows:dict(protected_fixture=True);co.resources=lambda initial:dict(resource_fixture=True)
 co.H=H;co.cleanup_used=0;co.secondary=[];co.begin_cleanup=lambda:time.monotonic()+90;co.end_cleanup=lambda:None
 co.time_failures=lambda:[]
 own={'run_id':'mxr','cards':[5],'source':{'path':'/not-published/mxr.json','bytes':1,'sha256':'0'*64}}
 plan={'members':[own]};binding=dict(policy=POLICY,plan=plan,row=own,ref={'path':'/not-published/cohort.json','bytes':1,'sha256':'0'*64})
 co.cohort=RUNTIME.Shared(C,L,H,binding,{},lambda unused:None)
 cls=ns['controller'](H);ctl=cls.__new__(cls);ctl.co=co;ctl.h=frozen;ctl.card=None;ctl.cid='a'*64;ctl.out=Path('/fixture-only/cpu');ctl.primary=None;ctl.secondary=[];ctl.child=None;ctl.child_label='software15';ctl.canary_proofs=[];ctl.gate_proofs=[];ctl.expected_child_argv=[]
 def call(label,argv,**kw):
  need(label in('smi','running-declarations','stop-retain','release-smi'),'no unexpected controller operation in fixture');return dict(stdout=''if label=='running-declarations'else'fixture',observed_utc='2026-10-13T21:00:00+00:00'),publish(Path('/fixture-only/'+label),{})
 ctl.call=call;ctl.inspect=lambda **kw:({'State':{'Running':False,'Pid':0,'OOMKilled':False},'ExecIDs':[]},publish(Path('/fixture-only/inspect'),{}))
 return co,ctl,publications,idle

class Rounds(unittest.TestCase):
 def test01_round1_adapter_clock_is_only_production_delta(self):
  p=TEMP/'mxr-r156-diag16-defect-20261013-037/adapter.py';b=exact(p,3092,'ca9a82e01500ab203d1fa4d01a348d9187d50858d4f91c256687c04fd1185242')
  old=b.replace(b'dict(start=1791916056,cutoff=1792002456)',b'dict(start=1791879730,cutoff=1791922930)');self.assertEqual(hashlib.sha256(old).hexdigest(),'79f0cb8c3803079843ae3af6f5071ae2f91346a7d517eabde442743c2f99f5c7')
 def test02_real_original_CPU_observe_rejects_other4(self):
  co,ctl,_,_=view(False,[(4,0,12345)])
  with self.assertRaisesRegex(ValueError,'real foreign physical/chip'):co.observe(ctl,'cpu')
 def test03_real_original_single5_observe_rejects_other4(self):
  co,ctl,_,_=view(False,[(4,0,12345)]);ctl.card=5
  with self.assertRaisesRegex(ValueError,'real foreign physical/chip'):co.observe(ctl,'numeric')
 def test04_three_seam_proposal_CPU_keeps_other4_as_observation(self):
  co,ctl,rows,idle=view(True,[(4,0,12345)]);proofs,_=co.observe(ctl,'cpu');self.assertEqual(proofs,[]);self.assertEqual(idle,[])
  other=[x for x in rows if'cohort_other_cards'in x][-1]['cohort_other_cards'];self.assertEqual(other[0]['actual'][0]['classification'],'foreign-occupied-other-card-no-authority')
 def test05_three_seam_proposal_single5_still_checks_own5(self):
  co,ctl,_,idle=view(True,[(4,0,12345)]);ctl.card=5;co.observe(ctl,'numeric');self.assertEqual(idle,[5])
  co,ctl,_,_=view(True,[(5,1,12345)]);ctl.card=5
  with self.assertRaisesRegex(ValueError,'real foreign physical/chip'):co.observe(ctl,'numeric')
 def test06_real_Shared_fd_own_foreign_rejected_other_observed(self):
  f=dict(physical=5,pid=12345,cgroup='/foreign',cmdline_sha256='0'*64);co,ctl,_,_=view(True,[],[f]);ctl.card=5
  with self.assertRaisesRegex(ValueError,'foreign FD/UDA on own card'):co.observe(ctl,'numeric')
  f['physical']=4;co,ctl,rows,_=view(True,[],[f]);ctl.card=5;co.observe(ctl,'numeric');self.assertTrue(any('cohort_other_fds'in x for x in rows))
 def test07_real_original_CPU_cleanup_falsely_requires_other4_idle(self):
  co,ctl,_,idle=view(False,[(4,0,12345)]);ctl.cleanup();self.assertTrue(ctl.secondary);self.assertEqual(idle,[4])
 def test08_scoped_CPU_cleanup_has_no_device_idle_borrow(self):
  co,ctl,rows,idle=view(True,[(4,0,12345)]);ctl.cleanup();self.assertEqual(ctl.secondary,[]);self.assertEqual(idle,[]);self.assertTrue(rows[-1]['stopped']);self.assertTrue(rows[-1]['retained'])
 def test09_scoped_single5_cleanup_requires_only5_idle(self):
  co,ctl,rows,idle=view(True,[(4,0,12345)]);ctl.card=5;ctl.cleanup();self.assertEqual(idle,[5]);self.assertEqual(ctl.secondary,[])
  co,ctl,_,_=view(True,[(5,0,12345)]);ctl.card=5;ctl.cleanup();self.assertTrue(ctl.secondary)
 def test10_MAIN_protected_observer_still_rejects_our_PID(self):
  with self.assertRaisesRegex(OBS.ObservationError,'owned PID'):OBS.observe([(0,0,12345)],lambda unused:None,lambda:None,lambda unused:[],lambda unused:None,owned_pids=[12345])
 def test11_real_cohort_sum_preserves_MXR4GiB_not256MiB(self):
  GiB=1024**3;members=[dict(run_id=n,guest_bytes=8*GiB,host_bytes=GiB//2,output_bytes=4*GiB,cache_bytes=GiB//2)for n in('mxr','other')];plan=dict(members=members,reserve_bytes=8*GiB);used={n:dict(output_bytes=0,cache_bytes=0)for n in('mxr','other')}
  kw=dict(swap_total=0,swap_free=0,disk_free=17*GiB,used_by_run=used)
  self.assertEqual(POLICY.resources(plan,mem_available=25*GiB,**kw)['held_bytes'],25*GiB)
  with self.assertRaisesRegex(ValueError,'aggregate cohort RAM'):POLICY.resources(plan,mem_available=25*GiB-1,**kw)
  used['mxr']['output_bytes']=4*GiB+1
  with self.assertRaisesRegex(ValueError,'per-owner byte cap'):POLICY.resources(plan,mem_available=25*GiB,**kw)
 def test12_cohort_CPU_assignments_are_disjoint(self):
  plan=dict(members=[dict(run_id='mxr',host_cpu=0,guest_cpus=[1]),dict(run_id='other',host_cpu=2,guest_cpus=[3])],reserve_cpus=[4,5]);host=dict(effective_capacity=7,effective_cpus=list(range(7)),ancestor_cpuset=list(range(7)),quota_ancestors=[dict(key='q',capacity=7)]);daemon=dict(effective_capacity=7,effective_cpus=list(range(7)),quota_ancestors=[dict(key='q',capacity=7)])
  a=POLICY.cpu_plan(plan,'mxr',host,daemon);b=POLICY.cpu_plan(plan,'other',host,daemon);self.assertFalse({a['host_cpu'],a['guest_cpu']} & {b['host_cpu'],b['guest_cpu']})
  daemon['quota_ancestors'][0]['capacity']=5
  with self.assertRaisesRegex(ValueError,'summed CPU budget'):POLICY.cpu_plan(plan,'mxr',host,daemon)
 def test13_existing_runtime_compatibility_gap_remains_explicit(self):
  text=(CURRENT/'cohort_runtime.py').read_text();self.assertIn('256*1024**2',text);self.assertIn("mm['files']['guest.py']",text);self.assertIn("root=Path(row['output_root'])/'physical-single'",text);self.assertIn('exact_host_argv',text)
  self.assertFalse(any(x in sys.modules for x in('torch','torch_npu','triton')))
 def test14_complete_AST_inverse_three_seams_only(self):
  original=ast.parse(RAW);new=scope_tree()
  for tree in(original,new):
   joint=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Joint')
   functions={n.name:n for n in joint.body if isinstance(n,ast.FunctionDef)}
   if tree is original:before=functions
   else:
    for name in('__init__','resources','protected_check','rss','begin_cleanup','end_cleanup'):self.assertEqual(ast.dump(before[name],include_attributes=False),ast.dump(functions[name],include_attributes=False))

if __name__=='__main__':unittest.main(verbosity=2)
