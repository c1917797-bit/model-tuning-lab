"""Off-device source-body/publication tests, NOT Torch/model/native-runtime proof."""
import ast,copy,hashlib,importlib.util,io,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import screen_contract as C
import boundary_journal as J
import transport as T
import entry as E
import screen_predecessor as PRE
import worker as W
BASE=Path(os.environ.get("KIVI_SCREEN_PRODUCER_ARCHIVE",
 "C:/Users/Huawei/AppData/Local/Temp/kivi-firstdecode-hbm-budget-v018-20261010/bootstrap"))
SHARED=Path(os.environ.get("KIVI_SCREEN_REVIEWED_DEPS",
 "C:/Users/Huawei/AppData/Local/Packages/sandbox.{48fdcea7-5947-498c-a068-4bc4cdaddb04}/AC/Temp/kivi-c132-reviewed-source/model-deps"))
def source_module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
 sys.modules[name]=m;spec.loader.exec_module(m);return m
def exact(path,digest):
 if os.name!="nt" and not path.is_file():
  mf=json.loads((BASE/"SOURCE_MANIFEST.json").read_bytes())
  path=Path(next(r["path"]for r in mf["files"]+mf["dependencies"]if r["sha256"]==digest))
 wire=path.read_bytes()
 if hashlib.sha256(wire).hexdigest()!=digest:raise ValueError("exact reviewed source")
 return wire
class Temp(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
class Contract(Temp):
 def test01_common_identical_except_explicit_arm(self):
  p=E.plan(self.root/"new",8250,"a")
  self.assertEqual(p["stages"][0]["native_argv"],p["stages"][1]["native_argv"])
  self.assertTrue(p["execution_available"]);self.assertFalse(p["C16_verified"])
  self.assertEqual(C.COMMON["max_num_seqs"],1);self.assertEqual(C.COMMON["kv_cache_memory_bytes"],6*1024**3)
  self.assertEqual(C.BUDGET["hbm_reserve_mib"],3072);self.assertEqual(C.BUDGET["cutoff_epoch"],1791788425)
  self.assertNotEqual(p["stages"][0]["output"],p["stages"][1]["output"])
 def test02_prompt_matches_actual018_formula_and_full_length(self):
  recipe=(BASE/"input_recipe.py").read_text()
  tree=ast.parse(recipe)
  found=[n for n in ast.walk(tree)if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name)and x.id=="prompt"for x in n.targets)]
  self.assertEqual(len(found),1)
  actual=eval(compile(ast.Expression(found[0].value),str(BASE/"input_recipe.py"),"eval"),{})
  self.assertEqual(C.prompt(),actual);self.assertEqual(len(actual),32768)
 def test03_exact_fixed1024_and_full_prefill_warmups(self):
  rows=C.rows("scope")
  self.assertEqual([r["outputs"]for r in rows],[2,2,129])
  for row in rows:
   p=C.payload(C.prompt(),row["outputs"])
   self.assertEqual(p["min_tokens"],p["max_tokens"]);self.assertTrue(p["ignore_eos"])
   self.assertNotIn("request_id",p);self.assertNotIn("messages",p)
 def test04_mismatched_common_or_reused_output_rejects(self):
  a=C.native_argv(8250,"Worker");b=list(a);b[b.index("--max-num-seqs")+1]="16"
  with self.assertRaises(ValueError):C.matched_argv(a,b)
  with self.assertRaises(ValueError):E.plan(self.root,8250,"a")
 def test05_default_OFF_imports_no_framework(self):
  before=set(sys.modules)
  with patch("sys.stdout",new=io.StringIO())as out:self.assertEqual(E.main([]),0)
  self.assertFalse(json.loads(out.getvalue())["enabled"])
  self.assertFalse(set(sys.modules)-before & {"torch","torch_npu","triton"})
 def test06_execute_missing_prerequisite_has_no_device_path(self):
  with self.assertRaisesRegex(ValueError,"actual018"):
   E.main(["--execute","--output",str(self.root/"new")])
  self.assertFalse((self.root/"new").exists())
 def test07_full_E2E_not_decode_only_or_singlepair_acceptance(self):
  row=dict(completion_tokens=129,done=True,finish_reason="length",submitted=1,first=11,last=21,response_end=23)
  m=C.metrics(row);self.assertEqual(m["wall_seconds"],22)
  self.assertEqual(m["mean_ttft_seconds"],10);self.assertEqual(m["mean_tpot_seconds"],10/128)
  p=C.pair(m,dict(m,output_tokens_per_second=m["output_tokens_per_second"]*1.11))
  self.assertFalse(p["screen_pass"]);self.assertFalse(p["performance_accepted"])
 def test08_predecessor_missing_originals_rejects_before_loading(self):
  with patch.object(PRE,"module",side_effect=AssertionError("must not load")):
   with self.assertRaisesRegex(ValueError,"complete actual"):PRE.replay({})
