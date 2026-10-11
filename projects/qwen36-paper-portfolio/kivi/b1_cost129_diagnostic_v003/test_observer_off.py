"""Source-projected inert control-path audit, not tensor math/NPU permission."""
import ast,hashlib,importlib.util,json,os,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
BASE=Path(os.environ["KIVI_SCREEN_PRODUCER_ARCHIVE"])/"producer.py"
PIN="f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5"
NEW_PIN="1687f25252dc5ca94c69b666e1307f5721e83a81da74cccfa4c7e25a3ed2e726"
RESULTS={}
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def tree(path):return ast.parse(path.read_bytes())
def method(path):
 cls=next(n for n in tree(path).body if isinstance(n,ast.ClassDef)and n.name=="PackedBatch")
 return next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="append_read")
def row_loop(path):
 return next(n for n in ast.walk(method(path))if isinstance(n,ast.For)and
  any(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=="update"
  and any(k.arg=="controls"for k in x.keywords)for x in ast.walk(n)))
class Prefix(tuple):
 calls=0;copied=0
 def __iter__(self):
  type(self).calls+=1;type(self).copied+=len(self);return super().__iter__()
class Storage:
 def __init__(self,n):self.n=n
 def data_ptr(self):return self.n
class Tensor:
 def __init__(self,shape,ptr):self.shape=shape;self.dtype="bfloat16";self.device="npu:0";self.ptr=ptr
 def is_contiguous(self):return True
 def untyped_storage(self):return Storage(self.ptr)
 def __getitem__(self,key):return self
