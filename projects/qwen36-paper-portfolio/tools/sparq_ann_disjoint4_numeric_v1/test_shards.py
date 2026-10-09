"""SOFTWARE only: real allocation/header/inspector/cleanup/create/source seams.
No synthetic receipt grants numerical/model/throughput authority; no Torch.
"""
import ast,copy,json,tempfile,types,unittest
from pathlib import Path
from unittest import mock
import shard_contract as sc
import shard_host as host
from shard_consume import header_union
def fixture_reports():
 plan=sc.allocation();reports=[]
 for part in plan["shards"]:
  reports.append(dict(schema=sc.SHARD_SCHEMA,status="shard_passed",shard_id=part["shard_id"],
   physical=part["physical"],logical=0,allocation_sha256=sc.digest(plan),assigned_cases=part["assigned_cases"],
   completed_cases=part["assigned_count"],completed_steps=part["assigned_steps"],
   cases=[{k:row[k] for k in ("batch","mode","reallocation","trial")} for row in part["assigned_cases"]]))
 return plan,reports
class Coverage(unittest.TestCase):
 def test_exact_128_20480_disjoint(self):
  p=sc.allocation();sc.validate_allocation(p)
  keys=[sc.coordinate(r) for part in p["shards"] for r in part["assigned_cases"]]
  self.assertEqual((len(keys),len(set(keys))),(128,128))
  self.assertEqual(sum(v["assigned_steps"] for v in p["shards"]),20480)
  self.assertEqual([v["assigned_count"] for v in p["shards"]],[32]*4)
 def test_true_B1_to16_two_per_shard(self):
  for p in sc.allocation()["shards"]:
   self.assertEqual({b:sum(r["batch"]==b for r in p["assigned_cases"]) for b in range(1,17)},{b:2 for b in range(1,17)})
 def test_original_global_seed(self):
  for p in sc.allocation()["shards"]:
   for r in p["assigned_cases"]:self.assertEqual(r["seed"],49585+r["batch"]+100*r["trial"])
 def test_cost_is_explicit_not_measured_time(self):
  p=sc.allocation();self.assertFalse(p["cost_model"]["measured_elapsed"])
  totals=[v["estimated_token_work"] for v in p["shards"]]
  self.assertEqual(min(totals),max(totals))
  self.assertEqual(p,sc.allocation())
 def test_omission_rejected(self):
  p=sc.allocation();p["shards"][0]["assigned_cases"].pop()
  with self.assertRaises(ValueError):sc.validate_allocation(p)
 def test_overlap_rejected(self):
  p=sc.allocation();p["shards"][0]["assigned_cases"][0]=p["shards"][1]["assigned_cases"][0]
  with self.assertRaises(ValueError):sc.validate_allocation(p)
 def test_seed_drift_rejected(self):
  r=sc.row((4,"graph",True,2));r["seed"]+=1
  with self.assertRaises(ValueError):sc.coordinate(r)
 def test_card_map_drift_rejected(self):
  p=sc.allocation();p["shards"][0]["physical"]=0
  with self.assertRaises(ValueError):sc.validate_allocation(p)
 def test_original128_label_on_subset_rejected(self):
  p,rs=fixture_reports();rs[0]["schema"]="sparq.token-numeric/v6-author-ann-FP32-compensation"
  with self.assertRaises(ValueError):sc.check_headers(rs[0],p,0)
 def test_header_global_union(self):
  p,rs=fixture_reports();self.assertEqual(header_union(rs,p),dict(cases=128,changing_feedback_steps=20480,shards=4))
 def test_partial_not_promoted(self):
  p,rs=fixture_reports()
  with self.assertRaises(ValueError):header_union(rs[:3],p)
 def test_duplicate_shard_not_promoted(self):
  p,rs=fixture_reports();rs[3]=copy.deepcopy(rs[0])
  with self.assertRaises(ValueError):header_union(rs,p)
 def test_bad_step_total_rejected(self):
  p,rs=fixture_reports();rs[0]["completed_steps"]-=1
  with self.assertRaises(ValueError):header_union(rs,p)
 def test_reordered_header_rejected(self):
  p,rs=fixture_reports();rs[0]["cases"].reverse()
  with self.assertRaises(ValueError):header_union(rs,p)