class Wire(Temp):
 def lines(self,plan,*,count=None,usage=True,done=True,wrong_id=False):
  count=plan["outputs"]if count is None else count
  sid="cmpl-"+plan["header_id"]+("-wrong"if wrong_id else"")
  rows=[dict(id=sid,choices=[dict(index=0,prompt_token_ids=C.prompt(),token_ids=[])])]
  rows += [dict(id=sid,choices=[dict(index=0,token_ids=[(i+5)%32768])])for i in range(count)]
  rows += [dict(id=sid,choices=[dict(index=0,token_ids=[],finish_reason="length")])]
  if usage:rows.append(dict(id=sid,choices=[],usage=dict(prompt_tokens=32768,completion_tokens=count,total_tokens=32768+count)))
  raw=[b"data: "+C.canonical(r)+b"\n"for r in rows]
  if done:raw.append(b"data: [DONE]\n")
  return raw
 def request(self,plan,**kw):
  lines=self.lines(plan,**kw);requests=[]
  class Response:
   status=200
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def __iter__(self):return iter(lines)
  def urlopen(request,timeout):
   requests.append(request);self.assertEqual(timeout,4800);return Response()
  with patch.object(T,"urlopen",side_effect=urlopen):
   reference=T.request(self.root,8250,plan)
  return C.read(reference),requests
 def test09_original_parser_source_exact(self):
  self.assertEqual(hashlib.sha256((Path(T.__file__).parent/"bench_original.py").read_bytes()).hexdigest(),T.BENCH_SHA)
  self.assertEqual(T.stream_state().__name__,"StreamState")
 def test10_whole1024_real_wire_publication_and_independent_replay(self):
  plan=C.rows("scope")[-1];row,requests=self.request(plan)
  self.assertTrue(T.replay(row,plan,self.root)["wire_checked"])
  self.assertFalse(T.replay(row,plan,self.root)["native_finished_checked"])
  self.assertEqual(len(row["output_tokens"]),129);self.assertEqual(len(requests),1)
  payload=json.loads(requests[0].data);self.assertEqual(payload,C.payload(C.prompt(),129))
 def test11_short_output_rejected_not_token_chunk_count(self):
  plan=C.rows("scope")[-1];row,_=self.request(plan,count=128)
  self.assertFalse(row["ok"])
  with self.assertRaises(ValueError):T.replay(row,plan,self.root)
 def test12_missing_usage_rejects(self):
  plan=C.rows("scope")[0];row,_=self.request(plan,usage=False)
  self.assertFalse(row["ok"])
  with self.assertRaises(ValueError):T.replay(row,plan,self.root)
 def test13_wrong_actual_response_id_rejects(self):
  plan=C.rows("scope")[0];row,_=self.request(plan,wrong_id=True)
  self.assertFalse(row["ok"])
  with self.assertRaises(ValueError):T.replay(row,plan,self.root)
 def test14_truncated_wire_ref_rejects(self):
  plan=C.rows("scope")[0];row,_=self.request(plan)
  row["raw_sse"]["bytes"]-=1
  with self.assertRaisesRegex(ValueError,"whole raw"):T.replay(row,plan,self.root)
 def test15_changed_token_or_timestamp_rejects(self):
  plan=C.rows("scope")[0];row,_=self.request(plan);bad=copy.deepcopy(row);bad["output_tokens"][0]+=1
  with self.assertRaises(ValueError):T.replay(bad,plan,self.root)
  row["submitted"]=row["response_end"]+1
  with self.assertRaisesRegex(ValueError,"interval"):T.replay(row,plan,self.root)
 def test16_full_wire_no_silent_overwrite(self):
  plan=C.rows("scope")[0];self.request(plan)
  with self.assertRaises(FileExistsError):self.request(plan)
