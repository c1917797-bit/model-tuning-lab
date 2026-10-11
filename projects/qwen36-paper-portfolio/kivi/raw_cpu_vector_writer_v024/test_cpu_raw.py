"""Local stdlib fixtures; no remote process/device/concurrency PASS."""
import ast,copy,hashlib,importlib.util,json,os,re,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import cpu_raw_resources as j
PRODUCER_ARCHIVE=None
BASE_WHOLE=None
REVIEWED_DEPS=None
PEER_ARCHIVE=None
PROVENANCE_ARCHIVE=None
def view(pid,cpus,cap=16):
 return dict(process=dict(pid=pid,start_ticks=pid+100,cgroup="/actual/"+str(pid)),effective_cpus=cpus,
  effective_capacity=min(len(cpus),cap),quota_ancestors=[dict(key="root",capacity=16),dict(key="leaf:"+str(pid),capacity=cap)])
def mem(pid,leaf,limit=None,used=0):
 return dict(process=view(pid,[])["process"],ancestors=[dict(key=leaf,limit=limit,used=used),
  dict(key="root",limit=160*j.GIB,used=40*j.GIB)])
def fixture():
 pa=dict(total=7,host=1,guest=4,reserve=2,host_cpu=0,guest_cpus=[1,2,3,4],reserve_cpus=[5,6])
 h=view(10,[7]);d=view(20,list(range(16)));ph=view(30,[0]);pg=view(40,[1,2,3,4],4)
 x=dict(schema=j.SCHEMA,host_cpu=h,daemon_cpu=d,peer_host_cpu=ph,peer_guest_cpu=pg,peer_allocation=pa,
  host_memory=mem(10,"host"),daemon_memory=mem(20,"daemon"),peer_host_memory=mem(30,"peerhost"),
  peer_guest_memory=mem(40,"peerguest",64*j.GIB,32*j.GIB),memory=dict(MemAvailable=100*j.GIB,SwapTotal=0,SwapFree=0),
  disk_free_bytes=400*j.GIB,output_bytes=1024,output_allowance_bytes=j.WORKSPACE,
  aggregate_rss_kib=100,host_peak_rss_kib=60,child_peak_rss_kib=40,engine_NCPU=16)
 x["peer"]=dict(state="running",plan={},owned={"cid":"b"*64},inspect={},peer_host_cpu=ph,peer_guest_cpu=pg,
  peer_allocation=pa,peer_host_memory=x["peer_host_memory"],peer_guest_memory=x["peer_guest_memory"])
 x["cpu_allocation"]=j.allocate(h,d,x["peer"])
 x["joint_memory"]=j.memory_budget(x["host_memory"],x["daemon_memory"],x["peer"])
 return x
class Budget(unittest.TestCase):
 def test_disjoint_host1_guest1_and_peer7(self):
  x=fixture();a=j.admit(x);self.assertEqual((a["host_cpu"],a["guest_cpus"],a["total_cpu_budget"]),(7,[8],9))
 def test_common7_queues_without_device_lease(self):
  x=fixture()
  for k in("host_cpu","daemon_cpu","peer_host_cpu","peer_guest_cpu"):x[k]["quota_ancestors"][0]["capacity"]=7
  with self.assertRaisesRegex(ValueError,"joint finite"):j.admit(x)
 def test_peer_reserve_never_borrowed(self):
  x=fixture();x["host_cpu"]["effective_cpus"]=[5];x["host_cpu"]["effective_capacity"]=1
  with self.assertRaisesRegex(ValueError,"disjoint raw host"):j.admit(x)
 def test_no_guest_slot_queues(self):
  x=fixture();x["daemon_cpu"]["effective_cpus"]=list(range(8))
  with self.assertRaisesRegex(ValueError,"disjoint raw guest"):j.admit(x)
 def test_joint_ram_short_queues(self):
  x=fixture();x["memory"]["MemAvailable"]=j.GIB
  with self.assertRaisesRegex(ValueError,"joint ordinary RAM"):j.admit(x)
 def test_joint_ancestor_short_queues(self):
  x=fixture();x["daemon_memory"]["ancestors"][-1]["limit"]=41*j.GIB
  with self.assertRaisesRegex(ValueError,"joint cgroup"):j.admit(x)
 def test_resident_peer_not_double_charged(self):
  x=fixture();self.assertEqual(x["joint_memory"]["ordinary_undrawn_floor_bytes"],57*j.GIB)
  self.assertEqual(x["joint_memory"]["full_declared_ceiling_bytes"],89*j.GIB)
 def test_raw_residency_not_double_charged(self):
  x=fixture();x["own_guest_memory"]=mem(50,"rawguest",8*j.GIB,4*j.GIB)
  x["joint_memory"]=j.memory_budget(x["host_memory"],x["daemon_memory"],x["peer"],x["own_guest_memory"])
  self.assertEqual(x["joint_memory"]["ordinary_undrawn_floor_bytes"],53*j.GIB);j.admit(x)
 def test_wrong_guest_limit_rejected(self):
  x=fixture();x["peer_guest_memory"]["ancestors"][0]["limit"]=65*j.GIB
  with self.assertRaisesRegex(ValueError,"exact memory limit"):j.admit(x)
 def test_active_swap_rejected(self):
  x=fixture();x["memory"]["SwapTotal"]=1
  with self.assertRaisesRegex(ValueError,"active swap"):j.admit(x)
 def test_disk_short_queues(self):
  x=fixture();x["disk_free_bytes"]=j.WORKSPACE
  with self.assertRaisesRegex(ValueError,"workspace"):j.admit(x)
 def test_budget_tamper_rejected(self):
  x=fixture();x["joint_memory"]["ordinary_undrawn_floor_bytes"]-=1
  with self.assertRaisesRegex(ValueError,"reconstruction"):j.admit(x)
 def test_raw_full_output_cap_unchanged(self):
  x=fixture();x["output_bytes"]=j.WORKSPACE+1
  with self.assertRaisesRegex(ValueError,"32GiB"):j.admit(x)
 def test_hugeTLB_is_not_additive(self):
  x=fixture();x["memory"]["MemAvailable"]=1;x["memory"]["Hugetlb"]=1000*j.GIB
  with self.assertRaisesRegex(ValueError,"ordinary RAM"):j.admit(x)
