"""Actual new pure helpers/file chains plus explicit inert native ABI fixtures. No HAL."""
import ast,copy,hashlib,importlib.util,io,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import screen_contract as C,transport as T,screen_gate as G,screen_evidence as E
import dense_boundary as D,server_entry as S,input_recipe as I,screen_whole as H
HERE=Path(__file__).resolve().parent
SHARED=Path(os.environ.get("KIVI_SCREEN_REVIEWED_DEPS",
 "C:/Users/Huawei/AppData/Local/Packages/sandbox.{48fdcea7-5947-498c-a068-4bc4cdaddb04}/AC/Temp/kivi-c132-reviewed-source/model-deps"))
def module(path,name,sha=None):
 wire=path.read_bytes()
 if sha is not None:C.need(hashlib.sha256(wire).hexdigest()==sha,"source identity")
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
 sys.modules[name]=m;spec.loader.exec_module(m);return m
class Base(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.pub=lambda name,value:T.publish(self.root/(name+".json"),value)
class Parameters(Base):
 def test29_actual_server_all_common_flags(self):
  argv=S.native_argv(8250,6*1024**3)
  for flag,value in (("--max-num-seqs","1"),("--kv-cache-memory-bytes",str(6*1024**3)),
   ("--max-model-len","33792"),("--dtype","bfloat16"),("--seed","0")):
   self.assertEqual(argv[argv.index(flag)+1],value)
  self.assertIn("--no-async-scheduling",argv);self.assertIn("--enforce-eager",argv)
  self.assertEqual(argv,S.native_argv(8250,6*1024**3))
 def test30_original_environment_body_exact_algorithm_delta(self):
  tree=ast.parse((HERE/"safety_host.py").read_bytes())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="environment")
  ns=dict(c=types.SimpleNamespace(require=C.need))
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HERE/"safety_host.py"),"exec"),ns)
  d,k=(ns["environment"](False,arm)for arm in("dense","candidate"))
  delta={name for name in d if d[name]!=k[name]}
  self.assertEqual(delta,{"QWEN36_KIVI_SCREEN_ARM","QWEN36_KIVI_PACKED_QKAV_QWEN_INSTALLER",
   "QWEN36_KIVI_EXPLICIT_CACHE_PROVIDER","QWEN36_KIVI_PACKED_QKAV_OWNED_SEAM","QWEN36_KIVI_PACKED_QKAV_SOURCE_CANDIDATE"})
  self.assertEqual(d["QWEN36_KIVI_OBSERVER_OFF_TIMING"],k["QWEN36_KIVI_OBSERVER_OFF_TIMING"])
  self.assertEqual(ns["environment"](True,"dense")["ASCEND_RT_VISIBLE_DEVICES"],"")
 def test31_actual_recipe_producer_three_independent_full_inputs(self):
  config=self.pub("config",dict(model_type="qwen3_5",text_config=dict(model_type="qwen3_5_text",vocab_size=300000)))
  tok=self.pub("tokenizer_config",dict(fixture=True));mf=self.pub("model",dict(host_model_root=str(self.root)))
  source=self.pub("source",dict(fixture=True));reads=[]
  def bound(path,sha):
   reads.append(str(path));return config
  contract=types.SimpleNamespace(obj=C.read,require=C.need,CONFIG_SHA=config["sha256"],bound=bound,
   write=lambda p,v:T.publish(p,v),ref=lambda p:tok,checked=lambda r:r)
  out=self.root/"producer";out.mkdir()
  plan,protocol=I.create(contract,source,mf,out,"actual-fixture",host=False)
  self.assertEqual([Path(x)for x in reads],[Path("/models/Qwen3.6-27B/config.json")])
  pp=C.read(protocol);rows=C.read(plan)["rows"]
  self.assertEqual(len(rows),3);self.assertEqual([r["outputs"]for r in pp["requests"]],[2,2,129])
  for r in rows:self.assertEqual(C.read(r["prompt_token_ids_ref"]),C.prompt())
  self.assertEqual(len({r["declared_passed_id"]for r in rows}),3)
 def test32_missing_or_boolean_vocabulary_is_not_accepted(self):
  for text in ({},{"model_type":"qwen3_5_text","vocab_size":True},{"model_type":"wrong","vocab_size":300000}):
   with self.assertRaises(ValueError):I.validate_config(dict(model_type="qwen3_5",text_config=text),C.prompt(),C.need)
 def test33_same_pinned_critical_math(self):
  expected={
   "producer.py":"1687f25252dc5ca94c69b666e1307f5721e83a81da74cccfa4c7e25a3ed2e726",
   "explicit_provider.py":"2d2f9dd141880213ba463953c35a7498a9902ee957c472c783aa6a3f9ca64389"}
  for name,sha in expected.items():self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(),sha)
 def test34_no_software_guard_removed_or_device_branch_added(self):
  tree=ast.parse((HERE/"host_run.py").read_bytes())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="software_only")
  text=ast.unparse(fn)
  self.assertNotIn('"candidate"',text);self.assertNotIn("'candidate'",text);self.assertNotIn("n1",text)
  self.assertIn("cpu-preflight",text);self.assertIn("consume_software_stage",text)
 def test35_consumer_first_initial_resource_is_exact_source_ref(self):
  tree=ast.parse((HERE/"screen_whole.py").read_bytes())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="producer_only")
  self.assertIn("model_observations(ctx, npu, owner, owned, host['pid'], output, allocation)",ast.unparse(fn))
  self.assertEqual(H.MODEL_OBSERVATION_PINS["host_run.py"],hashlib.sha256((HERE/"host_run.py").read_bytes()).hexdigest())
  self.assertEqual(H.MODEL_OBSERVATION_PINS["ownership.py"],hashlib.sha256((HERE/"ownership.py").read_bytes()).hexdigest())
 def test36_client_default_off_no_framework(self):
  import client
  before=set(sys.modules)
  with patch("sys.stdout",new=io.StringIO()):self.assertEqual(client.main([]),0)
  self.assertFalse((set(sys.modules)-before)&{"torch","torch_npu","triton"})
