"""Actual closure dataflow and import-boundary regressions; no native proof.
Local archive mode executes the exact reader return expression with dependency
sentinels; MAIN full software invokes the original complete reader factory and
its strict file loader. No fixture inserts compiler keys into that return.
Framework imports are transparent module fixtures here, never HAL qualification.
"""
import ast,copy,hashlib,importlib.util,inspect,io,json,os,sys,tempfile,types,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ARCHIVE=os.environ.get("KIVI_FRAMEWORK_ARCHIVE_FIXTURE")
DEPS=os.environ.get("KIVI_PUBLICATION_ARCHIVE_FIXTURE")
READER_SHA="b6544b2edc38b513495716a07d8f4638bdbbe63561988318467149b815b78a81"
READER_MF="0fe4a4ed69031586d0684aa454f39a2e5bc2d03f0a02ed6861423a6795ed74b3"
def load(name):
 s=importlib.util.spec_from_file_location("_closure_test_"+name,HERE/(name+".py"));m=importlib.util.module_from_spec(s)
 sys.modules[s.name]=m;s.loader.exec_module(m);return m
L=load("loader");B=load("runtime_boundary");W=load("worker");P=load("producer")
_READER=None
def original_reader():
 global _READER
 if _READER is not None:return dict(_READER)
 if ARCHIVE:
  path=Path(ARCHIVE)/"main.py";wire=path.read_bytes()
  if hashlib.sha256(wire).hexdigest()!=READER_SHA:raise ValueError("exact actual reader source")
  tree=ast.parse(wire);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="runtime_modules")
  statement=next(n for n in fn.body if isinstance(n,ast.Return))
  # Exact actual factory expression, not a handwritten dictionary of expected keys.
  names={n.id for n in ast.walk(statement.value)if isinstance(n,ast.Name)}-{"dict"}
  env={n:object()for n in names}
  _READER=eval(compile(ast.Expression(statement.value),str(path),"eval"),env)
 else:
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  r=next(x for x in m["dependencies"]if x["sha256"]==READER_SHA)
  entry=L.module("_closure_actual_reader_factory",r)
  _READER=entry.runtime_modules(READER_MF)
 return dict(_READER)
def original(name,sha,filename=None):
 if DEPS:path=Path(DEPS)/(filename or name+".py")
 else:
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  path=Path(next(x for x in m["dependencies"]if x["sha256"]==sha)["path"])
 ref=L.ref(path)
 if ref["sha256"]!=sha:raise ValueError("actual source before module execution")
 return L.module("_closure_original_"+name,ref),ref
def loaded_context():
 """Execute actual own load() body; only unchanged outer admission is fixture.
 Actual formal/metadata files are checked, loaded and returned by L.module.
 """
 source=dict(path="/fixture/source",bytes=1,sha256="f"*64)
 roles={}
 for name in ("installer","producer","provenance","kernel","spans","book","bindings",
              "assignment_capture","assignment_oracle","journal","formal","metadata","kivi_layout_consumer"):
  roles[name]=dict(path="/fixture/"+name+".py",bytes=1,sha256="a"*64)
 formal,roles["formal"]=original("formal","d9e8dd2fa2656c79616e3576a2e58b3ce82a113f6c5fd55e4b41e504ae246841")
 metadata,roles["metadata"]=original("metadata","e1a07bf5cac73bc689130e2a68ba54297e11f2513610d1e2003ba4bb545df539")
 for name,sha in (("installer",L.INSTALLER_SHA),("producer",L.PRODUCER_SHA),
                  ("provenance",L.PROVENANCE_SHA),("kernel",L.KERNEL_SHA)):roles[name]["sha256"]=sha
 roles["donor_main"]=dict(path="/fixture/donor.py",bytes=1,sha256=L.DONOR_MAIN_SHA)
 m=dict(runtime_roles=roles,files=[dict(path="/fixture/"+n+".py",bytes=1,sha256="b"*64)
  for n in("cann_python","prebind","worker","runtime_owner","ownership","raw_journal","finish_after_native","explicit_provider","provider_independent","explicit_geometry")])
 memory=types.SimpleNamespace(memory=lambda **kw:dict(process=dict(pid=12)),consume_memory=lambda *a,**kw:None)
 cann=types.SimpleNamespace(install=lambda *a:dict(fixture_only=True))
 returned=original_reader()
 # Original donor additions are irrelevant to this compiler defect. No triton/tl.
 donor=types.SimpleNamespace(load_modules=lambda sha:({},returned,object(),object(),object(),object(),object()))
 installer=types.SimpleNamespace(CRITICAL_SHA=dict(kernel=L.KERNEL_SHA))
 actual_module=L.module
 def modules(name,ref):
  if ref==roles["formal"]:return formal
  if ref==roles["metadata"]:return metadata
  if ref==roles["donor_main"]:return donor
  if ref["path"].endswith("/cann_python.py"):return cann
  if ref==roles["installer"]:return installer
  return types.SimpleNamespace()
 with patch.object(L,"source",return_value=(m,source)),patch.object(L,"memory_module",return_value=memory),patch.object(L,"module",side_effect=modules):
  result=L.load(source["sha256"],memory_limit=64*1024**3)
 return result,returned
