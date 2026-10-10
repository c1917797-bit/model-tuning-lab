"""Real-file explicit provider/worker/consumer seam regressions.
Native factory/allocator/arena bodies execute with inert tensor fixtures.
Original Collector, JournalPublisher, PackedBatch and strict geometry consumers
execute unchanged. Only the final native-model installer invocation is spied:
this is ABI/publication evidence, NOT Torch, model output or device permission.
"""
import ast,copy,functools,hashlib,importlib.util,inspect,json,os,sys,tempfile,types,unittest
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def load(name,path=None,alias=None):
 path=path or HERE/(name+".py");key=alias or "_explicit_integration_"+name
 if key in sys.modules:
  old=sys.modules[key]
  if Path(old.__file__).resolve()!=Path(path).resolve():raise ValueError("foreign source namespace")
  return old
 spec=importlib.util.spec_from_file_location(key,path);m=importlib.util.module_from_spec(spec)
 sys.modules[key]=m;spec.loader.exec_module(m);return m
T=load("test_provider");F=T.F;P=T.P;I=load("provider_independent",alias="provider_independent")
def original(name,sha,local):
 if os.environ.get("KIVI_PROVIDER_LOCAL_ARCHIVE")=="1":path=F.SHARED/local
 else:
  manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  path=Path(next(r["path"]for r in manifest["dependencies"]if r["sha256"]==sha))
 if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError("exact original dependency "+name)
 return load(name,path,alias=name)
layout=original("kivi_layout_consumer","71f45ada3acf89b68b0338a74897cbb68ab5cc980a3788aa6c4afd282d823927","kivi_layout_consumer.py")
spans=original("provider_zeroer","2eb0a604dead0181c51e4314a15efb6aca48d51436f7eeb254ef3f5ce4518831","spans.py")
G=load("explicit_geometry",alias="explicit_geometry")
C=load("model_contract");W=load("worker");PRE=load("prebind");OWNER=load("runtime_owner")
L=load("loader");WRITER=load("consume_prefill");PRODUCER=load("producer");INSTALL=load("installer")
AD=original("_explicit_original_adapter",W.ADAPTER_SHA,"adapter.py")
CAP=original("_explicit_original_capture","398cd59b469af2ffa81df15a2c5786f048b41836a22ed7348803900495d7c88a","capture.py")
CB=original("_explicit_original_callback",INSTALL.CALLBACK_SHA,"callback.py")
J=original("_explicit_original_journal","cd5b012684607465b2a5c489303a30bb55970c93786c455d675037d6723bb851","ingress-consume.py")
BIND=original("_explicit_original_bindings",INSTALL.INGRESS_SHA,"bindings.py")
BOOK=original("_explicit_original_book",INSTALL.BOOK_SHA,"book.py")
FORMAL=original("_explicit_original_formal",INSTALL.FORMAL_SHA,"formal.py")
METADATA=original("_explicit_original_metadata",INSTALL.CRITICAL_SHA["metadata"],"metadata.py")
if os.environ.get("KIVI_PROVIDER_LOCAL_ARCHIVE")=="1":
 kernel_path=F.SHARED.parent.parent/"kivi-c132-masked-signed-cast-v3-20261010/kernel.py"
 # Actual exact sibling archive, not a guessed runtime source.
 kernel_path=Path("C:/Users/Huawei/AppData/Local/Packages/sandbox.{48fdcea7-5947-498c-a068-4bc4cdaddb04}/AC/Temp/kivi-c132-masked-signed-cast-v3-20261010/kernel.py")