class Boundary(Temp):
 def setUp(self):
  super().setUp();self.ident=dict(pid=101,start_ticks=202,cgroup="explicit-test-only")
  self.owner=T.publish(self.root/"owner.json",dict(fixture=True))
  self.event=T.publish(self.root/"event.json",dict(fixture=True))
  self.publish=lambda name,value:T.publish(self.root/(name+".json"),value)
  self.j=J.BoundaryJournal(self.publish,lambda:dict(self.ident),0,self.owner,self.event,["r"],C.read)
 def ingress(self):
  return self.j("INGRESS",dict(schema="kivi.actual-native-ingress/v1",rank=0,identity=self.ident,
   req_id="r",scheduled_type="SchedulerOutput/NewRequestData",prompt_token_ids=C.prompt()))
 def retire(self):
  return self.j("RETIRE",dict(schema="kivi.actual-packed-qwen-retire/v1",rank=0,identity=self.ident,
   request_id="r",slot=0,epoch=1,actual_native_finished=True))
 def final(self,**kw):
  x=dict(schema="kivi.actual-packed-qwen-installer-final/v1",rank=0,identity=self.ident,owner_ref=self.owner,
   event_ref=self.event,finished=["r"],diagnostic=False,timing_model_prerequisite_external=True,
   graph_checked=False,model_ready=False,run_authority=False);x.update(kw)
  return self.publish("INSTALLER-FINAL",x)
 def test17_boundary_full_actual_file_roundtrip(self):
  self.ingress();self.j("UPDATE",dict(schema="kivi.actual-packed-qwen-update/v1",rank=0,identity=self.ident,rows=(1,2)))
  self.retire();out=C.read(self.j.finish(self.final()))
  self.assertFalse(out["complete_per_token_journal"]);self.assertFalse(out["numeric_verified"])
  self.assertEqual(len(out["boundary_refs"]),3)
 def test18_no_HTTP_DONE_retirement_substitution(self):
  self.ingress()
  with self.assertRaisesRegex(ValueError,"Book.close"):self.j.finish(self.final())
 def test19_duplicate_retire_and_unknown_owner_reject(self):
  with self.assertRaises(ValueError):self.retire()
  self.ingress();self.retire()
  with self.assertRaises(ValueError):self.retire()
 def test20_timing_rejects_per_token_FRAME_OUTPUT_and_raw(self):
  for schema in ("kivi.actual-packed-qwen-frame/v1","kivi.actual-packed-qwen-output/v1","kivi.actual-packed-raw/v1"):
   with self.assertRaisesRegex(ValueError,"timing forbids"):self.j("NO",dict(schema=schema))
 def test21_failure_prevents_final_promotion(self):
  self.ingress();self.retire();self.j("FAIL",dict(schema="kivi.actual-packed-failed/v1"))
  with self.assertRaisesRegex(ValueError,"nonfailed"):self.j.finish(self.final())
 def test22_stale_identity_rejects(self):
  self.ident["pid"]+=1
  with self.assertRaisesRegex(ValueError,"live boundary"):self.ingress()
 def test23_source_actual_Book_sequential_slot_epochs_and_native_close(self):
  wire=exact(SHARED/"book.py","6488a5ca3fb6f606bbb82bf86e226fc30741e8dc7288ff03e3e5e8b71cec07c7")
  ns={};exec(compile(wire,str(SHARED/"book.py"),"exec"),ns)
  ids=[r["header_id"]for r in C.rows("scope")];book=ns["Book"](ids,{r:32768 for r in ids})
  layers=tuple("layer%d"%i for i in range(16));epochs=[];fepoch=0
  for rid,out in zip(ids,[2,2,129]):
   for computed,n in [(0,32768)]+[(32768+i,1)for i in range(out-1)]:
    fepoch+=1;frame=dict(epoch=fepoch,req_ids=[rid],scheduled_counts=[n],computed_tokens=[computed],
      query_start_loc=[0,n],positions=list(range(computed,computed+n)),total_tokens=n,req_id_to_index={rid:0})
    book.plan(frame)
    if computed==0:epochs.append((book.live[rid]["slot"],book.live[rid]["epoch"]))
    for name in layers:book.layer_done(rid,fepoch,name)
    book.complete(frame,layers)
   book.retire([rid],[],[],lambda *a:None)
  self.assertEqual(epochs,[(0,1),(0,2),(0,3)]);self.assertTrue(book.close())
 def test28_actual_installer_update_retire_to_native_finish_file_chain(self):
  self.ingress()
  wire=exact(SHARED/"book.py","6488a5ca3fb6f606bbb82bf86e226fc30741e8dc7288ff03e3e5e8b71cec07c7")
  ns={};exec(compile(wire,str(SHARED/"book.py"),"exec"),ns)
  book=ns["Book"](["r"],{"r":32768});layers=tuple("layer%d"%i for i in range(16))
  for epoch,computed,n in ((1,0,32768),(2,32768,1)):
   frame=dict(epoch=epoch,req_ids=["r"],scheduled_counts=[n],computed_tokens=[computed],
    query_start_loc=[0,n],positions=list(range(computed,computed+n)),total_tokens=n,req_id_to_index={"r":0})
   book.plan(frame)
   for name in layers:book.layer_done("r",epoch,name)
   book.complete(frame,layers)
  contexts={}
  for name in layers:
   req=types.SimpleNamespace(owner="r",epoch=1,length=32769,pending=False)
   arena=types.SimpleNamespace(active={0:req},owned=lambda r:None)
   arena.release=lambda r,a=arena:a.active.clear()
   contexts[name]=dict(arena=arena,packed_batch=types.SimpleNamespace(qualify_boundary=lambda:None))
  runner=types.SimpleNamespace(requests={"r":object()},input_batch=types.SimpleNamespace(num_reqs=1,req_ids=["r"]))
  def native(scheduler):
   runner.requests.clear();runner.input_batch.req_ids.clear();runner.input_batch.num_reqs=0
   return "actual-native-fixture-return"
  source=exact(BASE/"installer.py","4e3961a725db155b243ede704d44b104728a9af81bda400ba7e07bae0168aa81")
  install=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=="install")
  nodes=[n for n in install.body if isinstance(n,ast.FunctionDef)and n.name in ("update","release")]
  env=dict(need=C.need,state=dict(active=None,failed=False,scheduler_type=None,update_seq=0,metadata_proofs={}),
   diagnostic=False,timing_layout=lambda *a:(),initial_layout=(),event={},layer_contexts=contexts,
   callback=None,writer_guard=lambda *a:None,owner={"zeroer_writer_receipt_ref":self.event},
   identity=lambda:dict(self.ident),ident=self.ident,rank=0,book=book,layer_names=layers,capture_raw=False,
   ingress_bindings=types.SimpleNamespace(check_new=lambda *a:[]),orig_update=native,RUNNER_SHA="fixture-only",
   send=self.j,publish=self.j,original_prefills={})
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(BASE/"installer.py"),"exec"),env)
  runner._update_states=types.MethodType(env["update"],runner)
  finish=source_module(BASE/"finish_after_native.py","_screen_actual_native_finish")
  results=[]
  def close():
   self.assertTrue(book.close());return self.j.finish(self.final())
  final=finish.install(runner,close,["r"],
    "4e3961a725db155b243ede704d44b104728a9af81bda400ba7e07bae0168aa81",results.append)
  answer=runner._update_states(types.SimpleNamespace(finished_req_ids=["r"],scheduled_new_reqs=[]))
  self.assertEqual(answer,"actual-native-fixture-return")
  self.assertEqual(final(),results[0]);self.assertEqual(C.read(final())["finished"],["r"])
  self.assertTrue(all(not x["arena"].active for x in contexts.values()))
