"""Real stdlib contracts and independent paper arithmetic, not NPU evidence."""
import ast,copy,hashlib,json,math,sys,tempfile,unittest
from pathlib import Path
from sparq_token_v4.core import MeanBook
from sparq_token_v4.oracle import reference
class Mean(unittest.TestCase):
    def test_native_lease_and_paused_requests(self):
        b=MeanBook();b.begin("a",1,7,2);b.begin("paused",4,2,3);b.append("a",1,7,2)
        self.assertEqual(b.native_live(["paused","a"])["paused"],(4,2,3))
        with self.assertRaises(ValueError):b.native_live(["a"])
    def test_duplicate_append_is_rejected(self):
        b=MeanBook();b.begin("a",1,7,2);b.append("a",1,7,2)
        with self.assertRaises(ValueError):b.append("a",1,7,2)
    def test_finished_slot_aba(self):
        b=MeanBook();b.begin("a",1,7,2);self.assertEqual(b.finish("a",1),7);b.begin("b",2,7,1)
        with self.assertRaises(ValueError):b.append("a",1,7,1)
        with self.assertRaises(ValueError):b.append("b",1,7,1)
    def test_slot_alias_or_bool_rejected(self):
        b=MeanBook();b.begin("a",1,2,1)
        for slot in (True,2,16,-1):
            with self.subTest(slot=slot),self.assertRaises(ValueError):b.begin("b",2,slot,1)
class Equation(unittest.TestCase):
    def fixture(self):return [[1.,-2.,.2],[.3,1.,-3.]],[[0.,1.,2.],[2.,0.,1.],[-1.,2.,0.]],[[1.,2.,3.],[-1.,.5,2.],[2.,-2.,.1]]
    def test_full_support_is_exact_and_mean_toggle_not_invented_gain(self):
        q,k,v=self.fixture()
        a=reference(q,k,v,3,3,reallocation=False);b=reference(q,k,v,3,3,reallocation=True)
        for ya,yb in zip(a["output"],b["output"]):
            for x,y in zip(ya,yb):self.assertAlmostEqual(x,y)
        for alpha in a["alpha"]:self.assertAlmostEqual(alpha,1.)
    def test_local_forced_and_token_not_page(self):
        q,k,v=self.fixture();a=reference(q,k,v,1,2,local=1)
        self.assertEqual(len(a["support"]),2);self.assertIn(2,a["support"])
        self.assertEqual(a["channels"],[2])
    def test_gqa_common_support_and_head_specific_mass(self):
        q,k,v=self.fixture();a=reference(q,k,v,2,1,local=1)
        self.assertEqual(a["support"],[2]);self.assertNotAlmostEqual(a["alpha"][0],a["alpha"][1])
    def test_zero_query_defined_stable_tie_adaptation(self):
        _,k,v=self.fixture();a=reference([[0.,0.,0.]],k,v,1,2,local=1)
        self.assertEqual(a["support"],[0,2]);self.assertAlmostEqual(a["alpha"][0],2/3)
    def test_mean_correction_scalar_identity(self):
        q,k,v=self.fixture();a=reference(q,k,v,2,2,reallocation=False);b=reference(q,k,v,2,2,reallocation=True)
        for h in range(2):
            for j in range(3):self.assertAlmostEqual(b["output"][h][j],a["alpha"][h]*a["output"][h][j]+(1-a["alpha"][h])*a["mean"][j])
class Source(unittest.TestCase):
    def test_graph_path_has_no_known_host_tensor_copy(self):
        from pathlib import Path
        sources=globals().get("_PREP_IN_MEMORY_SOURCES",{})
        source=sources.get("sparq_token_v4/core.py")
        if source is None:source=(Path(__file__).parent/"sparq_token_v4/core.py").read_text()
        tree=ast.parse(source);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="GraphTokenWorkspace")
        fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="run")
        forbidden=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                   and n.func.attr in ("tensor","arange") and isinstance(n.func.value,ast.Name) and n.func.value.id=="torch"]
        self.assertEqual(forbidden,[])
    def test_native_writer_source_pin_is_actual(self):
        import hashlib
        from pathlib import Path
        p=Path("/cache/cch/qwen36-adakv-prep-20261007/immutable-source-660/device_op.py");raw=p.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),"de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47")
        tree=ast.parse(raw);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="BaseDeviceAdaptor")
        fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="reshape_and_cache")
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
                         n.func.attr=="_npu_reshape_and_cache" for n in ast.walk(fn)),1)