class Prerequisite(Base):
 def value(self):
  return dict(status="FIRSTDECODE_OWNED_RAW_AND_WHOLE_CONSUMED",producer_source=C.PRODUCER,
   firstdecode_integration_checked=True,FA_frames=64,native_finished_all4_checked=True,
   original_prefill_tokens=32768,actual_first_decode_length=32769,model_ready=False,
   performance_ready=False,run_authority=False)
 def test37_all64_before_any_timing_permission(self):
  self.assertIs(G.check_consumed(self.value(),C)["model_ready"],False)
 def test38_short_or_wrong_prerequisite_never_promoted(self):
  for key,bad in (("FA_frames",63),("original_prefill_tokens",16),("actual_first_decode_length",32768),
   ("status","RAW_CAPTURED_PENDING_INDEPENDENT_WHOLE_CONSUMPTION"),("run_authority",True)):
   v=self.value();v[key]=bad
   with self.assertRaises(ValueError):G.check_consumed(v,C)
 def test39_worker_rejects_wrong_common_scope(self):
  source=self.pub("source",dict(fixture=True))
  gate=self.pub("gate",dict(schema="kivi.screen.actual-firstdecode-prerequisite/v1",source=source,successful=True,
   whole_source=C.WHOLE,raw_source=C.RAW,NPU=False,model_ready=False,performance_ready=False,
   run_authority=False,consumed=self.value()))
  recipe=dict(firstdecode_prerequisite_ref=gate,algorithm_arm="candidate",screen_output_counts=[2,2,129],cache_bytes=6*1024**3)
  G.worker_check(recipe,C.read,source)
  for key,bad in (("algorithm_arm","C16"),("screen_output_counts",[2]),("cache_bytes",10*1024**3)):
   other=dict(recipe);other[key]=bad
   with self.assertRaises(ValueError):G.worker_check(other,C.read,source)
