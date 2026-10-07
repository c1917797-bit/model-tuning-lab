#!/usr/bin/env python3
"""Actual stdlib software tests only; no Docker/Torch/NPU fixture promotion."""
import contextlib,copy,hashlib,io,json,math,sys,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import contract as c,oracle,consumer,main,native
class SoftwareTests(unittest.TestCase):
 def test_default_off_imports_no_torch_or_device(self):
  with mock.patch.object(main,"source_identity",side_effect=AssertionError("source must not be read")),mock.patch.object(main,"run_device",side_effect=AssertionError("device must not dispatch")),contextlib.redirect_stdout(io.StringIO()) as out:
   self.assertEqual(main.main([]),0)
  r=json.loads(out.getvalue());self.assertFalse(r["default_enabled"]);self.assertFalse(r["npu_executed"]);self.assertFalse(r["serving_ready"])
  self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
 def test_explicit_source_ref_required(self):
  with self.assertRaisesRegex(ValueError,"source Ref"):main.main(["--execute"])
 def test_single_entry_modes_exclusive(self):
  with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):main.parser().parse_args(["--execute","--consume"])
 def test_fixed_full_matrix(self):
  p=c.protocol();self.assertEqual(p["batch_sizes"],list(range(1,17)));self.assertEqual(p["steps"],160)
  self.assertEqual(len(c.MODES)*2*16*c.STEPS,20480);self.assertFalse(p["model_consumer_verified"])
 def test_fixed_original_limits(self):
  self.assertEqual(c.LIMITS,{"relative_rms":.005,"cosine":.99998,"max_abs":.00303,"lse_max_abs":.00303})
 def test_all_schedules_replay_full(self):
  scheduled=0
  for batch in range(1,17):
   for qw in (1,4):
    for mode,trial in c.MODES:
     book=c.SlotBook(batch);generations=0
     for step in range(c.STEPS):
      frame=book.advance(batch,qw,step);self.assertEqual(len(set(frame["slots"])),batch)
      self.assertEqual(len(frame["rows"]),batch);self.assertEqual(frame["counts"],c.query_counts(batch,qw,step))
      self.assertTrue(all(0<=r["length"]<=c.N for r in frame["rows"]))
      self.assertTrue(all(len(row)==qw for row in c.visible_lengths(frame,qw)));scheduled+=1
     self.assertTrue(any(r["generation"]>0 for r in book.rows))
  self.assertEqual(scheduled,20480)
 def test_empty_and_mixed_query_rows(self):
  book=c.SlotBook(4);f=book.advance(4,4,0)
  self.assertEqual(f["counts"],[0,1,4,2]);v=c.visible_lengths(f,4)
  self.assertEqual(v[0],[0,0,0,0]);self.assertEqual(v[1][1:],[0,0,0]);self.assertEqual(v[3][2:],[0,0])
 def test_explicit_reset_generation(self):
  book=c.SlotBook(16)
  for i in range(65):frame=book.advance(16,4,i)
  s=frame["explicit_reset_slot"];self.assertEqual(s,4);self.assertGreater(book.rows[s]["generation"],0)
 def test_direct_empty(self):
  self.assertEqual(oracle.direct([1.,2.],[],[],.5),([0.,0.],float("-inf")))
 def test_direct_scalar_known(self):
  y,l=oracle.direct([0.,0.],[[1.,2.],[3.,4.]],[[2.,6.],[4.,10.]],.5)
  self.assertEqual(y,[3.,8.]);self.assertAlmostEqual(l,math.log(2))
 def test_composition_independent_direct(self):
  q=[.3,-.1,.2,.4];keys=[[i*.03,j*.02,.5,-.2] for i,j in ((0,1),(2,3),(4,5),(6,7))]
  values=[[i*.05,.2,-.1,.7] for i in range(4)]
  direct,l=oracle.direct(q,keys,values,.5)
  a,la=oracle.direct(q,keys[:2],values[:2],.5);b,lb=oracle.direct(q,keys[2:],values[2:],.5)
  got,lgot=oracle.compose([(a,la,True),(b,lb,True)],4)
  for x,y in zip(got,direct):self.assertAlmostEqual(x,y,places=14)
  self.assertAlmostEqual(lgot,l,places=14)
 def test_inactive_nan_infinite_output_ignored_before_product(self):
  got,l=oracle.compose([([float("nan"),float("inf")],float("-inf"),False),([2.,4.],0.,True)],2)
  self.assertEqual((got,l),([2.,4.],0.))
 def test_all_empty_nan_identity(self):
  got,l=oracle.compose([([float("nan")]*2,float("-inf"),False)]*3,2)
  self.assertEqual(got,[0.,0.]);self.assertTrue(math.isinf(l) and l<0)
 def test_defined_nan_fail_closed(self):
  with self.assertRaises(ValueError):oracle.compose([([float("nan")],0.,True)],1)
 def test_defined_infinite_lse_fail_closed(self):
  with self.assertRaises(ValueError):oracle.compose([([1.],float("inf"),True)],1)
 def test_large_lse_stable(self):
  got,l=oracle.compose([([1.,3.],10000.,True),([3.,5.],10000.,True)],2)
  self.assertEqual(got,[2.,4.]);self.assertAlmostEqual(l,10000.+math.log(2))
 def test_zero_reference_exact(self):
  self.assertTrue(c.metric([0.,0.],[0.,0.])["passed"]);self.assertFalse(c.metric([0.,.0001],[0.,0.])["passed"])
 def test_per_head_metric_not_mean_cancellation(self):
  self.assertFalse(c.metric([.1,-.1],[.1,.1])["passed"])
 def test_finite_metric(self):
  self.assertFalse(c.metric([float("nan")],[1.])["passed"])
 def test_scalar_metric_binds_thresholds(self):
  m=c.metric([1.,2.,3.],[1.,2.,3.]);c.metric_record(m)
  m["max_abs"]=.1
  with self.assertRaises(ValueError):c.metric_record(m)
 def test_declared_metric_pass_not_sufficient(self):
  with self.assertRaises(ValueError):c.metric_record({"finite":True,"passed":True,"relative_rms":1.,"cosine":1.,"max_abs":0.})
 def test_partial_matrix_cannot_promote(self):
  report={"schema":"flashinfer.native-state-numerics/v5","status":"passed","protocol":c.protocol(),"cases":[]}
  with self.assertRaisesRegex(ValueError,"128 exact"):c.validate_cases(report)
 def test_old_launch_schema_cannot_borrow(self):
  with self.assertRaisesRegex(ValueError,"owned launch"):c.validate_launch({"schema":"kvbp.short-horizon-launch-identity/v5"},{},{},[])
 def terminal(self):
  return {"targetPeerId":"expected","routeDecision":"peer_direct","result":{"record":{
   "state":"completed","exitCode":0,"timedOut":False,"cancelled":False,"command":"/usr/bin/docker","args":[],"stdout":"","stderr":""}}}
 def test_original_terminal_exact(self):
  r=consumer.terminal_record(self.terminal(),"expected");self.assertEqual(r["exitCode"],0)
 def test_wrong_peer_cannot_promote(self):
  with self.assertRaises(ValueError):consumer.terminal_record(self.terminal(),"other")
 def test_gateway_route_cannot_promote(self):
  t=self.terminal();t["routeDecision"]="gateway_proxy"
  with self.assertRaises(ValueError):consumer.terminal_record(t,"expected")
 def test_failed_running_timeout_cancel_never_promote(self):
  for k,v in (("state","running"),("exitCode",1),("timedOut",True),("cancelled",True)):
   t=self.terminal();t["result"]["record"][k]=v
   with self.subTest(k=k),self.assertRaises(ValueError):consumer.terminal_record(t,"expected")
 def test_marker_missing_duplicate(self):
  for text in ("","MAIN_FLASHINFER_NATIVE_STATE_V5_REPORT {}\nMAIN_FLASHINFER_NATIVE_STATE_V5_REPORT {}"):
   with self.subTest(text=text),self.assertRaises(ValueError):consumer.producer_marker(text)
 def test_marker_exact_payload(self):
  self.assertEqual(consumer.producer_marker("noise\nMAIN_FLASHINFER_NATIVE_STATE_V5_REPORT {\"status\":\"failed\"}"),{"status":"failed"})
 def test_actual_launch_refs_required(self):
  a=main.parser().parse_args(["--consume"])
  with self.assertRaisesRegex(ValueError,"original actual"):consumer.consume(a,{}, {})

