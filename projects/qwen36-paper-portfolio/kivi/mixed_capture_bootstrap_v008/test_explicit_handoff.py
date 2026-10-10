"""Focused B16 explicit-provider integration, not Torch/NPU/model/numerical PASS.
Pinned native method/factory/allocator bodies run with inert tensor storage.
Real source-qualified geometry and JSON files are consumed. No device entry.
"""
import ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
BASE=Path("C:/Users/Huawei/AppData/Local/Temp/kivi-firstdecode-hbm-budget-v018-20261010/bootstrap")
SHARED=Path("C:/Users/Huawei/AppData/Local/Packages/sandbox.{48fdcea7-5947-498c-a068-4bc4cdaddb04}/AC/Temp/kivi-c132-reviewed-source/model-deps")
def source_path(sha,local):
 if os.name=="nt":return Path(local)
 manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
 matches=[x for x in manifest["files"]+manifest["dependencies"]if x["sha256"]==sha]
 paths={x["path"] for x in matches}
 if len(paths)!=1:raise ValueError("one source-qualified test dependency")
 return Path(next(iter(paths)))
def load(path,name,sha=None):
 p=Path(path);blob=p.read_bytes()
 if sha is not None:assert hashlib.sha256(blob).hexdigest()==sha,str(p)
 if name in sys.modules:
  old=sys.modules[name];assert Path(old.__file__).resolve()==p;return old
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m
 s.loader.exec_module(m);return m