class NativeBoundary(Base):
 def fixture(self):
  self.ident=dict(pid=101,start_ticks=202,cgroup="f"*64)
  self.rows=C.rows("nativefixture");self.ids=["cmpl-"+r["header_id"]+"-0"for r in self.rows]
  self.calls=[];self.refs=[];self.finals=[]
  class Runner:
   def __init__(s):
    s.requests={};s.input_batch=types.SimpleNamespace(num_reqs=0,req_ids=[])
   def _update_states(s,scheduler):
    self.calls.append(scheduler)
    for item in scheduler.scheduled_new_reqs:s.requests[item.req_id]=item
    for rid in scheduler.finished_req_ids:s.requests.pop(rid)
    s.input_batch.req_ids=list(s.requests);s.input_batch.num_reqs=len(s.requests)
    return lambda:"actual-deferred-fixture-value"
  r=Runner();old=r._update_states
  def check(scheduler,ident,rank,publish):
   for req in scheduler.scheduled_new_reqs:
    publish("ingress-"+req.req_id,dict(schema="kivi.actual-native-ingress/v1",rank=rank,identity=ident,
     req_id=req.req_id,prompt_token_ids=C.prompt(),scheduled_type="SchedulerOutput/NewRequestData"))
  binding=types.SimpleNamespace(owner=dict(rank_bindings={"0":self.ident}),expected=dict.fromkeys(self.ids),check_new=check)
  def publish(label,row):
   ref=self.pub(label,row);self.refs.append(ref);return ref
  with patch.object(D,"pin")as pinned:
   state=D.install(r,binding,lambda:dict(self.ident),0,publish,self.finals.append,{"fixture":"source"},{"fixture":"recipe"},lambda *a:[])
  self.assertEqual(pinned.call_count,2)
  return r,state,old
 def test40_actual_dense_wrapper_calls_original_once_and_publishes_native_finish(self):
  r,state,old=self.fixture()
  for rid in self.ids:
   answer=r._update_states(types.SimpleNamespace(scheduled_new_reqs=[types.SimpleNamespace(req_id=rid)],finished_req_ids=[]))
   self.assertEqual(answer(),"actual-deferred-fixture-value")
   r._update_states(types.SimpleNamespace(scheduled_new_reqs=[],finished_req_ids=[rid]))
  self.assertEqual(len(self.calls),6);self.assertEqual(r._update_states,old)
  self.assertEqual(state["final"],self.finals[0])
  value=C.read(state["final"]);self.assertEqual(value["finished"],sorted(self.ids))
  self.assertEqual(len(value["boundary_refs"]),6);self.assertFalse(value["numeric_verified"])
 def test41_HTTP_only_or_unseen_finish_rejects_before_native(self):
  r,state,old=self.fixture()
  with self.assertRaises(ValueError):r._update_states(types.SimpleNamespace(scheduled_new_reqs=[],finished_req_ids=[self.ids[0]]))
  self.assertEqual(self.calls,[]);self.assertIsNone(state["final"])
 def test42_more_than_B1_rejects_before_native(self):
  r,state,old=self.fixture()
  with self.assertRaises(ValueError):
   r._update_states(types.SimpleNamespace(scheduled_new_reqs=[types.SimpleNamespace(req_id=x)for x in self.ids[:2]],finished_req_ids=[]))
  self.assertEqual(self.calls,[])
 def test43_wrong_live_identity_rejects(self):
  r,state,old=self.fixture();self.ident=dict(self.ident,pid=102)
  with self.assertRaises(ValueError):
   r._update_states(types.SimpleNamespace(scheduled_new_reqs=[],finished_req_ids=[]))