class Resources(unittest.TestCase):
 def views(self,quota=7):
  q=[dict(key="/actual-shared",capacity=quota)]
  return dict(effective_capacity=1,effective_cpus=[0],quota_ancestors=q),dict(effective_capacity=7,effective_cpus=list(range(8)),quota_ancestors=q)
 def test_seven_actual_slots(self):
  a,b=self.views();p=sc.joint_budget(a,b)
  self.assertEqual((p["host_cpu"],p["guest_cpus"],p["reserve_cpus"]),(0,[1,2,3,4],[5,6]))
 def test_shared_quota6_rejects(self):
  a,b=self.views(6)
  with self.assertRaises(ValueError):sc.joint_budget(a,b)
 def test_daemon_effective_not_inventory(self):
  a,b=self.views();b["effective_capacity"]=5
  with self.assertRaises(ValueError):sc.joint_budget(a,b)
 def test_distinct_cpuset_not_cpu_count(self):
  a,b=self.views();b["effective_cpus"]=[0,1,2,3,4,5]
  with self.assertRaises(ValueError):sc.joint_budget(a,b)
class SourceSeams(unittest.TestCase):
 def native(self):
  c,source,files=sc.native();self.assertEqual(source,sc.BASE_SOURCE)
  self.assertEqual(c.sha(Path(source["path"]).parent/"matrix.py"),sc.ORIGINAL_MATRIX_SHA)
  return c,__import__("host")
 def test_exact_current_math_substrate(self):
  c,_=self.native();source,files=c.source_identity(Path(sc.BASE_SOURCE["path"]).parent,Path(sc.BASE_SOURCE["path"]),sc.BASE_SOURCE["sha256"])
  self.assertEqual((len(files),source),(31,sc.BASE_SOURCE))
 def test_real_producer_calls_frozen_run_case_no_selector_clone(self):
  tree=ast.parse((sc.ROOT/"shard_numeric.py").read_text())
  imports=[n for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module=="matrix"]
  self.assertEqual([[v.name for v in n.names] for n in imports],[["run_case"]])
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="run_case"]
  self.assertEqual(len(calls),1);self.assertEqual(len(calls[0].args),9)
  self.assertFalse(any(isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ("support","source_legality","conditional_fp64") for n in ast.walk(tree)))
 def test_one_global_deadline_no_reset_in_producer(self):
  text=(sc.ROOT/"shard_numeric.py").read_text()
  self.assertIn('deadline=proof["common_deadline_monotonic"]-sc.CLEANUP_SECONDS',text)
  self.assertNotIn('deadline=time.monotonic()+',text)
 def test_exact_expanded_argv_proof_and_shard_scope(self):
  c,_=self.native();p=dict(path="/cache/cch/owned/proof.json",sha256="f"*64)
  a=dict(path="/cache/cch/owned/ALLOCATION.json",sha256="a"*64)
  own=dict(path=str(sc.ROOT/"SOURCE_MANIFEST.json"),sha256="b"*64)
  v=sc.shard_argv(Path("/sparq-results/gate"),p,a,own,2)
  self.assertEqual(v[:4],[c.PY,"-B",str(sc.ROOT/"shard_numeric.py"),"--execute"])
  self.assertEqual(v[v.index("--shard-id")+1],"2")
  self.assertNotIn("--batches",v)
 def test_primitive_noPA_not_model_scope(self):
  text=(sc.ROOT/"shard_rows.py").read_text()
  self.assertIn('row["native_PA_executed"] is False',text)
  self.assertIn('numerical_component_checked":False',text)
  self.assertIn('metrics(row["author_conditional_fp64_metric"],b)',text)
