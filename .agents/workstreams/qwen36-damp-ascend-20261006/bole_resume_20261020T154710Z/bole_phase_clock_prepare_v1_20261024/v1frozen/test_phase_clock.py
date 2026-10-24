"""Bounded actual-entry controls; process/mount/authority doubles, no devices."""
import copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
BASE=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_fa_cache_diagnostic_prepare_v1_20261024/prepared-source-short8-cache-diagnostic-v1")
sys.path.insert(0,str(ROOT));import shared_phase_clock as P,adapt_phase_clock as A
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(ref(r['path'])==r,'actual fixture Ref3');return json.loads(Path(r['path']).read_text())
def write(p,v):
 with Path(p).open('x')as f:json.dump(v,f)
 return ref(p)
def module(name,raw,file):
 m=types.ModuleType(name);m.__file__=str(file);sys.modules[name]=m;exec(compile(raw,str(file),'exec'),m.__dict__);return m
NAMES=('contract090.py','host_service.py','owned_create.py','external025.py')
BASEFILES={n:(BASE/n).read_bytes()for n in NAMES}
NEW,DELTA=A.adapt(BASEFILES)
class Test(unittest.TestCase):
 def setUp(self):
  self.oldmods=dict(sys.modules);self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.out=self.root/'output';self.out.mkdir()
  self.leaf=self.out/'dense';self.leaf.mkdir();self.receipt=self.leaf/'receipts';self.receipt.mkdir()
  self.m=json.loads((BASE/'SOURCE_BOUND.json').read_bytes());self.m.update(root=str(self.root),output_root=str(self.out),model_receipt_root=str(self.receipt),phase_clock_contract=dict(P.CONTRACT))
  self.m['dependencies']=[];self.m['files']=dict(self.m['files'],shared_phase_clock=ref(P.__file__))
  self.m['files']['shared_phase_clock.py']=ref(P.__file__);self.m['files']['host_service.py']=dict(path=str(self.root/'host_service.py'),bytes=1,sha256='a'*64)
  self.sr=write(self.root/'SOURCE_BOUND.json',self.m)
  self.clock=dict(mono=1000.,wall=6000.);self.container=None;self.calls=[]
  self.V=types.ModuleType('followup_source_validate')
  def window(m,*,clock,require_phase):
   self.calls.append(require_phase)
   need(m['qualification_authority_ref']==self.m['qualification_authority_ref'],'actual unchanged authority Ref')
   need(self.clock['wall']<10000 and (not require_phase or self.clock['wall']+3780<=10000),'window')
   return dict(cutoff_epoch=10000)
  self.V.execution_window=window
  self.C=types.SimpleNamespace(need=need,ref=ref,obj=obj,write=write)
  self.cid='b'*64;P._PARENT=None
  oldread=Path.read_bytes
  def read(p):
   if str(p)=='/proc/self/cmdline':return ('python3\0-I\0-B\0'+str(self.root/'host_service.py')+'\0').encode()
   return oldread(p)
  self.patches=[patch.dict(sys.modules,{'followup_source_validate':self.V,'shared_phase_clock':P}),
   patch.object(P.time,'monotonic',side_effect=lambda:self.clock['mono']),
   patch.object(P.time,'time',side_effect=lambda:self.clock['wall']),
   patch.object(P,'cid',side_effect=lambda:self.container),
   patch.object(P,'boot',return_value='boot-1'),patch.object(P,'time_ns',return_value='time:[123]'),
   patch.object(P,'proc_start',return_value='777'),patch.object(Path,'read_bytes',read)]
  for p in self.patches:p.start()
  self.ctl=types.SimpleNamespace(created_monotonic=900.,deadline=4500.,out=self.leaf,cid=self.cid)
  P.bind_parent(self.C,self.sr,self.m,900.)
  self.mounts={'/adakv-results':(str(self.leaf),True)}
  P.prepare_mount(self.C,self.sr,self.ctl,'dense',self.mounts)
  self.d=self.out/'.phase-clock'/'dense'
  self.expected=dict(cid=self.cid,name='exact-owned',image='sha256:'+('c'*64),arm='dense',source=self.sr,mounts=self.mounts)
  self.ctl.expected=self.expected;write(self.leaf/'OWNED.json',self.expected)
  self.inspect=dict(Id=self.cid,Name='/exact-owned',Image=self.expected['image'],State=dict(Running=True,Pid=111),
    Mounts=[dict(Source=str(self.d),Destination=str(self.d),RW=False)])
  ir=write(self.leaf/'inspect.json',dict(stdout=json.dumps([self.inspect])))
  # Reuse actual already-pinned atomic publisher and its donor, not an invented write protocol.
  spec=importlib.util.spec_from_file_location('snapshot_publication',BASE/'snapshot_publication.py')
  pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub);sys.modules['snapshot_publication']=pub
  P.publish(self.C,self.sr,self.ctl,self.inspect,ir)
  self.path=self.d/'PHASE.json';self.original=json.loads(self.path.read_text())
  self.container=self.cid;self.clock.update(mono=2000.,wall=7000.)
  self.mount_patch=patch.object(P,'readonly_mount',side_effect=self.mount);self.mount_patch.start()
  self.env=patch.dict(os.environ,{P.FLAG:str(self.path)});self.env.start()
 def mount(self,d):
  need(d==self.d and self.inspect['Mounts'][0]['RW']is False,'actual mount fixture')
 def tearDown(self):
  self.env.stop();self.mount_patch.stop()
  for p in reversed(self.patches):p.stop()
  P._PARENT=None;sys.modules.clear();sys.modules.update(self.oldmods);self.tmp.cleanup()
 def change(self,fn):
  v=copy.deepcopy(self.original);fn(v);self.path.write_text(json.dumps(v))
 def admission(self):return P.admission(self.C,self.sr,self.m)
 def test_actual_producer_and_shared_child(self):
  self.assertEqual(self.admission()['cutoff_epoch'],10000);self.assertFalse(self.calls[-1])
 def test_cold_entry_still_full(self):
  self.container=None
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(ValueError):self.admission()
  self.assertTrue(self.calls[-1])
 def test_missing_guest_proof_refuses(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(ValueError):self.admission()
 def test_wrong_source(self):
  self.change(lambda v:v.update(source=dict(self.sr,sha256='0'*64)))
  with self.assertRaises(ValueError):self.admission()
 def test_wrong_cid(self):
  self.container='d'*64
  with self.assertRaises(ValueError):self.admission()
 def test_wrong_owner(self):
  self.change(lambda v:v.update(name='other'))
  with self.assertRaises(ValueError):self.admission()
 def test_wrong_boot(self):
  with patch.object(P,'boot',return_value='other'):
   with self.assertRaises(ValueError):self.admission()
 def test_wrong_time_namespace(self):
  with patch.object(P,'time_ns',return_value='time:[555]'):
   with self.assertRaises(ValueError):self.admission()
 def test_extended_deadline(self):
  self.change(lambda v:v['phase'].update(deadline=4501.))
  with self.assertRaises(ValueError):self.admission()
 def test_expired_parent(self):
  self.clock['mono']=4321.
  with self.assertRaises(ValueError):self.admission()
 def test_expired_authority(self):
  self.clock['wall']=10001.
  with self.assertRaises(ValueError):self.admission()
 def test_writable_mount_refuses(self):
  self.inspect['Mounts'][0]['RW']=True
  with self.assertRaises(ValueError):self.admission()
 def test_forged_path_refuses(self):
  with patch.dict(os.environ,{P.FLAG:str(self.leaf/'PHASE.json')}):
   with self.assertRaises(ValueError):self.admission()
 def test_mutated_owned_refuses(self):
  p=self.leaf/'OWNED.json';v=json.loads(p.read_text());v['name']='other';p.write_text(json.dumps(v))
  with self.assertRaises(ValueError):self.admission()
 def test_wrong_directory_identity(self):
  self.change(lambda v:v['directory'].update(inode=0))
  with self.assertRaises(ValueError):self.admission()
 def test_extra_external_hardlink_refuses(self):
  os.link(self.path,self.leaf/'unowned-link')
  with self.assertRaises(ValueError):self.admission()
 def test_staging_wrong_inode_refuses(self):
  pending=next(q for q in self.d.iterdir()if q!=self.path)
  # Fixture only: replace expected retained alias, never experiment evidence.
  pending.unlink();pending.write_bytes(self.path.read_bytes())
  with self.assertRaises(ValueError):self.admission()
 def test_extra_custody_file_refuses(self):
  (self.d/'unexpected').write_bytes(b'x')
  with self.assertRaises(ValueError):self.admission()
 def test_actual_contract_and_native_plugin_entry(self):
  io=types.ModuleType('sourceio');io.need=need;io.ref=ref;io.obj=obj;io.checked=lambda r:Path(r['path']);io.write=write
  bm=types.ModuleType('bind_model');bm.readset=lambda sr:[]
  g=types.ModuleType('g1_contract');g.SCOPE=self.m['service_experiment']
  perf=types.ModuleType('bole_performance_profile');perf.FLAG='BOLE_PAIRED_PERFORMANCE_ENABLE';perf.select=lambda *a:True
  with patch.dict(sys.modules,{'sourceio':io,'bind_model':bm,'g1_contract':g,'bole_performance_profile':perf}):
   actual=module('contract090',NEW['contract090.py'],self.root/'contract090.py')
   self.assertEqual(actual.source(self.sr),self.m)
   native=module('_actual_native_receipt',(BASE/'native_receipt090.py').read_bytes(),BASE/'native_receipt090.py')
   torch=types.SimpleNamespace(npu=types.SimpleNamespace(matmul=types.SimpleNamespace(allow_hf32=True)))
   signal=types.SimpleNamespace(SIGUSR1=10,SIG_DFL=0,SIG_IGN=1,getsignal=lambda n:0,signal=lambda *a:None)
   native.signal=signal
   with patch.dict(sys.modules,{'torch':torch,'torch_npu':types.SimpleNamespace()}),patch.dict(os.environ,{'DENSE_OPPORTUNITY090_ENABLE':'1','DENSE_OPPORTUNITY090_SOURCE_REF':json.dumps(self.sr),'DENSE_OPPORTUNITY090_RECEIPT_ROOT':str(self.receipt)}):
    self.assertTrue(callable(native.register()));self.assertFalse(torch.npu.matmul.allow_hf32)
 def test_actual_environment_and_both_server_arms_preserve_phase(self):
  ext=module('_actual_external_phase',NEW['external025.py'],BASE/'external025.py');ext.OUT=self.out
  env=ext.environment(self.expected);self.assertEqual(env[P.FLAG],str(self.path))
  # Actual server apply_environment cannot erase the non-BOLE custody key.
  tree=__import__('ast').parse((BASE/'server090.py').read_bytes());node=next(n for n in tree.body if isinstance(n,__import__('ast').FunctionDef)and n.name=='apply_environment')
  ns={};exec(compile(__import__('ast').Module(body=[node],type_ignores=[]),'actual-server-apply','exec'),ns)
  for arm in ('native_ar','bole'):
   e={P.FLAG:str(self.path),'BOLE_OLD':'1'};ns['apply_environment'](e,{P.FLAG:str(self.path),'ARM':arm});self.assertEqual(e[P.FLAG],str(self.path));self.assertNotIn('BOLE_OLD',e)
 def test_complete_exact_inverse(self):
  self.assertEqual(A.inverse(NEW,DELTA),BASEFILES)
  self.assertEqual(set(DELTA),set(NAMES)|{'shared_phase_clock.py'})
if __name__=='__main__':unittest.main()