class ActualIngressWire(Base):
 def setUp(self):
  super().setUp()
  self.bind=module(SHARED/"bindings.py","_runtime_actual_bindings",
   "71b5c3650eab308b86a26da62abcd249c77fc7528c4c8022bf779af56ef38f99")
  path=Path(os.environ.get("KIVI_SCREEN_ORACLE_ARCHIVE","C:/Users/Huawei/AppData/Local/Temp/c164-kivi-e2e-deps/oracle.py"))
  self.oracle=module(path,"_runtime_actual_assignment_oracle",
   "f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333")
  self.cid="a"*64;self.front=dict(pid=10,start_ticks=20,cgroup=self.cid)
  self.ids={str(rank):dict(pid=100+rank,start_ticks=200+rank,cgroup=self.cid)for rank in range(4)}
  self.fr=self.pub("frontend",self.front);external=self.pub("external",dict(fixture=True))
  self.owner=self.pub("ranks",dict(container_id=self.cid,rank_bindings=self.ids,
   frontend_binding_ref=self.fr,external_owner_authority_ref=external))
  prompt=self.pub("prompt",C.prompt());decl=[]
  for row in C.rows("wirefixture"):
   server="cmpl-"+row["header_id"];rid=server+"-0"
   decl.append(dict(header_request_id=row["header_id"],body_request_id=None,declared_server_id=server,
    declared_passed_id=rid,prompt_token_ids_ref=prompt))
  dummy=self.pub("producer",dict(fixture=True))
  self.plan=self.pub("plan",dict(schema="kivi.declared-model-ingress-plan/v1",profile=self.bind.PROFILE,
   rows=decl,input_producer_ref=dummy,tokenizer_ref=dummy,model_binding_ref=dummy,
   declared_randomization_off=True,model_ready=False,run_authority=False))
  self.recipe=dict(source_ref=dummy,algorithm_arm="dense",run_id="wirefixture",screen_output_counts=[2,2,129],
   declared_ingress_plan_ref=self.plan,diagnostic_root=str(self.root),container_id=self.cid,
   rank_bindings_path=self.owner["path"],frontend_binding_path=self.fr["path"])
  self.rr=self.pub("recipe",self.recipe)
 def bundle(self,rank):
  ident=self.ids[str(rank)];refs=[];rows=C.read(self.plan)["rows"]
  for row in rows:
   rid=row["declared_passed_id"]
   assigned=self.pub("assign-r%d-%s"%(rank,rid),dict(schema="vllm023.actual-assignment/v1",
    before_external_req_id=None,before_request_id=rid,after_external_req_id=rid,after_request_id=rid,
    disable_request_id_randomization=True,source_sha256=self.oracle.ASSIGN_SHA,identity=self.front))
   refs.append(self.pub("ingress-r%d-%s"%(rank,rid),dict(schema="kivi.actual-native-ingress/v1",
    rank=rank,identity=ident,req_id=rid,prompt_token_ids=C.prompt(),scheduled_type="SchedulerOutput/NewRequestData",
    scheduled_source_sha256=self.bind.SCHED_SHA,runner_source_sha256=self.bind.NPU_SHA,
    actual_assignment_ref=assigned,frontend_binding_ref=self.fr,rank_bindings_ref=self.owner,plan_ref=self.plan,
    prompt_token_ids_ref=row["prompt_token_ids_ref"])))
   path=E.retirement_path(self.recipe,ident,rank,rid)
   refs.append(T.publish(path,dict(schema="kivi.actual-packed-qwen-retire/v1",rank=rank,identity=ident,
    request_id=rid,actual_native_finished=True,model_ready=False)))
  return self.pub("dense-r%d-final"%rank,dict(schema="kivi.b1-dense-native-final/v1",rank=rank,identity=ident,
   source_ref=self.recipe["source_ref"],recipe_ref=self.rr,finished=sorted(r["declared_passed_id"]for r in rows),
   boundary_refs=refs,runner_source_sha256=self.bind.NPU_SHA,original_update_restored=True,
   complete_per_token_journal=False,numeric_verified=False,model_ready=False,run_authority=False))
 def test44_all4_original_assignment_verifier_full32768_real_file_replay(self):
  for rank in range(4):
   ref=self.bundle(rank)
   result=E.rank_bundle(ref,self.recipe,self.rr,rank,self.ids[str(rank)],C.read,self.bind,self.oracle,"fixture")
   self.assertTrue(result["actual_ingress_checked"]);self.assertFalse(result["numeric_verified"])
 def test45_missing_retire_rejects_no_HTTP_substitute(self):
  ref=self.bundle(0);value=C.read(ref);value["boundary_refs"]=value["boundary_refs"][:-1]
  bad=self.pub("missing",value)
  with self.assertRaises(ValueError):E.rank_bundle(bad,self.recipe,self.rr,0,self.ids["0"],C.read,self.bind,self.oracle,"fixture")
 def test46_changed_original_prompt_rejected(self):
  ref=self.bundle(0);value=C.read(ref);row=C.read(value["boundary_refs"][0]);row["prompt_token_ids"][0]+=1
  value["boundary_refs"][0]=self.pub("wrong-prompt",row);bad=self.pub("wrong-bundle",value)
  with self.assertRaises(ValueError):E.rank_bundle(bad,self.recipe,self.rr,0,self.ids["0"],C.read,self.bind,self.oracle,"fixture")
 def test47_wrong_assignment_identity_rejected(self):
  ref=self.bundle(0);value=C.read(ref);row=C.read(value["boundary_refs"][0])
  assignment=C.read(row["actual_assignment_ref"]);assignment["identity"]=dict(self.front,pid=11)
  row["actual_assignment_ref"]=self.pub("wrong-assign",assignment)
  value["boundary_refs"][0]=self.pub("wrong-ingress",row);bad=self.pub("wrong-bundle",value)
  with self.assertRaises(ValueError):E.rank_bundle(bad,self.recipe,self.rr,0,self.ids["0"],C.read,self.bind,self.oracle,"fixture")
 def test48_no_per_token_schema_permitted_in_timing_final(self):
  ref=self.bundle(0);value=C.read(ref);value["boundary_refs"].insert(1,self.pub("raw",dict(schema="kivi.actual-packed-qwen-frame/v1")))
  bad=self.pub("raw-bundle",value)
  with self.assertRaises(ValueError):E.rank_bundle(bad,self.recipe,self.rr,0,self.ids["0"],C.read,self.bind,self.oracle,"fixture")

 def test55_actual_common_client_three_http_requests_all4_original_oracle(self):
  import client,loader
  from test_screen import Wire
  protocol=self.pub("protocol",dict(source_ref=self.recipe["source_ref"],plan_ref=self.plan,
   protocol=C.PROTOCOL,requests=[dict(row,payload=C.payload(C.prompt(),row["outputs"]))for row in C.rows(self.recipe["run_id"])]))
  prerequisite=dict(status="FIRSTDECODE_OWNED_RAW_AND_WHOLE_CONSUMED",producer_source=C.PRODUCER,
   firstdecode_integration_checked=True,FA_frames=64,native_finished_all4_checked=True,
   original_prefill_tokens=32768,actual_first_decode_length=32769,model_ready=False,performance_ready=False,run_authority=False)
  gate=self.pub("gate",dict(schema="kivi.screen.actual-firstdecode-prerequisite/v1",source=self.recipe["source_ref"],
   successful=True,whole_source=C.WHOLE,raw_source=C.RAW,NPU=False,model_ready=False,performance_ready=False,
   run_authority=False,consumed=prerequisite))
  self.recipe.update(actual_input_protocol_ref=protocol,firstdecode_prerequisite_ref=gate,cache_bytes=6*1024**3)
  self.rr=self.pub("complete-recipe",self.recipe)
  import cost_runtime
  # Explicit inert schema fixture; no target/device timing is claimed.
  mf=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  fixture_source=self.pub("cost-fixture-source",mf)
  self.recipe["source_ref"]=fixture_source
  protocol_value=C.read(protocol);protocol_value["source_ref"]=fixture_source
  protocol=self.pub("cost-protocol",protocol_value);self.recipe["actual_input_protocol_ref"]=protocol
  gate_value=C.read(gate);gate_value["source"]=fixture_source
  gate=self.pub("cost-gate",gate_value);self.recipe["firstdecode_prerequisite_ref"]=gate
  self.rr=self.pub("cost-recipe",self.recipe)
  for rank in range(4):
   bundle=self.bundle(rank);self.pub("RANK-%d-FINAL-INDEX"%rank,bundle)
   refs={n:mf["runtime_roles"][n]for n in cost_runtime.M.TARGETS if n!="writer"}
   refs["writer"]=next(r for r in mf["dependencies"]if r["sha256"]=="051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b")
   windows=[]
   for name,count in(("warmup0",2),("warmup1",2),("request00",129)):
    for phase,num in(("prefill",1),("decode",count-1),("retire",1)):
     windows.extend(dict(phase=name+"."+phase,wall_ns=1,thread_cpu_ns=0,failed=False)for unused in range(num))
   self.pub("COST-r%d"%rank,dict(schema=cost_runtime.M.SCHEMA,rank=rank,arm="dense",
    source_ref=fixture_source,recipe_ref=self.rr,native_final_ref=bundle,profile=cost_runtime.PROFILE,
    declared_owner_ids=[v["declared_passed_id"]for v in C.read(self.plan)["rows"]],
    finished_owner_ids=sorted(v["declared_passed_id"]for v in C.read(self.plan)["rows"]),
    source_roles=refs,windows=windows,stats=[],new_synchronizations=0,tensor_snapshots=0,per_token_file_publications=0,
    device_kernel_time_measured=False,numerical_verified=False,performance_accepted=False,run_authority=False,
    timings_are_inclusive=True,wall_includes_probe_overhead=True,
    local_events=["PY_START","PY_RETURN"],global_events=["PY_UNWIND"]))
  roles=dict(bindings=C.ref(self.bind.__file__),assignment_oracle=C.ref(self.oracle.__file__),installer={"sha256":"fixture"})
  real_loader=types.SimpleNamespace(obj=C.read,ref=C.ref,module=loader.module,publish=T.publish)
  seen=[]
  class Response:
   status=200
   def __init__(s,lines):s.lines=lines
   def __enter__(s):return s
   def __exit__(s,*a):pass
   def __iter__(s):
    # The actual request buffer must not open its raw file during receipt.
    for row in s.lines:
     if seen[-1]["name"]=="request00":self.assertFalse((self.root/"http"/"request00.sse.jsonl").exists())
     yield row
  def opened(request,timeout):
   idx=len(seen);plan=C.rows(self.recipe["run_id"])[idx]
   self.assertEqual(json.loads(request.data),C.payload(C.prompt(),plan["outputs"]))
   seen.append(plan);return Response(Wire.lines(self,plan))
  with patch.object(T,"urlopen",side_effect=opened),patch("sys.stdout",new=io.StringIO()):
   self.assertEqual(client.run(real_loader,dict(runtime_roles=roles),self.recipe["source_ref"],self.rr,
    self.root/"CLIENT_RESULT.json",8250),0)
  result=C.read(C.ref(self.root/"CLIENT_RESULT.json"))
  self.assertEqual([v["outputs"]for v in seen],[2,2,129])
  self.assertEqual(result["status"],"COST129_HTTP_NATIVE_FINISHED")
  self.assertEqual(len(result["rank_bundle_refs"]),4)
  self.assertFalse(result["performance_ready"])
  self.assertTrue(E.client(result,self.recipe,self.rr,C.read,self.bind,self.oracle,"fixture")["whole_http_replayed"])