class SourceGuards(Temp):
 def test24_worker_default_OFF_does_not_read_any_source(self):
  flag="test-screen-off"
  with patch.dict(os.environ,{},clear=True):
   result=W.make_worker(object,None,None,None,None,None,None,None,None,layout_owner=None,layout_owner_ref=None,
    layout_mf=None,post_owner=None,post_owner_ref=None,installer=types.SimpleNamespace(FLAG=flag),spans=None,
    book=None,formal=None,producer=None,kernel=None,metadata=None,journal_module=None,source_refs=None,
    device_properties=None,qualify=None)
  self.assertIs(result,object)
 def test25_original_math_fences_and_scope_remain_source_pinned(self):
  source=exact(BASE/"producer.py","f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5").decode()
  self.assertIn("output=self.model(query,pool,self.metadata)",source)
  self.assertIn("t.npu.synchronize()",source);self.assertIn("self.metadata.assert_live()",source)
  self.assertIn('capture_raw is False and pre_refs is None',source)
  installer=exact(BASE/"installer.py","4e3961a725db155b243ede704d44b104728a9af81bda400ba7e07bae0168aa81").decode()
  self.assertIn("if diagnostic or boundary:send",installer)
  self.assertIn('if not diagnostic:return None',installer)
  self.assertIn("allocator_observer(torch,rank,send,diagnostic)",installer)