class ActualController(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.p=Path(self.tmp.name);self.saved=[];self.stops=[];self.lookups=[]
  source=PRODUCER_ARCHIVE/"safety_host.py";b=source.read_bytes()
  self.assertEqual(hashlib.sha256(b).hexdigest(),j.SAFETY_SHA)
  mod=types.ModuleType("_actual017_safety_raw_fixture");mod.__file__=str(source)
  sys.modules[mod.__name__]=mod;self.addCleanup(sys.modules.pop,mod.__name__,None)
  def write(p,v):
   self.saved.append((p,v));return dict(path=str(p),sha256="a"*64)
  C=types.SimpleNamespace(require=j.need,GIB=j.GIB,canonical=lambda x:json.dumps(x,sort_keys=True),write=write,
   CUT="2026-10-12T07:00:25+00:00")
  class Base:
   def __init__(s,a):
    s.out=a.output_dir;s.cid=None;s.cpu=None;s.expected=None;s.protected=None;s.secondary=[];s.primary=None
    s.cleanup_deadline=None;s.h=types.SimpleNamespace(protected=lambda text:[],idle_one=lambda *a:(_ for _ in()).throw(AssertionError("GPU idle forbidden")))
  H=types.SimpleNamespace(Controller=Base,SMI="/usr/local/sbin/npu-smi")
  ns=mod.__dict__;ns.update(c=C,H=H,Path=Path,os=os,time=__import__("time"),datetime=__import__("datetime"),
   json=json,re=re,resource=types.SimpleNamespace(getrusage=lambda k:types.SimpleNamespace(ru_maxrss=0),RUSAGE_SELF=0,RUSAGE_CHILDREN=1),inspect=__import__("inspect"),PHYSICAL=(4,5,6,7),
   MEM=64*j.GIB,HOST_MEM=j.RAW_HOST,RESERVE=8.5*j.GIB,WORKSPACE=j.WORKSPACE,PHASE=5400,CLEANUP=90,
   SMI=H.SMI,DOCKER="/usr/bin/docker",protected_boundary=lambda *a:dict(baseline=[],observed=[]))
  tree=ast.parse(b);nodes=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Controller"]
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),"exec"),ns)
  self.S=mod
 def installed(self):
  klass=j.install(self.S,{"mode":"standalone"},opt_in=True)
  ctl=klass(types.SimpleNamespace(output_dir=self.p),__import__("time").monotonic())
  ctl.server=None;ctl.client=None;return ctl
 def test_default_off_no_controller_change(self):
  old=self.S.Controller
  with self.assertRaisesRegex(ValueError,"default OFF"):j.install(self.S,{},opt_in=False)
  self.assertIs(self.S.Controller,old)
 def test_actual_observe_accepts_next_paper_no_idle_call(self):
  ctl=self.installed();ctl.resources=lambda initial:dict(fixture=True)
  ctl.call=lambda *a,**kw:(dict(stdout="NEXT PAPER ON4-7",observed_utc="actualfixture"),dict(path="smi"))
  ctl.observe("raw",True);record=self.saved[-1][1]
  self.assertEqual(record["Devices"],[]);self.assertFalse(record["device_lease_required"])
 def test_actual_cleanup_stops_only_own_and_allows_next_paper(self):
  ctl=self.installed();cid="a"*64;ctl.cid=cid;ctl.expected=dict(cid=cid,arm="cpu-preflight")
  state=dict(State=dict(Running=False,Pid=0,OOMKilled=False),ExecIDs=None)
  ctl.inspect=lambda **kw:(state,dict(path="inspect"))
  def call(label,argv,**kwargs):
   if label=="stop-retain":self.stops.append(argv);self.assertEqual(argv[-1],cid)
   return dict(stdout="NEXT PAPER ON4-7"),dict(path=label)
  ctl.call=call;ctl.cleanup();out=self.saved[-1][1]
  self.assertEqual(len(self.stops),1);self.assertTrue(out["stopped"]);self.assertEqual(out["errors"],[])
 def test_actual_cleanup_negative_identity_keeps_failure(self):
  ctl=self.installed();ctl.cid="a"*64;ctl.expected=dict(cid=ctl.cid,arm="cpu-preflight")
  ctl.inspect=lambda **kw:(_ for _ in()).throw(ValueError("source/CID mismatch"))
  ctl.cleanup();self.assertIn("source/CID mismatch",self.saved[-1][1]["errors"][0])
 def test_device_stage_override_rejected(self):
  ctl=self.installed()
  with self.assertRaisesRegex(ValueError,"cannot create device"):ctl.create({}, {}, {}, "candidate")
 def test_actual_inherited_cleanup_single_idle_hunk_only(self):
  old=self.S.Controller.cleanup;new=j.cleanup_without_device_idle(self.S)
  self.assertEqual(set(old.__code__.co_varnames)-{"card"},set(new.__code__.co_varnames))
  # Removing idle loop does not remove any call() exact own cleanup predicates.
  tree=ast.parse(PRODUCER_ARCHIVE.joinpath("safety_host.py").read_bytes())
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Controller")
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="cleanup")
  calls=[n.func.attr for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
  for key in("inspect","call","write"):self.assertIn(key,calls)
 def test_install_reentry_rejected(self):
  self.installed()
  with self.assertRaisesRegex(ValueError,"one source-bound"):j.install(self.S,{},opt_in=True)
 def resource_call(self,cap=16,state="running"):
  ctl=self.installed();x=fixture()
  for k in("host_cpu","daemon_cpu","peer_host_cpu","peer_guest_cpu"):x[k]["quota_ancestors"][0]["capacity"]=cap
  peer={k:x[k]for k in("peer_host_cpu","peer_guest_cpu","peer_allocation","peer_host_memory","peer_guest_memory")}
  peer.update(state="running",plan={},owned={"cid":"b"*64},inspect={})
  if state=="standalone":peer=dict(state=state,plan={"mode":"standalone"})
  if state=="stopped-retained":
   peer={k:v for k,v in peer.items()if k in("state","plan","owned","inspect","peer_allocation")};peer["state"]=state
   ctl.cpu=fixture()["cpu_allocation"]
  self.S.H.cpus=lambda s:[]
  self.S.H.cpu_view=lambda pid:x["host_cpu"]
  self.S.H.daemon_view=lambda:x["daemon_cpu"]
  self.S.c.output_scan=lambda root:({},0)
  ctl.rss=lambda:{k:x[k]for k in("aggregate_rss_kib","host_peak_rss_kib","child_peak_rss_kib")}
  ctl.call=lambda *a,**kw:(dict(stdout=json.dumps(dict(NCPU=16))),dict(path="engine"))
  realPath=Path
  def path(value):
   if str(value)=="/proc/meminfo":return types.SimpleNamespace(read_text=lambda:"MemAvailable: 104857600 kB\\nSwapTotal: 0 kB\\nSwapFree: 0 kB\\n".replace("\\n","\n"))
   return realPath(value)
  values=[dict(Id="b"*64,State=dict(Running=True,Pid=40,OOMKilled=False))]if state=="running"else[]
  with patch.object(j,"inventory",return_value={"values":values}),patch.object(j,"checked_peer",return_value=peer),patch.object(j,"memory_view",side_effect=lambda H,pid:x["host_memory"]if pid==os.getpid()else x["daemon_memory"]),patch.object(j,"Path",side_effect=path),patch.object(j.shutil,"disk_usage",return_value=types.SimpleNamespace(free=400*j.GIB)),patch.object(j.os,"sched_getaffinity",return_value={7},create=True):
   return ctl.resources(True)
 def test_actual_resources_positive_joint9(self):
  r=self.resource_call();self.assertEqual(r["cpu_allocation"]["total_cpu_budget"],9)
 def test_actual_resources_joint7_retains_then_queues(self):
  with self.assertRaisesRegex(ValueError,"joint finite"):self.resource_call(7)
  # Refusal occurs before CPU create/device lease; existing evidence is retained.
  self.assertFalse(self.stops)
 def test_actual_resources_standalone_common2(self):
  r=self.resource_call(2,"standalone");self.assertEqual(r["cpu_allocation"]["total_cpu_budget"],2)
 def test_actual_resources_stopped_peer_common7_reassessment(self):
  r=self.resource_call(7,"stopped-retained");self.assertEqual(r["cpu_allocation"]["total_cpu_budget"],5)
  self.assertEqual(r["cpu_allocation"]["guest_cpus"],[8])
class Wiring(unittest.TestCase):
 def test_original_full64_child_and_timebox_unchanged(self):
  tree=ast.parse(HERE.joinpath("raw_cpu8.py").read_bytes());s=ast.unparse(tree)
  self.assertIn("consume_raw_cpu.py",s);self.assertIn("5310",s);self.assertIn("cleanup_used > 90",s)
  self.assertIn("core.raw_result",s);self.assertNotIn("idle_one",s)
 def test_new_literal_main_requires_explicit_joint_plan(self):
  s=HERE.joinpath("main.py").read_text();self.assertIn("--cpu-only-raw",s);self.assertIn("--joint-peer-plan",s)
  self.assertIn("--raw-host-cpu",s);self.assertIn("inherited=load",s)
 def test_predecessor_refusal_report_parent_creates_no_lease(self):
  spec=importlib.util.spec_from_file_location("_raw16_publication",HERE/"main.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory()as t:
   lowbit=Path(t)/"lowbit";lowbit.mkdir();p=lowbit/"run-kivi-firstdecode-independent-raw-test"
   a=types.SimpleNamespace(mode="raw",output=p/"ENTRY.json",raw_phase_output=p)
   module.failed_raw_parent(a,{"producer_source":{"path":str(lowbit/"producer"/"SOURCE_MANIFEST.json")}})
   self.assertTrue(p.is_dir());self.assertEqual(list(p.iterdir()),[])
 def test_predecessor_refusal_wrong_packet_no_creation(self):
  spec=importlib.util.spec_from_file_location("_raw16_publication_wrong",HERE/"main.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory()as t:
   lowbit=Path(t)/"lowbit";lowbit.mkdir();p=lowbit/"wrong"
   a=types.SimpleNamespace(mode="raw",output=p/"ENTRY.json",raw_phase_output=p)
   with self.assertRaisesRegex(ValueError,"exact new lowbit"):module.failed_raw_parent(a,{"producer_source":{"path":str(lowbit/"producer"/"SOURCE_MANIFEST.json")}})
   self.assertFalse(p.exists())

class ActualWholeCPU(unittest.TestCase):
 def setUp(self):
  def load(p,name):
   s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
  self.core=load(BASE_WHOLE/"consume_whole.py","_raw_cpu_original014_whole_fixture")
  self.old=load(BASE_WHOLE/"test_whole.py","_raw_cpu_original014_tests_fixture")
  self.old.CORE=self.core;self.old.PRODUCER_ARCHIVE=PRODUCER_ARCHIVE;self.old.REVIEWED_DEPS=REVIEWED_DEPS
  self.e=self.old.Evidence();self.e.setUp();self.addCleanup(self.e.tearDown)
 def fixture(self):
  ctx,o,x=self.e.cleanup_fixture();ctx._joint_base_whole=BASE_WHOLE
  o["arm"]="cpu-preflight";o["guest_cpus"]=[7]
  o["create_receipt"]=self.e.artifact(dict(exit_code=0,stdout=o["cid"]+"\n",requested_argv=ctx.s["create_argv"](o)))
  ins=self.e.inspect(o)
  for k in("before_inspect","after_inspect"):
   x[k]=self.e.artifact(dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",o["cid"]],stdout=json.dumps([ins])))
  release=self.core.obj(x["release_smi"]);release["stdout"]="NEXT PAPER IS NOT A RAW DEVICE LEASE"
  x["release_smi"]=self.e.artifact(release)
  return ctx,o,x
 def test_real_whole_cpu_cleanup_no_gpu_idle(self):
  ctx,o,x=self.fixture()
  with self.assertRaises(ValueError):ctx.cleanup(self.e.artifact(x),o,5000)
  after=j.consume_cleanup(ctx,self.e.artifact(x),o,5000)
  self.assertEqual(after["State"]["Pid"],0)
 def test_real_whole_foreign_stop_still_rejected(self):
  ctx,o,x=self.fixture();stop=self.core.obj(x["stop_receipt"]);stop["requested_argv"][-1]="f"*64
  x["stop_receipt"]=self.e.artifact(stop)
  with self.assertRaisesRegex(ValueError,"exact own stop"):j.consume_cleanup(ctx,self.e.artifact(x),o,5000)
 def test_real_whole_oom_still_rejected(self):
  ctx,o,x=self.fixture();after=self.core.obj(x["after_inspect"]);v=json.loads(after["stdout"]);v[0]["State"]["OOMKilled"]=True
  after["stdout"]=json.dumps(v);x["after_inspect"]=self.e.artifact(after)
  with self.assertRaisesRegex(ValueError,"OOM"):j.consume_cleanup(ctx,self.e.artifact(x),o,5000)
 def test_real_whole_protected_own0_still_rejected(self):
  ctx,o,x=self.fixture();row=dict(physical=0,chip=0,pid=5000,start_ticks=1,cgroup="/docker/"+o["cid"],cmdline_sha256="f"*64)
  x["protected_boundary"]=dict(baseline=[],observed=[row])
  with self.assertRaisesRegex(ValueError,"owned process"):j.consume_cleanup(ctx,self.e.artifact(x),o,5000)
 def test_real_whole_source_drift_still_rejected(self):
  ctx,o,x=self.fixture();o["sources"]["client.py"]="f"*64
  with self.assertRaisesRegex(ValueError,"complete source"):j.consume_cleanup(ctx,self.e.artifact(x),o,5000)

def standalone():
 x=fixture();x["peer"]={"state":"standalone","plan":{"mode":"standalone"}}
 x["cpu_allocation"]=j.allocate(x["host_cpu"],x["daemon_cpu"],x["peer"])
 x["joint_memory"]=j.memory_budget(x["host_memory"],x["daemon_memory"],x["peer"])
 return x
def released():
 x=fixture();x["peer"]={k:v for k,v in x["peer"].items()if k in("state","plan","owned","inspect","peer_allocation")}
 x["peer"]["state"]="stopped-retained"
 x["fixed_guest_cpu"]=8
 x["cpu_allocation"]=j.allocate(x["host_cpu"],x["daemon_cpu"],x["peer"],fixed_guest=8)
 x["joint_memory"]=j.memory_budget(x["host_memory"],x["daemon_memory"],x["peer"])
 return x
class ResourceTransitions(unittest.TestCase):
 def test_standalone_two_cpu_legal(self):
  x=standalone()
  for k in("host_cpu","daemon_cpu"):x[k]["quota_ancestors"][0]["capacity"]=2
  x["cpu_allocation"]=j.allocate(x["host_cpu"],x["daemon_cpu"],x["peer"])
  self.assertEqual(j.admit(x)["total_cpu_budget"],2)
 def test_standalone_memory_ceiling_and_disk(self):
  x=standalone();self.assertEqual(x["joint_memory"]["full_declared_ceiling_bytes"],int(16.5*j.GIB))
  x["disk_free_bytes"]=40*j.GIB;j.admit(x)
 def test_standalone_common_one_queues(self):
  x=standalone();x["daemon_cpu"]["quota_ancestors"][0]["capacity"]=1
  with self.assertRaisesRegex(ValueError,"joint finite"):j.admit(x)
 def test_stopped_peer_common7_continues_own_slots(self):
  x=released()
  for k in("host_cpu","daemon_cpu"):x[k]["quota_ancestors"][0]["capacity"]=7
  x["cpu_allocation"]=j.allocate(x["host_cpu"],x["daemon_cpu"],x["peer"],fixed_guest=8)
  a=j.admit(x);self.assertEqual(a["total_cpu_budget"],5);self.assertEqual(a["guest_cpus"],[8])
 def test_stopped_peer_does_not_free_host_and_reserve(self):
  x=released();self.assertEqual(x["cpu_allocation"]["peer_reserved_cpus"],[0,5,6])
  self.assertEqual(x["joint_memory"]["full_declared_ceiling_bytes"],25*j.GIB)
 def test_stopped_peer_fresh_ram_still_can_queue(self):
  x=released();x["memory"]["MemAvailable"]=24*j.GIB
  with self.assertRaisesRegex(ValueError,"joint ordinary"):j.admit(x)
 def test_running_to_stopped_fixed_guest_not_reselected(self):
  a=fixture()["cpu_allocation"];b=released()["cpu_allocation"]
  self.assertEqual((a["host_cpu"],a["guest_cpus"]),(b["host_cpu"],b["guest_cpus"]))
 def test_fixed_guest_conflict_failclosed(self):
  x=fixture()
  with self.assertRaisesRegex(ValueError,"fixed actual"):j.allocate(x["host_cpu"],x["daemon_cpu"],x["peer"],fixed_guest=2)
 def test_standalone_no_peer_source_required(self):
  c=types.SimpleNamespace(obj=lambda r:(_ for _ in()).throw(AssertionError("no peer read")))
  H=types.SimpleNamespace(cpu_view=lambda p:(_ for _ in()).throw(AssertionError("no peer PID")))
  peer=j.checked_peer(c,{"mode":"standalone"},None,H,None)
  self.assertEqual(peer,{"state":"standalone","plan":{"mode":"standalone"}})
 def test_parallel_missing_profile_rejects_before_read(self):
  plan=dict(mode="reviewed-peer",profile={},source={},owned={},resources={})
  with self.assertRaisesRegex(ValueError,"MISSING_CURRENT"):j.profile_source(None,plan,None)
 def test_arbitrary_profile_parameter_rejected(self):
  plan=dict(mode="reviewed-peer",profile={"source":"bad"},source={},owned={},resources={})
  with self.assertRaisesRegex(ValueError,"SHA-bound adapter"):j.profile_source(None,plan,{"source":"reviewed"})
 def test_standalone_cannot_hide_peer_claim(self):
  with self.assertRaisesRegex(ValueError,"exact reviewed peer"):j.profile_source(None,{"mode":"standalone","owned":{}},None)

class ActualPeerProtocol(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
  def ref(p):
   b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  def obj(r):
   self.assertEqual(ref(Path(r["path"])),r);return json.loads(Path(r["path"]).read_bytes())
  def artifact(name,v):
   p=self.p/name;p.write_bytes(json.dumps(v,sort_keys=True).encode()+b"\n");return ref(p)
  self.artifact=artifact
  # Execute the real historical resources.allocate AST, not reimplemented budget
  # logic. This temporary copied source is a SOFTWARE fixture, never a live peer.
  original=PEER_ARCHIVE/"resources.py"
  b=original.read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),"660cdd7e2639db7fbf4400a257de116b264bba9c42a530df2fe5bc734ae9624c")
  q=self.p/"resources.py";q.write_bytes(b);rr=ref(q)
  hp=PEER_ARCHIVE/"MAIN_HOST.py"
  hb=hp.read_bytes();self.assertEqual(hashlib.sha256(hb).hexdigest(),"6067bb0a327b1dded44efda7415429db98262668bfcf41b1cc37f41afc60542e")
  hq=self.p/"MAIN_HOST.py";hq.write_bytes(hb);hr=ref(hq)
  tree=ast.parse(b);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="allocate")
  ns=dict(require=j.need);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(q),"exec"),ns)
  self.R=types.SimpleNamespace(allocate=ns["allocate"])
  sr=artifact("SOURCE_MANIFEST.json",dict(schema="skvq.current72h.preprojection.sources/v1",default_enabled=False,files=[rr,hr],dependencies=[]))
  x=fixture();rs=dict(host_cpu=x["peer_host_cpu"],daemon_cpu=x["daemon_cpu"])
  rs["allocation"]=self.R.allocate(rs["host_cpu"],rs["daemon_cpu"])
  rref=artifact("FRESH_RESOURCES.json",rs)
  self.profile=dict(schema="kivi.reviewed-skvq-peer-profile/v1",source=sr,resources_source=rr,host_source=hr,
   owner="skvq-current72h-preprojection-v1-008",phase="tp4-capture",guest_memory_bytes=64*j.GIB,
   guest_CPU=4,total_CPU=7,guest_future_workspace_bytes=320*j.GIB)
  owned=dict(source=sr["sha256"],phase="tp4-capture",npu=True,mem=64*j.GIB,resource_ref=rref,
   cid="b"*64,name="reviewed-peer",cpuset="1,2,3,4",mounts={"/stage":[str(self.p),True]},env={"TMPDIR":"/stage"})
  self.owned=owned;self.rs=rs
  self.plan=dict(mode="reviewed-peer",profile=self.profile,source=sr,owned=artifact("OWNED.json",owned),resources=rref)
  dev=[dict(PathOnHost="/dev/davinci"+str(k),PathInContainer="/dev/davinci"+str(k-4),CgroupPermissions="rwm")for k in range(4,8)]
  dev += [dict(PathOnHost="/dev/"+k,PathInContainer="/dev/"+k,CgroupPermissions="rwm")for k in("davinci_manager","devmm_svm","hisi_hdc")]
  owned["devices"]={v["PathOnHost"]:v["PathInContainer"]for v in dev}
  self.plan["owned"]=artifact("OWNED-FULL.json",owned)
  self.inspect=dict(Id=owned["cid"],Name="/"+owned["name"],Image="image660",
   Config=dict(Image="image660",Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],
    Labels={"model-tuning-lab.owner":self.profile["owner"],"model-tuning-lab.source":sr["sha256"]},Env=["TMPDIR=/stage"]),
   HostConfig=dict(Memory=64*j.GIB,MemorySwap=64*j.GIB,NanoCpus=4*10**9,CpusetCpus=owned["cpuset"],
    NetworkMode="none",Privileged=False,CgroupnsMode="host",Devices=dev,IpcMode="private",ShmSize=2*j.GIB,
    PidsLimit=1024,CapDrop=["ALL"],SecurityOpt=["no-new-privileges"],DeviceRequests=[],DeviceCgroupRules=[]),
   Mounts=[dict(Destination="/stage",Source=str(self.p),RW=True,Type="bind")],
   State=dict(Running=False,Pid=0,OOMKilled=False,Restarting=False,Dead=False,FinishedAt="2026-10-10T12:00:00Z"),ExecIDs=None)
  self.c=types.SimpleNamespace(obj=obj,checked=lambda r:ref(Path(r["path"])),IMAGE="image660",module=lambda *a:self.R)
  self.H=types.SimpleNamespace(cpu_view=lambda p:(_ for _ in()).throw(AssertionError("dead/reused PID must not be read")))
 def raw(self):
  return dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",self.owned["cid"]],stdout=json.dumps([self.inspect]))
 def call(self,cid):
  raw=self.raw();return raw,self.artifact("inspect.json",raw)
 def test_actual_allocator_to_profile_owned_stopped_branch(self):
  p=j.checked_peer(self.c,self.plan,self.call,self.H,self.profile)
  self.assertEqual(p["state"],"stopped-retained")
  self.assertNotIn("peer_host_cpu",p);self.assertNotIn("peer_guest_cpu",p)
 def test_wrong_owner_rejected(self):
  self.inspect["Config"]["Labels"]["model-tuning-lab.owner"]="skvq-current72h-preprojection-v1-006"
  with self.assertRaisesRegex(ValueError,"exact owned"):j.checked_peer(self.c,self.plan,self.call,self.H,self.profile)
 def test_wrong_resources_pin_rejected(self):
  other=copy.deepcopy(self.profile);other["resources_source"]["sha256"]="f"*64
  plan=dict(self.plan,profile=other)
  with self.assertRaisesRegex(ValueError,"resources module"):j.checked_peer(self.c,plan,self.call,self.H,other)
 def test_running_requires_real_peer_pid_views(self):
  self.inspect["State"].update(Running=True,Pid=40)
  with self.assertRaisesRegex(AssertionError,"dead/reused"):j.checked_peer(self.c,self.plan,self.call,self.H,self.profile)
 def test_stopped_exec_remaining_rejected(self):
  self.inspect["ExecIDs"]=["exec"]
  with self.assertRaisesRegex(ValueError,"stopped-retained"):j.checked_peer(self.c,self.plan,self.call,self.H,self.profile)
 def test_stopped_oom_not_promoted_to_release(self):
  self.inspect["State"]["OOMKilled"]=True
  with self.assertRaisesRegex(ValueError,"noOOM"):j.checked_peer(self.c,self.plan,self.call,self.H,self.profile)
 def test_foreign_device_mapping_rejected(self):
  self.inspect["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci0"
  with self.assertRaisesRegex(ValueError,"no0-3"):j.checked_peer(self.c,self.plan,self.call,self.H,self.profile)
 def test_wrong_mount_rejected_before_release(self):
  self.inspect["Mounts"][0]["RW"]=False
  with self.assertRaisesRegex(ValueError,"mounts"):j.checked_peer(self.c,self.plan,self.call,self.H,self.profile)

class ActualInventory(unittest.TestCase):
 def test_actual_empty_inventory_standalone(self):
  saved=[];raw=dict(exit_code=0,stdout="")
  def call(label,argv):saved.append(argv);return raw,{"path":label}
  r=j.inventory(call);self.assertEqual(r["values"],[]);self.assertEqual(len(saved),2)
 def test_inventory_race_rejects(self):
  values=iter([dict(exit_code=0,stdout=""),dict(exit_code=0,stdout="a"*64)])
  with self.assertRaisesRegex(ValueError,"changed during"):j.inventory(lambda *a:(next(values),{}))
 def test_unreviewed_next_main_stage_queues(self):
  x=standalone();row=dict(Id="c"*64,State=dict(Running=True,Pid=60,OOMKilled=False),
   Config=dict(Labels={"model-tuning-lab.owner":"skvq-current72h-preprojection-v1-008"}),
   HostConfig=dict(Devices=[],CpusetCpus="10"))
  with self.assertRaisesRegex(ValueError,"unaccounted MAIN"):j.inventory_admit({"values":[row]},x["cpu_allocation"],x["peer"],None,lambda s:[int(s)])
 def test_foreign_cpuset_is_eligible_not_reserved(self):
  x=standalone();row=dict(Id="c"*64,State=dict(Running=True,Pid=60,OOMKilled=False),Config=dict(Labels={}),
   HostConfig=dict(Devices=[],CpusetCpus="7"))
  self.assertTrue(j.inventory_admit({"values":[row]},x["cpu_allocation"],x["peer"],None,lambda s:[int(s)]))
 def test_protected_external_disjoint_container_not_stopped(self):
  x=standalone();row=dict(Id="c"*64,State=dict(Running=True,Pid=60,OOMKilled=False),Config=dict(Labels={}),
   HostConfig=dict(Devices=[dict(PathOnHost="/dev/davinci0")],CpusetCpus="12"))
  self.assertTrue(j.inventory_admit({"values":[row]},x["cpu_allocation"],x["peer"],None,lambda s:[int(s)]))
 def actual043f_external_rows(self):
  # Field projection from MAIN actual043f at2026-10-10T14:12:07.517981Z.
  # Running came from docker ps; remaining State fields below are explicitly
  # SOFTWARE fixtures, not a new actual process/idle/overlap assertion.
  rows=[("87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa",2742184,"",list(range(8))),
   ("d2a11a6cadbaeb6b79e5366413e8957e25b96e222620350d782c471d5b0edae8",2214196,"",list(range(8))),
   ("efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6",88529,"",[]),
   ("e93f8e1ca42b64baf2bfa4ae59289f10dbaabc6069f70e7aa44e7956a9b0f54b",49725,"",list(range(8))),
   ("748ff800682d5f085fea77d7cb2b403f7bff18dca9d98bc536b07da9ca48ae98",3779641,"112-191",list(range(4)))]
  return [dict(Id=cid,State=dict(Running=True,Pid=pid,OOMKilled=False),Config=dict(Labels={}),
   HostConfig=dict(CpusetCpus=cs,CpuQuota=0,CpuPeriod=0,NanoCpus=0,Memory=0,
    Devices=[dict(PathOnHost="/dev/davinci"+str(k))for k in dev]))for cid,pid,cs,dev in rows]
 def test_actual043f_foreign_declarations_allow_standalone(self):
  x=standalone();seen=[]
  def cpus(s):seen.append(s);return list(range(112,192))
  self.assertTrue(j.inventory_admit({"values":self.actual043f_external_rows()},x["cpu_allocation"],x["peer"],None,cpus))
  self.assertEqual(seen,["112-191"])
 def test_actual043f_does_not_discount_raw_cpu_budget(self):
  x=standalone();j.inventory_admit({"values":self.actual043f_external_rows()},x["cpu_allocation"],x["peer"],None,lambda s:[])
  x["daemon_cpu"]["quota_ancestors"][0]["capacity"]=1
  with self.assertRaisesRegex(ValueError,"joint finite"):j.admit(x)
 def test_actual043f_does_not_discount_ordinary_ram(self):
  x=standalone();j.inventory_admit({"values":self.actual043f_external_rows()},x["cpu_allocation"],x["peer"],None,lambda s:[])
  x["memory"]["MemAvailable"]=j.GIB
  with self.assertRaisesRegex(ValueError,"joint ordinary RAM"):j.admit(x)
 def test_declared_device47_does_not_bypass_main_lease(self):
  x=standalone();row=self.actual043f_external_rows()[0]
  row["Config"]["Labels"]={"model-tuning-lab.owner":"skvq-current72h-preprojection-v1-008"}
  with self.assertRaisesRegex(ValueError,"unaccounted MAIN resource lease"):j.inventory_admit({"values":[row]},x["cpu_allocation"],x["peer"],None,lambda s:[])
 def test_actual_limit_bool_is_not_cpu_commitment(self):
  x=standalone();row=self.actual043f_external_rows()[0];row["HostConfig"]["NanoCpus"]=True
  with self.assertRaisesRegex(ValueError,"resource limit type"):j.inventory_admit({"values":[row]},x["cpu_allocation"],x["peer"],None,lambda s:[])

class ActualObservationReplay(unittest.TestCase):
 setUp=ActualWholeCPU.setUp
 fixture=ActualWholeCPU.fixture
 # Reuse fixture builders only. Existing five cleanup tests remain registered
 # once in ActualWholeCPU; these five exercise the new observation predicate.
 def snapshot(self,ctx,o,state="standalone",initial=False):
  x=standalone()if state=="standalone"else(released()if state=="stopped-retained"else fixture())
  if state=="standalone":ctx._joint_peer_plan={"mode":"standalone"};ctx._joint_reviewed_profile=None
  else:
   q=self.peerfixture;q.inspect["State"].update(Running=state=="running",Pid=40 if state=="running"else 0)
   pr=q.artifact("snapshot-"+str(len(self.snapshots))+".json",q.raw())
   peer=dict(state=state,plan=q.plan,owned=q.owned,inspect=pr,peer_allocation=q.rs["allocation"])
   if state=="running":
    peer.update({k:x["peer"][k]for k in("peer_host_cpu","peer_guest_cpu","peer_host_memory","peer_guest_memory")})
    peer["peer_guest_cpu"]["process"]["cgroup"]="/docker/"+q.owned["cid"]
    peer["peer_guest_memory"]["process"]["cgroup"]="/docker/"+q.owned["cid"]
   x["peer"]=peer;ctx._joint_peer_plan=q.plan;ctx._joint_reviewed_profile=q.profile
  o["guest_cpus"]=x["cpu_allocation"]["guest_cpus"]
  ox=self.e.inspect(o);ox["State"].update(Running=True,Pid=50,OOMKilled=False)
  if not initial:
   x["fixed_guest_cpu"]=o["guest_cpus"][0]
   x["own_inspect"]=self.e.artifact(dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",o["cid"]],stdout=json.dumps([ox])))
   pc=view(50,o["guest_cpus"],1);pc["process"]["cgroup"]="/docker/"+o["cid"]
   mv=mem(50,"own",8*j.GIB,4*j.GIB);mv["process"]["cgroup"]=pc["process"]["cgroup"]
   x.update(own_guest_cpu=pc,own_guest_memory=mv)
  x["cpu_allocation"]=j.allocate(x["host_cpu"],x["daemon_cpu"],x["peer"],fixed_guest=x.get("fixed_guest_cpu"))
  x["joint_memory"]=j.memory_budget(x["host_memory"],x["daemon_memory"],x["peer"],x.get("own_guest_memory"))
  rows=[]if initial else[ox]
  if state=="running":rows.append(copy.deepcopy(self.peerfixture.inspect))
  ids=[r["Id"]for r in rows];argv=["/usr/bin/docker","ps","--no-trunc","-q"]
  ps=dict(exit_code=0,requested_argv=argv,stdout="\n".join(ids))
  inv=dict(before=self.e.artifact(ps),after=self.e.artifact(ps),values=rows,inspect=None)
  if ids:inv["inspect"]=self.e.artifact(dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",*ids],stdout=json.dumps(rows)))
  x["running_inventory"]=inv;x["engine"]=self.e.artifact(dict(exit_code=0,requested_argv=["/usr/bin/docker","info","--format","{{json .}}"],stdout=json.dumps({"NCPU":16})))
  x["actual_output_scan_ref"]=self.e.artifact({"softwarefixture":True})
  smi=dict(exit_code=0,requested_argv=["/usr/local/sbin/npu-smi","info"],stdout="NEXT PAPER4-7",observed_utc="2026-10-10T12:00:00Z")
  r=dict(CPU_only=True,Devices=[],device_lease_required=False,smi=self.e.artifact(smi),npu_smi=smi["stdout"],
   observed_utc=smi["observed_utc"],protected0_3=[],protected_boundary=ctx.boundary([],[],[o["cid"]],[10]),resources=x)
  self.snapshots.append(r);return r
 def replay_context(self):
  ctx,o,_=self.fixture();o["arm"]="cpu-preflight";self.snapshots=[]
  p=REVIEWED_DEPS/"h8_host_run.py";b=p.read_bytes()
  self.assertEqual(hashlib.sha256(b).hexdigest(),"4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20")
  f=next(n for n in ast.parse(b).body if isinstance(n,ast.FunctionDef)and n.name=="cpus")
  ns=dict(require=j.need,re=re);exec(compile(ast.Module(body=[f],type_ignores=[]),str(p),"exec"),ns)
  q=ActualPeerProtocol(methodName="test_actual_allocator_to_profile_owned_stopped_branch");q.setUp();self.addCleanup(q.doCleanups);self.peerfixture=q
  def module(path,sha,name):
   if Path(path)==p:
    self.assertEqual(sha,hashlib.sha256(b).hexdigest());return types.SimpleNamespace(cpus=ns["cpus"])
   return q.R
  ctx.c=types.SimpleNamespace(obj=self.core.obj,checked=lambda r:self.core.ref(Path(r["path"])),
   IMAGE="image660",module=module,H8=p,DEPS={str(p):hashlib.sha256(b).hexdigest()})
  ctx.scanner=types.SimpleNamespace(consume=lambda scan,root:1024)
  return ctx,o
 def test_actual_standalone_original_inspect_and_observation(self):
  ctx,o=self.replay_context();a=self.snapshot(ctx,o,initial=True);b=self.snapshot(ctx,o)
  aa=j.consume_observation(ctx,self.e.artifact(a),o,10,self.e.root,True)
  bb=j.consume_observation(ctx,self.e.artifact(b),o,10,self.e.root,False)
  self.assertEqual(aa,bb);self.assertEqual(aa["guest_cpu_budget"],1)
 def test_actual_running_then_stopped_resource_replay_stable_own(self):
  ctx,o=self.replay_context();a=self.snapshot(ctx,o,"running",True);b=self.snapshot(ctx,o,"stopped-retained")
  aa=j.consume_observation(ctx,self.e.artifact(a),o,10,self.e.root,True)
  bb=j.consume_observation(ctx,self.e.artifact(b),o,10,self.e.root,False)
  self.assertEqual(aa,bb);self.assertEqual(a["resources"]["cpu_allocation"]["total_cpu_budget"],9)
  self.assertEqual(b["resources"]["cpu_allocation"]["total_cpu_budget"],5)
 def test_actual_observation_budget_tamper_rejected(self):
  ctx,o=self.replay_context();a=self.snapshot(ctx,o);a["resources"]["joint_memory"]["ordinary_undrawn_floor_bytes"]=1
  with self.assertRaisesRegex(ValueError,"reconstruction"):j.consume_observation(ctx,self.e.artifact(a),o,10,self.e.root)
 def test_actual_observation_stopped_peer_restart_rejected(self):
  ctx,o=self.replay_context();a=self.snapshot(ctx,o,"stopped-retained",True)
  j.consume_observation(ctx,self.e.artifact(a),o,10,self.e.root,True);b=self.snapshot(ctx,o,"running")
  with self.assertRaisesRegex(ValueError,"restart/reuse"):j.consume_observation(ctx,self.e.artifact(b),o,10,self.e.root)
 def test_actual_observation_own_namespace_drift_rejected(self):
  ctx,o=self.replay_context();a=self.snapshot(ctx,o);a["resources"]["own_guest_cpu"]["process"]["start_ticks"]+=1
  with self.assertRaisesRegex(ValueError,"namespace"):j.consume_observation(ctx,self.e.artifact(a),o,10,self.e.root)

# Actual retained018 source/receipt regression. No tensor math or reconstructed
# historical PASS; the unchanged original strict seven-source expression is
# extracted from the pinned scalar reference and exercised on original bytes.
PREFILL_ACTUAL_REFS={"client":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/CLIENT_RESULT.json","bytes":2619,"sha256":"3c2429534f4911c5fad9cadafa65b99781554cf473eae88d045f1d777bb21fc4"},"rank":{"bytes":8515,"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/run-kivi-owned-layout-1791664208586952020/r0-p397-s58987110-PACKED-QWEN-r0-FIRSTDECODE-FINAL.json","sha256":"e04443b25859fe0a12eadf6ac24ad7c92d4054f88f6077f8157970b365fcf8eb"},"frame":{"bytes":194377,"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/run-kivi-owned-layout-1791664208586952020/r0-p397-s58987110-r0-language_model-model-layers-11-self_attn-attn-e000002-PACKED-FRAME.json","sha256":"8596a2cd5d31c748b91e8054630a7658a7e7579bbc056b1e85b35c216a3c1135"},"owner":{"bytes":2030,"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/run-kivi-owned-layout-1791664208586952020/r0-p397-s58987110-PACKED-QWEN-r0-language_model.model.layers.11.self_attn.attn-e000002-r00-OWNER.json","sha256":"621187bfaf60a73c1ec4e82d209114de7f778d318c3a3d50171bb8033a3cea47"},"provenance":{"bytes":175975,"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/run-kivi-owned-layout-1791664208586952020/r0-p397-s58987110-PACKED-QWEN-r0-language_model.model.layers.11.self_attn.attn-e000001-s00-ORIGINAL-PREFILL.json","sha256":"301aea71ff6584a17913760c88eaf3ea83e22e31f9f32ce7e3dd6fa72bf4a4ac"}}
class ActualProvenanceCaller(unittest.TestCase):
 def setUp(self):
  self.manifest=json.loads(PRODUCER_ARCHIVE.joinpath("SOURCE_MANIFEST.json").read_bytes())
  self.roles=self.manifest["runtime_roles"]
  path=PRODUCER_ARCHIVE/"consume_prefill.py";b=path.read_bytes()
  self.assertEqual(hashlib.sha256(b).hexdigest(),"3e4a100be9225c3ec464e1d256761a780648fad3dfd4b1dc79db8f883fd092f1")
  tree=ast.parse(b);pin=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=="PINS"for t in n.targets))
  self.assertIsInstance(pin.value,ast.Call);self.assertEqual(ast.dump(pin.value.func),ast.dump(ast.Name(id="dict",ctx=ast.Load())))
  self.assertEqual(pin.value.args,[]);self.assertTrue(all(k.arg is not None for k in pin.value.keywords))
  self.pins={k.arg:ast.literal_eval(k.value)for k in pin.value.keywords}
  self.guard=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=="need"
   and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value=="exact unchanged critical sources")
  self.guard_code=compile(ast.Expression(body=self.guard),str(path),"eval")
  self.documents={}
  for key,r in PREFILL_ACTUAL_REFS.items():
   name={"client":"CLIENT_RESULT.json","rank":"RANK0.json","frame":"FRAME.json","owner":"SLOT_OWNER.json","provenance":"ORIGINAL_PREFILL.json"}[key]
   p=PROVENANCE_ARCHIVE/name if PROVENANCE_ARCHIVE is not None else Path(r["path"])
   bb=p.read_bytes();self.assertEqual(len(bb),r["bytes"]);self.assertEqual(hashlib.sha256(bb).hexdigest(),r["sha256"])
   self.documents[key]=json.loads(bb)
 def guarded(self,p=None,capture=None):
  return eval(self.guard_code,{"need":j.need,"provenance":p or self.documents["provenance"],"PINS":self.pins,
   "installer_sha256":self.roles["installer"]["sha256"],
   "capture_sha256":capture or self.roles["provenance"]["sha256"]})
 def chain(self,d):
  c,r,f,o,p=(d[k]for k in("client","rank","frame","owner","provenance"))
  j.need(c["rank_bundle_refs"][0]==PREFILL_ACTUAL_REFS["rank"],"actual client rank Ref")
  layer=o["layer"];j.need(r["frame_refs"][layer]==PREFILL_ACTUAL_REFS["frame"],"actual rank frame Ref")
  row=f["rows"][0];j.need(row["identity_refs"]["slot_owner"]==PREFILL_ACTUAL_REFS["owner"],"actual frame slot owner Ref")
  j.need(o["original_prefill_ref"]==PREFILL_ACTUAL_REFS["provenance"],"actual owner original prefill Ref")
  j.need(r["identity"]==o["identity"]==p["identity"]and r["rank"]==o["rank"]==p["rank"]==0,"actual all source owner identity")
  j.need(row["request_id"]==o["request_id"]==p["request_id"]and p["layer"]==layer,"actual request layer")
  j.need(c["usage"]["prompt_tokens"]==r["prompt_tokens"]==p["prompt_length"]==32768
   and r["first_decode_length"]==32769 and len(p["tiles"])==256,"complete original extent, not sample")
  self.guarded(p)
 def test_actual_five_originals_chain_and_seven_source_positive(self):
  self.chain(self.documents)
 def test_old_native_capture_role_deterministically_rejected(self):
  self.assertNotEqual(self.roles["capture"]["sha256"],self.roles["provenance"]["sha256"])
  with self.assertRaisesRegex(ValueError,"exact unchanged critical sources"):
   self.guarded(capture=self.roles["capture"]["sha256"])
 def test_all_seven_actual_critical_source_mutations_rejected(self):
  keys=["installer_source_sha256","capture_source_sha256",*self.pins]
  self.assertEqual(len(keys),7)
  for key in keys:
   with self.subTest(key=key):
    p=copy.deepcopy(self.documents["provenance"]);p[key]="0"*64
    with self.assertRaisesRegex(ValueError,"exact unchanged critical sources"):self.guarded(p)
 def test_actual_chain_changed_reference_and_identity_rejected(self):
  for group,key in(("owner","original_prefill_ref"),("rank","identity")):
   with self.subTest(group=group):
    d=copy.deepcopy(self.documents)
    if key=="identity":d[group][key]["start_ticks"]+=1
    else:d[group][key]["sha256"]="0"*64
    with self.assertRaises(ValueError):self.chain(d)
 def caller(self,digest=None):
  path=HERE/"consume_raw_cpu.py";b=path.read_bytes();sha=hashlib.sha256(b).hexdigest()
  tree=ast.parse(b);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="entry")
  source=self.manifest["files"];original=next(r for r in source if Path(r["path"]).name=="consume_raw.py")
  checked=[];calls=[];oracle=types.SimpleNamespace(np=types.SimpleNamespace(__version__="1.26.4"));result={}
  reference_mf=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  reference_sha=hashlib.sha256((HERE/"SOURCE_MANIFEST.json").read_bytes()).hexdigest()
  for role,name in(("writer","consume_prefill_vector.py"),("vector","independent_vector_writer.py"),("aggregate","consume_first_decode_progress.py")):
   reference_mf["reference_sources"][role]=dict(path=str(HERE/name),**reference_mf["files"][name])
  memory=types.SimpleNamespace(memory=lambda **kw:{"fixture":True},consume_memory=lambda *a,**kw:None)
  def aggregate(*args,**kw):
   calls.append(kw);self.assertEqual(args[0],self.documents["client"]["rank_bundle_refs"])
   self.guarded(capture=kw["capture_sha256"])
   return {"frames":[{"writer":{"installer_source_sha256":kw["installer_sha256"],
    "capture_source_sha256":kw["capture_sha256"]}}for _ in range(64)],"software_fixture_not_numeric":True}
  def module(name,r):
   if name=="fast_oracle":return oracle
   if name=="_kivi_firstdecode_fast_raw":return types.SimpleNamespace(oracle=oracle)
   if name=="_kivi_firstdecode_aggregate":return types.SimpleNamespace(consume=aggregate)
   return types.SimpleNamespace()
  def own(m,name):return next(r for r in m["files"]if Path(r["path"]).name==name)
  fake=dict(source=lambda s:(self.manifest,self.documents["client"]["source_ref"]),own=own,
   checked=lambda r:checked.append(r),memory_module=lambda m:memory,module=module,
   obj=lambda r:reference_mf if Path(r["path"]).name=="SOURCE_MANIFEST.json"else self.documents["client"],ref=lambda p:dict(path=str(p),bytes=p.stat().st_size,
    sha256=hashlib.sha256(p.read_bytes()).hexdigest()),publish=lambda p,v:result.update(v)or v)
  class Exec:
   def exec_module(s,m):m.__dict__.update(fake)
  spec=types.SimpleNamespace(name="_kivi_firstdecode_raw_source",loader=Exec())
  util=types.SimpleNamespace(spec_from_file_location=lambda *a:spec,module_from_spec=lambda s:types.ModuleType(s.name))
  previous=sys.modules.get(spec.name)
  def restore():
   if previous is None:sys.modules.pop(spec.name,None)
   else:sys.modules[spec.name]=previous
  self.addCleanup(restore)
  ns=dict(__file__=str(path),Path=Path,hashlib=hashlib,need=j.need,sys=sys,importlib=types.SimpleNamespace(util=util))
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),"exec"),ns)
  # This is actual corrected entry control flow with source-qualified producer
  # metadata. Device, memory and scalar aggregate are labelled test fixtures.
  with patch.object(Path,"resolve",lambda p:p if p==path else Path.absolute(p)):
   ns["entry"](self.documents["client"]["source_ref"]["sha256"],PREFILL_ACTUAL_REFS["client"],Path("fixture-output"),digest or sha,reference_sha)
  self.assertIn(original,checked);self.assertIn(self.roles["capture"],checked);self.assertIn(self.roles["provenance"],checked)
  return result,calls
 def test_actual_corrected_entry_delivers_provenance_not_layout_role(self):
  result,calls=self.caller()
  self.assertEqual(len(calls),1);self.assertEqual(calls[0]["capture_sha256"],self.roles["provenance"]["sha256"])
  self.assertEqual(result["original_prefill_capture_source"],self.roles["provenance"])
  self.assertEqual(result["native_layout_capture_source"],self.roles["capture"])
 def test_actual_entry_wrong_source_digest_rejected_before_loading(self):
  with self.assertRaisesRegex(ValueError,"exact explicitly source-bound"):self.caller("0"*64)
 def test_aggregate_numerical_call_only_capture_role_changed(self):
  def call(path):
   t=ast.parse(path.read_bytes())
   return next(n for n in ast.walk(t)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
    and isinstance(n.func.value,ast.Name)and n.func.value.id=="consume"and n.func.attr=="consume")
  old=call(PRODUCER_ARCHIVE/"consume_raw.py");new=call(HERE/"consume_raw_cpu.py")
  kw=next(k for k in new.keywords if k.arg=="capture_sha256")
  self.assertEqual(ast.dump(kw.value),ast.dump(ast.parse('roles["provenance"]["sha256"]',mode="eval").body))
  kw.value=ast.parse('roles["capture"]["sha256"]',mode="eval").body
  writer=next(k for k in new.keywords if k.arg=="writer_reader_ref")
  self.assertEqual(ast.dump(writer.value),ast.dump(ast.parse('references["writer"]',mode="eval").body))
  writer.value=ast.parse('roles["writer_reader"]',mode="eval").body
  self.assertEqual(ast.dump(new),ast.dump(old),"same original mathematical arguments except explicit new writer source/provenance")
 def test_whole_consumes_exact_new_caller_and_all64_source_records(self):
  s=importlib.util.spec_from_file_location("_provenance_whole_fixture",BASE_WHOLE/"consume_whole.py")
  core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
  entry=json.loads(HERE.joinpath("SOURCE_MANIFEST.json").read_bytes())["adapted_raw_entry_source"]
  original=next(r for r in self.manifest["files"]if Path(r["path"]).name=="consume_raw.py")
  mf=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  own_ref=dict(path=str(Path(entry["path"]).parent/"SOURCE_MANIFEST.json"),bytes=(HERE/"SOURCE_MANIFEST.json").stat().st_size,
   sha256=hashlib.sha256((HERE/"SOURCE_MANIFEST.json").read_bytes()).hexdigest())
  aggregate=next(r for r in self.manifest["files"]if Path(r["path"]).name=="consume_first_decode.py")
  value=dict(adapted_raw_entry_source=entry,original_raw_entry_source=original,
   writer_reader_source=mf["reference_sources"]["writer"],original_writer_reader_source=self.roles["writer_reader"],
   independent_vector_source=mf["reference_sources"]["vector"],aggregate_reference_source=mf["reference_sources"]["aggregate"],
   original_aggregate_source=aggregate,reference_manifest_source=own_ref,reference_numpy_version="1.26.4",
   original_prefill_capture_source=self.roles["provenance"],native_layout_capture_source=self.roles["capture"],
   frames=[{"writer":{"installer_source_sha256":self.roles["installer"]["sha256"],
    "capture_source_sha256":self.roles["provenance"]["sha256"],"codec_ref":self.roles["codec"],
    "independent_vector_source":mf["reference_sources"]["vector"],"numpy_version":"1.26.4",
    "scalar_reference_preserved":True,"candidate_math_called":False}}for _ in range(64)])
  with patch.object(core,"read",return_value=b"source fixture already pinned by actual own MF"),patch.object(core,"ref",return_value=own_ref):
   self.assertEqual(core.adapted_raw_sources(value,self.manifest,entry),entry)
   for field in("original_prefill_capture_source","native_layout_capture_source","original_raw_entry_source","writer_reader_source","independent_vector_source","aggregate_reference_source","original_aggregate_source"):
    with self.subTest(field=field):
     bad=copy.deepcopy(value);bad[field]["sha256"]="0"*64
     with self.assertRaises(ValueError):core.adapted_raw_sources(bad,self.manifest,entry)
   bad=copy.deepcopy(value);bad["frames"].pop()
   with self.assertRaisesRegex(ValueError,"all64"):core.adapted_raw_sources(bad,self.manifest,entry)
   bad=copy.deepcopy(value);bad["frames"][63]["writer"]["capture_source_sha256"]=self.roles["capture"]["sha256"]
   with self.assertRaisesRegex(ValueError,"every original writer"):core.adapted_raw_sources(bad,self.manifest,entry)