class Request:
 def __init__(self,length):
  self.slot=0;self.epoch=1;self.owner="actual-test-owner";self.generation=length;self.length=length
  self.pending=False;self.read=False
  self.kp=Prefix(range(length//128));self.vp=Prefix(range(length-128))
class Arena:
 def __init__(self,mod,events,length=32768):
  self.dtype="bfloat16";self.device="npu:0";self.bits=2
  self.pool={n:Tensor((1,),100+i)for i,n in enumerate(mod.FIELDS)}
  self.r=Request(length);self.events=events
 def owned(self,r):
  if r is not self.r or r.slot!=0 or r.epoch!=1:raise ValueError("inert owner rejection")
  self.events.append("owned")
 def begin(self,r,k,v,p):
  self.owned(r);assert r.length==p and not r.pending;r.pending=True;self.events.append("begin");return r.generation
 def view(self,r):self.events.append("view");return object()
 def finish(self,r,ticket):
  self.owned(r);assert r.pending and r.read and r.generation==ticket
  r.pending=False;r.read=False;r.length+=1;r.generation+=1;self.events.append("finish")
class Meta:
 batch=1
 def __init__(self,events):self.events=events
 def refresh(self,views):self.events.append("metadata.refresh")
 def assert_tensors(self,q,fmt):self.events.append("metadata.assert_tensors")
 def assert_live(self):self.events.append("metadata.assert_live")
def full_off(mod,length=32768,wrong_owner=False):
 events=[];a=Arena(mod,events,length)
 torch=types.SimpleNamespace(float16="float16",bfloat16="bfloat16",
  npu=types.SimpleNamespace(is_current_stream_capturing=lambda:False,synchronize=lambda:events.append("sync")))
 dl=types.SimpleNamespace(Request=Request,CompactArena=Arena)
 b=mod.PackedBatch(torch,dict(kernel=object(),metadata=object(),lifecycle=dl,callback=object()),
  source_refs={},device_properties={},get_format=lambda x:2,
  qualify=lambda:(_ for _ in ()).throw(AssertionError("cold qualify in steady OFF")),
  actual_identity=lambda:(_ for _ in ()).throw(AssertionError("process I/O in steady OFF")),rank=0,
  publish=lambda *x:(_ for _ in ()).throw(AssertionError("publication in steady OFF")),
  diagnostic=False,model_qualify=lambda:None)
 b.qualified=True;b.qualified_identity=dict(pid=1)
 b.metadata=Meta(events);out=Tensor((1,6,256),999)
 def model(q,pool,meta):
  assert pool is a.pool and meta is b.metadata
  events.append("same model");return out
 b.model=model
 if wrong_owner:a.r.epoch=2
 with patch.dict(os.environ,{mod.FLAG:"1","QWEN36_KIVI_PACKED_QKAV_SOURCE_CANDIDATE":"1",mod.TIMING_FLAG:"1"}):
  with patch.object(Path,"read_bytes",side_effect=AssertionError("file bytes on steady OFF")),patch.object(Path,"read_text",side_effect=AssertionError("text on steady OFF")):
   result=b.append_read(a,(a.r,),Tensor((1,6,256),1),Tensor((1,256),2),Tensor((1,256),3),(length,),
    pre_refs=None,capture_raw=False,sequence="audit0")
 return result is out,events,(a.r.length,a.r.generation,a.r.pending)
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  assert hashlib.sha256(BASE.read_bytes()).hexdigest()==PIN and hashlib.sha256((ROOT/"producer.py").read_bytes()).hexdigest()==NEW_PIN
  cls.old=load(BASE,"_audit_original");cls.new=load(ROOT/"producer.py","_audit_new")
 def test01_real_complete_OFF_method_same_model_metadata_finish_fences(self):
  Prefix.calls=Prefix.copied=0;old=full_off(self.old)
  count=(Prefix.calls,Prefix.copied)
  Prefix.calls=Prefix.copied=0;new=full_off(self.new)
  self.assertEqual(old,new);self.assertEqual(count,(2,32896));self.assertEqual(Prefix.calls,0)
  RESULTS["OFF_first_decode_old_list_copies"]=count;RESULTS["OFF_new_list_copies"]=0
  RESULTS["same_actual_method_trace"]=old[1]
 def test02_long_tail_same_output_identity_and_all_calls(self):
  Prefix.calls=Prefix.copied=0;old=full_off(self.old,33790);count=(Prefix.calls,Prefix.copied)
  Prefix.calls=Prefix.copied=0;new=full_off(self.new,33790)
  self.assertEqual(old,new);self.assertEqual(count,(2,33925));self.assertEqual(Prefix.calls,0)
 def test03_original_and_new_reject_dynamic_owner(self):
  for m in(self.old,self.new):
   with self.assertRaisesRegex(ValueError,"inert owner rejection"):full_off(m,wrong_owner=True)
 def test04_real_diagnostic_loop_fields_byte_equal(self):
  for length in(32768,32895,32896,33790):
   actual=[]
   for path in(BASE,ROOT/"producer.py"):
    r=Request(length);rows=[dict(request_id=r.owner)];records=[]
    env=dict(self=types.SimpleNamespace(diagnostic=True,rank=0),rows=rows,requests=(r,),tickets=(r.generation,),
     identity=dict(pid=1),pending_refs=[],pub=lambda label,value:records.append((label,value)))
    exec(compile(ast.Module(body=[row_loop(path)],type_ignores=[]),str(path),"exec"),env)
    actual.append((json.dumps(records,sort_keys=True),rows))
   self.assertEqual(*actual)
 def test05_source_delta_only_ignored_diagnostic_dict_update(self):
  a=tree(BASE);b=tree(ROOT/"producer.py")
  loop=row_loop(ROOT/"producer.py")
  self.assertIsInstance(loop.body[0],ast.If);self.assertEqual(ast.unparse(loop.body[0].test),"self.diagnostic")
  # Normalize exactly the one added conditional; all other candidate/guard code identical.
  target=next(n for n in ast.walk(b)if isinstance(n,ast.For)and ast.dump(n)==ast.dump(loop))
  target.body[:1]=target.body[0].body
  self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
 def test06_full1024_logical_copy_count_not_walltime(self):
  n=sum(p//128+p-128 for p in range(32768,33791))
  self.assertEqual(n,34178938)
  RESULTS["logical_pointer_references_per_request_FA"]=n
  RESULTS["logical_pointer_bytes_B1_all64"]=n*64*8
  RESULTS["logical_pointer_bytes40_all64"]=n*64*40*8
  RESULTS["not_measured_memory_traffic_or_E2E"]=True
 def test07_actual_all64_timing_layout_counts_descriptors_without_file_reads(self):
  mf=json.loads((ROOT/"SOURCE_MANIFEST.json").read_bytes())
  path=(Path(os.environ["KIVI_SCREEN_REVIEWED_DEPS"])/"callback.py" if os.name=="nt" else Path(mf["runtime_roles"]["callback"]["path"]))
  assert hashlib.sha256(path.read_bytes()).hexdigest()==mf["runtime_roles"]["callback"]["sha256"]
  callback=load(path,"_audit_callback")
  class T(Tensor):
   def stride(self):return (1,)
   def element_size(self):return 2
   def numel(self):return 1
   def storage_offset(self):return 0
   def data_ptr(self):return self.ptr
   def untyped_storage(self):return types.SimpleNamespace(data_ptr=lambda:self.ptr,nbytes=lambda:2)
  static={};layers={};contexts={}
  for i in range(64):
   name="layer%02d"%i;pair=[T((1,),i*2+100),T((1,),i*2+101)]
   static[name]=types.SimpleNamespace(kv_cache=pair)
   layers[name]=dict(kind="FA"if i<16 else "GDN",views=[callback.scalar_tensor(t)for t in pair])
   if i<16:
    pool={n:T((1,),1000+i*9+j)for j,n in enumerate((*self.old.FIELDS,"shifts"))}
    pool.update(allocated_bytes=18,dense_shadow_bytes=0)
    contexts[name]=dict(arena=types.SimpleNamespace(pool=pool,pool_bytes=18))
  runner=types.SimpleNamespace(speculative_config=None,compilation_config=types.SimpleNamespace(static_forward_context=static))
  for path in(ROOT/'installer.py',):
   ins=load(path,"_audit_layout");calls=[]
   cb=types.SimpleNamespace(scalar_tensor=lambda t:(calls.append(t),callback.scalar_tensor(t))[1])
   with patch.object(Path,"read_bytes",side_effect=AssertionError("file read in layout")),patch.object(Path,"read_text",side_effect=AssertionError("file read in layout")):
    ins.timing_layout(runner,dict(layers=layers),contexts,cb)
   self.assertEqual(len(calls),272)
  RESULTS["actual_OFF_layout_descriptor_calls_per_scheduler_step"]=272
 def test08_actual_common_cached_ingress_no_static_hash_and_dynamic_guards(self):
  S=type("SchedulerOutput",(),{"__module__":"vllm.v1.core.sched.output"})
  s=S();s.scheduled_new_reqs=[];s.finished_req_ids=[];s.scheduled_spec_decode_tokens=[];s.preempted_req_ids=[]
  s.scheduled_cached_reqs=types.SimpleNamespace(resumed_req_ids=[],req_ids=['live'])
  ident=dict(pid=1);binding=types.SimpleNamespace(owner=dict(rank_bindings={'0':ident}),seen={'live'})
  for path in(ROOT/'installer.py',):
   ins=load(path,"_audit_ingress")
   with patch.object(Path,"read_bytes",side_effect=AssertionError("file read in cached ingress")),patch.object(Path,"read_text",side_effect=AssertionError("file read in cached ingress")):
    self.assertEqual(ins.timing_cached_ingress(binding,s,S,ident,0),[])
    s.preempted_req_ids=['live']
    with self.assertRaises(ValueError):ins.timing_cached_ingress(binding,s,S,ident,0)
    s.preempted_req_ids=[]
    with self.assertRaises(ValueError):ins.timing_cached_ingress(binding,s,S,dict(pid=2),0)
 def test09_real_loader_installer_runtime_role_closure(self):
  mf=json.loads((ROOT/"SOURCE_MANIFEST.json").read_bytes())
  l=load(ROOT/"loader.py","_audit_pinned_loader");ins=load(ROOT/"installer.py","_audit_pinned_installer")
  self.assertEqual(l.PRODUCER_SHA,NEW_PIN);self.assertEqual(ins.PRODUCER_SHA,NEW_PIN)
  self.assertEqual(mf["runtime_roles"]["producer"]["sha256"],NEW_PIN)
  self.assertEqual(l.INSTALLER_SHA,hashlib.sha256((ROOT/"installer.py").read_bytes()).hexdigest())
  self.assertEqual(mf["runtime_roles"]["installer"]["sha256"],l.INSTALLER_SHA)
  self.assertEqual(hashlib.sha256((ROOT/"producer.py").read_bytes()).hexdigest(),NEW_PIN)
if __name__=="__main__":
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 print(json.dumps(dict(tests=result.testsRun,successful=result.wasSuccessful(),observations=RESULTS,
  source_projected_inert_tensor_fixture=True,numerical_or_NPU_qualification=False)))
 raise SystemExit(not result.wasSuccessful())