class ActualTimingLayout(unittest.TestCase):
 def setUp(self):
  from test_screen import ActualWorkerBridge,BASE
  ActualWorkerBridge.setUpClass();it=ActualWorkerBridge.integration
  self.case=it.ExplicitIntegration("test01_actual_native_provider_real_publication_all16_consumer")
  self.case.setUp();self.addCleanup(self.case.doCleanups);self.it=it
  self.old=module(BASE/"installer.py","_screen_layout_original")
  self.new=module(HERE/"installer.py","_screen_layout_new")
  self.contexts={name:dict(arena=arena)for name,arena in self.case.state["arenas"].items()}
  self.event=copy.deepcopy(self.case.event);static={}
  for name,row in self.event["layers"].items():
   views=[types.SimpleNamespace(untyped_storage=lambda:None,descriptor=copy.deepcopy(d))for d in row["views"]]
   static[name]=types.SimpleNamespace(kv_cache=views)
  self.runner=types.SimpleNamespace(speculative_config=None,compilation_config=types.SimpleNamespace(static_forward_context=static))
  self.callback=types.SimpleNamespace(scalar_tensor=lambda v:v.descriptor if hasattr(v,"descriptor")else it.F.describe(v))
 def test49_actual_CompactArena_two_integers_old_failure_new_whole_layout(self):
  with self.assertRaises(AttributeError):self.old.timing_layout(self.runner,self.event,self.contexts,self.callback)
  stamp=self.new.timing_layout(self.runner,self.event,self.contexts,self.callback)
  self.assertEqual(len(stamp[0]),64);self.assertEqual(len(stamp[1]),16)
  self.assertTrue(all(len(row[3])==9 for row in stamp[1]))
  self.assertTrue(all(row[2]["dense_shadow_bytes"]==0 for row in stamp[1]))
 def test50_control_bool_not_silently_skipped(self):
  next(iter(self.contexts.values()))["arena"].pool["allocated_bytes"]=True
  with self.assertRaises(ValueError):self.new.timing_layout(self.runner,self.event,self.contexts,self.callback)
 def test51_hidden_tensor_not_skipped(self):
  a=next(iter(self.contexts.values()))["arena"];a.pool["hidden"]=a.pool["shifts"]
  with self.assertRaises(ValueError):self.new.timing_layout(self.runner,self.event,self.contexts,self.callback)
 def test52_all64_native_metadata_change_rejects(self):
  row=next(iter(self.runner.compilation_config.static_forward_context.values()))
  row.kv_cache[0].descriptor["data_ptr"]+=1
  with self.assertRaises(ValueError):self.new.timing_layout(self.runner,self.event,self.contexts,self.callback)
 def test53_live_accounting_change_rejects(self):
  a=next(iter(self.contexts.values()))["arena"];a.pool["allocated_bytes"]+=4
  with self.assertRaises(ValueError):self.new.timing_layout(self.runner,self.event,self.contexts,self.callback)
 def test54_critical_install_math_body_remains_identical(self):
  def body(module):
   node=next(n for n in ast.parse(Path(module.__file__).read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=="install")
   return ast.dump(node,include_attributes=False)
  self.assertEqual(body(self.old),body(self.new))


class ObservationAndTitle(Base):
 def test56_source_first_resource_ref_only(self):
  pre={"path":"original-first","sha256":"fixture"}
  self.assertTrue(H.model_observation_initial({"label":"model-preflight"},pre,0,pre))
  for row,ref,index in (({"label":"model-preflight"},{"path":"other"},0),
   ({"label":"model-startup"},pre,0),({"label":"model-preflight"},pre,1),
   ({"label":"model-startup"},pre,1),({"label":"unknown"},{"path":"later"},1)):
   with self.subTest(row=row,index=index):
    with self.assertRaises(ValueError):H.model_observation_initial(row,ref,index,pre)
 def test57_source_all_live_labels_not_initial(self):
  for label in H.MODEL_LIVE_LABELS:
   self.assertFalse(H.model_observation_initial({"label":label},{"path":"later"},1,{"path":"first"}))
  self.assertIn("kivi-real-all4-owner-bind",H.MODEL_LIVE_LABELS)
 def test58_real_file_observation_sequence_actual_source_and_no_late_reset(self):
  refs=[self.pub("obs%d"%i,{"label":label,"actual_compute":[i]})
   for i,label in enumerate(("model-preflight","all4-N1","kivi-real-all4-owner-bind","model-after-firstdecode"))]
  own={n:H.ref(HERE/n)for n in H.MODEL_OBSERVATION_PINS};calls=[]
  def observation(ref,*args,initial=False):calls.append(initial);return "same"
  ctx=types.SimpleNamespace(own=own,observation=observation)
  self.assertEqual(H.model_observations(ctx,{"observations":refs},{"resource_ref":refs[0]},None,5,None,"same"),[0,1,2,3])
  self.assertEqual(calls,[True,False,False,False])
  with self.assertRaises(ValueError):H.model_observations(ctx,{"observations":refs+[refs[0]]},{"resource_ref":refs[0]},None,5,None,"same")
  with self.assertRaises(ValueError):H.model_observations(ctx,{"observations":refs[:-1]},{"resource_ref":refs[0]},None,5,None,"same")
 def test59_exact_same_rank_native_title_hash_representation(self):
  for rank in range(4):
   title="VLLM::Worker_TP%d"%rank
   for padding in (1,2,141,4096):
    digest=hashlib.sha256(title.encode()+b"\0"*padding).hexdigest()
    self.assertTrue(H.cmdline_digest_matches([title],digest,rank))
    if padding>1:self.assertFalse(H.cmdline_digest_matches([title],digest,(rank+1)%4))
 def test60_frontend_and_non_tail_changes_do_not_gain_padding_exception(self):
  for argv,wire,rank in ((["ordinary"],b"ordinary"+b"\0"*141,0),
   (["/python","arg"],b"/python\0arg\0\0",None),
   (["VLLM::Worker_TP0"],b"VLLM::Worker_TP0\0x\0",0),
   (["VLLM::Worker_TP0"],b"VLLM::Worker_TP0"+b"\0"*4097,0)):
   self.assertFalse(H.cmdline_digest_matches(argv,hashlib.sha256(wire).hexdigest(),rank))
  self.assertTrue(H.cmdline_digest_matches(["/python","arg"],hashlib.sha256(b"/python\0arg\0").hexdigest()))
  with self.assertRaises(ValueError):H.cmdline_digest_matches(["a\0b"],"f"*64)


class ActualInstalledDriverOrigin(Base):
 # Whole source-qualified actual0548 originals; no generated driver/module keys.
 FIXTURES={"CANARY_N1.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/CANARY_N1.json","bytes":127423,"sha256":"0c2b63410a068f25ad92971aba5993421d26fcdb484b09145f7322325c6612f4"},"RECIPE.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/RECIPE.json","bytes":5012,"sha256":"9798f7557332382032756ad9001dfefea10292d088ab76533d504ba9fc614ed7"},"KIVI_ALL4_NAMESPACE_RAW.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/KIVI_ALL4_NAMESPACE_RAW.json","bytes":24074,"sha256":"154a008968f09ecdadcf72aa1e74869c6236fd69d4cee28e3bac623a9eeb5c6e"},"DRIVER-PROPERTIES-r0.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/run-kivi-owned-layout-1791664208586952020/DRIVER-PROPERTIES-r0.json","bytes":2210,"sha256":"2363cfd8aea8e4796c9edbd3e99402bd7f97c5fffaaee75f02573d9dfaae5b59"},"DRIVER-PROPERTIES-r1.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/run-kivi-owned-layout-1791664208586952020/DRIVER-PROPERTIES-r1.json","bytes":2210,"sha256":"cdd9bef6f46e8c963bf96bf2680e1aa25f09cc8415d74fc6f37099e069119fc8"},"DRIVER-PROPERTIES-r2.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/run-kivi-owned-layout-1791664208586952020/DRIVER-PROPERTIES-r2.json","bytes":2210,"sha256":"3b499aeed759d2d7c568f32467d5d266976b9b176ed632ca550aab47cb5a959c"},"DRIVER-PROPERTIES-r3.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/run-kivi-owned-layout-1791664208586952020/DRIVER-PROPERTIES-r3.json","bytes":2210,"sha256":"376b78a4f1b78081cfc1e373662a6cef0eb6bf21a8c4d33d5a673de1adbdd2df"}}
 def actual(self,name):
  row=self.FIXTURES[name];archive=os.environ.get("KIVI_SCREEN_DRIVER_ARCHIVE")
  path=Path(archive)/name if archive else Path(row["path"])
  wire=path.read_bytes()
  self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(row["bytes"],row["sha256"]))
  return H.decode(wire)
 def actual_mf(self):
  from test_screen import BASE
  wire=(BASE/"SOURCE_MANIFEST.json").read_bytes()
  self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(C.PRODUCER["bytes"],C.PRODUCER["sha256"]))
  return H.decode(wire)
 def test61_actual_all4_N1_original_driver_helper_origin(self):
  n=self.actual("CANARY_N1.json");m=self.actual_mf()
  self.assertEqual(n["source"],C.PRODUCER);self.assertEqual(n["status"],"N1_ALL4_TINY_CHECKED")
  self.assertEqual(len(n["canary"]),4)
  for rank,row in enumerate(n["canary"]):
   proof=row["actual_driver_properties"]
   self.assertEqual(H.driver_properties(proof,rank,m),proof["device_properties"])
   self.assertEqual(proof["helper_source"]["path"],H.DRIVER_HELPER_ORIGIN)
 def test62_actual_unknown_archive_or_noncanonical_origin_rejected(self):
  proof=self.actual("CANARY_N1.json")["canary"][0]["actual_driver_properties"];m=self.actual_mf()
  for path in(m["runtime_abi_original_refs"]["helper"]["path"],
   "/cache/cch/vllm-ascend/vllm_ascend/ops/triton/triton_utils.py",
   "/unknown"+H.DRIVER_HELPER_ORIGIN,H.DRIVER_HELPER_ORIGIN.replace("/ops/","/ops/../ops/")):
   bad=copy.deepcopy(proof);bad["helper_source"]["path"]=path
   with self.subTest(path=path),self.assertRaisesRegex(ValueError,"installed helper path"):H.driver_properties(bad,0,m)
 def test63_actual_origin_keeps_bytes_SHA_rank_dependency_guards(self):
  proof=self.actual("CANARY_N1.json")["canary"][0]["actual_driver_properties"];m=self.actual_mf()
  for key,value in(("bytes",True),("bytes",2091),("sha256","f"*64)):
   bad=copy.deepcopy(proof);bad["helper_source"][key]=value
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,"installed helper path"):H.driver_properties(bad,0,m)
  with self.assertRaisesRegex(ValueError,"driver rank"):H.driver_properties(proof,1,m)
  bad=copy.deepcopy(m);bad["dependencies"]=[r for r in bad["dependencies"]if r!=bad["runtime_abi_original_refs"]["helper"]]
  with self.assertRaisesRegex(ValueError,"installed helper path"):H.driver_properties(proof,0,bad)
 def test64_actual_four_worker_files_exact_N1_recipe_namespace_identity(self):
  canary=self.actual("CANARY_N1.json");recipe=self.actual("RECIPE.json")
  namespace=self.actual("KIVI_ALL4_NAMESPACE_RAW.json");m=self.actual_mf()
  self.assertEqual(recipe["source_ref"],C.PRODUCER)
  for rank in range(4):
   row=self.actual("DRIVER-PROPERTIES-r%d.json"%rank)
   self.assertEqual(row["source_ref"],canary["source"]);self.assertEqual(row["recipe_ref"],self.FIXTURES["RECIPE.json"])
   self.assertEqual(row["identity"],namespace["host_processes"][rank+1]["guest_identity"])
   self.assertIn(recipe["container_id"],row["identity"]["cgroup"])
   proof={k:v for k,v in row.items()if k not in("source_ref","recipe_ref","identity")}
   self.assertEqual(proof,canary["canary"][rank]["actual_driver_properties"])
   self.assertEqual(H.driver_properties(proof,rank,m),proof["device_properties"])