from unittest import mock
import receipt,numeric_gate,consume_numeric
class Receipts(unittest.TestCase):
    def refs(self):
        return {"path":"/source/SOURCE_MANIFEST.json","sha256":"1"*64},{"numeric_gate.py":"2"*64},{"path":"/cache/cch/proof.json","sha256":"3"*64}
    def record(self):
        s,f,p=self.refs();argv=receipt.image_argv(Path("/source"),Path("/sparq-results/gate"),p,s)
        command=receipt.docker_argv("6"*64,argv);rr={"path":"/sparq-results/gate/REPORT.json","sha256":"4"*64}
        r={"command":command[0],"args":command[1:],"stdout":"MAIN_SPARQ_TOKEN_V5_REPORT "+json.dumps({"report":rr,"status":"passed","source_manifest":s,"script_sha256":f["numeric_gate.py"],"device_proof":p})}
        return r,command,rr,s,f,p
    def test_full_cli_marker_pure_contract_not_NPU_PASS(self):
        r,cmd,rr,s,f,p=self.record();m=receipt.check_terminal(r,cmd,rr,s,f,p)
        self.assertEqual(m["report"],rr);self.assertNotIn("torch",sys.modules)
    def test_same_flag_substring_different_actual_cli_rejected(self):
        for mutation in (lambda r:r["args"].append("--other"),lambda r:r["args"].__setitem__(1,"5"*64),
          lambda r:r["args"].__setitem__(r["args"].index("160"),"16"),lambda r:r["args"].__setitem__(r["args"].index("/sparq-results/gate"),"/sparq-results/old")):
            r,cmd,rr,s,f,p=self.record();mutation(r)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):receipt.check_terminal(r,cmd,rr,s,f,p)
    def test_report_hash_marker_source_proof_changes_fail_closed(self):
        for k,value in (("report",{"path":"/sparq-results/gate/REPORT.json","sha256":"0"*64}),("status","failed"),
          ("source_manifest",{"path":"/other","sha256":"0"*64}),("device_proof",{"path":"/other","sha256":"0"*64}),("script_sha256","0"*64)):
            r,cmd,rr,s,f,p=self.record();m=receipt.marker(r["stdout"]);m[k]=value;r["stdout"]="MAIN_SPARQ_TOKEN_V5_REPORT "+json.dumps(m)
            with self.subTest(k=k),self.assertRaises(ValueError):receipt.check_terminal(r,cmd,rr,s,f,p)
    def test_missing_duplicate_marker_rejected(self):
        for text in ("","MAIN_SPARQ_TOKEN_V5_REPORT {}\nMAIN_SPARQ_TOKEN_V5_REPORT {}"):
            with self.subTest(text=text),self.assertRaises(ValueError):receipt.marker(text)
    def test_twelve_source_count_graph3_scope(self):
        self.assertEqual(len(receipt.OWN),23);self.assertEqual(receipt.MODES,(("eager",0),("graph",0),("graph",1),("graph",2)))
        self.assertEqual(16*4*2*160,20480)
    def test_original_typed_terminal_failures_actual_file_ref(self):
        for key,value in (("exitCode",1),("timedOut",True),("cancelled",True),("state","running")):
            r,cmd,rr,s,f,p=self.record();record={**r,"state":"completed","exitCode":0,"timedOut":False,"cancelled":False,"error":None};record[key]=value
            envelope={"ok":True,"routeDecision":"peer_direct","targetPeerId":"fixture-only","operationId":"software-fixture",
              "result":{"state":"completed","record":record}}
            with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
                path=Path(td)/"terminal.json";ref=receipt.write_new(path,envelope)
                with self.subTest(key=key),self.assertRaises(ValueError):consume_numeric.terminal(path,ref["sha256"],"fixture-only","6"*64,cmd,rr,s,f,p)
    def test_wrong_peer_and_original_marker_missing_not_pass(self):
        r,cmd,rr,s,f,p=self.record();record={**r,"state":"completed","exitCode":0,"timedOut":False,"cancelled":False,"error":None}
        envelope={"ok":True,"routeDecision":"peer_direct","targetPeerId":"fixture-only","operationId":"software-fixture","result":{"state":"completed","record":record}}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
            path=Path(td)/"terminal.json";ref=receipt.write_new(path,envelope)
            with self.assertRaises(ValueError):consume_numeric.terminal(path,ref["sha256"],"wrong","6"*64,cmd,rr,s,f,p)
    def test_default_cli_no_torch(self):
        import contextlib,io
        with mock.patch.object(sys,"argv",["numeric_gate.py"]),contextlib.redirect_stdout(io.StringIO()) as out:
            numeric_gate.main()
        self.assertFalse(json.loads(out.getvalue())["ready"]);self.assertNotIn("torch",sys.modules)
    def test_cpu_double_oracle_not_native_candidate(self):
        source=(Path(__file__).parent/"numeric_gate.py").read_text();tree=ast.parse(source)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="golden")
        text=ast.get_source_segment(source,fn);self.assertIn("detach().cpu().double()",text);self.assertNotIn("workspace.run",text)
        self.assertNotIn("._npu_",text)
    def test_every_static_topology_and_guards_in_source(self):
        source=(Path(__file__).parent/"sparq_token_v4/core.py").read_text()
        for name in ("rows","lengths","logical","logical_page","offset","batch_index","pa_table","budget_tensor","key","value","output","corrected"):
            self.assertIn("self."+name+"=alloc(",source)
        self.assertIn("self.bytes=sum(g.bytes()",source)
        numeric=(Path(__file__).parent/"numeric_gate.py").read_text();self.assertIn("kguard=Guarded",numeric);self.assertIn("vguard=Guarded",numeric)
        self.assertIn("native_cache_input_outer_guards",numeric);self.assertIn("g.intact() for g in inputs_guard",numeric)
    def test_per_head_no_old_batch_mean_in_gate(self):
        source=(Path(__file__).parent/"numeric_gate.py").read_text();self.assertNotIn("mean((1,2))",source)
        self.assertIn("mean(-1)",source);self.assertIn("actual_step_refs",source);self.assertIn("workspace_guards",source)
    def test_all_cases_hardware_scope_stays_pending_in_consumer(self):
        source=(Path(__file__).parent/"consume_numeric.py").read_text()
        for field in ("model_executed","matched1024_e2e_verified","final2048_task_verified"):
            self.assertIn('"'+field+'":False',source)