else:kernel_path=Path(json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())["runtime_roles"]["kernel"]["path"])
KERNEL=load("actual_kernel",kernel_path)
class ExplicitIntegration(unittest.TestCase):
 def setUp(self):
  self.fixture=T.ProviderTests("test01_actual_off_returns_without_source_or_tensor");self.fixture.setUp()
  self.addCleanup(self.fixture.tearDown);self.t=self.fixture.t
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.stack=ExitStack();self.addCleanup(self.stack.close)
  if os.name=="nt":
   sentinel=-90725
   view=types.SimpleNamespace(O_RDONLY=os.O_RDONLY,O_DIRECTORY=getattr(os,"O_DIRECTORY",0),
    open=lambda p,f:sentinel if Path(p).is_dir()else os.open(p,f),
    fsync=lambda fd:None if fd==sentinel else os.fsync(fd),
    close=lambda fd:None if fd==sentinel else os.close(fd),link=os.link)
   self.stack.enter_context(patch.object(C,"os",view))
  self.ident=dict(pid=99111,start_ticks=99112,cgroup="explicit-provider-fixture")
  self.source=C.write(self.root/"source.json",dict(fixture=True))
  self.recipe_ref=C.write(self.root/"recipe.json",dict(fixture=True))
  def publish(label,value):
   return C.write(self.root/(label+".json"),dict(value,rank=0,identity=self.ident,
                                               source_ref=self.source,recipe_ref=self.recipe_ref))
  self.publish=publish
  def describe(t):return dict(F.describe(t),layout="ND_CONTIGUOUS")
  self.describe=describe
  selected=P.make_worker(self.fixture.native,self.fixture.u,self.fixture.kv,self.fixture.dl,self.t,
   bits=2,allocation_margin_bytes=256*1024**2,describe=describe,qualify=lambda:None,
   publish=publish,consume_allocations=I.consume,install_after_native=G.post_native_allocated)
  self.worker=selected();self.worker.vllm_config=self.fixture.cfg
  self.worker.cache_config=self.fixture.cfg.cache_config
  self.worker.init_snapshot=types.SimpleNamespace(free_memory=64*1024**3)
  self.worker.model_runner=F.new_runner(self.fixture.runner_cls,self.fixture.cfg,self.fixture.specs,self.fixture.events)
  self.worker.determine_available_memory()
  self.worker.initialize_from_config(self.fixture.config_for(self.worker._kivi_explicit_provider["plan"]))
  self.state=self.worker._kivi_explicit_provider
  self.event,self.zero,unused=self.fixture.native_event_fixture(self.state["plan"],self.state["native_descriptors"])
  self.event["identity"]=self.ident;self.zero["identity"]=self.ident
  self.event_ref=C.write(self.root/"event.json",self.event)
  self.zero_ref=C.write(self.root/"zero.json",self.zero)
  self.owner=dict(explicit_plan_ref=self.state["plan_ref"],explicit_allocation_ref=self.state["allocation_ref"])
 def geometry(self,name=None):
  name=name or next(iter(self.state["arenas"]))
  return G.geometry(self.state,self.event,self.event_ref,self.zero_ref,name)
 def test01_actual_native_provider_real_publication_all16_consumer(self):
  allocation=G.document(self.state["allocation_ref"])
  result=G.consume_rank(self.owner,self.event,allocation["compact"],self.zero)
  self.assertTrue(result["zeroer_after_initialize_checked"]);self.assertEqual(result["fields"],144)
  for name in self.state["arenas"]:
   g=self.geometry(name);r=C.write(self.root/(name+".json"),g)
   self.assertEqual(G.consume_geometry(G.document(r),self.event),allocation["compact"][name])
  self.assertFalse(result["numerical_checked"])
 def test02_original_prefill_source_geometry_consumes_actual_new_refs(self):
  g=self.geometry();ref=C.write(self.root/"geometry.json",g);name=g["layer"];layer=self.event["layers"][name]
  prov=dict(event_ref=self.event_ref,geometry_ref=ref,rank=0,identity=self.ident,layer=name,
            native_shape=layer["views"][0]["shape"],native_views=layer["views"])
  desc={f["name"]:f["descriptor"]for f in g["fields"]}
  frame=dict(bits=2,dtype="bfloat16",pool_geometry=[g["pages"],g["pages"]*128,16],
             pool_fields={n:dict(bytes=desc[n]["logical_bytes"])for n in WRITER.FIELDS},
             live_alias_descriptors_before_snapshot={n:{k:v for k,v in desc[n].items()
                if k not in("layout","observed_format_code")}for n in WRITER.FIELDS})
  proof=WRITER.source_geometry(frame,prov,dict(layer=name,rank=0,identity=self.ident))
  self.assertEqual(proof["pages"],2376);self.assertEqual(proof["native_capacity"],198*1536)
  self.assertEqual(proof["captured_bytes"],sum(x["bytes"]for x in frame["pool_fields"].values()))
 def test03_wrong_whole_allocation_ref_bytes_rejected(self):
  bad=dict(self.owner);bad["explicit_allocation_ref"]=dict(bad["explicit_allocation_ref"],bytes=1)
  with self.assertRaisesRegex(ValueError,"bytes/SHA"):G.consume_rank(bad,self.event,{},self.zero)
 def test04_wrong_rank_provider_cannot_borrow_geometry(self):
  bad=copy.deepcopy(self.event);bad["rank"]=1
  with self.assertRaisesRegex(ValueError,"owner/rank/FA"):G.consume_geometry(self.geometry(),bad)
 def test05_mutated_live_field_before_install_rejected(self):
  a=G.document(self.state["allocation_ref"]);bad=copy.deepcopy(a["compact"])
  bad[next(iter(bad))]["key_codes"]["data_ptr"]+=4
  with self.assertRaisesRegex(ValueError,"match original"):G.consume_rank(self.owner,self.event,bad,self.zero)
 def test06_native_GDN_dimension_mutation_rejected(self):
  bad=copy.deepcopy(self.event);name=next(n for n,r in bad["layers"].items()if r["kind"]=="GDN")
  bad["layers"][name]["views"][0]["shape"][0]-=1
  with self.assertRaises(ValueError):
   G.consume_rank(self.owner,bad,G.document(self.state["allocation_ref"])["compact"],self.zero)
 def test07_not_native_padding_and_no_false_permission(self):
  g=self.geometry();g["newly_allocated_device_bytes"]=0
  with self.assertRaisesRegex(ValueError,"separately allocated"):G.consume_geometry(g,self.event)
  g=self.geometry();g["model_ready"]=True
  with self.assertRaisesRegex(ValueError,"honest explicit"):G.consume_geometry(g,self.event)
 def test08_provider_state_other_worker_cannot_install(self):
  with self.assertRaises(ValueError):G.post_native_allocated(types.SimpleNamespace(_kivi_explicit_provider={}),self.state)
 def test09_actual_post_input_publishes_explicit_not_firstfit_regions(self):
  plan=C.write(self.root/"plan.json",dict(rows=[dict(fixture=True)]))
  original_input=C.write(self.root/"input.json",dict(fixture=True))
  final=C.write(self.root/"layout-final.json",dict(fixture=True))
  bindings=types.SimpleNamespace(owner=dict(container_id="a"*64,rank_bindings={"0":self.ident}),
   plan_ref=plan,expected={"fixture":dict(prompt=[1]*32768)},frontend_binding_ref=plan,rank_bindings_ref=plan)
  recipe=dict(container_id="a"*64,actual_input_protocol_ref=original_input,bits=2,run_id="fixture",
   diagnostic_root=str(self.root),native_format_binding={},external_owner_authority_ref=plan,
   compiled_numeric_qualification_ref=plan)
  def publish(label,value):return C.write(self.root/(label+".json"),value)
  owner,ref=OWNER.post_input(recipe,bindings,self.event,self.event_ref,final,self.zero,G,spans,publish,
                            provider_state=self.state)
  self.assertEqual(C.obj(ref),owner)
  self.assertTrue(owner["native_capacity_reduced"]);self.assertTrue(owner["compact_new_allocation_explicit"])
  self.assertTrue(all(set(r)=={"pages","bits","allocation_ref"}for r in owner["regions"].values()))
  self.assertEqual(owner["explicit_plan_ref"],self.state["plan_ref"])
 def test10_factory_propagates_actual_initializer_and_requires_complete_state(self):
  capture=types.SimpleNamespace(source_file=CAP.source_file)
  mods=dict(layout=(None,capture),lifecycle=self.fixture.dl,callback=CB,fields=object(),
            triton=object(),tl=object(),base=object())
  sources={n:L.ref(m.__file__)for n,m in (("kernel",KERNEL),("metadata",METADATA),
        ("lifecycle",self.fixture.dl),("callback",CB),("explicit_provider",P))}
  # P is the exact own copied source, not a modified namespace.
  handed=[];answer=object()
  @functools.wraps(PRE.make_worker)
  def handoff(*args,**kw):
   inspect.signature(PRE.make_worker).bind(*args,**kw);handed.append((args,kw));return answer
  prebind=types.SimpleNamespace(make_worker=handoff)
  bindings=BIND.Bindings.__new__(BIND.Bindings)
  self.stack.enter_context(patch.dict(os.environ,{INSTALL.FLAG:"1"}))
  result=W.make_worker(self.fixture.native,mods,AD,prebind,self.t,object(),object(),self.fixture.kv,object(),
   layout_owner={},layout_owner_ref={},layout_mf="f"*64,post_owner=None,post_owner_ref=None,
   installer=INSTALL,spans=spans,book=BOOK,formal=FORMAL,producer=PRODUCER,kernel=KERNEL,metadata=METADATA,
   journal_module=J,source_refs=sources,device_properties=dict(num_aicore=7,num_vectorcore=13),qualify=lambda:None,
   ingress_bindings=bindings,resolve_post_owner=lambda *a:None,finish_module=object(),publish_final=lambda r:None,
   provider_initialize=type(self.worker).initialize_from_config,provider_state=self.state,explicit_geometry=G)
  self.assertIs(result,answer);self.assertEqual(len(handed),1)
  self.assertIs(handed[0][1]["native_initialize"],type(self.worker).initialize_from_config)
  self.assertEqual(handed[0][1]["native_initialize_sha"],sources["explicit_provider"]["sha256"])
 def test11_bootstrap_determine_uses_actual_provider_without_new_controller(self):
  tree=ast.parse((HERE/"kivi_firstdecode_bootstrap.py").read_bytes())
  cls=next(n for n in ast.walk(tree)if isinstance(n,ast.ClassDef)and n.name=="FirstDecodeWorker")
  node=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="determine_available_memory")
  fn=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]));seen=[]
  runtime=types.SimpleNamespace(initialize=lambda invoke,**kw:invoke())
  own=dict(ownership=types.SimpleNamespace(rank_request=lambda *a:seen.append("rank-request")))
  # Fresh exact provider instance; method cannot fabricate reduced capacity.
  selected=type(self.worker);w=selected();w.vllm_config=self.fixture.cfg;w.cache_config=self.fixture.cfg.cache_config
  w.init_snapshot=self.worker.init_snapshot;w.model_runner=F.new_runner(self.fixture.runner_cls,self.fixture.cfg,self.fixture.specs,self.fixture.events)
  # Actual provider publisher is exclusive; use a different namespace for this plan.
  self.worker._kivi_explicit_provider["state"]="existing_not_reused"
  env=dict(tp=types.SimpleNamespace(get_tensor_model_parallel_rank=lambda:0),own=own,capture=object(),
   recipe={},source_ref=self.source,l=types.SimpleNamespace(publish=lambda *a:None),provider_cls=selected,
   boundary=runtime,recipe_ref=self.recipe_ref,boundary_ref=self.source,identity=self.ident)
  exec(compile(fn,str(HERE/"kivi_firstdecode_bootstrap.py"),"exec"),env)
  # Exclusive publication proves a second worker cannot replay/overwrite rank0.
  with self.assertRaisesRegex(ValueError,"exclusive"):env["determine_available_memory"](w)
  self.assertEqual(seen,["rank-request"])
 def test12_source_bindings_and_original_math_unchanged(self):
  self.assertEqual(L.ref(HERE/"installer.py")["sha256"],L.INSTALLER_SHA)
  self.assertEqual(L.ref(HERE/"explicit_geometry.py")["sha256"],W.FIELDS_SHA)
  self.assertEqual(L.ref(HERE/"prebind.py")["sha256"],W.PREBIND_SHA)
  self.assertEqual(L.ref(HERE/"provider_independent.py")["sha256"],G.INDEPENDENT_SHA)
  self.assertEqual(L.ref(HERE/"producer.py")["sha256"],INSTALL.PRODUCER_SHA)
  self.assertEqual(INSTALL.CRITICAL_SHA["kernel"],"ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a")
  # Execute the existing actual create argv functions: CPU arm has Devices[].
  source=ast.parse((HERE/"safety_host.py").read_bytes())
  names={"environment","labels","create_argv","device_map"}
  nodes=[n for n in source.body if isinstance(n,ast.FunctionDef)and n.name in names]
  env=dict(c=C,DOCKER="/usr/bin/docker",MEM=64*C.GIB,OWNER="fixture-only",PHYSICAL=(4,5,6,7))
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(HERE/"safety_host.py"),"exec"),env)
  declared=dict(arm="cpu-preflight",name="fixture",source=self.source,host_sha256="f"*64,
                guest_cpus=[7],mounts={str(self.root):(str(self.root),True)})
  argv=env["create_argv"](declared)
  self.assertNotIn("--device",argv);self.assertNotIn("--gpus",argv)
  self.assertFalse(any("/dev/davinci" in x for x in argv))
  self.assertIn("ASCEND_RT_VISIBLE_DEVICES=",argv)
  self.assertEqual(argv[argv.index("--memory")+1],str(8*C.GIB))
  self.assertEqual(argv[argv.index("--cpus")+1],"1")
  host=ast.parse((HERE/"host_run.py").read_bytes())
  software=next(n for n in host.body if isinstance(n,ast.FunctionDef)and n.name=="software_only")
  creates=[n for n in ast.walk(software)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=="create"]
  self.assertEqual(len(creates),1);self.assertEqual(ast.literal_eval(creates[0].args[-1]),"cpu-preflight")
  self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id in("run","make_recipe","owner_precondition")
                       for n in ast.walk(software)))
  literals=[n.value for n in ast.walk(software)if isinstance(n,ast.Constant)and isinstance(n.value,str)]
  self.assertNotIn("candidate",literals);self.assertNotIn("n1",literals)
  self.assertIn("software_check.py",literals)
  main=next(n for n in host.body if isinstance(n,ast.FunctionDef)and n.name=="main")
  selected=next(n for n in main.body if isinstance(n,ast.If)and ast.unparse(n.test)=="a.software_only")
  self.assertIsInstance(selected.body[0],ast.Return)
  self.assertEqual(selected.body[0].value.func.id,"software_only")
  # 3.9 can compile host and all packet bodies; Python3.12 is explicit only for software execution.
  py=ast.parse((HERE/"software_check.py").read_bytes())
  entry=next(n for n in py.body if isinstance(n,ast.FunctionDef)and n.name=="main")
  statements=[ast.unparse(n)for n in entry.body]
  version=next(i for i,n in enumerate(statements)if "sys.version_info[:2]" in n)
  tests=next(i for i,n in enumerate(statements)if "focused_tests" in n)
  self.assertLess(version,tests)
  priming=next(i for i,n in enumerate(statements)if n=="closure_test.original_reader()")
  extensions=next(i for i,n in enumerate(statements)if "test_provider_integration.py" in n)
  self.assertLess(priming,extensions)
  # Execute the actual input producer until its first source-bound config read.
  # This proves default host vs explicit guest resolution without fake checkpoint bytes.
  recipe=load("input_recipe");seen=[];marker=RuntimeError("read-boundary")
  def bound(path,digest):
   seen.append((str(path),digest));raise marker
  facade=types.SimpleNamespace(require=C.require,CONFIG_SHA=C.CONFIG_SHA,
   obj=lambda ref:dict(host_model_root="/cache/efim/Qwen3.6-27B"),bound=bound)
  for kw,path in (({},"/cache/efim/Qwen3.6-27B/config.json"),
                  (dict(host=False),"/models/Qwen3.6-27B/config.json")):
   with self.assertRaisesRegex(RuntimeError,"read-boundary"):
    recipe.create(facade,{}, {},self.root,"scope-only",**kw)
   self.assertEqual(seen[-1],(str(Path(path)),C.CONFIG_SHA))
  with self.assertRaisesRegex(ValueError,"explicit host"):
   recipe.create(facade,{}, {},self.root,"scope-only",host="false")


 def live_zeroer(self):
  runner=self.worker.model_runner;runner.speculative_config=None
  if os.environ.get("KIVI_PROVIDER_LOCAL_ARCHIVE")=="1":path=F.SHARED/"runner.py"
  else:
   mf=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
   path=Path(next(r["path"]for r in mf["dependencies"]if r["sha256"]==spans.GPU_SHA))
  self.assertEqual(L.ref(path)["sha256"],spans.GPU_SHA)
  node=next(n for n in ast.walk(ast.parse(path.read_bytes()))if isinstance(n,ast.FunctionDef)and n.name=="_zero_block_ids")
  env={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),"exec"),env)
  runner._zero_block_ids=types.MethodType(env["_zero_block_ids"],runner)
  actual=spans.snapshot_zeroer(self.t,runner,self.event,CB,lambda:self.ident,0)
  ref=C.write(self.root/"live-zeroer.json",actual)
  runner._kivi_explicit_provider=self.state
  return runner,ref
 def test13_actual_live_zeroer_source_rechecked_at_guard(self):
  runner,ref=self.live_zeroer()
  contexts={n:dict(arena=a,packed_batch=types.SimpleNamespace(format=lambda v:2))
            for n,a in self.state["arenas"].items()}
  callback=types.SimpleNamespace(scalar_tensor=F.describe)
  proof=G.guard_current(self.t,callback,lambda:self.ident,0,runner,self.event,contexts,ref)
  self.assertTrue(proof["zeroer_after_initialize_checked"])
  runner.speculative_config=object()
  with self.assertRaisesRegex(ValueError,"absent zeroer"):
   G.guard_current(self.t,callback,lambda:self.ident,0,runner,self.event,contexts,ref)
 def test14_actual_bound_format_preserves_native_collector_count(self):
  boot=load("kivi_firstdecode_bootstrap");arena=next(iter(self.state["arenas"].values()))
  collector=AD.Collector(types.SimpleNamespace(publish=C.write),CAP,
      dict(diagnostic_root=str(self.root)),self.source,"f"*64,0,self.ident)
  seen=[];collector.fn=lambda t:seen.append(t)or 2;collector.enum_cls=object()
  # Getter return semantics are a fixture; original descriptor and comparison execute.
  policy=types.SimpleNamespace(normalize=lambda code,enum:code)
  capture=types.SimpleNamespace(descriptor=lambda t,probe:dict(F.describe(t),observed_format_code=probe(t)))
  with patch.object(AD,"_ACTIVE",collector),patch.object(AD,"FORMAT_POLICY",policy):
   for value in arena.pool.values():
    if type(value)is not int:boot.allocation_descriptor(value,capture,types.SimpleNamespace(scalar_tensor=F.describe),AD)
  self.assertEqual(len(seen),9);self.assertEqual(collector.calls,[])
 def test15_mutating_format_getter_rejected_without_native_journal_pollution(self):
  boot=load("kivi_firstdecode_bootstrap");value=next(iter(self.state["arenas"].values())).pool["key_codes"]
  collector=AD.Collector(types.SimpleNamespace(publish=C.write),CAP,
      dict(diagnostic_root=str(self.root)),self.source,"f"*64,0,self.ident)
  def bad(t):t.base+=4096;return 2
  collector.fn=bad;collector.enum_cls=object()
  capture=types.SimpleNamespace(descriptor=lambda t,probe:probe(t))
  with patch.object(AD,"_ACTIVE",collector),patch.object(AD,"FORMAT_POLICY",types.SimpleNamespace(normalize=lambda c,e:c)):
   with self.assertRaisesRegex(ValueError,"without metadata mutation"):
    boot.allocation_descriptor(value,capture,types.SimpleNamespace(scalar_tensor=F.describe),AD)
  self.assertEqual(collector.calls,[])
 def test16_actual_worker_bridge_live_arenas_journal_and_installer_handoff(self):
  runner,unused_zero=self.live_zeroer();del runner._kivi_explicit_provider
  # Native tensor/storage APIs are inert fixture metadata, never actual Torch.
  tensor_cls=F.Tensor
  def stride(t):
   out=[];v=1
   for n in reversed(t.shape):out.insert(0,v);v*=n
   return tuple(out)
  methods=dict(stride=stride,storage_offset=lambda t:0,data_ptr=lambda t:t.base,
      is_contiguous=lambda t:True,untyped_storage=lambda t:types.SimpleNamespace(
          data_ptr=lambda:t.base,nbytes=lambda:t.numel()*t.element_size()))
  for n,fn in methods.items():self.stack.enter_context(patch.object(tensor_cls,n,fn,create=True))
  capture=types.SimpleNamespace(source_file=CAP.source_file,descriptor=CAP.descriptor,identity=lambda:self.ident)
  mods=dict(layout=(None,capture),lifecycle=self.fixture.dl,callback=CB,fields=object(),
       triton=object(),tl=object(),base=object())
  sources={n:L.ref(m.__file__)for n,m in (("kernel",KERNEL),("metadata",METADATA),("lifecycle",self.fixture.dl),
      ("callback",CB),("explicit_provider",P),("installer",INSTALL))}
  owner=dict(self.owner,schema="kivi.packed-qwen-install-input/v1",model_ready=False,run_authority=False,
      actual_assignment_protocol_ref=self.source,capacity_receipt_ref=self.source,
      external_owner_authority_ref=self.source,compiled_numeric_qualification_ref=self.source,
      rank_bindings={"0":self.ident},declared_passed_request_ids=["fixture"],diagnostic_root=str(self.root),
      regions={n:dict(pages=self.state["plan"]["pages"],bits=2,allocation_ref=self.state["allocation_ref"])
               for n in self.state["arenas"]})
  owner_ref=C.write(self.root/"install-input.json",owner)
  handed=[];closed=[]
  @functools.wraps(PRE.make_worker)
  def handoff(*args,**kw):
   inspect.signature(PRE.make_worker).bind(*args,**kw);handed.append((args,kw));return object()
  binder=BIND.Bindings.__new__(BIND.Bindings)
  binder.matches_install_owner=lambda *a:None
  finish=types.SimpleNamespace(install=lambda *a:closed.append(a))
  self.stack.enter_context(patch.dict(os.environ,{INSTALL.FLAG:"1"}))
  tp=types.SimpleNamespace(get_tensor_model_parallel_rank=lambda:0,get_tensor_model_parallel_world_size=lambda:4)
  npu=object();context=object()
  W.make_worker(self.fixture.native,mods,AD,types.SimpleNamespace(make_worker=handoff),self.t,npu,tp,
    self.fixture.kv,context,layout_owner={},layout_owner_ref={},layout_mf="f"*64,post_owner=None,post_owner_ref=None,
    installer=INSTALL,spans=spans,book=BOOK,formal=FORMAL,producer=PRODUCER,kernel=KERNEL,metadata=METADATA,
    journal_module=J,source_refs=sources,device_properties=dict(num_aicore=7,num_vectorcore=13),qualify=lambda:None,
    ingress_bindings=binder,resolve_post_owner=lambda *a:(owner,owner_ref),finish_module=finish,
    publish_final=lambda r:None,provider_initialize=type(self.worker).initialize_from_config,
    provider_state=self.state,explicit_geometry=G)
  args,kw=handed[0];actual_owner,actual_ref=kw["resolve_post_owner"]()
  collector=AD.Collector(types.SimpleNamespace(publish=C.write),capture,dict(diagnostic_root=str(self.root)),
                         owner_ref,"f"*64,0,self.ident)
  collector.fn=lambda t:2;collector.enum_cls=object();collector.binding=dict(fixture=True)
  collector.bind_raw_ref=self.source;collector.install_ref=self.source
  final=C.write(self.root/"native-layout-final.json",dict(original_initialize_returned=True,exact_owned_restore=True,
                         primary=None,secondary=[],layout_ref=self.event_ref))
  called=[];original=INSTALL.install
  def install(actual_runner,**passed):
   inspect.signature(original).bind(actual_runner,**passed)
   self.assertIs(actual_runner,runner);self.assertEqual(len(passed["layer_contexts"]),16)
   self.assertIs(type(passed["publish"]),J.JournalPublisher)
   self.assertTrue(passed["writer_guard"](runner,self.event,passed["layer_contexts"],
                          passed["owner"]["zeroer_writer_receipt_ref"])["zeroer_after_initialize_checked"])
   self.assertTrue(all(ctx["arena"]is self.state["arenas"][name] and type(ctx["packed_batch"])is PRODUCER.PackedBatch
                      for name,ctx in passed["layer_contexts"].items()))
   called.append(passed);return lambda:dict(fixture_only=True)
  policy=types.SimpleNamespace(normalize=lambda code,enum:code,serial=lambda code,enum:code)
  with patch.object(AD,"FORMAT_POLICY",policy),patch.object(INSTALL,"install",side_effect=install):
   close=args[3].install(runner,mods,AD,self.t,npu,tp,context,owner=actual_owner,owner_ref=actual_ref,
     event=self.event,event_ref=self.event_ref,regions=owner["regions"],publish=collector.publish,layout_final_ref=final)
  self.assertTrue(callable(close));self.assertEqual(len(called),1);self.assertEqual(len(closed),1)
  self.assertEqual(len(collector.calls),144)
  used=called[0]["owner"];self.assertEqual(len(used["field_geometry_refs"]),16)
  for n,r in used["field_geometry_refs"].items():G.consume_geometry(C.obj(r),self.event)
if __name__=="__main__":unittest.main(verbosity=2)