class ActualNativeCompletionWire(Base):
 FIXTURES={"RECIPE.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/RECIPE.json","bytes":5012,"sha256":"9798f7557332382032756ad9001dfefea10292d088ab76533d504ba9fc614ed7"},"RAW_SSE.jsonl":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/RAW_SSE.jsonl","bytes":164844,"sha256":"f8564f69fc02f49450e753991fcbd86dc92efacc620bd4ee6926f8ae75d73128"},"CLIENT_RESULT.json":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/CLIENT_RESULT.json","bytes":2619,"sha256":"3c2429534f4911c5fad9cadafa65b99781554cf473eae88d045f1d777bb21fc4"}}
 def actual_bytes(self,name):
  r=self.FIXTURES[name];archive=os.environ.get("KIVI_SCREEN_DRIVER_ARCHIVE")
  p=Path(archive)/name if archive else Path(r["path"]);wire=p.read_bytes()
  self.assertEqual((len(wire),hashlib.sha256(wire).hexdigest()),(r["bytes"],r["sha256"]));return wire
 def feed(self,outputs):
  state=T.stream_state()(C.prompt(),outputs)
  for ordinal,line in enumerate(self.actual_bytes("RAW_SSE.jsonl").splitlines()):
   event=json.loads(line);self.assertEqual(set(event),{"raw_line"});raw=event["raw_line"]
   # Original018 has raw_line only, no arrival time. Ordinal is only an inert
   # parser input; this test cannot supply timing or1024 completion evidence.
   if raw.startswith("data: "):state.feed(raw[6:].strip().encode(),float(ordinal))
  return state
 def test65_actual0548_wire_original_completion_parser_and_client(self):
  state=self.feed(2);state.finish_check();client=H.decode(self.actual_bytes("CLIENT_RESULT.json"))
  recipe=H.decode(self.actual_bytes("RECIPE.json"))
  self.assertEqual(client["source_ref"],C.PRODUCER)
  self.assertEqual(client["recipe_ref"],self.FIXTURES["RECIPE.json"])
  self.assertEqual(client["raw_sse_ref"],self.FIXTURES["RAW_SSE.jsonl"])
  self.assertEqual(recipe["source_ref"],C.PRODUCER)
  self.assertEqual(state.server_id,client["actual_server_response_id"])
  self.assertEqual(state.tokens,client["completion_token_ids"]);self.assertEqual(len(state.tokens),2)
  self.assertEqual(state.usage,client["usage"]);self.assertTrue(state.done)
  self.assertFalse(client["model_ready"]);self.assertFalse(client["performance_ready"])
 def test66_actual_two_tokens_cannot_be1024_or_timing_evidence(self):
  state=self.feed(1024)
  with self.assertRaisesRegex(ValueError,"stream IDs/prompt/length/DONE"):state.finish_check()
  rows=[json.loads(line)for line in self.actual_bytes("RAW_SSE.jsonl").splitlines()]
  self.assertTrue(all(set(row)=={"raw_line"}for row in rows))
  first=json.loads(rows[0]["raw_line"][6:]);first["choices"][0]["prompt_token_ids"][0]+=1
  with self.assertRaisesRegex(ValueError,"prompt changed"):
   T.stream_state()(C.prompt(),2).feed(C.canonical(first),0.0)

if __name__=="__main__":unittest.main(verbosity=2)