import model_bridge,host,preflight
class V3HostAndActualModelSoftware(unittest.TestCase):
 def test_model_bridge_default_off_without_source_or_Torch(self):
  with mock.patch.dict(__import__("os").environ,{"QWEN36_SPARQ_TOKEN_ENABLED":"0"}):
   self.assertFalse(model_bridge.install_from_env()["default_enabled"])
  self.assertNotIn("torch",sys.modules)
 def test_actual_deployed_model_sources_and_real_interface(self):
  for name,ref in receipt.MODEL_SOURCES.items():
   path=Path(ref["captured_source_ref"]["path"]);self.assertEqual(receipt.sha(path),ref["runtime_ref"]["sha256"])
   tree=ast.parse(path.read_bytes())
   if name=="attention_v1":
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="AscendAttentionBackendImpl")
    forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="forward_impl")
    self.assertEqual([a.arg for a in forward.args.args],["self","query","key","value","kv_cache","attn_metadata","output"])
    writer=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="forward")
    calls=[n for n in ast.walk(writer) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
    self.assertLess(min(n.lineno for n in calls if n.func.attr=="reshape_and_cache"),min(n.lineno for n in calls if n.func.attr=="forward_impl"))
   else:
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="NPUModelRunner")
    prepare=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="_prepare_inputs")
    self.assertEqual([a.arg for a in prepare.args.args],["self","scheduler_output","num_scheduled_tokens"])
 def row(self,rid="a",obj=101,computed=4,scheduled=1):return dict(rid=rid,object_id=obj,computed=computed,scheduled=scheduled)
 def test_real_request_ledger_paused_and_reordered_native_lengths(self):
  b=model_bridge.RequestLedger(3);a=b.prepare([self.row("a"),self.row("paused",102,8,2)])
  b.prepare([self.row("a",101,5,1)])
  self.assertIn("paused",b.live);self.assertEqual(b.live["paused"]["slot"],a[1]["slot"])
  b.prepare([self.row("paused",102,10,1),self.row("a",101,6,1)])
  out=b.decode([11,7]);self.assertEqual([x["rid"] for x in out],["paused","a"])
  self.assertEqual([x["slot"] for x in out],[a[1]["slot"],a[0]["slot"]])
 def test_finished_reuse_new_generation_no_stale_alias(self):
  b=model_bridge.RequestLedger();a=b.prepare([self.row()])[0]
  b.prepare([self.row("a",102,0,1)],finished=["a"]);now=b.decode([1])[0]
  self.assertEqual(now["generation"],a["generation"]+1);self.assertEqual(now["slot"],a["slot"])
 def test_no_implicit_live_request_object_ABA_or_rewind(self):
  b=model_bridge.RequestLedger();b.prepare([self.row()])
  for row in (self.row(obj=999),self.row(computed=3)):
   with self.subTest(row=row),self.assertRaises(ValueError):b.prepare([row])
 def test_true_native_length_mismatch_or_multitoken_decode_rejected(self):
  b=model_bridge.RequestLedger();b.prepare([self.row()])
  with self.assertRaises(ValueError):b.decode([9])
  b.prepare([self.row(computed=5,scheduled=2)])
  with self.assertRaises(ValueError):b.decode([7])
 def test_paused_slot_never_stolen_to_admit_overcapacity(self):
  b=model_bridge.RequestLedger(1);b.prepare([self.row()])
  with self.assertRaises(ValueError):b.prepare([self.row("other",202)])
 def test_new_no_device_guest_args_have_no_devices(self):
  e={"name":"cpu-fixture","cid":"6"*64,"source":{"sha256":"1"*64},"host_sha256":"2"*64,
   "numeric_sha256":"3"*64,"guest_cpu":1,"mounts":{},"mode":"cpu"}
  self.assertNotIn("--device",host.create_argv(e));self.assertEqual(host.expected_devices("cpu"),{})
  e["mode"]="npu";self.assertIn("/dev/davinci6:/dev/davinci0:rwm",host.create_argv(e))
 def test_same5400_lease_and_CPU_stop_before_NPU_creation(self):
  source=Path(host.__file__).read_text()
  self.assertIn("cpu_ctl.created_monotonic=ctl.created_monotonic;cpu_ctl.deadline=ctl.deadline",source)
  self.assertLess(source.index("cpu_cleanup=cpu_ctl.cleanup()"),source.index("  ctl.create({},source,files)"))
  self.assertIn('self.device_phase="cpu"',source)
 def test_schema_before_init_for_canary_and_matrix(self):
  for mod,fn_name in ((host,"inside_canary"),(numeric_gate,"main")):
   tree=ast.parse(Path(mod.__file__).read_text());fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==fn_name)
   checks=[n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="recheck_preinit"]
   inits=[n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="set_device"]
   self.assertEqual(len(checks),1);self.assertEqual(len(inits),1);self.assertLess(checks[0],inits[0])
 def test_preflight_actual_no_node_and_single_signature_not_union(self):
  source=Path(preflight.__file__).read_text()
  self.assertIn('require(witnesses,',source)
  self.assertIn('actual_guest_device_nodes_after',source)
  self.assertIn('a.observation_ref=save_observations(a,observation)',source)
  self.assertIn('names>=needed',source)
 def test_partial_preflight_never_promotes(self):
  with self.assertRaises(ValueError):preflight.validate_abi({"status":"actual-schema-checked","npu_executed":False},{},{})
 def test_full_native_consumer_pending_service_requires_real_host(self):
  source=Path(consume_numeric.__file__).read_text()
  for name in ("source_device_proof","actual_npu_python_process_proofs","cpu_only_cleanup","numerical_child","protected_before","stopped_owned_inspect"):
   self.assertIn(name,source)
  self.assertIn('host_result_sha',source);self.assertIn('MAIN_original_operation_authority_verified',source)
 def test_eager_bridge_not_full_graph_and_not_double_KV_writer(self):
  source=Path(model_bridge.__file__).read_text();self.assertIn('runner.model_config.enforce_eager is True',source)
  self.assertIn('require(not attention._EXTRA_CTX.capturing',source)
  tree=ast.parse(source);fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="forward")
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in
   ("reshape_and_cache","_npu_reshape_and_cache","do_kv_cache_update") for n in ast.walk(fn)))
  self.assertIn('workspace.run(query,kc,vc,None',source);self.assertIn('same',Path(receipt.__file__).read_text())
 def test_optin_sitecustom_failure_cannot_silently_run_dense(self):
  source=(Path(__file__).parent/"sitecustomize.py").read_text()
  self.assertIn("except BaseException:",source);self.assertIn("os._exit(78)",source);self.assertIn("traceback.print_exc",source)
 def test_model_toggle_never_consumes_mock_or_incomplete_authority(self):
  source=Path(model_bridge.__file__).read_text()
  self.assertIn('checked.get("actual_numerical_steps")==20480',source)
  self.assertIn('checked.get("MAIN_original_operation_authority_verified") is True',source)
  self.assertIn('source_files',source);self.assertNotIn('model_ready":True',source)