class Isolation(unittest.TestCase):
 def setup(self,card=4):
  _,nh=SourceSeams().native()
  e=dict(cid="a"*64,name="sparq-disjoint-software-only",image=nh.IMAGE,owner=sc.OWNER,source=sc.BASE_SOURCE,
   host_sha256="b"*64,numeric_sha256="c"*64,guest_cpu=1,mounts={"/sparq-results":("/cache/cch/owned-output",True)},
   physical=card,shard_id=card-4,packet_source=dict(path="/exact/source",sha256="d"*64),mode="npu")
  x=dict(Id=e["cid"],Name="/"+e["name"],Image=nh.IMAGE,Config=dict(Image=nh.IMAGE,Entrypoint=["/bin/bash"],
   Cmd=["-c","exec /bin/sleep infinity"],WorkingDir=str(nh.ROOT),Labels=host.card_labels(e,nh),
   Env=[k+"="+v for k,v in nh.environment().items()]),
   HostConfig=dict(Privileged=False,Memory=sc.GUEST_BYTES,MemorySwap=sc.GUEST_BYTES,NanoCpus=10**9,
    CpusetCpus="1",NetworkMode="none",IpcMode="private",ShmSize=2*1024**3,PidsLimit=512,
    DeviceRequests=None,DeviceCgroupRules=None,CapDrop=["ALL"],SecurityOpt=["no-new-privileges"],
    Devices=[dict(PathOnHost=h,PathInContainer=d,CgroupPermissions="rwm") for h,d in host.devices(card).items()]),
   Mounts=[dict(Destination="/sparq-results",Source="/cache/cch/owned-output",RW=True,Type="bind")])
  return nh,e,x
 def test_actual_inspect_all_four_maps(self):
  for card in sc.CARDS:
   nh,e,x=self.setup(card);host.inspect_card(x,e,nh)
 def test_own0_rejected(self):
  nh,e,x=self.setup();x["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci0"
  with self.assertRaises(ValueError):host.inspect_card(x,e,nh)
 def test_foreign_owner_rejected(self):
  nh,e,x=self.setup();x["Config"]["Labels"]["model-tuning-lab.owner"]="foreign"
  with self.assertRaises(ValueError):host.inspect_card(x,e,nh)
 def test_declared_budget_not_actual_rejected(self):
  nh,e,x=self.setup();x["HostConfig"]["NanoCpus"]=2*10**9
  with self.assertRaises(ValueError):host.inspect_card(x,e,nh)
 def test_immutable_mount_rw_rejected(self):
  nh,e,x=self.setup();x["Mounts"][0]["RW"]=False
  with self.assertRaises(ValueError):host.inspect_card(x,e,nh)
 def test_real_creation_argv_exact_one_mapping(self):
  nh,e,x=self.setup(7);argv=host.card_create_argv(e,nh)
  self.assertIn("/dev/davinci7:/dev/davinci0:rwm",argv)
  self.assertNotIn("/dev/davinci6:/dev/davinci0:rwm",argv)
  self.assertEqual(argv.count("model-tuning-lab.owner="+sc.OWNER),1)
 def test_cleanup_actual_method_normal_admission_not_called(self):
  _,nh=SourceSeams().native();c=types.SimpleNamespace(write_new=lambda p,v:v)
  co=types.SimpleNamespace(nh=nh,c=c,cleanup_deadline=100,protected_check=lambda v:{"own_on_protected":False})
  _,Card=host.controller_classes(co);obj=Card.__new__(Card)
  obj.cid="a"*64;obj.primary=None;obj.secondary=[];obj.card=4;obj.out=Path("/cache/cch/owned");obj.child=None
  obj.h=types.SimpleNamespace(protected=lambda s:[],idle_one=lambda s,n:None)
  # Transparent external IO spies only; execute real Card.cleanup body.
  state=dict(State=dict(Running=False,Pid=0,OOMKilled=False),ExecIDs=None)
  obj.inspect=lambda cleanup=False:(state,{"path":"/exact/inspect","sha256":"f"*64}) if cleanup else (_ for _ in ()).throw(AssertionError("normal inspect"))
  calls=[]
  def call(label,argv,cap=30,cleanup=False):
   self.assertTrue(cleanup);calls.append((label,argv))
   return {"stdout":"actual-release-software-spy"},{"path":"/exact/"+label,"sha256":"e"*64}
  obj.call=call
  result=obj.cleanup()
  self.assertTrue(result["stopped"]);self.assertTrue(result["retained"]);self.assertEqual(result["errors"],[])
  self.assertEqual(calls[0],("stop-retain",["/usr/bin/docker","stop","--time","15","a"*64]))
 def test_cleanup_first_inspect_failure_never_stops(self):
  _,nh=SourceSeams().native();c=types.SimpleNamespace(write_new=lambda p,v:v)
  co=types.SimpleNamespace(nh=nh,c=c,cleanup_deadline=100,protected_check=lambda v:None)
  _,Card=host.controller_classes(co);obj=Card.__new__(Card)
  obj.cid="a"*64;obj.primary=None;obj.secondary=[];obj.card=4;obj.out=Path("/cache/cch/owned")
  obj.inspect=lambda cleanup=False:(_ for _ in ()).throw(ValueError("foreign exact inspect"))
  obj.call=lambda *a,**k:(_ for _ in ()).throw(AssertionError("must not stop before ownership"))
  result=obj.cleanup();self.assertFalse(result["stopped"]);self.assertTrue(result["errors"])
class OriginalFailure(unittest.TestCase):
 def fixture(self):
  c,_=SourceSeams().native()
  p=Path(sc.BASE_SOURCE["path"]).parent/"original_operation_get_ma0e85.json";v=json.loads(p.read_bytes())
  out=v.get("structuredContent",v);op=out["operation"];rec=op["result"]["record"];rec["exitCode"]=1
  # Change ONLY fixture copies; never write original source or borrow a PASS.
  for b in v.get("content",[]):
   if b.get("type")=="text":b["text"]=json.dumps(out)
  return v
 def test_actual_whole_operation_shape_failure_reader(self):
  v=self.fixture();r=host.extract_original(v,"lgw_a6109c51076a4a2c9d2674ca5a8704a0");self.assertEqual(r["exitCode"],1)
 def test_actual_failed_exit_code_annotation_is_not_transport_error(self):
  v=self.fixture();out=v.get("structuredContent",v);out["operation"]["result"]["record"]["error"]="exit code"
  for b in v.get("content",[]):
   if b.get("type")=="text":b["text"]=json.dumps(out)
  self.assertEqual(host.extract_original(v,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")["exitCode"],1)
 def test_transport_error_never_grants_predecessor_authority(self):
  v=self.fixture();out=v.get("structuredContent",v);out["operation"]["result"]["record"]["error"]="transport closed"
  for b in v.get("content",[]):
   if b.get("type")=="text":b["text"]=json.dumps(out)
  with self.assertRaises(ValueError):host.extract_original(v,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 def test_unknown_or_notfound_rejected(self):
  v=self.fixture();out=v.get("structuredContent",v);out["operation"]["result"].pop("record")
  for b in v.get("content",[]):
   if b.get("type")=="text":b["text"]=json.dumps(out)
  with self.assertRaises(ValueError):host.extract_original(v,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 def test_truncation_rejected(self):
  v=self.fixture();v["stdoutTruncated"]=True
  with self.assertRaises(ValueError):host.extract_original(v,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
class ArtifactMountClosure(unittest.TestCase):
 ROOT=Path(sc.BASE_SOURCE["path"]).parent
 ABI={"path":str(ROOT/"receipt.py"),"sha256":"689f7c4fab787af26a09d75fb193bde952790ebfb6931c9aba52cb9a7f3be9e7"}
 def mounts(self):
  _,nh=SourceSeams().native()
  ctl=types.SimpleNamespace(out=self.ROOT/"sparq_token_v4")
  co=types.SimpleNamespace(out=self.ROOT,allocation_ref={"path":str(self.ROOT/"SOURCE_MANIFEST.json")},
   packet_source={"path":str(sc.ROOT/"SOURCE_MANIFEST.json")},manifest={"native_external_pins":{}})
  return host.closure_mounts(ctl,co,nh)
 def test_common_tree_covers_other_phase_and_future_proofs(self):
  mounts=self.mounts();self.assertEqual(mounts[str(self.ROOT)],(str(self.ROOT),False))
  for rel in ("cpu-preflight/ABI.json","cpu-preflight/cleanup.json","PLAN.json","shard-3-physical7/proof.json"):
   self.assertIn(self.ROOT,(self.ROOT/rel).parents)
  self.assertNotIn(str(self.ROOT/"sparq_token_v4"),mounts)
 def test_only_own_alias_writable_no_broad_cache_mount(self):
  mounts=self.mounts()
  self.assertEqual([(d,s) for d,(s,rw) in mounts.items() if rw],
   [("/sparq-results",str(self.ROOT/"sparq_token_v4"))])
  self.assertNotIn("/cache/cch",mounts)
 def test_real_ref_hash_reader_with_mountinfo_io_spy_only(self):
  row="123 1 0:1 / "+str(self.ROOT)+" ro,relatime - ext4 /exact ro\n"
  with mock.patch.object(Path,"read_text",return_value=row):
   result=host.artifact_audit(self.ROOT,[self.ABI])
  self.assertEqual(result["refs"],[self.ABI]);self.assertFalse(result["npu_executed"])
 def test_rw_common_root_rejected_before_file_read(self):
  row="123 1 0:1 / "+str(self.ROOT)+" rw,relatime - ext4 /exact rw\n"
  with mock.patch.object(Path,"read_text",return_value=row):
   with self.assertRaises(ValueError):host.artifact_audit(self.ROOT,[self.ABI])
 def test_actual_missing_ref_and_changed_hash_rejected(self):
  row="123 1 0:1 / "+str(self.ROOT)+" ro,relatime - ext4 /exact ro\n"
  with mock.patch.object(Path,"read_text",return_value=row):
   with self.assertRaises(ValueError):host.artifact_audit(self.ROOT,[dict(self.ABI,sha256="0"*64)])
   with self.assertRaises(ValueError):host.artifact_audit(self.ROOT,[dict(self.ABI,path=str(self.ROOT/"NEVER_CREATED.json"))])
class FirstFaultCapture(unittest.TestCase):
 """Real canonical helper/receipt IO; metadata only, never NPU acceptance."""
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix="sparq-canonical-first-fault-")
  self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.c,_=SourceSeams().native()
  self.co=types.SimpleNamespace(out=self.root,packet_source={"path":"/fixture/packet.json","sha256":"a"*64},
   source=sc.BASE_SOURCE,secondary=[])
 def missing(self):
  try:(self.root/"absent"/"actual-missing.txt").read_text()
  except FileNotFoundError as error:return error
  self.fail("actual missing file must fail")
 def capture(self,error):
  ref=host.record_first_fault(self.co,self.c,error)
  return ref,self.c.load(ref)
 def actual_handler(self,error):
  outer=next(n for n in next(n for n in ast.parse((sc.ROOT/"shard_host.py").read_text()).body
   if isinstance(n,ast.FunctionDef) and n.name=="execute").body if isinstance(n,ast.Try))
  handler=next(n for n in outer.handlers if n.name=="error")
  ns=dict(error=error,co=self.co,c=self.c,record_first_fault=host.record_first_fault)
  exec(compile(ast.Module(body=handler.body,type_ignores=[]),"<actual-canonical-first-catch>","exec"),ns)
  return outer,ns
 def test_actual_missing_filename_errno_and_trace(self):
  error=self.missing();ref,row=self.capture(error)
  self.assertEqual((row["errno"],row["filename"],row["message"]),(2,error.filename,str(error)))
  self.assertEqual(row["primary_error"],repr(error));self.assertIn("FileNotFoundError",row["traceback"])
  self.assertIn("actual-missing.txt",row["traceback"]);self.assertFalse(row["traceback_truncated"])
 def test_actual_atomic_receipt_and_source_pid_binding(self):
  ref,row=self.capture(self.missing())
  self.assertEqual(ref["sha256"],self.c.sha(self.root/"FIRST_FAULT.json"))
  self.assertEqual(row["packet_source"],self.co.packet_source);self.assertEqual(row["native_source"],sc.BASE_SOURCE)
  self.assertEqual(row["host_pid"],host.os.getpid());self.assertGreater(row["observed_unix_ns"],0)
 def test_actual_catch_preserves_primary_before_cleanup(self):
  error=self.missing();outer,ns=self.actual_handler(error)
  self.assertIs(ns["primary"],error);self.assertIsNotNone(ns["first_fault"])
  self.assertEqual([n.targets[0].id for n in next(n for n in outer.handlers if n.name=="error").body
   if isinstance(n,ast.Assign)],["primary","first_fault"])
  self.assertTrue(outer.finalbody)
  self.assertIn("if primary is not None:raise primary",(sc.ROOT/"shard_host.py").read_text())
 def test_real_existing_fault_write_fail_preserves_primary(self):
  (self.root/"FIRST_FAULT.json").write_bytes(b"retain original fault")
  error=self.missing();_,ns=self.actual_handler(error)
  self.assertIs(ns["primary"],error);self.assertIsNone(ns["first_fault"])
  self.assertEqual((self.root/"FIRST_FAULT.json").read_bytes(),b"retain original fault")
  self.assertEqual(len(self.co.secondary),1);self.assertIn("FileExistsError",self.co.secondary[0])
 def test_real_missing_parent_capture_failure_is_secondary(self):
  self.co.out=self.root/"missing-parent";error=self.missing()
  _,ns=self.actual_handler(error);self.assertIs(ns["primary"],error);self.assertIsNone(ns["first_fault"])
  self.assertEqual(len(self.co.secondary),1);self.assertIn("first-fault capture:",self.co.secondary[0])
 def test_generic_error_does_not_invent_filename(self):
  _,row=self.capture(ValueError("explicit primary"))
  self.assertIsNone(row["errno"]);self.assertIsNone(row["filename"]);self.assertIsNone(row["filename2"])
  self.assertEqual(row["exception_type"],"builtins.ValueError")
 def test_second_filename_and_bytes_roundtrip(self):
  error=FileNotFoundError(2,"rename-shaped",b"/missing-\xff",None,b"/destination-\xfe")
  _,row=self.capture(error)
  self.assertEqual(host.os.fsencode(row["filename"]),error.filename)
  self.assertEqual(host.os.fsencode(row["filename2"]),error.filename2)
 def test_trace_bound_is_explicit(self):
  _,row=self.capture(ValueError("z"*70000))
  self.assertTrue(row["traceback_truncated"]);self.assertEqual(len(row["traceback"]),65536)
 def test_exception_cause_chain_retained(self):
  try:
   try:raise ValueError("independent original cause")
   except ValueError as cause:raise FileNotFoundError(2,"outer error","/missing-chain") from cause
  except FileNotFoundError as error:
   _,row=self.capture(error)
   self.assertIn("independent original cause",row["traceback"]);self.assertIn("direct cause",row["traceback"])

class OwnedExitLifecycle(unittest.TestCase):
 """Real Linux short-lived Popen + raw /proc; Docker/SMI IO spies never grant NPU authority."""
 BODY="import sys; print('ready',flush=True); sys.stdin.read(1)"
 def spawn(self,body=None):
  import subprocess,sys
  argv=[sys.executable,"-B","-c",body or self.BODY]
  child=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  self.addCleanup(self.reap,child);self.assertEqual(child.stdout.readline().strip(),"ready")
  ctl=types.SimpleNamespace(cid="/",child=child,child_label="canary",
   child_started=host.utc(),expected_child_argv=argv,known_processes={},end=host.time.monotonic()+10)
  # '/' is transparent container-IO fixture association only, never a Docker CID.
  before=host.proc_snapshot(child.pid);frames=host.proc_frames(before)
  proof=dict(pid=child.pid,start_ticks=frames[-1]["start_ticks"],argv=argv,
   cgroup=before["reads"]["cgroup"]["text"],started_utc=ctl.child_started.isoformat())
  host.remember_owned(ctl,proof,dict(path="/software-only/prior-live",sha256="a"*64))
  return ctl,before,proof
 def reap(self,child):
  if child.poll() is None:child.terminate()
  child.wait(timeout=3)
  for value in (child.stdin,child.stdout,child.stderr):
   if value is not None and not value.closed:value.close()
 def release(self,ctl,reap=True):
  ctl.child.stdin.write("x");ctl.child.stdin.flush()
  if reap:ctl.child.wait(timeout=3)
 def test_real_short_popen_observed_Z_with_exact_same_start(self):
  ctl,before,_=self.spawn();self.release(ctl,False);end=host.time.monotonic()+3
  while True:
   after=host.proc_snapshot(ctl.child.pid);frames=host.proc_frames(after)
   if frames and frames[-1]["state"]=="Z":break
   self.assertLess(host.time.monotonic(),end);host.time.sleep(.005)
  result=host.completed_owned_exit(ctl,ctl.child.pid,before,after)
  self.assertEqual(result["terminal_state"],"Z");self.assertFalse(result["numerical_authority"])
 def test_real_short_popen_absence_after_reap(self):
  ctl,before,_=self.spawn();self.release(ctl)
  result=host.completed_owned_exit(ctl,ctl.child.pid,before,host.proc_snapshot(ctl.child.pid))
  self.assertEqual((result["terminal_state"],result["child_returncode"]),("absent",0))
 def test_live_empty_argv_and_root_cgroup_never_qualifies(self):
  ctl,before,_=self.spawn();after=host.proc_snapshot(ctl.child.pid)
  after["reads"]["cmdline"]=dict(status="ok",hex="");after["reads"]["cgroup"]=dict(status="ok",text="0::/\n")
  with self.assertRaises(ValueError):host.completed_owned_exit(ctl,ctl.child.pid,before,after)
 def test_unknown_absent_pid_never_qualifies(self):
  ctl,before,_=self.spawn();ctl.known_processes={};self.release(ctl)
  with self.assertRaises(ValueError):host.completed_owned_exit(ctl,ctl.child.pid,before,host.proc_snapshot(ctl.child.pid))
 def test_pid_reuse_start_mismatch_rejected(self):
  ctl,before,_=self.spawn();self.release(ctl);altered=copy.deepcopy(before)
  for key in ("stat_before","stat_after"):
   row=altered["reads"][key];text=row["text"];end=text.rfind(")");fields=text[end+2:].split()
   fields[19]=str(int(fields[19])+1);row["text"]=text[:end+2]+" ".join(fields)+"\n"
  with self.assertRaises(ValueError):host.completed_owned_exit(ctl,ctl.child.pid,altered,host.proc_snapshot(ctl.child.pid))
 def test_permission_error_not_disappearance(self):
  ctl,before,_=self.spawn();self.release(ctl);after=host.proc_snapshot(ctl.child.pid)
  after["reads"]["cmdline"]=dict(status="error",exception_type="PermissionError",errno=13,message="actual denial fixture")
  with self.assertRaises(ValueError):host.completed_owned_exit(ctl,ctl.child.pid,before,after)
 def test_phase_identity_cannot_borrow_canary(self):
  ctl,before,_=self.spawn();self.release(ctl);ctl.child_label="matrix"
  with self.assertRaises(ValueError):host.completed_owned_exit(ctl,ctl.child.pid,before,host.proc_snapshot(ctl.child.pid))
 def test_different_popen_object_cannot_borrow_pid(self):
  ctl,before,_=self.spawn();self.release(ctl);after=host.proc_snapshot(ctl.child.pid);pid=ctl.child.pid
  ctl.child=types.SimpleNamespace(pid=pid,poll=lambda:0,returncode=0)
  with self.assertRaises(ValueError):host.completed_owned_exit(ctl,pid,before,after)
 def test_malformed_stat_fails_closed(self):
  ctl,before,_=self.spawn();before["reads"]["stat_before"]=dict(status="ok",text="invalid original stat")
  with self.assertRaises(ValueError):host.proc_frames(before)
 def joint(self,ctl,proof):
  from datetime import timedelta
  records={}
  def write(path,value):
   ref=dict(path=str(path),sha256=host.hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest())
   records[ref["path"]]=copy.deepcopy(value);return ref
  co=host.Joint.__new__(host.Joint);co.out=Path("/software-only");co.cards=[ctl];co.deadline=host.time.monotonic()+100
  co.c=types.SimpleNamespace(write_new=write);co.nh=types.SimpleNamespace(H=types.SimpleNamespace(started=lambda value:value,timedelta=timedelta))
  co.protected_check=lambda value:{"own_on_protected":False};co.resources=lambda initial=False:{}
  ctl.card=4;ctl.canary_proofs=[];ctl.gate_proofs=[]
  reader=lambda pid:dict(proof) if ctl.child.poll() is None else dict(proof,argv=[],cgroup="0::/")
  ctl.h=types.SimpleNamespace(protected=lambda text:[],legacy=lambda:types.SimpleNamespace(process_rows=lambda text:[(4,0,ctl.child.pid)]),
   idle_one=lambda text,card:None,gate_process=lambda pid:reader(pid))
  def call(label,argv):
   return dict(stdout="software-only SMI fixture" if label=="joint-smi" else "",observed_utc=host.utc().isoformat()),dict(path="/software-only/"+label,sha256="b"*64)
  ctl.call=call
  return co,records
 def test_real_observe_keeps_prior_live_and_accepts_completed_exit_only(self):
  ctl,before,proof=self.spawn();ctl.known_processes={};co,records=self.joint(ctl,proof)
  with mock.patch.object(host,"holders",return_value=[]):
   co.observe(ctl,"software-live");self.release(ctl);co.observe(ctl,"software-exit")
  self.assertEqual(len(ctl.canary_proofs),1)
  obs=[v for v in records.values() if "owned_exit_transitions" in v]
  self.assertEqual(len(obs[-1]["owned_exit_transitions"]),1)
  self.assertFalse(obs[-1]["owned_exit_transitions"][0]["numerical_authority"])
  self.assertTrue(any("snapshot_after" in v for v in records.values()))
 def test_real_observe_unknown_exit_still_refuses(self):
  ctl,before,proof=self.spawn();ctl.known_processes={};co,records=self.joint(ctl,proof);self.release(ctl)
  with mock.patch.object(host,"holders",return_value=[]):
   with self.assertRaises(ValueError):co.observe(ctl,"unknown-exit")
  self.assertEqual(ctl.canary_proofs,[]);self.assertTrue(any("snapshot_after" in v for v in records.values()))
 def test_real_observe_foreign_live_still_refuses(self):
  ctl,before,proof=self.spawn();ctl.known_processes={};co,records=self.joint(ctl,dict(proof,cgroup="FOREIGN"))
  with mock.patch.object(host,"holders",return_value=[]):
   with self.assertRaises(ValueError):co.observe(ctl,"foreign-live")
  self.assertEqual(ctl.canary_proofs,[])
 def test_actual_begin_resets_registry_before_new_popen(self):
  tree=ast.parse((sc.ROOT/"shard_host.py").read_text())
  begin=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="begin")
  reset=next(i for i,n in enumerate(begin.body) if isinstance(n,ast.Assign) and
   isinstance(n.targets[0],ast.Attribute) and n.targets[0].attr=="known_processes")
  creation=next(i for i,n in enumerate(begin.body) if isinstance(n,ast.Assign) and
   isinstance(n.targets[0],ast.Attribute) and n.targets[0].attr=="child")
  self.assertLess(reset,creation)
 def test_completed_nonzero_child_not_promoted_by_transition(self):
  import io
  ctl,before,proof=self.spawn(self.BODY+"; sys.exit(1)");self.release(ctl)
  exit_row=host.completed_owned_exit(ctl,ctl.child.pid,before,host.proc_snapshot(ctl.child.pid))
  self.assertEqual(exit_row["child_returncode"],1);self.assertFalse(exit_row["numerical_authority"])
  _,nh=SourceSeams().native();receipts=[]
  c=types.SimpleNamespace(write_new=lambda p,v:receipts.append(v) or v,bound=lambda p,h:dict(path=str(p),sha256=h),sha=lambda p:"f"*64)
  _,Card=host.controller_classes(types.SimpleNamespace(nh=nh,c=c))
  obj=Card.__new__(Card);obj.child=ctl.child;obj.child_label="canary";obj.sf=io.StringIO();obj.ef=io.StringIO()
  obj.canary_proofs=[proof];obj.gate_proofs=[];obj.out=Path("/software-only");obj.child_request=["software-only"]
  obj.expected_child_argv=ctl.expected_child_argv;obj.child_started=ctl.child_started
  obj.wrapper=lambda argv:argv;obj.so=Path("/software-only/stdout");obj.se=Path("/software-only/stderr")
  with self.assertRaises(ValueError):obj.finish()
  self.assertEqual(receipts[-1]["primary_error"],"actual child exit1")

if __name__=="__main__":unittest.main()