def runtime(initialized=True,rank=0):
 # Execute the exact installed helper functions, not replacement count getters.
 path=Path(os.environ["KIVI_RUNTIME_ABI_ARCHIVE_FIXTURE"])/"triton_utils.py" if os.environ.get("KIVI_RUNTIME_ABI_ARCHIVE_FIXTURE") else None
 if path is None:
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes());path=Path(m["runtime_abi_original_refs"]["helper"]["path"])
 wire=path.read_bytes()
 if len(wire)!=2090 or hashlib.sha256(wire).hexdigest()!=B.HELPER_SHA:raise ValueError("exact helper")
 current=[rank];state=[initialized];calls=[]
 npu=types.SimpleNamespace(is_initialized=lambda:state[0],current_device=lambda:current[0],device_count=lambda:4)
 torch=types.ModuleType("torch");torch.npu=npu;tn=types.ModuleType("torch_npu")
 triton=types.ModuleType("triton");tl=types.ModuleType("triton.language")
 def properties(device):calls.append(device);return dict(num_aicore=7,num_vectorcore=13)
 triton.runtime=types.SimpleNamespace(driver=types.SimpleNamespace(active=types.SimpleNamespace(utils=types.SimpleNamespace(get_device_properties=properties))))
 exports=types.ModuleType("vllm.triton_utils");exports.HAS_TRITON=True;exports.triton=triton;exports.tl=tl
 rt=types.ModuleType(B.HELPER_NAME);rt.__file__=str(path)
 rt.torch=torch;rt.triton=triton;rt.tl=tl;rt.HAS_TRITON=True;rt._NUM_AICORE=-1;rt._NUM_VECTORCORE=-1
 nodes=[n for n in ast.parse(wire).body if isinstance(n,ast.FunctionDef)and n.name in("init_device_properties_triton","get_aicore_num","get_vectorcore_num")]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),"exec"),rt.__dict__)
 modules={"torch":torch,"torch_npu":tn,"vllm.triton_utils":exports,B.HELPER_NAME:rt}
 return torch,tn,triton,tl,rt,modules,current,state,calls