class PreNpuActualSourceRegression(unittest.TestCase):
 def test_cpu_golden_smoke_is_in_predevice_actual_producer(self):
  import preflight
  text=Path(preflight.__file__).read_text()
  self.assertIn("cpu_smoke=cpu_golden_smoke(torch,torch_npu)",text)
  self.assertIn('"actual_cpu_golden":cpu_smoke',text)
  self.assertIn('validate_cpu_golden(report.get("actual_cpu_golden"))',text)
  self.assertNotIn("set_device",ast.unparse(next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=="cpu_golden_smoke")))

 def test_actual_original_operation_get_not_flattened(self):
  from original_terminal import original_terminal
  path=Path(__file__).parent/"original_operation_get_ma0e85.json"
  self.assertEqual(receipt.sha(path),"ec6ae5ebcec57d7226b97460ec182920b0817eb96a5da6afaf716af1c86a3eb6")
  raw=json.loads(path.read_bytes());got=original_terminal(raw,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
  self.assertEqual(got["operation_id"],"exec-0000000000000e85")
  self.assertEqual(got["record"],raw["structuredContent"]["operation"]["result"]["record"])
  self.assertEqual(got["record_origin"],"structuredContent.operation.result.record")
  self.assertEqual(got["origin_shape"],"operation_get")
  self.assertNotIn("routeDecision",raw["structuredContent"])
  self.assertIsNone(raw["structuredContent"]["result"])
 def test_actual_original_not_found_rejected(self):
  from original_terminal import original_terminal
  path=Path(__file__).parent/"original_operation_get_ma0e7f_not_found.json"
  self.assertEqual(receipt.sha(path),"59d954ea2e39533ed91ca2390baa1e25702634f6edb9997072b0190c0d6d9363")
  with self.assertRaises(ValueError):original_terminal(json.loads(path.read_bytes()),"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 def test_actual_envelope_negative_variants(self):
  import copy
  from original_terminal import original_terminal
  raw=json.loads((Path(__file__).parent/"original_operation_get_ma0e85.json").read_bytes())
  for mode in ("failed","cancelled","timeout","missing-record","wrong-id","wrong-target","disagreement","truncated"):
   x=copy.deepcopy(raw);x.pop("content",None);s=x["structuredContent"];op=s["operation"];record=op["result"]["record"]
   if mode=="failed":record["exitCode"]=1
   if mode=="cancelled":record["cancelled"]=True
   if mode=="timeout":record["timedOut"]=True
   if mode=="missing-record":op["result"].pop("record")
   if mode=="wrong-id":record["id"]="exec-000000000000dead"
   if mode=="wrong-target":op["targetPeerId"]="lgw_wrong"
   if mode=="disagreement":s["routeDecision"]="wrong"
   if mode=="truncated":record["stdoutTruncated"]=True
   with self.subTest(mode=mode),self.assertRaises(ValueError):original_terminal(x,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
  x=copy.deepcopy(raw);x["content"][0]["text"]=x["content"][0]["text"][:-10]
  with self.assertRaises((ValueError,json.JSONDecodeError)):original_terminal(x,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 def test_cpu_fp64_actual_runtime_guard_positive_negative(self):
  from types import SimpleNamespace
  from numeric_gate import assert_cpu_fp64
  fake_torch=SimpleNamespace(float64="float64")
  tensor=lambda dtype,device:SimpleNamespace(dtype=dtype,device=SimpleNamespace(type=device))
  assert_cpu_fp64(fake_torch,tensor("float64","cpu"),tensor("float64","cpu"))
  for dtype,device in (("float32","cpu"),("float64","npu"),("bfloat16","cpu")):
   with self.subTest(dtype=dtype,device=device),self.assertRaises(ValueError):assert_cpu_fp64(fake_torch,tensor(dtype,device))
  with self.assertRaises(ValueError):assert_cpu_fp64(fake_torch)
 def test_golden_original_V_selected_V_mean_are_cpu_fp64(self):
  import numeric_gate
  tree=ast.parse(Path(numeric_gate.__file__).read_text())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="golden")
  values={t.id:n.value for n in ast.walk(fn) if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
  self.assertIsInstance(values["val"],ast.Call);self.assertEqual(values["val"].func.attr,"double")
  self.assertNotIn("float",[(n.func.attr) for n in ast.walk(values["val"]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)])
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="assert_cpu_fp64" and
   {"q","nk","nv","weights","prob"}<={a.id for a in n.args if isinstance(a,ast.Name)} for n in ast.walk(fn)))
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="assert_cpu_fp64" and
   {"exact","alpha","mean"}<={a.id for a in n.args if isinstance(a,ast.Name)} for n in ast.walk(fn)))
 def test_support_queries_keep_independent_feedback(self):
  import numeric_gate
  text=Path(numeric_gate.__file__).read_text();tree=ast.parse(text)
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="golden"]
  self.assertEqual({n.args[1].id for n in calls if isinstance(n.args[1],ast.Name)},{"q","rq"})
  self.assertIn('enumerate(finite_precision["supports"])',text)
  self.assertIn('"reference_feedback_support_equal":not any(support_divergence)',text)
  self.assertIn("reference_previous.copy_(expected",text)
  self.assertIn("previous.copy_(out)",text)
  self.assertNotIn("rq=q",text)
 def test_formal_event_is_debug_off(self):
  before=model_bridge._MODE
  try:
   model_bridge._MODE="formal"
   self.assertIsNone(model_bridge._event(None,0,"sparse-decode",None))
  finally:model_bridge._MODE=before
  tree=ast.parse(Path(model_bridge.__file__).read_text());parents={}
  for node in ast.walk(tree):
   for child in ast.iter_child_nodes(node):parents[id(child)]=node
  for node in ast.walk(tree):
   if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or node.func.attr not in ("guards","cpu"):continue
   cursor=node;ancestors=[]
   while id(cursor) in parents:
    cursor=parents[id(cursor)];ancestors.append(cursor)
   # Existing native block-table CPU copy is algorithm input, not a selected/channel trace.
   if node.func.attr=="cpu" and ast.unparse(node.func.value)=="metadata.block_tables.detach()":continue
   self.assertTrue(any(isinstance(a,ast.If) and isinstance(a.test,ast.Compare) and isinstance(a.test.left,ast.Name) and a.test.left.id=="_MODE" and isinstance(a.test.comparators[0],ast.Constant) and a.test.comparators[0].value=="diagnostic" for a in ancestors))
  self.assertIn('diag.get("actual_TP4_64_layer_model_execution_verified") is True',Path(model_bridge.__file__).read_text())
 def test_actual_attention_writer_precedes_forward_impl(self):
  ref=receipt.MODEL_SOURCES["attention_v1"]["captured_source_ref"]
  self.assertEqual(receipt.sha(Path(ref["path"])),ref["sha256"])
  tree=ast.parse(Path(ref["path"]).read_bytes())
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="AscendAttentionBackendImpl")
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="forward")
  writer=[n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="reshape_and_cache"]
  invoke=[n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="forward_impl"]
  self.assertTrue(writer and invoke);self.assertLess(max(writer),min(invoke))