def ref(path):
 p=Path(path);wire=p.read_bytes();return dict(path=str(p),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
class ProviderHandoff(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  global BASE
  if os.name!="nt":
   manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
   BASE=Path(manifest["reviewed_firstdecode_v018_ref"]["path"]).parent
  os.environ["KIVI_PROVIDER_LOCAL_ARCHIVE"]="1"if os.name=="nt"else"0"
  cls.f=load(BASE/"provider_projection.py","_mixed007_actual_projection",
   "f1937cab64c2dd97272dcdd976a22b1f7e106fd55ee046f9fd07d595be6dd39b")
  cls.p=load(HERE/"explicit_provider.py","_mixed007_provider")
  cls.i=load(HERE/"provider_independent.py","provider_independent",
   "332b222442ace7ba90a2ed41cae66f0806dec3639d8711cac86609955afe6f9c")
  load(source_path("71f45ada3acf89b68b0338a74897cbb68ab5cc980a3788aa6c4afd282d823927",
   SHARED/"kivi_layout_consumer.py"),"kivi_layout_consumer",
   "71f45ada3acf89b68b0338a74897cbb68ab5cc980a3788aa6c4afd282d823927")
  cls.spans=load(source_path("2eb0a604dead0181c51e4314a15efb6aca48d51436f7eeb254ef3f5ce4518831",
   SHARED/"spans.py"),"provider_zeroer",
   "2eb0a604dead0181c51e4314a15efb6aca48d51436f7eeb254ef3f5ce4518831")
  cls.g=load(HERE/"explicit_geometry.py","explicit_geometry",
   "77b678af5eea524c59405d98a3681415810e2e77b7f8cf9cde9fd241b28d4157")
  cls.owner=load(HERE/"runtime_owner.py","_mixed007_owner")
  cls.oldtests=load(BASE/"test_provider.py","_mixed007_original_fixture")
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.events=[];self.t,self.kv,self.u,self.dl,self.native,self.runner=self.f.actual_modules(self.events)
  self.cfg=self.f.config(max_seqs=16)
  for n,v in dict(max_num_batched_tokens=40960,enable_chunked_prefill=True,async_scheduling=False,
   scheduler_reserve_full_isl=True,long_prefill_token_threshold=0,max_num_partial_prefills=1,
   max_long_partial_prefills=1,max_num_scheduled_tokens=None).items():setattr(self.cfg.scheduler_config,n,v)
  self.ident=dict(pid=99701,start_ticks=99702,cgroup="mixed007-fixture-only")
  self.source=self.write("source",dict(fixture_not_authority=True))
  self.recipe_ref=self.write("recipe",dict(fixture_not_authority=True))
  self.env=patch.dict(os.environ,{self.p.FLAG:"1"});self.env.start();self.addCleanup(self.env.stop)
 def write(self,label,value):
  path=self.root/(label+".json")
  with path.open("xb")as output:output.write((json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode())
  return ref(path)
 def selected(self):
  def publish(label,value):return self.write(label,dict(value,rank=0,identity=self.ident,
    source_ref=self.source,recipe_ref=self.recipe_ref))
  selected=self.p.make_worker(self.native,self.u,self.kv,self.dl,self.t,bits=2,
   allocation_margin_bytes=256*1024**2,describe=lambda t:dict(self.f.describe(t),layout="ND_CONTIGUOUS"),
   qualify=lambda:None,publish=publish,consume_allocations=self.i.consume,install_after_native=self.g.post_native_allocated)
  worker=selected();worker.vllm_config=self.cfg;worker.cache_config=self.cfg.cache_config
  worker.init_snapshot=types.SimpleNamespace(free_memory=64*1024**3)
  worker.model_runner=self.f.new_runner(self.runner,self.cfg,self.f.specs_from_actual(self.kv),self.events)
  return worker
 def initialized(self):
  worker=self.selected();budget=worker.determine_available_memory()
  specs=worker.get_kv_cache_spec()
  groups=self.u.get_kv_cache_groups(self.cfg,specs)
  config=self.u.get_kv_cache_config_from_groups(self.cfg,groups,budget)
  worker.initialize_from_config(config)
  return worker
 def test01_real_provider_native_factory_allocator_independent_json_chain(self):
  w=self.initialized();state=w._kivi_explicit_provider
  p=self.g.document(state["plan_ref"]);a=self.g.document(state["allocation_ref"])
  self.assertEqual(p["requested_max_num_seqs"],16);self.assertEqual(p["native"]["num_blocks"],198)
  self.assertEqual(p["full_resident_upper_bound"],7);self.assertEqual(p["total_budget_bytes"],6*1024**3)
  self.assertEqual(self.i.consume(p,{d["storage_base"]:d for d in a["native"]},a["compact"]),a["independent"])
  self.assertEqual(len(state["arenas"]),16);self.assertEqual(len(state["native_raw"]),64)
  self.assertIs(state["native_raw"],w.model_runner.raw);self.assertEqual(state["state"],"consumer_installed")
  self.assertEqual(self.events.count("native_profile"),1)
  self.assertEqual(self.events.count("native_initialize"),1)
  self.assertNotIn("_allocate_kv_cache_tensors",vars(w.model_runner))
  self.assertFalse(a["independent"]["numerical_checked"]);self.assertFalse(p["scheduler_preemption_supported"])
 def test02_wrong_reservation_fails_before_profile_or_allocation(self):
  self.cfg.scheduler_config.scheduler_reserve_full_isl=False
  with self.assertRaisesRegex(ValueError,"reservation"):self.selected().determine_available_memory()
  self.assertEqual(self.events,[])
 def test03_unchanged_http16_not_resident7_and_no_async_or_task_scope(self):
  for key,value in (("max_num_seqs",7),("async_scheduling",True),("max_num_batched_tokens",32768)):
   old=getattr(self.cfg.scheduler_config,key);setattr(self.cfg.scheduler_config,key,value)
   with self.assertRaises(ValueError):self.p.mixed_policy(self.cfg)
   setattr(self.cfg.scheduler_config,key,old)
  self.cfg.model_config.max_model_len=40960
  with self.assertRaises(ValueError):self.p.mixed_policy(self.cfg)
 def test04_source_native_layout_to_real_explicit_owner64_geometry(self):
  w=self.initialized();state=w._kivi_explicit_provider
  fixture=self.oldtests.ProviderTests("test01_actual_off_returns_without_source_or_tensor")
  event,zero,_=fixture.native_event_fixture(state["plan"],state["native_descriptors"])
  event["identity"]=zero["identity"]=self.ident
  er=self.write("event",event);zr=self.write("zero",zero);final=self.write("final",dict(fixture_not_authority=True))
  plan=self.write("input-plan",dict(rows=[dict(fixture_not_authority=True)for _ in range(64)]))
  bindings=types.SimpleNamespace(owner=dict(container_id="a"*64,rank_bindings={"0":self.ident}),plan_ref=plan,
   expected={"r%02d"%i:dict(prompt=[1]*32768)for i in range(64)},frontend_binding_ref=plan,rank_bindings_ref=plan)
  recipe=dict(container_id="a"*64,actual_input_protocol_ref=plan,bits=2,run_id="fixture",
   diagnostic_root=str(self.root),native_format_binding={},external_owner_authority_ref=plan,
   compiled_numeric_qualification_ref=plan)
  owner,r=self.owner.post_input(recipe,bindings,event,er,final,zero,self.g,self.spans,self.write,provider_state=state)
  self.assertEqual(self.g.document(r),owner);self.assertEqual(len(owner["declared_passed_request_ids"]),64)
  self.assertEqual(owner["explicit_plan_ref"],state["plan_ref"])
  capacity=self.g.document(owner["capacity_receipt_ref"])
  self.assertEqual(capacity["maximum_output"],1024);self.assertEqual(capacity["slots"],16)
  self.assertTrue(all(set(v)=={"pages","bits","allocation_ref"}for v in owner["regions"].values()))
  for name in state["arenas"]:
   g=self.g.geometry(state,event,er,zr,name);gr=self.write(name,g)
   self.assertEqual(len(self.g.consume_geometry(self.g.document(gr),event)),9)
  bindings.expected["r00"]["prompt"].pop()
  with self.assertRaisesRegex(ValueError,"all64"):self.owner.post_input(
   recipe,bindings,event,er,final,zero,self.g,self.spans,self.write,provider_state=state)
 def test05_original_critical_math_allocator_body_unchanged(self):
  def nodes(path):
   return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(path.read_bytes()).body
           if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  old=nodes(BASE/"explicit_provider.py");new=nodes(HERE/"explicit_provider.py")
  for name in ("native_summary","field_bytes","overhead","policy","plan","native_raw_check"):
   self.assertEqual(old[name],new[name],name)
  # The complete installer is byte-identical to independently frozen006.
  self.assertEqual(ref(HERE/"installer.py")["sha256"],
   "536131653087de8f2daab16a65c3d5ce863e4ff7d74a8cf0eabb03aec620cedc")
  for name in("prebind.py","explicit_geometry.py","provider_independent.py"):
   self.assertEqual((BASE/name).read_bytes(),(HERE/name).read_bytes())
  self.assertFalse(any(n.split(".")[0]in("torch","torch_npu","triton","vllm")for n in sys.modules))
if __name__=="__main__":
 if sys.argv[1:]!=["--execute"]:print(json.dumps(dict(enabled=False,model_ready=False,run_authority=False)))
 else:
  r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProviderHandoff))
  print(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),
   actual_framework=False,actual_model=False,numerical_checked=False,run_authority=False)))
  raise SystemExit(not r.wasSuccessful())