import host
class HostClosureSoftwareTests(unittest.TestCase):
 def proof(self):
  return {"schema":"portfolio.native-device-launch/v1","image_id":c.IMAGE,"container_id":"6"*64,"source_manifest":{},"sources":{},
   "physical_devices":[6],"logical_to_physical":{"0":6},"memory_cgroup_bytes":8*1024**3,"guest_cpu_budget":1,
   "image_python_argv_template":["python","-B","main.py","--execute","--launch-proof-sha256","@ACTUAL_LAUNCH_SHA256@"]}
 def test_actual_launch_bytes_ref_expands_single_sha(self):
  p=self.proof()
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   r=c.write_new(Path(td)/"launch.json",p);argv=c.expected_launch_argv(p,r)
   self.assertEqual(argv[-1],c.sha(r["path"]));self.assertNotIn("@ACTUAL_LAUNCH_SHA256@",argv)
   self.assertEqual(argv[:-1],p["image_python_argv_template"][:-1])
 def test_sha_ref_is_never_optional(self):
  with self.assertRaisesRegex(ValueError,"never optional"):c.expected_launch_argv(self.proof(),None)
 def test_wrong_launch_digest_rejected_actual_file(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   p=self.proof();r=c.write_new(Path(td)/"launch.json",p);r["sha256"]="0"*64
   with self.assertRaisesRegex(ValueError,"bytes changed"):c.expected_launch_argv(p,r)
 def test_loaded_mutation_cannot_expand_original_bytes(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   p=self.proof();r=c.write_new(Path(td)/"launch.json",p);p["guest_cpu_budget"]=2
   with self.assertRaisesRegex(ValueError,"canonical launch bytes"):c.expected_launch_argv(p,r)
 def test_noncanonical_bytes_cannot_promote(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   p=self.proof();path=Path(td)/"launch.json";path.write_text(json.dumps(p,indent=2))
   r={"path":str(path),"sha256":c.sha(path)}
   with self.assertRaisesRegex(ValueError,"canonical launch bytes"):c.expected_launch_argv(p,r)
 def test_placeholder_only_at_exact_flag(self):
  for template in (["@ACTUAL_LAUNCH_SHA256@"],["--other","@ACTUAL_LAUNCH_SHA256@"],
    ["--launch-proof-sha256","@ACTUAL_LAUNCH_SHA256@","--launch-proof-sha256","@ACTUAL_LAUNCH_SHA256@"],[]):
   with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
    p=self.proof();p["image_python_argv_template"]=template;r=c.write_new(Path(td)/"launch.json",p)
    with self.subTest(template=template),self.assertRaisesRegex(ValueError,"placeholder"):c.expected_launch_argv(p,r)
 def test_actual_wrong_cli_sha_rejected_before_device_evidence(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
   p=self.proof();r=c.write_new(Path(td)/"launch.json",p);argv=c.expected_launch_argv(p,r);argv[-1]="0"*64
   with self.assertRaisesRegex(ValueError,"full CLI"):c.validate_launch(p,{}, {},argv,launch_ref=r)
 def test_exact_host_cli_no_wrapper_substring(self):
  a=main.parser().parse_args(["--host-execute","--source-manifest","/source","--source-manifest-sha256","a"*64,"--output-dir","/cache/cch/new"])
  self.assertEqual(host.host_argv(a),["/usr/bin/python3","-B",str(host.INTEGRATED/"main.py"),"--host-execute","--source-manifest","/source","--source-manifest-sha256","a"*64,"--output-dir","/cache/cch/new"])
 def test_exact_four_devices_and_new_owner(self):
  self.assertEqual(host.expected_devices(),{"/dev/davinci6":"/dev/davinci0","/dev/davinci_manager":"/dev/davinci_manager","/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"})
  self.assertEqual(host.OWNER,"flashinfer-native-state-v5");self.assertEqual(host.H.OWNER,"kvbuffer-h8-host-v1")
 def fixture(self):
  e={"cid":"6"*64,"name":"fixture-only","source":{"sha256":"a"*64},"host_sha256":"b"*64,"guest_cpu":2,
     "mounts":{"/flashinfer-results":("/cache/cch/fake",True),"/source":("/source",False)}}
  x={"Id":e["cid"],"Name":"/"+e["name"],"Image":c.IMAGE,"Config":{"Image":c.IMAGE,"Entrypoint":["/bin/bash"],
     "Cmd":["-c","exec /bin/sleep infinity"],"WorkingDir":str(host.ROOT),"Labels":host.labels(e),
     "Env":[k+"="+v for k,v in host.environment().items()]},"HostConfig":{"Privileged":False,"Memory":host.MEM,
     "MemorySwap":host.MEM,"NanoCpus":10**9,"CpusetCpus":"2","NetworkMode":"none","IpcMode":"private","ShmSize":2*1024**3,
     "PidsLimit":512,"CapDrop":["ALL"],"SecurityOpt":["no-new-privileges"],"Devices":[
      {"PathOnHost":h,"PathInContainer":g,"CgroupPermissions":"rwm"} for h,g in host.expected_devices().items()]},
     "Mounts":[{"Type":"bind","Source":s,"Destination":d,"RW":rw} for d,(s,rw) in e["mounts"].items()]}
  return e,x
 def test_pure_inspect_fixture_contract_only(self):
  e,x=self.fixture();host.validate_inspect(x,e);self.assertNotIn("torch",sys.modules)
 def test_protected_device_extra_or_changed_rejected(self):
  for mutate in (lambda x:x["HostConfig"]["Devices"].append({"PathOnHost":"/dev/davinci0","PathInContainer":"/dev/davinci9","CgroupPermissions":"rwm"}),
   lambda x:x["HostConfig"]["Devices"][0].update(PathOnHost="/dev/davinci0")):
   e,x=self.fixture();mutate(x)
   with self.assertRaises(ValueError):host.validate_inspect(x,e)
 def test_full_inspect_identity_budget_mutations_rejected(self):
  mutators=(lambda x:x.update(Id="5"*64),lambda x:x["Config"]["Labels"].update({"model-tuning-lab.owner":"kvbuffer-h8-host-v1"}),
   lambda x:x["HostConfig"].update(Privileged=True),lambda x:x["HostConfig"].update(Memory=9*1024**3),
   lambda x:x["HostConfig"].update(CpusetCpus="0-3"),lambda x:x["HostConfig"].update(DeviceCgroupRules=["c *:* rwm"]),
   lambda x:x["Mounts"][1].update(RW=True),lambda x:x["Config"]["Env"].append("OMP_NUM_THREADS=2"))
  for mutate in mutators:
   e,x=self.fixture();mutate(x)
   with self.subTest(mutate=mutate),self.assertRaises(ValueError):host.validate_inspect(x,e)
 def test_create_resource_args_no_rm_protected_device(self):
  e,x=self.fixture();argv=host.create_argv(e)
  self.assertNotIn("--rm",argv);self.assertEqual(argv[argv.index("--memory")+1],str(8*1024**3))
  self.assertEqual(argv[argv.index("--cpus")+1],"1");self.assertIn("/dev/davinci6:/dev/davinci0:rwm",argv)
  self.assertNotIn("/dev/davinci0:/dev/davinci0:rwm",argv)
 def test_actual_cann_version_metadata_not_path_inference(self):
  self.assertEqual(host.canary_version("version=9.1.0\n"),"9.1.0")
  for text in ("","/usr/local/Ascend/cann-9.1.0","version=8.5.0\n","version=9.1.0-beta.1\n","version=9.1.0\nversion=9.2.0\n"):
   with self.subTest(text=text),self.assertRaises(ValueError):host.canary_version(text)
 def test_cleanup_cannot_extend_fixed_phase(self):
  ctl=object.__new__(host.Controller);ctl.deadline=110.;ctl.cleanup_deadline=None
  with mock.patch.object(host.time,"monotonic",return_value=100.),mock.patch.object(host,"utc",return_value=datetime(2026,10,7,tzinfo=timezone.utc)):
   self.assertEqual(ctl.remaining(cleanup=True,cap=90),10.)
   with self.assertRaises(ValueError):ctl.remaining(cleanup=False)
 def test_frozen_h8_globals_unmodified(self):
  self.assertEqual(host.H.CUTOFF.isoformat(),"2026-10-08T08:29:54+00:00")
  self.assertEqual(host.CUTOFF.isoformat(),"2026-10-09T11:17:31+00:00")
  self.assertNotEqual(host.OWNER,host.H.OWNER);self.assertEqual(len(c.DEPENDENCIES),3)
  self.assertEqual(host.H.FROZEN_SHA,c.DEPENDENCIES[str(host.H.FROZEN)])
 def test_host_modes_remain_default_off_no_device_import(self):
  with mock.patch.object(main,"source_identity",side_effect=AssertionError("source disabled")),contextlib.redirect_stdout(io.StringIO()) as out:
   main.main([])
  self.assertFalse(json.loads(out.getvalue())["default_enabled"]);self.assertNotIn("torch_npu",sys.modules)

class V5ActualAbiSoftwareTests(unittest.TestCase):
 ORIGINAL=Path("/cache/cch/flashinfer-native-abi-v1-20261007-1716-001/report.json")
 ORIGINAL_SHA="1d691e38880779c30804848be1416ec74dfe222384b859a1b2fef5c174250cd7"
 def actual(self):return c.load_ref(c.bound(self.ORIGINAL,self.ORIGINAL_SHA))
 def test_original_failed_cpu_report_is_not_numerical_pass(self):
  r=self.actual();self.assertFalse(r["passed"]);self.assertFalse(r["npu_executed"])
  self.assertEqual(r["schema_failures"],["npu_fused_infer_attention_score.out:missing=['attention_out', 'softmax_lse']"])
  self.assertEqual(r["versions"]["torch_npu"],"2.10.0.post4")
  with self.assertRaises(ValueError):c.validate_no_device_abi(r,{}, {})
 def test_actual_saved_four_schemas_support_new_required_args_not_named_outputs(self):
  r=self.actual()
  for name,overload in native.OPS:
   row=r["actual_exports"][name+"."+overload]
   self.assertGreaterEqual(set(row["arguments"]),native.required_schema(name,overload))
  out=r["actual_exports"]["npu_fused_infer_attention_score.out"]
  self.assertIn("Tensor[] out",out["schema"]);self.assertNotIn("attention_out",out["arguments"])
  self.assertNotIn("softmax_lse",out["arguments"]);self.assertIn("out",out["arguments"])
 def schema_fixture(self,name,overload,change=None):
  # Interface unit fixture only. Not actual Torch dispatcher or a device PASS.
  from types import SimpleNamespace as S
  row=self.actual()["actual_exports"][name+"."+overload]
  names=list(row["arguments"]);types={n:"Tensor" for n in names};types["out"]="List[Tensor]"
  if change:change(names,types)
  class Schema:
   arguments=[S(name=n,type=types[n]) for n in names]
   returns=[S(type=n) for n in row["return_types"]]
   def __str__(self):return row["schema"]
  return Schema()
 def test_interface_checker_accepts_actual_tensor_list_form_unit_only(self):
  for n,o in native.OPS:native.check_schema(n,o,self.schema_fixture(n,o))
  self.assertNotIn("torch",sys.modules)
 def test_named_output_legacy_schema_rejected_unit_only(self):
  def change(names,types):
   names.remove("out");names.extend(("attention_out","softmax_lse"))
   types.update(attention_out="Tensor",softmax_lse="Tensor")
  with self.assertRaisesRegex(ValueError,"Tensor\\[\\] out ABI"):native.check_schema("npu_fused_infer_attention_score","out",self.schema_fixture("npu_fused_infer_attention_score","out",change))
 def test_nonlist_out_rejected_unit_only(self):
  with self.assertRaisesRegex(ValueError,"out must"):
   native.check_schema("npu_fused_infer_attention_score","out",self.schema_fixture("npu_fused_infer_attention_score","out",lambda names,types:types.update(out="Tensor")))
 def test_native_ast_uses_exact_output_list_and_no_legacy_kwargs(self):
  import ast
  tree=ast.parse(Path(native.__file__).read_text())
  run=next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=="run")
  calls=[x for x in ast.walk(run) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=="op"]
  self.assertEqual(len(calls),2)
  for call in calls:
   keys={k.arg:k.value for k in call.keywords if k.arg}
   self.assertIn("workspace",keys);self.assertIsInstance(keys["out"],ast.List);self.assertEqual(len(keys["out"].elts),2)
   self.assertNotIn("attention_out",keys);self.assertNotIn("softmax_lse",keys)
 def test_both_canary_and_matrix_schema_precheck_before_device_init(self):
  import ast
  for module,name in ((main,"run_device"),(host,"inside_canary")):
   tree=ast.parse(Path(module.__file__).read_text())
   fn=next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name==name)
   pre=[x.lineno for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=="verify_preinit"]
   init=[x.lineno for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=="set_device"]
   self.assertEqual(len(pre),1);self.assertEqual(len(init),1);self.assertLess(pre[0],init[0])
 def test_no_device_producer_contains_no_device_init_or_tensor_kernel(self):
  import ast
  tree=ast.parse(Path(main.__file__).read_text())
  fn=next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=="no_device_abi")
  self.assertFalse(any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in
    ("set_device","init","synchronize","device_count","current_device","tensor","empty","zeros") for x in ast.walk(fn)))
 def test_host_no_device_stage_precedes_actual_observed_canary(self):
  source=Path(host.__file__).read_text();start=source.index('  cpu_out=');canary=source.index('  canary_child=ctl.observed_child')
  self.assertLess(start,canary);self.assertIn('_,ndidle=ctl.observe("post-no-device-idle",initial=True)',source[start:canary])
  self.assertIn('"--no-device-abi-ref",ndref["path"]',source[canary:])
 def test_no_device_initialized_api_missing_true_rejects_unit_only(self):
  from types import SimpleNamespace as S
  native.uninitialized(S(npu=S(is_initialized=lambda:False)))
  for npu in (S(),S(is_initialized=lambda:True),S(is_initialized=lambda:None)):
   with self.assertRaises(ValueError):native.uninitialized(S(npu=npu))
 def test_no_device_mode_is_exclusive_default_off(self):
  self.assertTrue(main.parser().parse_args(["--no-device-abi"]).no_device_abi)
  with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
   main.parser().parse_args(["--no-device-abi","--execute"])
 def test_pending_v5_schema_is_not_v3_success(self):
  r=self.actual();r["passed"]=True
  with self.assertRaises(ValueError):c.validate_no_device_abi(r,{}, {})


