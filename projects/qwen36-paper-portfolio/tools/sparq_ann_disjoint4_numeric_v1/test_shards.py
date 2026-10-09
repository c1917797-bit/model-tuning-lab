"""SOFTWARE only: real allocation/header/inspector/cleanup/create/source seams.
No synthetic receipt grants numerical/model/throughput authority; no Torch.
"""
import ast,copy,json,types,unittest
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
 def test_unknown_or_notfound_rejected(self):
  v=self.fixture();out=v.get("structuredContent",v);out["operation"]["result"].pop("record")
  for b in v.get("content",[]):
   if b.get("type")=="text":b["text"]=json.dumps(out)
  with self.assertRaises(ValueError):host.extract_original(v,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 def test_truncation_rejected(self):
  v=self.fixture();v["stdoutTruncated"]=True
  with self.assertRaises(ValueError):host.extract_original(v,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
if __name__=="__main__":unittest.main()
