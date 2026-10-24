import ast,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
PARENT=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/prepared-source-short8-v16")
sys.path.insert(0,str(ROOT))
import fa_cache_advisory as A

def need(v,s):
 if not v:raise ValueError(s)
class C:
 need=staticmethod(need)
 @staticmethod
 def ref(p):
  p=Path(p);raw=p.read_bytes()
  return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 @staticmethod
 def checked(r):
  need(C.ref(r['path'])==r,'same completeRef');return Path(r['path'])
 @staticmethod
 def obj(r):return json.loads(C.checked(r).read_text())
 @staticmethod
 def write(p,v):
  with open(p,'x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
  return C.ref(p)

def module(n,stubs):
 with patch.dict(sys.modules,stubs):
  spec=importlib.util.spec_from_file_location(n,ROOT/(n+'.py'))
  m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

_spec=importlib.util.spec_from_file_location('actual_sourceio',PARENT/'sourceio.py')
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)

class Test(unittest.TestCase):
 def setUp(self):
  A._AUTH=None;self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'dense';self.root.mkdir()
  self.receipts=self.root/'receipts';self.receipts.mkdir()
  self.leaf=self.receipts/'FASTPATH-NUMERIC-R0';self.leaf.mkdir()
  (self.root/'SOURCE_BOUND.json').write_text('{}')
  source=C.ref(self.root/'SOURCE_BOUND.json')
  self.m=json.loads((PARENT/'SOURCE_TEMPLATE.json').read_text())
  self.m.update(root=str(self.root),model_receipt_root=str(self.receipts),files={},
                own_fa_cache_advisory=dict(A.CONTRACT))
  self.c=dict(C=C,m=self.m,source=source,rank=0,root=self.leaf,used=0,metadata_bytes=0)
  self.cid='a'*64;self.membership='/docker/'+self.cid
  self.native_identity=module('worker_resource_v2',{})
  self.cg=self.root/'cg'/self.cid;self.cg.mkdir(parents=True)
  for n,v in {'memory.limit_in_bytes':str(48*2**30),'memory.usage_in_bytes':'4096',
              'cgroup.procs':str(os.getpid()),'memory.stat':'cache 0\nrss 4096\n'}.items():(self.cg/n).write_text(v)
  self.c['t']=types.SimpleNamespace(distributed=types.SimpleNamespace(is_initialized=lambda:True,get_world_size=lambda:4,get_rank=lambda:0))
  (self.root/'OWNED.json').write_text(json.dumps(dict(cid=self.cid,source=source,
     image=self.native_identity.IMAGE,arm='dense',mounts={str(self.root):[str(self.root),True]})))
  oldread=self.native_identity.read
  def kernel(path):
   path=str(path)
   if path=='/proc/self/cgroup':return '5:memory:'+self.membership+'\n'
   if path=='/proc/self/mountinfo':return '1 0 0:1 /docker '+str(self.cg.parent)+' rw - cgroup cgroup rw,memory\n'
   if path=='/proc/self/status':return 'VmRSS: 1 kB\nVmHWM: 1 kB\n'
   if path=='/proc/self/stat':return str(os.getpid())+' (python) '+' '.join(['S']+['0']*18+['42'])
   return oldread(path)
  self.native_identity.read=kernel
  self.D=types.SimpleNamespace(template_disk_cap=lambda:6375342080,archive_before=lambda *a,**k:None)
  self.B=module('fa_block_store',{'disk_ledger':self.D})
  self.m['files']={'fa_cache_advisory.py':C.ref(A.__file__),'fa_block_store.py':C.ref(self.B.__file__),'worker_resource_v2.py':C.ref(self.native_identity.__file__)}
  self.S=types.SimpleNamespace(_CONTEXT=self.c)
  self.env=patch.dict(os.environ,{A.FLAG:'1'});self.env.start()
  self.mods=patch.dict(sys.modules,{'worker_resource_v2':self.native_identity,
      'fa_block_store':self.B,'fastpath_numeric_sink':self.S,
      'resource32k_runtime':types.SimpleNamespace(require_actual=lambda c:None)});self.mods.start()
  old=Path.read_text;member=self.membership
  self.paths=patch.object(Path,'read_text',lambda p,*a,**k:
     '5:memory:'+member+'\n' if str(p)=='/proc/self/cgroup' else old(p,*a,**k));self.paths.start()
  self.hints=[]
  self.adv=patch.object(A.os,'posix_fadvise',side_effect=self.hint);self.adv.start()
 def tearDown(self):
  self.adv.stop();self.paths.stop();self.mods.stop();self.env.stop();self.tmp.cleanup()
 def hint(self,fd,offset,length,advice):
  self.hints.append((os.fstat(fd).st_ino,offset,length,advice));return None
 def store(self):return self.B.Store(self.c)
 def test_actual_store_and_reader_full_hash(self):
  store=self.store();data=b'x'*65536
  r=store.tensor(iter([data]),shape=[65536],dtype='uint8',family='L3:native:key',witness={'frame':1})
  R=self.B.Reader(store.root)
  self.assertEqual(R.raw(r,expected_witness={'frame':1}),data)
  store.put(data)
  self.assertEqual(len(self.hints),3)
  self.assertEqual(len(list(store.root.glob('*.bin'))),1)
  self.assertTrue(all(x[1:3]==(0,65536)for x in self.hints))
 def test_off_keeps_actual_original_read(self):
  os.environ[A.FLAG]='0';self.m.pop('own_fa_cache_advisory')
  store=self.store();r=store.put(b'hello')
  self.assertEqual(self.B.read_ref(r,store.root,65536),b'hello');self.assertEqual(self.hints,[])
 def test_advisory_false_fails_sticky(self):
  store=self.store()
  with patch.object(A.os,'posix_fadvise',return_value=False):
   with self.assertRaises(ValueError):store.put(b'hello')
  self.assertTrue(store.failed);self.assertTrue(list(store.root.glob('*.bin')))
  with self.assertRaises(ValueError):store.put(b'hello')
 def test_advisory_exception_fails_sticky(self):
  store=self.store()
  with patch.object(A.os,'posix_fadvise',side_effect=OSError('unsupported')):
   with self.assertRaises(ValueError):store.put(b'hello')
  self.assertTrue(store.failed)
 def test_failed_fsync_never_advises(self):
  store=self.store()
  with patch.object(A.os,'fsync',side_effect=OSError('sync failure')):
   with self.assertRaises(ValueError):store.put(b'hello')
  self.assertEqual(self.hints,[]);self.assertTrue(store.failed)
 def test_hash_drift_never_advises(self):
  store=self.store();r=store.put(b'hello');self.hints.clear()
  Path(r['path']).write_bytes(b'HELLO')
  with self.assertRaises(ValueError):self.B.read_ref(r,store.root,65536)
  self.assertEqual(self.hints,[])
 def test_symlink_leaf_and_hardlink_refuse(self):
  store=self.store();r=store.put(b'hello');self.hints.clear();p=Path(r['path'])
  link=store.root/'alias';os.link(p,link)
  with self.assertRaises(ValueError):self.B.read_ref(r,store.root,65536)
  link.unlink();p.unlink();p.symlink_to(self.root/'SOURCE_BOUND.json')
  with self.assertRaises(ValueError):self.B.read_ref(r,store.root,65536)
  self.assertEqual(self.hints,[])
 def test_foreign_source_context_pid_and_cgroup_refuse(self):
  store=self.store();r=store.put(b'hello');self.hints.clear()
  for mutate,restore in [
   (lambda:setattr(self.S,'_CONTEXT',dict(self.c)),lambda:setattr(self.S,'_CONTEXT',self.c)),
   (lambda:self.c.update(rank=1),lambda:self.c.update(rank=0)),
   (lambda:A._AUTH.update(pid=-1),lambda:A._AUTH.update(pid=os.getpid())),
   (lambda:A._AUTH.update(membership='/other'),lambda:A._AUTH.update(membership=self.membership))]:
   mutate()
   with self.assertRaises(ValueError):self.B.read_ref(r,store.root,65536)
   restore()
  self.assertEqual(self.hints,[])
 def test_root_replacement_refuses(self):
  store=self.store();r=store.put(b'hello');self.hints.clear()
  store.root.rename(self.leaf/'old');store.root.mkdir()
  with self.assertRaises(ValueError):A.selected(store.root,Path(r['path']))
  self.assertEqual(self.hints,[])
 def test_only_blob_not_pt_or_formal(self):
  store=self.store();p=store.root/'G1-O0.pt';p.write_bytes(b'not a blob')
  with self.assertRaises(ValueError):self.B.read_ref(C.ref(p),store.root,65536)
  A._AUTH=None;self.m['performance_profile']={'formal_performance':True}
  with self.assertRaises(ValueError):A.configure(self.c,store.root)
  self.assertEqual(self.hints,[])
 def test_short_read_and_same_inode_change_refuse(self):
  store=self.store();r=store.put(b'hello');self.hints.clear()
  with patch.object(A.os,'read',return_value=b'he'):
   with self.assertRaises(ValueError):self.B.read_ref(r,store.root,65536)
  self.assertEqual(self.hints,[])
  def mutate(fd,o,n,a):Path(r['path']).write_bytes(b'HELLO');return None
  with patch.object(A.os,'posix_fadvise',side_effect=mutate):
   with self.assertRaises(ValueError):self.B.read_ref(r,store.root,65536)
 def test_real_stat_sample_and_missing_best_effort(self):
  cg=self.root/'stat-only';cg.mkdir()
  (cg/'memory.stat').write_text('cache 10\nrss 20\ntotal_cache 11\ndirty 0\nwriteback 0\n')
  self.assertEqual(A.sample_memory_stat(cg)['values']['cache'],10)
  (cg/'memory.stat').write_text('cache 1\ncache 2\nrss 0\n')
  self.assertFalse(A.sample_memory_stat(cg)['available'])
 def test_actual_guard_first_refusal_preserves_exception_and_reservations(self):
  W=module('worker_resource_v2',{})
  g=W.Guard.__new__(W.Guard);g.c=self.c;g.generation=1;g.ordinal=3;g.enter_RSS=1;g.enter_HWM=1
  state={'failed':None,'slots':{str(i):{'bytes':W.PER_RANK}for i in range(4)}}
  v=dict(source=self.c['source'],rank=0,pid=os.getpid(),start_ticks=1,cid=self.cid,
   limit=W.LIMIT,usage=W.LIMIT-4*W.PER_RANK+1,VmRSS=1,VmHWM=1,
   memory_stat={'available':True,'values':{'cache':10,'rss':20}})
  before=json.dumps(state,sort_keys=True)
  with self.assertRaisesRegex(ValueError,'actual cgroup current plus all active'):g.check(state,v)
  self.assertEqual(before,json.dumps(state,sort_keys=True))
  report=json.loads((self.leaf/'G1-O3-RAM-first_refusal.json').read_text())
  self.assertEqual(report['reserved_total'],4*W.PER_RANK)
  self.assertEqual(report['memory_stat'],v['memory_stat'])
  with self.assertRaisesRegex(ValueError,'actual cgroup current plus all active'):g.check(state,v)
  self.assertEqual(g.first_refusal_record_error,'FileExistsError')
 def test_terminal_actual_field_contract(self):
  T=module('ram_terminal_join',{})
  self.assertIn('memory_stat',T.KEYS)
  A.validate_memory_stat({'available':True,'values':{'cache':0,'rss':4096}})
  for value in ({'available':True,'values':{'cache':False,'rss':1}},
                {'available':True,'values':{'cache':1,'rss':1,'unknown':1}},
                {'available':False,'error_type':'bad/path'}):
   with self.assertRaises(ValueError):A.validate_memory_stat(value)
 def test_actual_server_environment_with_actual_profile_and_sourceio(self):
  import importlib.util
  def native(n):
   spec=importlib.util.spec_from_file_location(n,PARENT/(n+'.py'))
   mod=importlib.util.module_from_spec(spec);sys.modules[n]=mod;spec.loader.exec_module(mod);return mod
  spec=importlib.util.spec_from_file_location('adapt_cache',ROOT/'adapt_cache_diagnostic.py')
  adapt=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapt)
  files={n:(PARENT/n).read_bytes()for n in
         ('fa_block_store.py','worker_resource_v2.py','ram_terminal_join.py','server090.py','preflight114.py')}
  changed,delta=adapt.adapt(files)
  self.assertEqual(adapt.inverse(changed,delta),files)
  m=json.loads((PARENT/'SOURCE_TEMPLATE.json').read_text())
  m.update(own_fa_cache_advisory=dict(A.CONTRACT),root=str(self.root),model_receipt_root=str(self.receipts))
  m['files']['fa_cache_advisory.py']=C.ref(A.__file__)
  p=self.root/'BOOTSTRAP-SOURCE.json';p.write_text(json.dumps(m));sr=C.ref(p)
  with patch.dict(sys.modules,{'contract090':C}),patch.object(sys,'path',[str(ROOT),str(PARENT),*sys.path]):
   perf=native('bole_performance_profile');obs=native('observation_profile');g1=native('g1_contract')
   S=types.ModuleType('actual_server_environment');S.__file__=str(ROOT/'server090.py')
   exec(compile(changed['server090.py'],S.__file__,'exec'),S.__dict__)
   env=S.environment({perf.FLAG:'1'},sr,self.receipts)
   self.assertEqual(env[A.FLAG],'1')
   self.assertNotIn(A.FLAG,{perf.FLAG:'1'})
 def test_partial_reads_complete_before_hint(self):
  store=self.store();r=store.put(b'hello');self.hints.clear()
  with patch.object(A.os,'read',side_effect=[b'he',b'llo',b'']):
   self.assertEqual(self.B.read_ref(r,store.root,65536),b'hello')
  self.assertEqual(len(self.hints),1)
 def test_actual_seven_stage_terminal_accepts_new_stat(self):
  W=self.native_identity;T=module('ram_terminal_join',{})
  g=W.Guard.__new__(W.Guard);g.c=self.c;g.generation=1;g.ordinal=0
  v=W.identity(self.c);g.enter_RSS=v['VmRSS'];g.enter_HWM=v['VmHWM']
  for stage in T.STAGES:g.record(stage,v,(3 if stage=='sink_returned'else 4)*W.PER_RANK)
  expected=set();ids={}
  refs=T.frame(C,self.m,self.c['source'],0,1,0,self.leaf,expected,ids,
               dict(cid=self.cid,owned=C.ref(self.root/'OWNED.json')))
  self.assertEqual(len(refs),7);self.assertEqual(len(expected),7)
  p=self.leaf/'G1-O0-RAM-post_wire.json';value=json.loads(p.read_text())
  value['memory_stat']['values']['cache']=False;p.write_text(json.dumps(value))
  with self.assertRaises(ValueError):
   T.frame(C,self.m,self.c['source'],0,1,0,self.leaf,set(),{},
           dict(cid=self.cid,owned=C.ref(self.root/'OWNED.json')))
 def test_guard_math_cap_original_ast_preserved(self):
  a=ast.parse((ROOT/'worker_resource_v2.py').read_text())
  b=ast.parse((PARENT/'worker_resource_v2.py').read_text())
  def check(tree):
   cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Guard')
   return next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='check')
  n=check(a);n.body=[x for x in n.body if not(isinstance(x,ast.If)and isinstance(x.test,ast.UnaryOp))]
  self.assertEqual(ast.dump(n),ast.dump(check(b)))
  for name in ('LIMIT','PER_RANK'):
   get=lambda t:next(x for x in t.body if isinstance(x,ast.Assign)and any(isinstance(y,ast.Name)and y.id==name for y in x.targets))
   self.assertEqual(ast.dump(get(a)),ast.dump(get(b)))

if __name__=='__main__':unittest.main()