class V5CPUIsolationSoftwareTests(unittest.TestCase):
 def cpu_fixture(self):
  e,x=HostClosureSoftwareTests().fixture();e["mode"]="cpu";e["name"]="cpu-fixture"
  x["Name"]="/"+e["name"];x["Config"]["Labels"]=host.labels(e);x["HostConfig"]["Devices"]=None
  return e,x
 def test_cpu_create_has_no_device_declarations_and_unique_phase_label(self):
  e,x=self.cpu_fixture();argv=host.create_argv(e)
  self.assertNotIn("--device",argv);self.assertEqual(host.expected_devices("cpu"),{})
  self.assertIn("model-tuning-lab.device-phase=cpu",argv);host.validate_inspect(x,e)
 def test_cpu_inspect_any_physical_or_control_node_rejected(self):
  for name in ("/dev/davinci0","/dev/davinci6","/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc"):
   e,x=self.cpu_fixture();x["HostConfig"]["Devices"]=[{"PathOnHost":name,"PathInContainer":name,"CgroupPermissions":"rwm"}]
   with self.subTest(name=name),self.assertRaises(ValueError):host.validate_inspect(x,e)
 def test_cpu_inspect_privileged_or_device_rules_rejected(self):
  for change in ({"Privileged":True},{"DeviceRequests":[{}]},{"DeviceCgroupRules":["c *:* rwm"]}):
   e,x=self.cpu_fixture();x["HostConfig"].update(change)
   with self.subTest(change=change),self.assertRaises(ValueError):host.validate_inspect(x,e)
 def test_cpu_wrong_phase_label_rejected(self):
  e,x=self.cpu_fixture();x["Config"]["Labels"]["model-tuning-lab.device-phase"]="npu"
  with self.assertRaises(ValueError):host.validate_inspect(x,e)
 def test_actual_node_inventory_required_not_only_initialized_flag(self):
  source=Path(main.__file__).read_text()
  self.assertIn('require(device_nodes==[]',source);self.assertIn('actual_guest_device_nodes_after',source)
  contract=Path(c.__file__).read_text();self.assertIn('r.get("actual_guest_device_nodes_before")==[]',contract)
 def test_both_guests_share_original_deadline_without_reset(self):
  source=Path(host.__file__).read_text()
  self.assertIn('cpu_ctl.created_monotonic=ctl.created_monotonic;cpu_ctl.deadline=ctl.deadline',source)
  self.assertNotIn('ctl.deadline=time.monotonic()',source)
  self.assertLess(source.index('cpu_cleanup=cpu_ctl.cleanup()'),source.index('  ctl.create({},source,files)'))
 def test_cpu_stop_retention_is_required_before_distinct_npu_creation(self):
  source=Path(host.__file__).read_text()
  self.assertIn('cc["stopped"] is True and cc["retained"] is True',source)
  self.assertLess(source.index('cpu_stop_inspect=cc["after_inspect"]'),source.index('  ctl.create({},source,files)'))
 def test_cpu_failure_cleanup_is_independently_retained_no_rm(self):
  source=Path(host.__file__).read_text()
  self.assertIn('if cpu_ctl is not None and cpu_cleanup is None:',source)
  self.assertIn('cpu_ctl.primary=primary',source);self.assertIn('ctl.secondary.extend("CPU: "+s',source)
  self.assertNotIn('DOCKER,"rm"',source)
 def test_cpu_phase_unknown_rejected(self):
  with self.assertRaises(ValueError):host.expected_devices("anything")

if __name__=="__main__":unittest.main(verbosity=2)