class NativeSlotInt32Boundary(unittest.TestCase):
 def tensor(self,dtype="int32",shape=(3,),device="npu",contiguous=True,format=2):
  from types import SimpleNamespace
  return SimpleNamespace(dtype=dtype,shape=shape,ndim=len(shape),
   device=SimpleNamespace(type=device),is_contiguous=lambda:contiguous,format=format)
 def fixture(self):
  torch=__import__("types").SimpleNamespace(int32="int32",bfloat16="bf16")
  npu=__import__("types").SimpleNamespace(get_npu_format=lambda x:x.format)
  cache=self.tensor("bf16",(325,128,1,256));indices=self.tensor();indices.device=cache.device
  return torch,npu,indices,cache
 def test_actual_ATB_int32_ND_source_contract_positive_not_native_PASS(self):
  torch,npu,indices,cache=self.fixture()
  numeric_gate.native_slot_layout(torch,npu,indices,3,cache)
  self.assertEqual(numeric_gate.native_slot_capacity(18,18,2048,160),41472)
  self.assertNotIn("torch",sys.modules)
 def test_int64_wrong_device_rank_stride_format_and_KVdtype_rejected(self):
  for mutation in ("int64","cpu","shape","stride","format","cache-rank","cache-dtype","cache-format"):
   torch,npu,indices,cache=self.fixture()
   if mutation=="int64":indices.dtype="int64"
   elif mutation=="cpu":indices.device=__import__("types").SimpleNamespace(type="cpu")
   elif mutation=="shape":indices.shape=(3,1)
   elif mutation=="stride":indices.is_contiguous=lambda:False
   elif mutation=="format":indices.format=29
   elif mutation=="cache-rank":cache.ndim=3
   elif mutation=="cache-dtype":cache.dtype="fp32"
   else:cache.format=29
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):
    numeric_gate.native_slot_layout(torch,npu,indices,3,cache)
 def test_static_int32_range_and_full160_capacity_negative(self):
  for args in ((18,18,2200,160),(2**31,18,2048,160),(True,18,2048,160),(18,0,2048,160),(18,18,2048,0)):
   with self.subTest(args=args),self.assertRaises(ValueError):numeric_gate.native_slot_capacity(*args)
 def test_actual_prefill_decode_reuse_boundaries_int32_internal_leases_int64(self):
  text=Path(numeric_gate.__file__).read_text();tree=ast.parse(text)
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run_case")
  assigns={t.id:n.value for n in ast.walk(fn) if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
  for name in ("indices","idx"):
   dtype=next(k.value for k in assigns[name].keywords if k.arg=="dtype")
   self.assertIsInstance(dtype,ast.Attribute);self.assertEqual(dtype.attr,"int32")
  self.assertEqual(assigns["mapping"].args[-1].attr,"int32")
  self.assertEqual(assigns["leases"].args[-1].attr,"int64")
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
  checks=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=="native_slot_layout"]
  self.assertEqual({n.args[2].id for n in checks},{"mapping","indices","idx"})
  first=next(n.lineno for n in checks if n.args[2].id=="indices")
  writer=min(n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=="reshape_and_cache")
  self.assertLess(first,writer)
  topology=next(n for n in ast.walk(fn) if isinstance(n,ast.FunctionDef) and n.name=="topology")
  native=next(n for n in ast.walk(topology) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
   n.func.attr=="tensor" and any(k.arg=="dtype" and isinstance(k.value,ast.Attribute) and k.value.attr=="int32" for k in n.keywords) and
   n.args and isinstance(n.args[0],ast.Name) and n.args[0].id=="positions")
  self.assertTrue(native);self.assertIn("len(set(positions))==b",ast.get_source_segment(text,topology))
 def test_no_graph_capture_conversion_or_changed_writer_keyword_API(self):
  text=Path(numeric_gate.__file__).read_text();tree=ast.parse(text)
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run_case")
  run=next(n for n in ast.walk(fn) if isinstance(n,ast.FunctionDef) and n.name=="run")
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ("to","tensor","item","cpu") for n in ast.walk(run)))
  writer=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="reshape_and_cache")
  self.assertEqual({k.arg for k in writer.keywords},{"key","value","key_cache","value_cache","slot_mapping"})
  self.assertEqual(next(k.value.id for k in writer.keywords if k.arg=="slot_mapping"),"mapping")
 def test_independent_golden_oracle_support_guard_matrix_and_limits_unchanged(self):
  text=Path(numeric_gate.__file__).read_text()
  self.assertEqual(numeric_gate.LIMITS,{"relative_rms":.005,"cosine":.99998})
  self.assertEqual(receipt.BATCHES,"1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16")
  self.assertEqual(16*4*2*160,20480)
  self.assertIn("query.detach().cpu().double()",text)
  self.assertIn("candidate_supports",text);self.assertIn("reference_feedback_independent",text)
  self.assertIn("kguard.intact() and vguard.intact()",text);self.assertIn("range(160)",text)


