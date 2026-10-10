"""Local real-file/HTTP and exact source-body regressions. NOT model or NPU proof."""
import ast,copy,hashlib,io,json,sys,tempfile,threading,time,types,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import screen_contract as C,transport as T,screen_evidence as E
import boundary_journal as J,book as B,mixed as M
ROOT=Path(__file__).resolve().parent
class Local(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
 def emit(self,name,value):return T.publish(self.root/(name+".json"),value)
 def test01_protocol_is_original_fixed40_C16_not_resident7(self):
  rows=C.rows("unit")
  self.assertEqual(len(rows),42);self.assertEqual(C.PROTOCOL["requests"],40)
  self.assertEqual(C.PROTOCOL["concurrency"],16);self.assertEqual(C.COMMON["max_num_seqs"],16)
  self.assertEqual([r["outputs"]for r in rows],[2,2]+[1024]*40)
  self.assertEqual([r["prompt_index"]for r in rows],[0,1]+list(range(40)))
  self.assertEqual(C.COMMON["kv_cache_memory_bytes"],6*1024**3)
  self.assertEqual(C.BUDGET["hbm_reserve_mib"],3072);self.assertEqual(C.CUTOFF,1791788425)
 def test02_original_prompt_formula_and_common_dense_candidate_argv(self):
  for i in range(40):
   original=[1000+j%257 for j in range(16384)]+[2000+(i*131+j*17)%4093 for j in range(16384)]
   self.assertEqual(C.prompt(i),original)
  a=C.native_argv(8250,"own.Worker");self.assertTrue(C.matched_argv(a,list(a)))
  b=list(a);b[b.index("--max-num-seqs")+1]="7"
  with self.assertRaises(ValueError):C.matched_argv(a,b)
 def test03_actual_input_producer_to_client_all42_expression(self):
  # The real expressions on both sides, not a hand-rebuilt equal list.
  def candidates(name,key):
   tree=ast.parse((ROOT/name).read_bytes())
   return [n for n in ast.walk(tree)if isinstance(n,ast.ListComp)and
     any(isinstance(x,ast.keyword)and x.arg==key for x in ast.walk(n))]
  a=candidates("input_recipe.py","payload");b=candidates("client.py","payload")
  self.assertEqual(len(a),1);self.assertEqual(len(b),1)
  left=eval(compile(ast.Expression(a[0]),str(ROOT/"input_recipe.py"),"eval"),{"policy":C,"run_id":"u"})
  right=eval(compile(ast.Expression(b[0]),str(ROOT/"client.py"),"eval"),{"c":C,"rows":C.rows("u")})
  self.assertEqual(left,right);self.assertEqual(len(left),42)
  old=[dict(row,payload=C.payload(C.prompt(),row["outputs"]))for row in C.rows("u")]
  self.assertEqual(sum(x!=y for x,y in zip(left,old)),40)
 def test04_complete_E2E_metrics_include40_full_prefills(self):
  rows=[dict(completion_tokens=1024,done=True,finish_reason="length",
   submitted=i,first=i+10,last=i+20,response_end=i+22)for i in range(40)]
  m=C.metrics(rows);self.assertEqual(m["wall_seconds"],61)
  self.assertEqual(m["output_tokens_per_second"],40960/61)
  self.assertEqual(m["mean_ttft_seconds"],10)
  with self.assertRaises(ValueError):C.metrics(rows[:39])
  rows[17]["completion_tokens"]=1023
  with self.assertRaises(ValueError):C.metrics(rows)
 def test05_actual_SSE_parser_pinned_and_token_count_not_chunks(self):
  self.assertEqual(hashlib.sha256((ROOT/"bench_original.py").read_bytes()).hexdigest(),T.BENCH_SHA)
  state=T.stream_state()(C.prompt(5),1024)
  state.feed(C.canonical(dict(id="test",choices=[dict(index=0,prompt_token_ids=C.prompt(5),
   token_ids=list(range(1024)),finish_reason="length")],usage=dict(
   prompt_tokens=32768,completion_tokens=1024,total_tokens=33792))),1)
  state.feed(b"[DONE]",2);state.finish_check()
  self.assertEqual(len(state.tokens),1024)
 def test06_real_loopback_HTTP16_all42_files_and_independent_replay(self):
  # Real HTTP transport, real original parser, immutable raw files. Synthetic server
  # values are explicit fixtures, NOT checkpoint output or native finished proof.
  lock=threading.Lock();barrier=threading.Barrier(16);state=dict(active=0,maximum=0,complete=0)
  class Handler(BaseHTTPRequestHandler):
   protocol_version="HTTP/1.1"
   def log_message(self,*args):pass
   def do_POST(self):
    body=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
    rid=self.headers["X-Request-Id"];measured="-request"in rid
    with lock:
     state["active"]+=1;state["maximum"]=max(state["maximum"],state["active"])
    if measured and int(rid[-2:])<16:barrier.wait(timeout=15)
    n=body["max_tokens"];prompt=body["prompt"]
    wire=b"data: "+C.canonical(dict(id="cmpl-"+rid,choices=[dict(index=0,prompt_token_ids=prompt,
     token_ids=list(range(n)),finish_reason="length")],
     usage=dict(prompt_tokens=len(prompt),completion_tokens=n,total_tokens=len(prompt)+n)))+b"\n\n"
    wire+=b"data: [DONE]\n\n"
    self.send_response(200);self.send_header("Content-Type","text/event-stream")
    self.send_header("Content-Length",str(len(wire)));self.end_headers();self.wfile.write(wire);self.wfile.flush()
    with lock:
     state["active"]-=1
     if measured:state["complete"]+=1
  class Server(ThreadingHTTPServer):
   request_queue_size=32
   daemon_threads=True
  server=Server(("127.0.0.1",0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
  retire_calls=[]
  def retired(plan,response):
   if plan["measured"]:
    with lock:self.assertEqual(state["complete"],40,"no per-request native barrier serializes timed cohort")
   retire_calls.append(plan["name"])
   return [self.emit(plan["name"]+"-fixture-r%d"%i,dict(fixture_only=True,not_native_proof=True))for i in range(4)]
  rr=T.run(self.root/"http",server.server_port,"wire",retired);report=C.read(rr)
  self.assertEqual(state["maximum"],16);self.assertEqual(state["complete"],40)
  self.assertEqual(retire_calls,[r["name"]for r in C.rows("wire")])
  self.assertEqual(len(report["rows"]),42)
  for row in report["rows"]:self.assertTrue(T.replay(C.read(row["response"]),row["plan"],self.root/"http")["wire_checked"])
  damaged=C.read(report["rows"][3]["response"]);damaged["raw_sse"]["bytes"]-=1
  with self.assertRaises(ValueError):T.replay(damaged,report["rows"][3]["plan"],self.root/"http")
 def frame(self,epoch,rows):
  ids=[x[0]for x in rows];cs=[x[1]for x in rows];ns=[x[2]for x in rows];starts=[0]
  for n in ns:starts.append(starts[-1]+n)
  return dict(epoch=epoch,req_ids=ids,scheduled_counts=ns,computed_tokens=cs,query_start_loc=starts,
   positions=[p for _,c,n in rows for p in range(c,c+n)],total_tokens=starts[-1],
   req_id_to_index={r:i for i,r in enumerate(ids)})
 def complete(self,book,frame):
  frame["kind"]=book.plan(frame);plan=M.partition(frame,book.prompts,B.frame_valid)
  for rid in frame["req_ids"]:
   for i in range(16):book.layer_done(rid,frame["epoch"],"FA%d"%i)
  book.complete(frame,tuple("FA%d"%i for i in range(16)))
  return plan
 def test07_actual_Book_mixed_join_and_native_slot_reuse42(self):
  ids=["r%02d"%i for i in range(42)];book=B.Book(ids,{r:32768 for r in ids})
  epoch=0;used=[];mixed=0
  # Inert schedule: seven current owners, staggered ingress produces genuine mixed
  # partition and all16 commits. Not a scheduler/model execution claim.
  for start in range(0,42,7):
   cohort=ids[start:start+7]
   for j,rid in enumerate(cohort):
    epoch+=1;rows=[(old,book.live[old]["length"],1)for old in cohort[:j]]+[(rid,0,32768)]
    plan=self.complete(book,self.frame(epoch,rows));mixed+=plan["kind"]=="mixed"
    used.append((rid,book.live[rid]["slot"],book.live[rid]["epoch"]))
   for rid in reversed(cohort):
    book.retire([rid],[r for r in book.live if r!=rid],[r for r in book.live if r!=rid],lambda *a:None)
  self.assertTrue(book.close());self.assertEqual(len(used),42);self.assertEqual(mixed,36)
  self.assertEqual({s for _,s,_ in used},set(range(7)));self.assertEqual(max(e for _,_,e in used),6)
 def test08_actual_Book_preemption_rewind_is_not_finish(self):
  book=B.Book(["r"],{"r":32768});self.complete(book,self.frame(1,[("r",0,32768)]))
  with self.assertRaisesRegex(ValueError,"sequential"):self.complete(book,self.frame(2,[("r",0,32768)]))
  with self.assertRaises(ValueError):book.retire(["r"],["r"],[],lambda *a:None)
  with self.assertRaises(ValueError):book.close()
 def test09_actual_update_release_finish_journal_file_chain42(self):
  import finish_after_native as F
  ids=["r%02d"%i for i in range(42)];ident=dict(pid=101,start_ticks=202,cgroup="fixture-only")
  owner=self.emit("owner",dict(fixture_only=True));event=self.emit("event",dict(fixture_only=True))
  journal=J.BoundaryJournal(self.emit,lambda:dict(ident),0,owner,event,ids,C.read)
  book=B.Book(ids,{r:32768 for r in ids});layers=tuple("FA%d"%i for i in range(16))
  contexts={};runner=types.SimpleNamespace(requests={},input_batch=types.SimpleNamespace(num_reqs=0,req_ids=[]))
  for layer in layers:
   arena=types.SimpleNamespace(active={},owned=lambda r:None)
   arena.release=lambda r,a=arena:a.active.pop(r.slot)
   contexts[layer]=dict(arena=arena,packed_batch=types.SimpleNamespace(qualify_boundary=lambda:None))
  sentinel=lambda:"native deferred fixture"
  def native(scheduler):
   for rid in scheduler.finished_req_ids:runner.requests.pop(rid)
   runner.input_batch.req_ids=list(runner.requests);runner.input_batch.num_reqs=len(runner.requests)
   return sentinel
  source=(ROOT/"installer.py").read_bytes()
  install=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=="install")
  nodes=[n for n in install.body if isinstance(n,ast.FunctionDef)and n.name in("update","release")]
  env=dict(need=C.need,state=dict(active=None,failed=False,scheduler_type=None,update_seq=0,metadata_proofs={}),
   diagnostic=False,timing_layout=lambda *a:(),initial_layout=(),event={},layer_contexts=contexts,
   callback=None,writer_guard=lambda *a:None,owner={"zeroer_writer_receipt_ref":event},
   identity=lambda:dict(ident),ident=ident,rank=0,book=book,layer_names=layers,capture_raw=False,
   ingress_bindings=types.SimpleNamespace(check_new=lambda *a:[]),orig_update=native,RUNNER_SHA="fixture-only",
   send=journal,publish=journal,original_prefills={},stage_observer=None)
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(ROOT/"installer.py"),"exec"),env)
  runner._update_states=types.MethodType(env["update"],runner);finals=[]
  def close():
   book.close()
   final=self.emit("actual-final",dict(schema="kivi.actual-packed-qwen-installer-final/v1",
    rank=0,identity=ident,owner_ref=owner,event_ref=event,finished=sorted(book.finished),
    diagnostic=False,timing_model_prerequisite_external=True,graph_checked=False,model_ready=False,run_authority=False))
   return journal.finish(final)
  finish=F.install(runner,close,ids,hashlib.sha256(source).hexdigest(),finals.append)
  for index,rid in enumerate(ids):
   journal("ingress-"+rid,dict(schema="kivi.actual-native-ingress/v1",rank=0,identity=ident,req_id=rid,
    scheduled_type="SchedulerOutput/NewRequestData",prompt_token_ids=C.prompt(index%40)))
   self.complete(book,self.frame(index+1,[(rid,0,32768)]))
   x=book.live[rid]
   for ctx in contexts.values():ctx["arena"].active[x["slot"]]=types.SimpleNamespace(
    slot=x["slot"],owner=rid,epoch=x["epoch"],length=32768,pending=False)
   runner.requests[rid]=object();runner.input_batch.req_ids=[rid];runner.input_batch.num_reqs=1
   returned=runner._update_states(types.SimpleNamespace(finished_req_ids=[rid],scheduled_new_reqs=[]))
   self.assertIs(returned,sentinel)
  final=C.read(finish());self.assertEqual(final["finished"],ids);self.assertEqual(len(finals),1)
  self.assertFalse(final["numeric_verified"]);self.assertTrue(all(not c["arena"].active for c in contexts.values()))
  self.assertEqual(len(final["boundary_refs"]),126)
 def test10_boundary_journal_forbids_per_token_publications(self):
  j=J.BoundaryJournal(self.emit,lambda:{"pid":1},0,{}, {},["r"],C.read)
  for schema in("kivi.actual-packed-qwen-frame/v1","kivi.actual-packed-qwen-output/v1","PACKED-RAW"):
   with self.assertRaises(ValueError):j("unexpected",dict(schema=schema))
 def test11_original_mixed_math_and_critical_bytes_unchanged(self):
  for name,sha in {
   "book.py":"c0882fa2868fa0b7e784bd031da3053d75a210362f4c955a5c93a0158fc63fa9",
   "mixed.py":"8e55b113337e8881b96634cc7ef2304b46374b1f39fe048d682ddf0b2ad16ce6",
   "installer.py":"536131653087de8f2daab16a65c3d5ce863e4ff7d74a8cf0eabb03aec620cedc",
   "producer.py":"f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5",
   "prebind.py":"fb98cb828319eed75de3d7be0bfe82c04404d9f91eb355431dc23dd6492a94bf"}.items():
   self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha,name)
  producer=(ROOT/"producer.py").read_text()
  self.assertIn("t.npu.synchronize()",producer);self.assertIn("self.metadata.assert_live()",producer)
 def test12_actual_factory_passes_source_qualified_mixed_and_timing_parameters(self):
  source=ast.parse((ROOT/"kivi_firstdecode_bootstrap.py").read_bytes())
  calls=[n for n in ast.walk(source)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
   and n.func.attr=="make_worker"]
  worker=[n for n in calls if any(k.arg=="mixed_module"for k in n.keywords)]
  self.assertEqual(len(worker),1);kwargs={k.arg:k.value for k in worker[0].keywords}
  self.assertEqual(ast.literal_eval(kwargs["diagnostic"]),False)
  self.assertEqual(ast.literal_eval(kwargs["capture_raw"]),False)
  self.assertEqual(ast.unparse(kwargs["mixed_module"]),"new['mixed']")
  source=ast.parse((ROOT/"worker.py").read_bytes())
  call=next(n for n in ast.walk(source)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
   and n.func.attr=="install"and isinstance(n.func.value,ast.Name)and n.func.value.id=="installer")
  self.assertEqual(ast.unparse(next(k.value for k in call.keywords if k.arg=="mixed_module")),"mixed_module")
 def test13_exact_parser_scalar_policy16_40960_and_no_HAL(self):
  import config_cpu as P,server_entry as S
  argv=S.native_argv(8250,6*1024**3)
  self.assertEqual(argv[argv.index("--max-num-seqs")+1],"16")
  self.assertEqual(argv[argv.index("--max-num-batched-tokens")+1],"40960")
  args=types.SimpleNamespace(model="/models/Qwen3.6-27B",max_model_len=33792,enforce_eager=True,
   enable_prefix_caching=False,mamba_cache_mode="none",max_num_batched_tokens=40960,max_num_seqs=16,
   enable_chunked_prefill=True,async_scheduling=False)
  scheduler=types.SimpleNamespace(**vars(args),long_prefill_token_threshold=0,max_num_partial_prefills=1,
   max_long_partial_prefills=1,max_num_scheduled_tokens=None,scheduler_reserve_full_isl=True)
  value=P.require_cpu_policy(args,scheduler,6*1024**3);self.assertEqual(value["max_num_seqs"],16)
  scheduler.scheduler_reserve_full_isl=False
  with self.assertRaises(ValueError):P.require_cpu_policy(args,scheduler,6*1024**3)
  self.assertFalse(any(x in sys.modules for x in("torch","torch_npu","triton","vllm")))
 def test15_N1_resolves_allocator_API_without_mutating_mixed_installer(self):
  import installer,runtime_boundary
  self.assertFalse(hasattr(installer,"allocator_observer"))
  self.assertTrue(callable(runtime_boundary.allocator_observer))
  tree=ast.parse((ROOT/"guest_probe.py").read_bytes())
  calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
   and n.func.attr=="allocator_observer"]
  self.assertEqual(len(calls),1);self.assertEqual(ast.unparse(calls[0].func),"boundary.allocator_observer")
  self.assertEqual(ast.unparse(next(k.value for k in calls[0].keywords if k.arg=="pin")),
   "new['installer'].callable_pin")
  observed=[]
  def forbidden(*a,**k):raise AssertionError("OFF must not read device/source/counters")
  self.assertIsNone(runtime_boundary.allocator_observer(None,None,forbidden,False,pin=forbidden)("OFF"))
  self.assertEqual(runtime_boundary.MEMORY_SHA,
   "b489a7dc22b77d5f50b3329801fe64cb4c7f908cf2abaea75c0efbd7f4c436c1")
 def test16_actual_frontend_Bindings_class_exact_pin(self):
  import importlib.util,ownership as O,loader as L
  path=ROOT/"bindings.py";name="_c16_actual_frontend_bindings"
  self.assertNotIn(name,sys.modules)
  value=L.module(name,L.ref(path));self.addCleanup(sys.modules.pop,name,None)
  self.assertEqual(O.BINDINGS_SHA,"a72c8ea47f6f04f661a9b8e6c159e02eb7f743aa3fe94a27c212e7a6cd7e8761")
  O.pin(value.Bindings,O.BINDINGS_SHA)
  with self.assertRaisesRegex(ValueError,"exact original callable whole SHA"):
   O.pin(value.Bindings,"71b5c3650eab308b86a26da62abcd249c77fc7528c4c8022bf779af56ef38f99")
 def test17_actual_server_to_frontend_pin_statement_and_consumer_identity(self):
  import ownership as O,loader as L,screen_whole as W
  mf=json.loads((ROOT/"SOURCE_MANIFEST.json").read_bytes())
  self.assertEqual(mf["runtime_roles"]["bindings"]["sha256"],O.BINDINGS_SHA)
  self.assertEqual(W.MODEL_OBSERVATION_PINS["ownership.py"],
   hashlib.sha256((ROOT/"ownership.py").read_bytes()).hexdigest())
  tree=ast.parse((ROOT/"server_entry.py").read_bytes())
  call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and
   isinstance(n.func,ast.Attribute)and n.func.attr=="install_frontend")
  self.assertEqual(ast.unparse(call.args[3]),"new['bindings']")
  name="_c16_actual_frontend_bindings_statement"
  value=L.module(name,L.ref(ROOT/"bindings.py"));self.addCleanup(sys.modules.pop,name,None)
  fn=next(n for n in ast.parse((ROOT/"ownership.py").read_bytes()).body
   if isinstance(n,ast.FunctionDef)and n.name=="install_frontend")
  statement=next(n for n in fn.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)
   and any(isinstance(v,ast.Attribute)and v.attr=="Bindings"for v in ast.walk(n)))
  # Execute the exact production statement with the actual source-loaded class.
  env=dict(pin=O.pin,bindings_module=value,BINDINGS_SHA=O.BINDINGS_SHA)
  exec(compile(ast.Module(body=[statement],type_ignores=[]),str(ROOT/"ownership.py"),"exec"),env)
  env["BINDINGS_SHA"]="71b5c3650eab308b86a26da62abcd249c77fc7528c4c8022bf779af56ef38f99"
  with self.assertRaisesRegex(ValueError,"exact original callable whole SHA"):
   exec(compile(ast.Module(body=[statement],type_ignores=[]),str(ROOT/"ownership.py"),"exec"),env)
 def test14_mixed_numeric_prerequisite_missing_cannot_be_B1_PASS(self):
  import mixed_gate
  with self.assertRaises((KeyError,ValueError)):mixed_gate.replay({},{"runtime_roles":{}})
  with self.assertRaises((KeyError,ValueError)):mixed_gate.check(
   {"status":"FIRSTDECODE_OWNED_RAW_AND_WHOLE_CONSUMED"}, {})
if __name__=="__main__":
 if sys.argv[1:]!=["--execute"]:print(json.dumps(dict(enabled=False,NPU=False)))
 else:
  result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Local))
  print(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
   real_loopback_HTTP=True,actual_framework=False,actual_model=False,NPU=False,run_authority=False)))
  raise SystemExit(not result.wasSuccessful())