class CompilerClosure(unittest.TestCase):
 def test_original_actual_reader_factory_has_no_four_missing_keys(self):
  mods=original_reader()
  self.assertFalse({"triton","tl","formal","metadata"}&set(mods))
  self.assertTrue({"layout","fields","callback","lifecycle","base"}<=set(mods))
 def test_MAIN_actual_factory_to_full_worker_factory_source_closure(self):
  # Run by MAIN's actual complete software entry, never by a local archive subset.
  # Only the native-class handoff is spied: every preceding worker guard is real.
  self.assertIsNone(ARCHIVE,"requires MAIN exact transitive reader source files; do not promote local projection")
  import functools
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes());mods=original_reader();roles=m["runtime_roles"]
  adapter,_=original("adapter",W.ADAPTER_SHA)
  loaded={name:L.module("_closure_worker_actual_"+name,roles[name])for name in
   ("kernel","metadata","formal","bindings","spans","book","journal")}
  installer=load("installer");prebind=load("prebind");finished=load("finish_after_native")
  L.module("provider_zeroer",roles["spans"])
  L.module("provider_independent",L.own(m,"provider_independent.py"))
  geometry=L.module("explicit_geometry",L.own(m,"explicit_geometry.py"))
  # Unbound actual nested initialize method, executed by integration regression.
  provider=load("explicit_provider")
  tree=ast.parse((HERE/"explicit_provider.py").read_bytes())
  cls=next(n for n in ast.walk(tree)if isinstance(n,ast.ClassDef)and n.name=="ExplicitProviderWorker")
  method=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="initialize_from_config")
  env={};exec(compile(ast.Module(body=[method],type_ignores=[]),str(HERE/"explicit_provider.py"),"exec"),env)
  provider_initialize=env["initialize_from_config"]
  binder=loaded["bindings"].Bindings.__new__(loaded["bindings"].Bindings)
  t,tn,tr,tl,rt,modules,current,state,calls=runtime();handed=[];answer=object()
  @functools.wraps(prebind.make_worker)
  def native_boundary(*args,**kw):
   inspect.signature(prebind.make_worker).bind(*args,**kw)
   handed.append((args,kw));return answer
  boundary=types.SimpleNamespace(make_worker=native_boundary)
  with patch.dict(sys.modules,modules),patch.dict(os.environ,{installer.FLAG:"1"}):
   compiled=L.framework(mods,t,tn,0)
   result=W.make_worker(object(),compiled,adapter,boundary,t,tn,object(),object(),object(),
    layout_owner={},layout_owner_ref={},layout_mf="f"*64,post_owner=None,post_owner_ref=None,
    installer=installer,spans=loaded["spans"],book=loaded["book"],formal=loaded["formal"],
    producer=P,kernel=loaded["kernel"],metadata=loaded["metadata"],journal_module=loaded["journal"],
    source_refs=roles,device_properties=dict(num_aicore=7,num_vectorcore=13),qualify=lambda:None,
    ingress_bindings=binder,finish_module=finished,publish_final=lambda r:None,
    resolve_post_owner=lambda *a:None,provider_initialize=provider_initialize,
    provider_state={},explicit_geometry=geometry)
  self.assertIs(result,answer);self.assertEqual(len(handed),1);self.assertIs(handed[0][0][1],compiled)
  self.assertIs(compiled["fields"],mods["fields"]);self.assertNotIn("triton",mods)
  self.assertIsNotNone(handed[0][1]["resolve_post_owner"])
 def test_actual_own_loader_loads_exact_formal_metadata_without_framework(self):
  before=set(sys.modules);result,donor=loaded_context();m,source,mods,adapter,new,own=result
  self.assertIsNot(mods,donor);self.assertEqual(mods,donor)
  self.assertEqual(new["formal"].capacity(4)["max_length"],33792)
  self.assertEqual(L.ref(new["formal"].__file__),m["runtime_roles"]["formal"])
  self.assertEqual(L.ref(new["metadata"].__file__),m["runtime_roles"]["metadata"])
  self.assertFalse({"torch","torch_npu","triton"}&(set(sys.modules)-before))
 def test_real_framework_return_to_original_boundary_all_four_ranks(self):
  result,donor=loaded_context();mods=result[2];t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  with patch.dict(sys.modules,modules):
   for rank in range(4):
    current[0]=rank;bound=L.framework(mods,t,tn,rank)
    props,proof=B.core_properties(t,bound["triton"],rank,L.ref)
    self.assertIs(bound["triton"],tr);self.assertIs(bound["tl"],tl)
    self.assertEqual(props,dict(num_aicore=7,num_vectorcore=13));self.assertEqual(proof["logical_rank"],rank)
  self.assertEqual(calls,[0,0,1,2,3]);self.assertNotIn("triton",mods);self.assertEqual(mods,donor)
 def test_original_v013_missing_key_reproduces_without_manual_compiler_keys(self):
  result,_=loaded_context()
  with self.assertRaises(KeyError):result[2]["triton"]
  with self.assertRaises(KeyError):result[2]["metadata"]
 def test_CPU_uninitialized_rejected_before_any_framework_import(self):
  result,_=loaded_context();t,tn,tr,tl,rt,modules,current,state,calls=runtime(False)
  import builtins
  old=builtins.__import__;seen=[]
  def importing(name,*args,**kwargs):
   if name in("torch","torch_npu","vllm.triton_utils"):seen.append(name);raise AssertionError("HAL import before guard")
   return old(name,*args,**kwargs)
  with patch.object(builtins,"__import__",side_effect=importing):
   with self.assertRaisesRegex(ValueError,"initialized owned TP4"):L.framework(result[2],t,tn,0)
  self.assertEqual(seen,[]);self.assertEqual(calls,[])
 def test_rank_device_boolean_guard_precedes_framework_import(self):
  mods=original_reader();t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  for rank in(True,4,-1,1):
   with self.assertRaisesRegex(ValueError,"initialized owned TP4"):L.framework(mods,t,tn,rank)
  self.assertEqual(calls,[])
 def test_missing_or_false_actual_exports_cannot_be_fabricated(self):
  mods=original_reader();t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  for name,bad in(("HAS_TRITON",False),("triton",None),("tl",None)):
   old=getattr(modules["vllm.triton_utils"],name);setattr(modules["vllm.triton_utils"],name,bad)
   with patch.dict(sys.modules,modules):
    with self.assertRaisesRegex(ValueError,"actual deployed framework"):L.framework(mods,t,tn,0)
   setattr(modules["vllm.triton_utils"],name,old)
  self.assertEqual(calls,[])
 def test_actual_imported_torch_npu_must_be_same_handles(self):
  mods=original_reader();t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  for name in("torch","torch_npu"):
   bad=dict(modules);bad[name]=types.ModuleType(name)
   with patch.dict(sys.modules,bad):
    with self.assertRaisesRegex(ValueError,"actual deployed framework"):L.framework(mods,t,tn,0)
 def test_actual_helper_binds_both_compiler_objects_not_only_triton(self):
  mods=original_reader();t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  for name in("triton","tl"):
   old=getattr(rt,name);setattr(rt,name,object())
   with patch.dict(sys.modules,modules):
    with self.assertRaisesRegex(ValueError,"both actual compiler"):L.framework(mods,t,tn,0)
   setattr(rt,name,old)
  self.assertEqual(calls,[])
 def test_wrong_helper_source_fails_before_driver_call(self):
  mods=original_reader();t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  with patch.dict(sys.modules,modules),patch.object(L,"ref",return_value=dict(path="/wrong",bytes=2090,sha256="0"*64)):
   with self.assertRaisesRegex(ValueError,"same660 helper"):L.framework(mods,t,tn,0)
  self.assertEqual(calls,[])
 def test_existing_foreign_compiler_rejected_not_replaced(self):
  mods=original_reader();t,tn,tr,tl,rt,modules,current,state,calls=runtime();foreign=object()
  for name in("triton","tl"):
   bad=dict(mods);bad[name]=foreign
   with patch.dict(sys.modules,modules):
    with self.assertRaisesRegex(ValueError,"foreign cached compiler"):L.framework(bad,t,tn,0)
   self.assertIs(bad[name],foreign)
 def test_binding_reentrant_same_object_without_donor_mutation(self):
  mods=original_reader();t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  with patch.dict(sys.modules,modules):
   one=L.framework(mods,t,tn,0);two=L.framework(one,t,tn,0)
  self.assertIsNot(one,two);self.assertIs(two["tl"],tl);self.assertNotIn("tl",mods);self.assertEqual(calls,[])
 def test_sourcequalified_metadata_constructor_and_cross_module_signatures(self):
  result,_=loaded_context();new=result[4]
  md=new["metadata"].Metadata
  values=(object(),(),33792,4,False,{},object(),object(),object(),())
  actual=md(*values);self.assertEqual(actual.max_pages,264);self.assertEqual(actual.batch,0)
  inspect.signature(new["formal"].gather_native).bind(object(),object(),object(),[],32768)
  inspect.signature(P.PackedBatch).bind(object(),{},source_refs={},device_properties={},get_format=lambda t:2,
   qualify=lambda:None,actual_identity=lambda:{},rank=0,publish=lambda *a:None)
 def test_actual_bootstrap_worker_call_consumes_loaded_context_and_framework(self):
  result,_=loaded_context();m,source,mods,adapter,new,own=result
  t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  tree=ast.parse((HERE/"kivi_firstdecode_bootstrap.py").read_bytes())
  fn=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=="_kivi_initialize_from_config")
  bind=next(n for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(v,ast.Name)and v.id=="compiled"for v in n.targets))
  select=next(n for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(v,ast.Name)and v.id=="selected"for v in n.targets))
  seen=[]
  def consume(*args,**kwargs):
   inspect.signature(W.make_worker).bind(*args,**kwargs)
   self.assertIs(args[1]["triton"],tr);self.assertIs(args[1]["tl"],tl)
   self.assertIs(kwargs["formal"],new["formal"]);self.assertIs(kwargs["metadata"],new["metadata"])
   # Actual PackedBatch constructor receives the same compiler and metadata handles.
   p=P.PackedBatch(t,dict(triton=args[1]["triton"],tl=args[1]["tl"],metadata=kwargs["metadata"]),
    source_refs={},device_properties={},get_format=lambda x:2,qualify=lambda:None,
    actual_identity=lambda:{},rank=0,publish=lambda *a:None)
   self.assertIs(p.modules["metadata"],new["metadata"]);seen.append(p);return object()
  own=dict(own,worker=types.SimpleNamespace(make_worker=consume))
  env=dict(l=L,mods=mods,torch=t,npu=tn,rank=0,own=own,new=new,native=object(),adapter=adapter,
   tp=object(),kv=object(),context=object(),layout={},layout_ref={},sha="f"*64,
   refs={},props={},qualify=lambda:None,bindings=object(),recipe=dict(raw_root="/fixture"),
   provider_cls=types.SimpleNamespace(initialize_from_config=lambda *a:None),
   self=types.SimpleNamespace(_kivi_explicit_provider={}),
   resolved=lambda *a:None,final=lambda *a:None)
  with patch.dict(sys.modules,modules):
   exec(compile(ast.Module(body=[bind,select],type_ignores=[]),str(HERE/"kivi_firstdecode_bootstrap.py"),"exec"),env)
  self.assertEqual(len(seen),1);self.assertNotIn("triton",mods)
 def test_every_bootstrap_worker_mods_key_has_real_factory_or_binding_origin(self):
  result,_=loaded_context();t,tn,tr,tl,rt,modules,current,state,calls=runtime()
  with patch.dict(sys.modules,modules):bound=L.framework(result[2],t,tn,0)
  # The exact original donor source adds format_policy. Layout/source fixture only.
  bound["format_policy"]=object()
  keys=set()
  for name in("kivi_firstdecode_bootstrap.py","worker.py","guest_probe.py","prebind.py"):
   for n in ast.walk(ast.parse((HERE/name).read_bytes())):
    if isinstance(n,ast.Subscript)and isinstance(n.value,ast.Name)and n.value.id in("mods","compiled")and isinstance(n.slice,ast.Constant):
     keys.add(n.slice.value)
  self.assertLessEqual(keys,set(bound));self.assertEqual(keys,{"layout","format_policy","callback","fields","lifecycle","base","triton","tl"})
 def actual_guest(self,mode):
  result,_=loaded_context();m,source,mods,adapter,new,own=result
  t,tn,tr,tl,rt,modules,current,state,calls=runtime(False);events=[]
  class Tiny:
   def __add__(self,value):events.append("tiny-add");return self
   def cpu(self):return self
   def tolist(self):return [4.,5.]
  def tensor(*a,**kw):state[0]=True;events.append("tiny");return Tiny()
  t.tensor=tensor;t.npu.set_device=lambda rank:current.__setitem__(0,rank)
  t.npu.synchronize=lambda:events.append("sync")
  t.ops=types.SimpleNamespace(npu=types.SimpleNamespace(get_npu_format=object()))
  def get_format(value):return 2
  tn.get_npu_format=get_format
  mods=dict(mods);mods["format_policy"]=types.SimpleNamespace(bind_getter=lambda *a:(get_format,object(),{}),serial=lambda value,enum:value)
  mods["layout"]=(object(),types.SimpleNamespace(source_file=lambda *a:None,identity=lambda:dict(fixture_only=True)))
  adapter=types.SimpleNamespace()
  class NPUWorker:
   def initialize_from_config(self,config):pass
   def load_model(self):pass
  api=types.SimpleNamespace(__file__=__file__)
  m=dict(m,installed_api_server_sha256=L.ref(__file__)["sha256"],native_format_patch_chain=dict(format={}))
  parsed=types.SimpleNamespace(async_scheduling=False,enable_chunked_prefill=True,enforce_eager=True,mamba_cache_mode="none",enable_prefix_caching=False)
  entry=types.SimpleNamespace(parse_native=lambda *a:parsed,native_argv=lambda *a:[],
   actual_config_precheck=lambda *a:events.append("config")or dict(fixture_only=True))
  own=dict(own,cann_python=types.SimpleNamespace(cached=lambda **kw:{}))
  guest=load("guest_probe");contract=load("model_contract")
  spec=types.SimpleNamespace(name="_fixture_loaded_exact_loader",loader=types.SimpleNamespace(exec_module=lambda m:None))
  imported=dict(modules,**{"vllm.entrypoints.openai.api_server":api,"vllm_ascend.worker.worker":types.SimpleNamespace(NPUWorker=NPUWorker)})
  def importing(name):events.append("import:"+name);return imported[name]
  def selected(name,ref):return B if ref["path"].endswith("runtime_boundary.py")else entry if ref["path"].endswith("server_entry.py")else object()
  def own_ref(manifest,name):return dict(path=str(HERE/name),bytes=1,sha256="f"*64)
  original=L.framework
  def framework(*args):events.append("framework");return original(*args)
  with tempfile.TemporaryDirectory(prefix="kivi-closure-guest-")as d,ExitStack()as stack:
   if os.name=="nt":
    sentinel=-90571
    view=types.SimpleNamespace(O_RDONLY=os.O_RDONLY,O_DIRECTORY=getattr(os,"O_DIRECTORY",0),
     open=lambda p,f:sentinel if Path(p).is_dir()else os.open(p,f),
     fsync=lambda fd:None if fd==sentinel else os.fsync(fd),
     close=lambda fd:None if fd==sentinel else os.close(fd),link=os.link)
    stack.enter_context(patch.object(contract,"os",view))
   stack.enter_context(patch.dict(sys.modules,modules))
   stack.enter_context(patch.object(guest,"importlib",types.SimpleNamespace(import_module=importing,
    util=types.SimpleNamespace(spec_from_file_location=lambda *a:spec,module_from_spec=lambda s:L))))
   stack.enter_context(patch.object(L,"load",return_value=(m,source,mods,adapter,new,own)))
   stack.enter_context(patch.object(L,"module",side_effect=selected));stack.enter_context(patch.object(L,"own",side_effect=own_ref))
   stack.enter_context(patch.object(L,"framework",side_effect=framework));stack.enter_context(patch.object(L,"publish",side_effect=contract.write))
   ref=guest.run(mode,"f"*64,Path(d)/"actual-guest.json",8250,10*1024**3)
   row=contract.obj(ref)
  return row,events,calls,mods
 def test_complete_actual_guest_run_N1_to_original_boundary_and_real_report(self):
  row,events,calls,mods=self.actual_guest("n1")
  self.assertEqual(row["status"],"N1_ALL4_TINY_CHECKED");self.assertEqual(len(row["canary"]),4)
  self.assertEqual(calls,[0,0,1,2,3]);self.assertEqual(events.count("framework"),4)
  self.assertEqual([x for x in events if x in("tiny","tiny-add","sync","framework","config")],
   ["tiny","tiny-add","sync","framework"]*4+["config"])
  self.assertNotIn("triton",mods)
  self.assertTrue(all(x["actual_driver_properties"]["device_properties"]==dict(num_aicore=7,num_vectorcore=13)for x in row["canary"]))
 def test_complete_actual_guest_CPU_has_no_compiler_binding_or_native_import(self):
  row,events,calls,mods=self.actual_guest("cpu")
  self.assertEqual(row["status"],"CPU_IMPORT_PARSER_CHECKED");self.assertEqual(row["canary"],[])
  self.assertNotIn("framework",events);self.assertNotIn("import:vllm_ascend.worker.worker",events)
  self.assertEqual(calls,[]);self.assertNotIn("triton",mods)
 def test_exact018c_import_API_and_both_calls_remain_NPU_only(self):
  loader_tree=ast.parse((HERE/"loader.py").read_bytes())
  fn=next(n for n in loader_tree.body if isinstance(n,ast.FunctionDef)and n.name=="framework")
  imports=[n for n in fn.body if isinstance(n,ast.ImportFrom)and n.module=="vllm.triton_utils"]
  self.assertEqual(len(imports),1);self.assertEqual([n.name for n in imports[0].names],["HAS_TRITON","tl","triton"])
  source_load=next(n for n in loader_tree.body if isinstance(n,ast.FunctionDef)and n.name=="load")
  self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=="framework"for n in ast.walk(source_load)))
  guest=ast.parse((HERE/"guest_probe.py").read_bytes())
  run=next(n for n in guest.body if isinstance(n,ast.FunctionDef)and n.name=="run")
  branch=next(n for n in run.body if isinstance(n,ast.If)and ast.dump(n.test)==ast.dump(ast.parse('mode=="n1"',mode="eval").body))
  loop=next(n for n in ast.walk(branch)if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=="device")
  calls=[n for n in ast.walk(loop)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
  order={n.func.attr:n.lineno for n in calls if n.func.attr in("synchronize","framework","core_properties")}
  self.assertLess(order["synchronize"],order["framework"]);self.assertLess(order["framework"],order["core_properties"])
if __name__=="__main__":unittest.main(verbosity=2)
