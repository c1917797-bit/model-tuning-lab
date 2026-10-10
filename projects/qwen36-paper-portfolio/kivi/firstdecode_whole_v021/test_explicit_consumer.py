"""Actual017 pure receipt consumers + native allocator source-body fixtures.
All tensor/device/process values are explicit inert fixtures, not runtime proof.
No candidate numerical/oracle body is copied or run; old71 suite is retained.
"""
import ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
CORE=None
COMMON=None
PRODUCER_ARCHIVE=None
class ExplicitReceipts(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.number=0
  self.env=patch.dict(os.environ,{"KIVI_PROVIDER_LOCAL_ARCHIVE":"1"if os.name=="nt"else"0"});self.env.start();self.addCleanup(self.env.stop)
  path=PRODUCER_ARCHIVE/"test_provider_integration.py"
  mf=json.loads((PRODUCER_ARCHIVE/"SOURCE_MANIFEST.json").read_bytes());own={Path(r["path"]).name:r for r in mf["files"]}
  wire=path.read_bytes();self.assertEqual(hashlib.sha256(wire).hexdigest(),own[path.name]["sha256"])
  alias="_whole017_actual_provider_fixture"
  if alias in sys.modules:self.T=sys.modules[alias]
  else:
   spec=importlib.util.spec_from_file_location(alias,path);self.T=importlib.util.module_from_spec(spec)
   sys.modules[alias]=self.T;spec.loader.exec_module(self.T)
  self.actual=self.T.ExplicitIntegration("test01_actual_native_provider_real_publication_all16_consumer")
  self.actual.setUp();self.addCleanup(self.actual.doCleanups)
  self.source=dict(path=CORE.PRODUCER_ROOT+"/SOURCE_MANIFEST.json",bytes=CORE.PRODUCER_BYTES,sha256=CORE.PRODUCER_SHA)
  self.recipe=dict(container_id="a"*64,bits=2);self.recipe_ref=self.artifact(self.recipe)
  ownlocal={name:CORE.ref(PRODUCER_ARCHIVE/name)for name in own}
  roles=dict(mf["runtime_roles"])
  roles["kivi_layout_consumer"]=CORE.ref(self.T.layout.__file__)
  roles["spans"]=CORE.ref(self.T.spans.__file__)
  self.ctx=types.SimpleNamespace(loader=self.T.L,own=ownlocal,m=dict(mf,runtime_roles=roles),producer=self.source)
  self.ids=[dict(pid=900+i,start_ticks=1000+i,cgroup="7:memory:/docker/"+self.recipe["container_id"])for i in range(4)]
  self.bundles=[]
  plan=self.T.G.document(self.actual.state["plan_ref"]);allocation=self.T.G.document(self.actual.state["allocation_ref"])
  for rank in range(4):
   ident=self.ids[rank]
   def rerank(x):
    if isinstance(x,list):return [rerank(v)for v in x]
    if isinstance(x,dict):
     out={k:rerank(v)for k,v in x.items()}
     if "rank"in out:out["rank"]=rank
     if "identity"in out:out["identity"]=dict(ident)
     if out.get("device")=="npu:0":out["device"]="npu:"+str(rank)
     return out
    return x
   p=rerank(copy.deepcopy(plan));a=rerank(copy.deepcopy(allocation));event=rerank(copy.deepcopy(self.actual.event))
   zero=rerank(copy.deepcopy(self.actual.zero))
   for document in(p,a):document["source_ref"]=self.source;document["recipe_ref"]=self.recipe_ref
   pr=self.artifact(p);a["plan_ref"]=pr
   native={d["storage_base"]:d for d in a["native"]}
   a["independent"]=self.T.I.consume(p,native,a["compact"])
   ar=self.artifact(a);er=self.artifact(event);zr=self.artifact(zero)
   geometries={}
   for name in self.actual.state["arenas"]:
    g=rerank(copy.deepcopy(self.actual.geometry(name)))
    g.update(plan_ref=pr,allocation_ref=ar,event_ref=er,zeroer_ref=zr)
    g["fields"]=[dict(name=n,descriptor=a["compact"][name][n])for n,*unused in self.T.I.expected_fields(p["pages"],p["bits"])]
    geometries[name]=self.artifact(g)
   owner=dict(explicit_plan_ref=pr,explicit_allocation_ref=ar,field_geometry_refs=geometries,
    zeroer_writer_receipt_ref=zr,rank_bindings={str(i):v for i,v in enumerate(self.ids)},container_id=self.recipe["container_id"],
    native_capacity_reduced=True,compact_new_allocation_explicit=True,allocation_replaced=False)
   decision=self.T.G.consume_rank(owner,event,a["compact"],zero)
   owner["layout_consumer_ref"]=self.artifact(decision)
   self.bundles.append(dict(rank=rank,identity=ident,owner_ref=self.artifact(owner),event_ref=er))
  self.client=dict(rank_bundle_refs=[self.artifact(v)for v in self.bundles])
 def artifact(self,value):
  self.number+=1;p=self.root/("%d.json"%self.number);p.write_bytes(json.dumps(value,sort_keys=True,separators=(",",":")).encode()+b"\n")
  return CORE.ref(p)
 def run_consumer(self):return CORE.explicit_allocations(self.ctx,self.client,self.recipe,self.recipe_ref,self.ids)
 def replace_owner(self,rank,change):
  bundle=self.bundles[rank];owner=CORE.obj(bundle["owner_ref"]);change(owner)
  bundle=dict(bundle,owner_ref=self.artifact(owner));self.client["rank_bundle_refs"][rank]=self.artifact(bundle)
 def test_actual_source_factory_all4_all64_native_and144_compact_receipts(self):
  rows=self.run_consumer();self.assertEqual([r["rank"]for r in rows],list(range(4)))
  self.assertTrue(all(len(r["geometry_refs"])==16 and r["independent"]["fields"]==144 for r in rows))
  self.assertTrue(all(r["independent"]["zeroer_after_initialize_checked"]for r in rows))
 def test_wrong_source_plan_cannot_borrow_old014_or_pure_flags(self):
  def change(owner):
   p=CORE.obj(owner["explicit_plan_ref"]);p["source_ref"]=dict(self.source,sha256="f"*64)
   owner["explicit_plan_ref"]=self.artifact(p)
  self.replace_owner(0,change)
  with self.assertRaises(ValueError):self.run_consumer()
 def test_wrong_recipe_allocation_rejected(self):
  def change(owner):
   a=CORE.obj(owner["explicit_allocation_ref"]);a["recipe_ref"]=dict(self.recipe_ref,sha256="f"*64)
   owner["explicit_allocation_ref"]=self.artifact(a)
  self.replace_owner(1,change)
  with self.assertRaises(ValueError):self.run_consumer()
 def test_missing_FA_geometry_keeps_full16_requirement(self):
  self.replace_owner(2,lambda owner:owner["field_geometry_refs"].pop(next(iter(owner["field_geometry_refs"]))))
  with self.assertRaisesRegex(ValueError,"all64 native"):self.run_consumer()
 def test_alias_overlap_and_stale_published_allocation_rejected(self):
  def change(owner):
   a=CORE.obj(owner["explicit_allocation_ref"]);first=next(iter(a["compact"].values()))
   first["key_codes"]["storage_base"]=a["native"][0]["storage_base"]
   owner["explicit_allocation_ref"]=self.artifact(a)
  self.replace_owner(0,change)
  with self.assertRaises(ValueError):self.run_consumer()
 def test_old_padding_geometry_and_stale_zeroer_rejected(self):
  def change(owner):
   name=next(iter(owner["field_geometry_refs"]));g=CORE.obj(owner["field_geometry_refs"][name])
   g["schema"]="kivi.actual-field-geometry/v1";owner["field_geometry_refs"][name]=self.artifact(g)
  original=copy.deepcopy(self.client)
  self.replace_owner(0,change)
  with self.assertRaises(ValueError):self.run_consumer()
  self.client=original
  def stale(owner):
   zero=CORE.obj(owner["zeroer_writer_receipt_ref"]);zero["identity"]=dict(zero["identity"],start_ticks=999999)
   owner["zeroer_writer_receipt_ref"]=self.artifact(zero)
  self.replace_owner(0,stale)
  with self.assertRaises(ValueError):self.run_consumer()
 def test_wrong_rank_identity_or_borrowed_container_rejected(self):
  bad=copy.deepcopy(self.ids);bad[3]["start_ticks"]+=1
  with self.assertRaisesRegex(ValueError,"rank/PID/start/CID"):
   CORE.explicit_allocations(self.ctx,self.client,self.recipe,self.recipe_ref,bad)
class SoftwareStage(unittest.TestCase):
 def setUp(self):
  self.common=COMMON.Evidence("test_original_success_and_envelope");self.common.setUp();self.addCleanup(self.common.tearDown)
  self.artifact=self.common.artifact;self.calls=[]
  self.source=self.common.source
  owned=self.common.owned("cpu-preflight");owned_ref=self.artifact(owned)
  inspection=self.common.inspect(owned)
  before=self.artifact(dict(exit_code=0,stdout=json.dumps([dict(inspection,State=dict(Running=True,Pid=800,OOMKilled=False))])))
  after=self.artifact(dict(exit_code=0,stdout=json.dumps([inspection])))
  clean=self.artifact(dict(container=owned["cid"],stopped=True,retained=True,deleted=False,errors=[],
    before_inspect=before,after_inspect=after,
    stop_receipt=self.artifact(dict(exit_code=0,requested_argv=["/usr/bin/docker","stop","--time","15",owned["cid"]]))))
  spec=importlib.util.spec_from_file_location("_whole017_stage_contract",PRODUCER_ARCHIVE/"model_contract.py")
  c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
  report=dict(source=self.source,successful=True,NPU=False,python_version=[3,12,13],
   execution_profile="same660-Devices[]-CPU8",no_framework_import=True,memory_before=dict(marker="before"),memory_after=dict(marker="after"))
  self.report_ref=self.artifact(report)
  expected=c.docker_argv(owned["cid"],[str(c.BASE/"software_check.py"),"--execute",
   "--source-manifest-sha256",self.source["sha256"],"--output",self.report_ref["path"]])
  child=self.artifact(dict(requested_argv=expected,exit_code=0,child_termination_observed=True))
  self.stage=dict(schema="kivi.actual-firstdecode-software-cpu-host/v1",status="SOFTWARE_ONLY_CONSUMED",
   source=self.source,report=self.report_ref,primary=None,secondary=[],NPU_created=False,model_ready=False,run_authority=False,
   owned=owned_ref,cleanup=clean,child=child,phase_seconds=240,cleanup_seconds=90,elapsed_seconds=1)
  # Actual host consume predicate and actual source-extracted validate_inspect.
  # Memory reader invocation is spied, never a claimed cgroup/process proof.
  c.obj=CORE.obj
  memory=types.SimpleNamespace(consume_memory=lambda v,**kw:self.calls.append((v,kw)))
  self.ctx=types.SimpleNamespace(c=c,own={"host_run.py":CORE.ref(PRODUCER_ARCHIVE/"host_run.py")},
   producer=self.source,s=self.common.extract_safety(),loader=types.SimpleNamespace(memory_module=lambda m:memory))
  original_obj=c.obj
  c.obj=lambda r:{"fixture_manifest":True}if r==self.source else original_obj(r)
 def consume(self,value=None):return CORE.consume_software_stage(self.ctx,self.artifact(value or self.stage),self.report_ref)
 def test_real_host_predicate_cleanup_original_inspect_and_cpu3_12_report(self):
  result=self.consume();self.assertEqual(len(self.calls),2)
  self.assertEqual([v[0]["marker"]for v in self.calls],["before","after"])
  self.assertTrue(all(v[1]==dict(expected_limit=8*CORE.GIB,container_id=self.common.cid)for v in self.calls))
  self.assertFalse(result["NPU"]);self.assertFalse(result["original_model_operation_verified"])
 def test_software_wrong_source_failed_or_wrong_report_reject(self):
  for changed in(dict(source={}),dict(primary="original error"),dict(report={})):
   with self.subTest(changed=changed),self.assertRaises(ValueError):self.consume(dict(self.stage,**changed))
 def test_software_Devices_or_not_stopped_are_not_silently_admitted(self):
  clean=CORE.obj(self.stage["cleanup"]);raw=CORE.obj(clean["after_inspect"]);x=json.loads(raw["stdout"])[0]
  x["State"]["Running"]=True;x["State"]["Pid"]=123;raw["stdout"]=json.dumps([x])
  clean["after_inspect"]=self.artifact(raw);self.stage["cleanup"]=self.artifact(clean)
  with self.assertRaises(ValueError):self.consume()
 def test_software_child_no_termination_or_wrong_current_source_reject(self):
  child=CORE.obj(self.stage["child"]);child["child_termination_observed"]=False
  self.stage["child"]=self.artifact(child)
  with self.assertRaisesRegex(ValueError,"exact software child"):self.consume()
 def test_real_consumer_ast_preserves_all_branches_only_import_is_resolved(self):
  source=CORE.read(self.ctx.own["host_run.py"],128*1024);tree=ast.parse(source)
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="consume_software_stage")
  self.assertIsInstance(fn.body[1],ast.Import)
  target=ast.parse(Path(CORE.__file__).read_bytes())
  wrapper=next(n for n in target.body if isinstance(n,ast.FunctionDef)and n.name=="consume_software_stage")
  pops=[n for n in ast.walk(wrapper)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=="pop"]
  self.assertEqual(len(pops),1);self.assertEqual(pops[0].args[0].value,1)
  self.assertFalse(any(isinstance(n,ast.Assign)and any(isinstance(z,ast.Attribute)and z.attr=="test"for z in n.targets)for n in ast.walk(wrapper)))