class ActualWorkerBridge(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  os.environ["KIVI_PROVIDER_LOCAL_ARCHIVE"]="1"if os.name=="nt"else"0"
  mf=json.loads((BASE/"SOURCE_MANIFEST.json").read_bytes())
  for name in ("test_provider_integration.py","test_provider.py","provider_projection.py"):
   reference=next(r for r in mf["files"]if Path(r["path"]).name==name)
   exact(BASE/name,reference["sha256"])
  cls.integration=source_module(BASE/"test_provider_integration.py","_screen_actual_integration")
 def invoke(self,diagnostic):
  integration=self.integration;qualified=[]
  original_factory=integration.W.make_worker
  def factory(*args,**kwargs):
   kwargs.update(diagnostic=diagnostic,model_qualify=(lambda:qualified.append(True))if not diagnostic else None)
   if not diagnostic:
    kwargs["source_refs"]=dict(kwargs["source_refs"],timing_journal=C.ref(J.__file__))
    kwargs["timing_journal_module"]=J
   return W.make_worker(*args,**kwargs)
  class Case(integration.ExplicitIntegration):
   def assertIs(inner,actual,expected,msg=None):
    # The inherited fixture asserts the diagnostic journal. New exact wrapper
    # intentionally uses the boundary journal; every other assertion is original.
    if expected is integration.J.JournalPublisher and not diagnostic:expected=J.BoundaryJournal
    return super().assertIs(actual,expected,msg)
  case=Case("test16_actual_worker_bridge_live_arenas_journal_and_installer_handoff")
  result=unittest.TestResult()
  with patch.object(integration.W,"make_worker",side_effect=factory):
   case.run(result)
  self.assertEqual(result.errors,[]);self.assertEqual(result.failures,[])
  self.assertEqual(len(qualified),0 if diagnostic else 1)
 def test26_real_original_provider_to_worker_diagnostic_bridge(self):self.invoke(True)
 def test27_real_original_provider_to_worker_timing_bridge(self):self.invoke(False)
if __name__=="__main__":unittest.main(verbosity=2)