class NativePAHostContext(unittest.TestCase):
 def test_host_clamp_CPU_int32_metadata_geometry_negative(self):
  from sparq_token_v4.core import host_pa_lengths,host_pa_layout
  from types import SimpleNamespace as S
  self.assertEqual(host_pa_lengths([2,2049],2,128,2304),[2,128])
  for lengths,budget,capacity in (([0],128,2304),([True],128,2304),([2305],128,2304),([1],True,2304),([1],1,True)):
   with self.assertRaises(ValueError):host_pa_lengths(lengths,1,budget,capacity)
  torch=S(int32="int32");good=S(shape=(2,),dtype="int32",device=S(type="cpu"),is_contiguous=lambda:True)
  host_pa_layout(torch,good,2)
  for key,value in (("shape",(2,1)),("dtype","int64"),("device",S(type="npu")),("is_contiguous",lambda:False)):
   bad=S(**vars(good));setattr(bad,key,value)
   with self.assertRaises(ValueError):host_pa_layout(torch,bad,2)
  self.assertNotIn("torch",sys.modules)
 def fake_protocol(self):
  import contextlib
  from types import SimpleNamespace as S
  from sparq_token_v4.core import NativePAHost
  calls=[]
  class Tensor:
   dtype="int32";shape=(2,);device=S(type="cpu")
   def is_contiguous(self):return True
   def copy_(self,value):self.values=list(value);return self
  tensor=Tensor();tensor.values=[0,0]
  class Event:
   def wait(self,stream):calls.append(("wait",stream))
   def reset(self,stream):calls.append(("reset",stream))
   def record(self,stream):calls.append(("record",stream))
  def workspace(**args):
   calls.append(("workspace",tuple(args["context_lens"].values)));return "software-workspace-only"
  def pa(**args):calls.append(("pa",tuple(args["context_lens"].values),"workspace" in args))
  npu=S(ExternalEvent=Event,Stream=lambda:"update-stream",current_stream=lambda:"capture-stream",stream=lambda _:contextlib.nullcontext(),
   graph_task_group_begin=lambda stream:calls.append(("group-begin",stream)),
   graph_task_group_end=lambda stream:calls.append(("group-end",stream)) or "software-handle-only",
   graph_task_update_begin=lambda stream,handle:calls.append(("update-begin",stream,handle)),
   graph_task_update_end=lambda stream:calls.append(("update-end",stream)))
  torch=S(int32="int32",tensor=lambda vals,**kw:list(vals),npu=npu)
  atb=S(_npu_paged_attention_get_workspace=workspace,_npu_paged_attention=pa)
  helper=object.__new__(NativePAHost)
  helper.batch=2;helper.budget=128;helper.capacity=2304;helper.context=S(value=tensor)
  helper.epoch=0;helper.updated_epoch=None;helper.capturing=False;helper.params=None;helper.handle=None;helper.event=None;helper.update_stream=None
  return helper,torch,atb,calls
 def test_source_protocol_actual_python_capture_update_epoch_not_NPU_PASS(self):
  helper,torch,atb,calls=self.fake_protocol()
  with mock.patch.dict(sys.modules,{"torch":torch,"torch_npu":atb}):
   helper.set_lengths([2049,100]);helper.prepare_capture()
   output=object();self.assertIs(helper.execute("q","k","v","table",output),output);helper.finish_capture()
   self.assertEqual([x[0] for x in calls],["workspace","wait","reset","group-begin","pa","group-end"])
   calls.clear();helper.set_lengths([2,2049])
   with self.assertRaises(ValueError):helper.check_replay()
   helper.update_graph();helper.check_replay()
   self.assertEqual([x[0] for x in calls],["workspace","update-begin","pa","update-end","record"])
   self.assertEqual(calls[0][1],(2,128));self.assertEqual(calls[2][1],(2,128))
   with self.assertRaises(ValueError):helper.update_graph()
   helper.set_lengths([3,2049])
   with self.assertRaises(ValueError):helper.check_replay()
  self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
 def test_known_host_topology_B1_to16_full160_step80_shortened_reuse(self):
  from sparq_token_v4.core import host_pa_lengths
  for b in range(1,17):
   slots=list(range(b));lengths={s:2048-3*s for s in slots};observed_short=False
   for step in range(160):
    if step%11==0:slots=slots[1:]+slots[:1]
    if step==80:lengths[slots[0]]=1
    actual=host_pa_lengths([lengths[s]+1 for s in slots],b,128,2304)
    expected=[lengths[s]+1 if lengths[s]+1<128 else 128 for s in slots]
    self.assertEqual(actual,expected)
    if step==80:self.assertEqual(actual[0],2);observed_short=True
    for s in slots:lengths[s]+=1
   self.assertTrue(observed_short)
 def test_capture_run_and_update_never_convert_device_context_to_host(self):
  core=ast.parse((Path(receipt.ROOT)/"sparq_token_v4/core.py").read_text())
  helper=next(n for n in core.body if isinstance(n,ast.ClassDef) and n.name=="NativePAHost")
  for name in ("execute","update_graph","check_replay"):
   fn=next(n for n in helper.body if isinstance(n,ast.FunctionDef) and n.name==name)
   self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in
    ("cpu","to","item","tolist","tensor","arange") for n in ast.walk(fn)),name)
  graph=next(n for n in core.body if isinstance(n,ast.ClassDef) and n.name=="GraphTokenWorkspace")
  run=next(n for n in graph.body if isinstance(n,ast.FunctionDef) and n.name=="run")
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ("cpu","item","tolist","tensor","arange") for n in ast.walk(run)))
  conversions=[n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="to"]
  self.assertEqual(len(conversions),1)
  self.assertEqual(ast.unparse(conversions[0].args[0]),"self.output.dtype")
  self.assertEqual(conversions[0].keywords,[])
 def test_actual_pinned_deployed_CPU_metadata_and_task_update_protocol(self):
  ref=receipt.MODEL_SOURCES["attention_v1"]["captured_source_ref"];raw=Path(ref["path"]).read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),ref["sha256"]);tree=ast.parse(raw)
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="AscendAttentionBackendImpl")
  for name,expected in (("full_graph_pa",["_npu_paged_attention_get_workspace","wait","reset","graph_task_group_begin","_npu_paged_attention","graph_task_group_end"]),
   ("update_graph_params",["_npu_paged_attention_get_workspace","graph_task_update_begin","_npu_paged_attention","graph_task_update_end","record"])):
   fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
   calls=sorted([n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in expected],key=lambda n:n.lineno)
   self.assertEqual([n.func.attr for n in calls[:len(expected)]],expected)
  text=raw.decode()
  self.assertIn("seq_lens = common_attn_metadata._seq_lens_cpu[:num_reqs]",text)
  self.assertIn("seq_lens = common_attn_metadata.seq_lens_cpu[:num_reqs]",text)
  self.assertIn('seq_lens = common_attn_metadata.seq_lens[:num_reqs].to("cpu")',text)
  self.assertIn("context_lens=attn_metadata.seq_lens",text)
 def test_driver_host_update_every_replay_and_model_eager_same_host_lengths(self):
  tree=ast.parse(Path(numeric_gate.__file__).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run_case")
  topology=next(n for n in ast.walk(fn) if isinstance(n,ast.FunctionDef) and n.name=="topology")
  host=next(n for n in ast.walk(topology) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="set_lengths")
  self.assertEqual(host.args[0].id,"live_lengths")
  update=next(n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="update_graph")
  replay=next(n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="replay")
  self.assertLess(update,replay);self.assertIn('if step==80:',ast.get_source_segment(Path(numeric_gate.__file__).read_text(),fn))
  import model_bridge
  self.assertIn("workspace.native_pa.set_lengths(lengths)",Path(model_bridge.__file__).read_text())
  self.assertIn("metadata.seq_lens_list",Path(model_bridge.__file__).read_text())
  self.assertIn("FULL attention task-group/replay is unsupported",Path(model_bridge.__file__).read_text())
 def test_independent_receipt_reconstructs_context_shortening_not_boolean_only(self):
  text=Path(receipt.__file__).read_text()
  self.assertIn('if s==80:pa_live[pa_slots[0]]=1',text)
  self.assertIn('expected_host_context=[min(pa_live[slot]+1,128) for slot in pa_slots]',text)
  self.assertIn('row.get("native_pa_graph_update_epoch")==(s+2 if m=="graph" else None)',text)
  self.assertEqual(numeric_gate.LIMITS,{"relative_rms":.005,"cosine":.99998})
  self.assertEqual(receipt.MODES,(("eager",0),("graph",0),("graph",1),("graph",2)))

if __name__=="__main__":unittest.main(verbosity=2)
