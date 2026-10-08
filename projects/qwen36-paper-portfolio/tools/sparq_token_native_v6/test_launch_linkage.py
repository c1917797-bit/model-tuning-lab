"""Stdlib-only host-generated proof/actual ABI-argv contract regression. No native/NPU authority."""
import ast,copy,gc,hashlib,json,os,resource,subprocess,sys,tempfile,time,types,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import host,receipt,preflight,consume_numeric
from sparq_token_v4 import proof as gate
OLD=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-token-native-v5-002")
# Test output ownership is independent of canonical or private source placement.
TEST_TMP_PARENT=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-token-native-v6-004")
class CrossModule(unittest.TestCase):
 def test_explicit_owned_temporary_parent_independent_of_source_placement(self):
  self.assertEqual(TEST_TMP_PARENT,Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-token-native-v6-004"))
  self.assertTrue(TEST_TMP_PARENT.is_dir());self.assertFalse(TEST_TMP_PARENT.is_symlink())
  self.assertEqual(TEST_TMP_PARENT.resolve(),TEST_TMP_PARENT)
  self.assertIn(Path("/cache/cch"),TEST_TMP_PARENT.parents)
  tree=ast.parse(Path(receipt.ROOT/"test_launch_linkage.py").read_text())
  dirs=[k.value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
   n.func.attr=="TemporaryDirectory" for k in n.keywords if k.arg=="dir"]
  self.assertEqual(len(dirs),7)
  self.assertTrue(all(isinstance(n,ast.Name) and n.id=="TEST_TMP_PARENT" for n in dirs))
  if Path("/cache/cch") not in Path(__file__).parents:
   self.assertNotEqual(TEST_TMP_PARENT,Path(__file__).parent)
 def fixture(self,root):
  source=dict(path=str(receipt.ROOT/"SOURCE_MANIFEST.json"),sha256="1"*64)
  files={n:receipt.sha(receipt.ROOT/n) for n in receipt.OWN}
  cpu_root=root/"cpu-preflight";cpu_root.mkdir()
  mounts={str(host.ROOT):(str(host.ROOT),False),str(cpu_root):(str(cpu_root),False),"/sparq-results":(str(cpu_root),True)}
  def inspect(e,pid,started,finished=""):
   return dict(Id=e["cid"],Name="/"+e["name"],Image=receipt.IMAGE,
    Config=dict(Image=receipt.IMAGE,Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],
     WorkingDir=str(host.ROOT),Labels=host.labels(e),Env=[k+"="+v for k,v in host.environment().items()]),
    HostConfig=dict(Privileged=False,Memory=host.MEM,MemorySwap=host.MEM,NanoCpus=10**9,CpusetCpus="1",
     IpcMode="private",NetworkMode="none",ShmSize=2*1024**3,PidsLimit=512,CapDrop=["ALL"],
     SecurityOpt=["no-new-privileges"],Devices=[dict(PathOnHost=p,PathInContainer=g,CgroupPermissions="rwm")
      for p,g in host.expected_devices(e["mode"]).items()]),
    Mounts=[dict(Type="bind",Source=p,Destination=g,RW=rw) for g,(p,rw) in e["mounts"].items()],
    State=dict(Running=pid>0,Pid=pid,StartedAt=started,FinishedAt=finished,OOMKilled=False),ExecIDs=None)
  cpu=dict(cid="c"*64,name="cpu-only-fixture",mode="cpu",source=source,host_sha256=files["host.py"],
   numeric_sha256=files["numeric_gate.py"],guest_cpu=1,mounts=mounts)
  npu=dict(cpu,mode="npu",cid="6"*64,name="npu-fixture")
  live=inspect(cpu,42,"2026-10-07T12:00:00Z")
  stopped=inspect(cpu,0,"2026-10-07T12:00:00Z","2026-10-07T12:00:01Z")
  x=inspect(npu,43,"2026-10-07T12:00:02Z")
  owned=receipt.write_new(cpu_root/"OWNED.json",cpu)
  live_ref=receipt.write_new(cpu_root/"live.json",[live]);stopped_ref=receipt.write_new(cpu_root/"stopped.json",[stopped])
  stop_ref=receipt.write_new(cpu_root/"stop.json",dict(requested_argv=[host.DOCKER,"stop","--time","15",cpu["cid"]],exit_code=0))
  cleanup=receipt.write_new(cpu_root/"cleanup.json",dict(container=cpu["cid"],stopped=True,retained=True,deleted=False,
   errors=[],primary_error=None,after_inspect=stopped_ref,stop_receipt=stop_ref))
  a=SimpleNamespace(source_manifest=Path(source["path"]),source_manifest_sha256=source["sha256"])
  # The full child vector is the actual host producer's exact args; no Torch/Docker executes.
  args=receipt.abi_image_argv(host.BASE,source,cpu_root)
  abi=dict(actual_argv=args,actual_observations=dict(actual_argv=args),actual_exports={"fixture_only":"no native evidence"},
   original_observations=dict(path=str(cpu_root/"ABI_OBSERVATIONS.json"),sha256="2"*64))
  ndref=receipt.write_new(cpu_root/"ABI.json",abi)
  command=receipt.docker_argv(cpu["cid"],args)
  child=receipt.write_new(cpu_root/"child.json",dict(requested_argv=command,
   argv=["/usr/bin/prlimit","--as=unlimited","--",*command],exit_code=0))
  canary=receipt.write_new(root/"canary.json",dict(native_no_device_abi=ndref,preinit_actual_exports=abi["actual_exports"],
   source_manifest=source,sources_before=files,sources_after=files,fresh_canary_passed=True,fixture_only=True))
  idle=receipt.write_new(root/"idle.json",dict(fixture_only=True))
  fields=dict(schema="sparq.token-device-proof/v4",privileged=False,container_id=npu["cid"],container_inspect=x,
   logical_to_physical={"0":6},physical_npu_ids=[6],source_manifest=source,sources=files,observed_at_unix_ns=100,
   exclusive_resource_check_passed=True,fresh_resource_audit={"fixture_only":"not actual resources"},
   actual_guest_cpu=dict(effective_capacity=1,effective_cpus=[1]),native_no_device_abi=ndref,native_no_device_child=child,
   canary=canary,cpu_container_id=cpu["cid"],cpu_only_inspect=live_ref,cpu_only_owned=owned,cpu_only_cleanup=cleanup,
   cpu_stopped_inspect=stopped_ref,probe_idle=idle)
  produced=host.make_device_proof(fields)
  pending=dict(path=str(root/"proof.json"),sha256="@ACTUAL_DEVICE_PROOF_SHA256@")
  produced["image_python_argv_template"]=[receipt.PY,"-B",*host.numerical_args(a,pending)]
  return dict(source=source,files=files,proof=produced,args=args,child_ref=child,abi_ref=ndref,cpu_root=cpu_root,a=a)
 def validate(self,f,root,value=None,validator=gate.validate_proof):
  value=f["proof"] if value is None else value
  digest=hashlib.sha256(receipt.canonical(value)+b"\n").hexdigest()
  path=root/("proof-"+digest+".json")
  if not path.exists():receipt.write_new(path,value)
  # Proof ref path is identity too: rebuild one producer template for the exact new SHA Ref.
  template=copy.deepcopy(value)
  index=template["image_python_argv_template"].index("--device-proof")+1
  template["image_python_argv_template"][index]=str(path)
  raw=receipt.canonical(template)+b"\n";path.write_bytes(raw)
  digest=hashlib.sha256(raw).hexdigest()
  argv=[digest if a=="@ACTUAL_DEVICE_PROOF_SHA256@" else a for a in template["image_python_argv_template"]]
  # Only actual native ABI checks are mocked. Every owner/mount/argv/proof/cleanup
  # guard below runs the real source; this fixture cannot produce a component.
  with mock.patch.object(preflight,"validate_abi",side_effect=lambda x,s,fs:x):
   return validator(str(path),digest,f["source"],f["files"],argv,now_ns=100)
 def test_actual_frozen_predecessor_sha_and_two_conflict_source_locations(self):
  expected={"host.py":"3de923e6b8048de76fc2f70e32c56b2c0c073b22776d1dfe1b8aec0ead14d8ca",
   "sparq_token_v4/proof.py":"70eed04080d4a3e8c6a81871d3da81aa1bed6fcde3c06b32d0e04d37d89c539c"}
  for n,s in expected.items():self.assertEqual(receipt.sha(OLD/n),s)
  host_text=(OLD/"host.py").read_text();old_text=(OLD/"sparq_token_v4/proof.py").read_text()
  self.assertIn('OWNER="sparq-token-v5"',host_text)
  self.assertIn('=="sparq-token-v4"',old_text)
  self.assertIn('"--host-output-root",str(cpu_out)',host_text)
  expected_node=next(n for n in ast.walk(ast.parse(old_text)) if isinstance(n,ast.Assign) and
   any(isinstance(t,ast.Name) and t.id=="expected" for t in n.targets))
  self.assertNotIn("--host-output-root",ast.unparse(expected_node))
 def test_actual_host_generated_proof_and_complete_CPU_argv_validate(self):
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-004-linkage-") as td:
   root=Path(td);f=self.fixture(root)
   got=self.validate(f,root)
   self.assertEqual(got["container_inspect"]["Config"]["Labels"]["model-tuning-lab.owner"],receipt.OWNER)
   self.assertEqual(got["cpu_host_output_root"],str(f["cpu_root"]))
   self.assertEqual(receipt.load(got["native_no_device_abi"])["actual_argv"],f["args"])
   self.assertNotIn("torch",sys.modules)
 def test_old_owner_source_rejected_without_union(self):
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-004-linkage-") as td:
   root=Path(td);f=self.fixture(root)
   for owner in ("sparq-token-v4","sparq-token-v5","other"):
    value=copy.deepcopy(f["proof"]);value["container_inspect"]["Config"]["Labels"]["model-tuning-lab.owner"]=owner
    with self.subTest(owner=owner),self.assertRaisesRegex(ValueError,"owned numeric container"):
     self.validate(f,root,value)
 def test_actual_predecessor_two_rejections_reproduced_without_device(self):
  module=types.ModuleType("sparq_token_v4._original_frozen_proof");module.__package__="sparq_token_v4"
  exec(compile((OLD/"sparq_token_v4/proof.py").read_bytes(),str(OLD/"sparq_token_v4/proof.py"),"exec"),module.__dict__)
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-004-linkage-") as td:
   root=Path(td);f=self.fixture(root)
   with self.assertRaisesRegex(ValueError,"owned numeric container"):
    self.validate(f,root,validator=module.validate_proof)
   value=copy.deepcopy(f["proof"]);value["container_inspect"]["Config"]["Labels"]["model-tuning-lab.owner"]="sparq-token-v4"
   with self.assertRaisesRegex(ValueError,"original Docker child"):
    self.validate(f,root,value,validator=module.validate_proof)
 def test_complete_ABI_command_negatives_before_NPU_and_again_in_proof(self):
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-004-linkage-") as td:
   root=Path(td);f=self.fixture(root);abi=receipt.load(f["abi_ref"]);child=receipt.load(f["child_ref"])
   receipt.validate_cpu_abi_child("c"*64,f["cpu_root"],f["source"],child,abi)
   for mode in ("omit-root","duplicate-root","wrong-root","reorder-root","wrong-source","wrong-CID","no-prlimit","failed","observer-argv","observer-root"):
    a=copy.deepcopy(abi);c=copy.deepcopy(child);args=list(f["args"]);i=args.index("--host-output-root")
    if mode=="omit-root":args=args[:i]
    if mode=="duplicate-root":args+=args[i:]
    if mode=="wrong-root":args[i+1]=str(root/"foreign")
    if mode=="reorder-root":args=args[:4]+args[i:]+args[4:i]
    if mode=="wrong-source":args[args.index("--source-manifest-sha256")+1]="0"*64
    if mode in ("omit-root","duplicate-root","wrong-root","reorder-root","wrong-source"):
     a["actual_argv"]=a["actual_observations"]["actual_argv"]=args
     c["requested_argv"]=receipt.docker_argv("c"*64,args);c["argv"]=["/usr/bin/prlimit","--as=unlimited","--",*c["requested_argv"]]
    if mode=="wrong-CID":c["requested_argv"][2]="b"*64
    if mode=="no-prlimit":c["argv"]=c["requested_argv"]
    if mode=="failed":c["exit_code"]=1
    if mode=="observer-argv":a["actual_observations"]["actual_argv"]=args[:-2]
    if mode=="observer-root":a["original_observations"]["path"]=str(root/"wrong/ABI_OBSERVATIONS.json")
    with self.subTest(mode=mode),self.assertRaises(ValueError):
     receipt.validate_cpu_abi_child("c"*64,f["cpu_root"],f["source"],c,a)
    value=copy.deepcopy(f["proof"])
    value["native_no_device_child"]=receipt.write_new(root/(mode+"-child.json"),c)
    value["native_no_device_abi"]=receipt.write_new(root/(mode+"-abi.json"),a)
    # Keep actual own ABI tree path; only shape fixture contents mutate.
    value["native_no_device_abi"]["path"]=f["abi_ref"]["path"]
    original=Path(f["abi_ref"]["path"]).read_bytes()
    Path(f["abi_ref"]["path"]).write_bytes(receipt.canonical(a)+b"\n")
    value["native_no_device_abi"]["sha256"]=receipt.sha(Path(f["abi_ref"]["path"]))
    canary=receipt.load(value["canary"]);canary["native_no_device_abi"]=value["native_no_device_abi"]
    value["canary"]=receipt.write_new(root/(mode+"-canary.json"),canary)
    try:
     with self.subTest(proof=mode),self.assertRaises(ValueError):self.validate(f,root,value)
    finally:Path(f["abi_ref"]["path"]).write_bytes(original)
 def test_CPU_root_comes_only_from_owned_mount_not_argv(self):
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-004-linkage-") as td:
   root=Path(td);f=self.fixture(root);value=copy.deepcopy(f["proof"])
   value["cpu_host_output_root"]=str(root/"different")
   with self.assertRaisesRegex(ValueError,"CPU output mount"):
    self.validate(f,root,value)
   fields=copy.deepcopy(f["proof"]);fields.pop("image_python_argv_template")
   with self.assertRaisesRegex(ValueError,"producer alone"):
    host.make_device_proof(fields)
 def test_host_calls_full_ABI_guard_before_NPU_create(self):
  tree=ast.parse(Path(host.__file__).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="execute")
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
  guard=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=="validate_cpu_abi_child")
  create=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=="create" and
   isinstance(n.func.value,ast.Name) and n.func.value.id=="ctl")
  self.assertLess(guard.lineno,create.lineno)
  self.assertTrue(any(isinstance(n.func,ast.Name) and n.func.id=="make_device_proof" for n in calls))
 def test_exact_single_helper_used_in_host_proof_and_original_consumer(self):
  host_text=Path(host.__file__).read_text();gate_text=Path(gate.__file__).read_text();consumer_text=Path(consume_numeric.__file__).read_text()
  self.assertIn("OWNER=c.OWNER",host_text);self.assertIn("==OWNER",gate_text)
  self.assertIn("probe_args=c.abi_image_argv(BASE,source,cpu_out)[2:]",host_text)
  for text in (host_text,gate_text,consumer_text):self.assertIn("validate_cpu_abi_child(",text)
  self.assertNotIn('=="sparq-token-v4"',gate_text);self.assertNotIn('=="sparq-token-v5"',gate_text)
 def test_source_changed_proof_not_claimed_byte_exact_math_unchanged(self):
  for n,s in {"sparq_token_v4/core.py":"fc7068c8c48473c23137c273603fec3a13d52760d5dfc89d1ae37a5ba2c8717c",
   "sparq_token_v4/oracle.py":"c6680b02473da9188d7ae1998769555b6fcea67b03c1284d3d590340e01a639f",
   "model_bridge.py":"a85dd04893ad74feaaf1f2bf85e807e387b2957ce6db6a6034bf098bb951e81d",
   "numeric_gate.py":"35d09584475510c034643f01d9b83d9c24ea9840a8d5238dcd736e98b4c202e8",
   "preflight.py":"3f1d51d767da1b762cbde06f54080f3e7e2aed253709a22c98af43e98978cbc0"}.items():
   self.assertEqual(receipt.sha(receipt.ROOT/n),s)
  self.assertNotEqual(receipt.sha(Path(gate.__file__)),"70eed04080d4a3e8c6a81871d3da81aa1bed6fcde3c06b32d0e04d37d89c539c")
  self.assertEqual(receipt.OWNER,"sparq-token-v6");self.assertNotIn("torch",sys.modules)

# A real stdlib subprocess produces inspection fixtures; it never invokes Docker,
# devices, Torch, or native code. These are cleanup control-flow tests only.
CLEANUP_FIXTURE_CLI=r"""
import json,sys,time
from pathlib import Path
path=Path(sys.argv[1]);action=sys.argv[2]
value=json.loads(path.read_text())
value["commands"].append(action)
if action=="stop":
 if value.get("fail_stop"):
  path.write_text(json.dumps(value));print("fixture stop failure",file=sys.stderr);sys.exit(3)
 value["inspect"]["State"].update(Running=False,Pid=0)
 value["inspect"]["ExecIDs"]=None
 path.write_text(json.dumps(value));print(value["inspect"]["Id"])
elif action=="inspect":
 path.write_text(json.dumps(value));print(json.dumps([value["inspect"]]))
elif action=="release":
 path.write_text(json.dumps(value));print("fixture-only release; no hardware evidence")
else:raise RuntimeError("no other fixture action permitted")
"""
def fixture_controller(cls,root,live,expected,primary=None):
 ctl=object.__new__(cls)
 ctl.out=root;root.mkdir()
 ctl.cid=expected["cid"];ctl.expected=copy.deepcopy(expected);ctl.name=expected["name"]
 ctl.primary=primary;ctl.secondary=[];ctl.child=None;ctl.cleanup_deadline=None
 ctl.created_monotonic=time.monotonic();ctl.deadline=ctl.created_monotonic+600
 ctl.protected="fixture-protected";ctl.cpu=None
 state=root/"fixture-cli-state.json"
 state.write_text(json.dumps(dict(inspect=live,commands=[])))
 def run(wrapped,limit):
  requested=wrapped[3:] if wrapped[:3]==["/usr/bin/prlimit","--as=unlimited","--"] else wrapped
  if requested==[host.DOCKER,"inspect",ctl.cid]:action="inspect"
  elif requested==[host.DOCKER,"stop","--time","15",ctl.cid]:action="stop"
  elif requested==[host.H.SMI,"info"]:action="release"
  else:raise RuntimeError("test runner refuses all non-cleanup operations")
  actual=[sys.executable,"-B","-c",CLEANUP_FIXTURE_CLI,str(state),action]
  child=subprocess.run(actual,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=limit,check=False)
  return dict(argv=list(wrapped),exit_code=child.returncode,stdout=child.stdout,stderr=child.stderr,
   observed_utc=host.utc().isoformat(),fixture_only=True,actual_test_subprocess_argv=actual)
 ctl.h=SimpleNamespace(run=run,protected=lambda text:"fixture-protected",idle_one=lambda text,card:None)
 def refuse_admission(*args,**kwargs):raise RuntimeError("ordinary RAM/CPU admission must not block exact owned cleanup")
 ctl.resources=refuse_admission
 return ctl,state
def cleanup_regression():
 # Sequential allocations make the real historical SELF+CHILD peaks cross the
 # unchanged 256MiB gate without concurrent ordinary RSS exceeding 256MiB.
 resource.setrlimit(resource.RLIMIT_AS,(host.HOST_MEM,host.HOST_MEM))
 resource.setrlimit(resource.RLIMIT_CPU,(10,10))
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
 pages=bytearray(128*1024**2)
 for i in range(0,len(pages),4096):pages[i]=1
 parent_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 del pages;gc.collect()
 parent_current=int(next(l.split()[1] for l in Path("/proc/self/status").read_text().splitlines() if l.startswith("VmRSS:")))
 memory_cli="import json,resource; p=bytearray(128*1024**2); print(json.dumps({'peak_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'torch_imported':False}))"
 child=subprocess.run([sys.executable,"-B","-c",memory_cli],capture_output=True,text=True,check=True,timeout=3)
 child_peak=json.loads(child.stdout)["peak_kib"]
 aggregate=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss+resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
 assert aggregate>host.HOST_MEM//1024,(parent_peak,child_peak,aggregate)
 assert parent_current+child_peak<=host.HOST_MEM//1024,(parent_current,child_peak)
 assert "torch" not in sys.modules
 with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-004-cleanup-") as td:
  root=Path(td);f=CrossModule().fixture(root)
  live=f["proof"]["container_inspect"]
  expected=dict(cid=live["Id"],name=live["Name"][1:],mode="npu",source=f["source"],
   host_sha256=host.sha(host.__file__),numeric_sha256=f["files"]["numeric_gate.py"],guest_cpu=1,
   mounts={m["Destination"]:(m["Source"],m["RW"]) for m in live["Mounts"]})
  old=types.ModuleType("_sparq_original_v6_002_host")
  old.__file__=str(TEST_TMP_PARENT.parent/"sparq-token-native-v6-002/host.py")
  exec(compile(Path(old.__file__).read_bytes(),old.__file__,"exec"),old.__dict__)
  assert receipt.sha(Path(old.__file__))=="921b33e7aab03145f7ef9bb2e95ef2a4afda01c315edc3515388900bcf36987d"
  old_ctl,state=fixture_controller(old.Controller,root/"old-rss",live,expected)
  result=receipt.load(old_ctl.cleanup());commands=json.loads(state.read_text())["commands"]
  assert not result["stopped"] and commands==["inspect"],(result,commands)
  assert "cumulative peak RSS" in str(result["errors"]),result
  expired,state=fixture_controller(old.Controller,root/"old-expired",live,expected)
  expired.deadline=time.monotonic()-1
  result=receipt.load(expired.cleanup())
  assert not result["stopped"] and json.loads(state.read_text())["commands"]==[]
  primary=ValueError("original numerical/admission failure retained")
  ctl,state=fixture_controller(host.Controller,root/"successor",live,expected,primary)
  ctl.deadline=time.monotonic()-1
  # Only software fixture cutoff is changed, not source/runtime cutoff.
  with mock.patch.object(host,"CUTOFF",host.datetime(1999,1,1,tzinfo=host.timezone.utc)):
   result=receipt.load(ctl.cleanup())
  commands=json.loads(state.read_text())["commands"]
  assert commands==["inspect","stop","inspect","release"],commands
  assert result["stopped"] is True and result["retained"] is True and result["deleted"] is False and result["errors"]==[]
  assert result["primary_error"]==repr(primary)
  assert len(ctl.secondary)==3 and any("256MiB" in s for s in ctl.secondary) and any("phase5400" in s for s in ctl.secondary) and any("cutoff" in s for s in ctl.secondary)
  assert 0<ctl.cleanup_deadline-time.monotonic()<=host.CLEANUP_SECONDS
  stop=receipt.load(result["stop_receipt"])
  assert stop["cleanup_safety_only"] and len(stop["original_admission_failures"])==3
  assert stop["requested_argv"]==[host.DOCKER,"stop","--time","15",expected["cid"]]
  assert stop["cleanup_resource_snapshot"]["formal_limit_bytes"]==256*1024**2
  assert stop["actual_test_subprocess_argv"][0]==sys.executable and stop["fixture_only"]
  # Normal call still runs the original actual RSS admission and stays failed.
  normal,state=fixture_controller(host.Controller,root/"normal",live,expected)
  try:normal.call("inspect",[host.DOCKER,"inspect",normal.cid])
  except ValueError as error:assert "cumulative peak RSS" in str(error)
  else:raise AssertionError("normal RSS gate was relaxed")
  # Full inspect source ownership is mandatory even in expired/RSS recovery.
  wrong=copy.deepcopy(live);wrong["Config"]["Labels"]["model-tuning-lab.owner"]="foreign"
  foreign,state=fixture_controller(host.Controller,root/"foreign",wrong,expected)
  foreign.deadline=time.monotonic()-1
  result=receipt.load(foreign.cleanup())
  assert not result["stopped"] and json.loads(state.read_text())["commands"]==["inspect"]
  assert "owned source/controller labels" in str(result["errors"])
  # No label/argv shortcut, additional work, pre-inspect stop or foreign CID.
  refusal,state=fixture_controller(host.Controller,root/"refusal",live,expected)
  for label,argv in [("stop-retain",[host.DOCKER,"stop","--time","15",refusal.cid]),
    ("create",[host.DOCKER,"create","x"]),("inspect",[host.DOCKER,"inspect","b"*64]),
    ("release-smi",[host.H.SMI,"info"])]:
   try:refusal.call(label,argv,cleanup=True)
   except ValueError:pass
   else:raise AssertionError("unvalidated cleanup work accepted")
  assert json.loads(state.read_text())["commands"]==[]
  bounded,state=fixture_controller(host.Controller,root/"bounded",live,expected)
  bounded.cleanup_deadline=time.monotonic()-1
  original=bounded.cleanup_deadline
  result=receipt.load(bounded.cleanup())
  assert not result["stopped"] and bounded.cleanup_deadline==original and json.loads(state.read_text())["commands"]==[]
  failed,state=fixture_controller(host.Controller,root/"stop-failed",live,expected)
  sv=json.loads(state.read_text());sv["fail_stop"]=True;state.write_text(json.dumps(sv))
  result=receipt.load(failed.cleanup())
  assert not result["stopped"] and json.loads(state.read_text())["commands"]==["inspect","stop"]
  assert result["errors"] and failed.secondary
  oom=copy.deepcopy(live);oom["State"]["OOMKilled"]=True
  invalid,state=fixture_controller(host.Controller,root/"OOM-invalid",oom,expected)
  result=receipt.load(invalid.cleanup())
  assert result["stopped"] and result["retained"] and result["errors"] and any("OOM" in e for e in result["errors"])
  protected,state=fixture_controller(host.Controller,root/"protected-changed",live,expected)
  protected.h.protected=lambda text:"changed-protected"
  result=receipt.load(protected.cleanup())
  assert result["stopped"] and result["retained"] and result["errors"] and any("protected0..3" in e for e in result["errors"])
  summary=dict(actual_stdlib_subprocess=True,parent_peak_kib=parent_peak,parent_current_after_free_kib=parent_current,
   child_peak_kib=child_peak,latched_aggregate_kib=aggregate,unchanged_formal_limit_bytes=host.HOST_MEM,
   instantaneous_parent_current_plus_child_peak_kib=parent_current+child_peak,
   predecessor_RSS_stopped=False,predecessor_expired_stopped=False,successor_exact_stop_retained=True,
   original_primary_preserved=True,resource_and_expiry_secondary_preserved=True,ordinary_admission_not_called=True,
   ownership_failure_never_stopped=True,normal_RSS_gate_not_relaxed=True,cleanup_90s_not_reset=True,
   stop_failure_preserved=True,OOM_and_protected_failures_after_stop_preserved=True,
   torch_imported=False,docker_executed=False,npu_executed=False,numerical_PASS=False)
 return summary
class CleanupLinkage(unittest.TestCase):
 def test_actual_subprocess_latched_RSS_expiry_and_exact_cleanup(self):
  child=subprocess.run([sys.executable,"-B",str(receipt.ROOT/"test_launch_linkage.py"),"--cleanup-regression"],
   capture_output=True,text=True,check=False,timeout=7)
  self.assertEqual(child.returncode,0,child.stdout+"\n"+child.stderr)
  summary=json.loads(child.stdout)
  self.assertTrue(summary["actual_stdlib_subprocess"]);self.assertTrue(summary["successor_exact_stop_retained"])
  self.assertGreater(summary["latched_aggregate_kib"],256*1024)
  self.assertLessEqual(summary["instantaneous_parent_current_plus_child_peak_kib"],256*1024)
  self.assertFalse(summary["docker_executed"]);self.assertFalse(summary["npu_executed"])
  print("SPARQ_V6_003_REAL_CLEANUP_REGRESSION "+json.dumps(summary,sort_keys=True),flush=True)
 def test_frozen_H8_not_mutated_normal_rss_and_original_lease_remain(self):
  self.assertEqual(host.H.HOST_MEM,256*1024**2)
  self.assertEqual(host.HOST_MEM,256*1024**2)
  self.assertEqual(host.PHASE_SECONDS,5400);self.assertEqual(host.CLEANUP_SECONDS,90)
  self.assertEqual(host.CUTOFF.isoformat(),"2026-10-09T11:17:31+00:00")
  self.assertEqual(receipt.sha(host.H8),host.H8_SHA)
  ctl=object.__new__(host.Controller);ctl.deadline=time.monotonic()-1;ctl.cleanup_deadline=None
  with self.assertRaises(ValueError):ctl.remaining()
  with mock.patch.object(host,"CUTOFF",host.datetime(1999,1,1,tzinfo=host.timezone.utc)):
   ctl.deadline=time.monotonic()+600
   with self.assertRaises(ValueError):ctl.remaining()
  self.assertEqual(host.Controller.cleanup,host.H.Controller.cleanup)

 def test_final_time_failure_is_latched_before_success_not_a_new_lease(self):
  with mock.patch.object(host,"CUTOFF",host.datetime(2099,1,1,tzinfo=host.timezone.utc)):
   self.assertEqual(host.formal_time_failures(time.monotonic()+600),[])
   self.assertEqual(host.formal_time_failures(time.monotonic()-1),
    ["formal whole phase5400 exhausted; safety-only recovery"])
  with mock.patch.object(host,"CUTOFF",host.datetime(1999,1,1,tzinfo=host.timezone.utc)):
   self.assertEqual(host.formal_time_failures(time.monotonic()+600),
    ["fixed portfolio cutoff exhausted; safety-only recovery"])
   self.assertEqual(len(host.formal_time_failures(time.monotonic()-1)),2)
  tree=ast.parse(Path(host.__file__).read_text())
  execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="execute")
  guard=next(n for n in ast.walk(execute) if isinstance(n,ast.For) and isinstance(n.iter,ast.Call) and
   isinstance(n.iter.func,ast.Name) and n.iter.func.id=="formal_time_failures")
  success=next(n for n in ast.walk(execute) if isinstance(n,ast.Assign) and
   any(isinstance(t,ast.Name) and t.id=="success" for t in n.targets))
  self.assertLess(guard.lineno,success.lineno)
  self.assertIn("not ctl.secondary",ast.unparse(success))


def raise_actual_peak():
 # Real SELF+CHILD latched aggregate >256MiB; sequential current RSS remains <256MiB.
 pages=bytearray(128*1024**2)
 for i in range(0,len(pages),4096):pages[i]=1
 del pages;gc.collect()
 current=int(next(l.split()[1] for l in Path("/proc/self/status").read_text().splitlines() if l.startswith("VmRSS:")))
 cli="import resource,json; p=bytearray(128*1024**2); print(json.dumps({'peak_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))"
 child=subprocess.run([sys.executable,"-B","-c",cli],capture_output=True,text=True,check=True,timeout=3)
 peak=json.loads(child.stdout)["peak_kib"]
 aggregate=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss+resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
 assert aggregate>256*1024 and current+peak<=256*1024,(aggregate,current,peak)
 return dict(latched_aggregate_kib=aggregate,instantaneous_current_plus_child_peak_kib=current+peak)
CREATE_FIXTURE_CLI=r"""
import json,sys
from pathlib import Path
path=Path(sys.argv[1]);action=sys.argv[2];value=json.loads(path.read_text());value["commands"].append(action)
path.write_text(json.dumps(value))
if action=="unique":print("")
elif action=="create":
 print(value["create_stdout"]);sys.exit(value["create_exit"])
else:raise RuntimeError("no real Docker CLI or other test action permitted")
"""
def create_regression(mode):
 assert mode in ("old-rss","new-rss","new-expiry","new-malformed","new-failed","new-preexpiry","new-preRSS")
 resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(10,10))
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
 cls=host.Controller
 if mode=="old-rss":
  old=types.ModuleType("_sparq_original_v6_003_create")
  old.__file__=str(TEST_TMP_PARENT.parent/"sparq-token-native-v6-003/host.py")
  assert receipt.sha(old.__file__)=="a6256c84a5bb05a4e835d9d816463983340727a8474138a1a29f8aafeda7a848"
  exec(compile(Path(old.__file__).read_bytes(),old.__file__,"exec"),old.__dict__);cls=old.Controller
 with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-004-create-") as td:
  root=Path(td);f=CrossModule().fixture(root)
  ctl=object.__new__(cls);ctl.out=root/"owned";ctl.out.mkdir();ctl.cid=None;ctl.expected=None
  ctl.name="create-fixture-only";ctl.device_phase="cpu";ctl.cpu=dict(guest_cpu=1)
  ctl.primary=None;ctl.secondary=[];ctl.child=None;ctl.protected="fixture-protected"
  ctl.cleanup_deadline=None;ctl.created_monotonic=time.monotonic();ctl.deadline=ctl.created_monotonic+600
  ctl.mounts=lambda artifacts=None:{str(root):(str(root),False),"/sparq-results":(str(ctl.out),True)}
  state=ctl.out/"fixture-cli-state.json";cid="d"*64
  state.write_text(json.dumps(dict(commands=[],create_stdout="not-a-complete-cid" if mode=="new-malformed" else cid,
   create_exit=2 if mode=="new-failed" else 0)))
  actual_peak={}
  def run(wrapped,limit):
   requested=wrapped[3:] if wrapped[:3]==["/usr/bin/prlimit","--as=unlimited","--"] else wrapped
   if requested==[host.DOCKER,"ps","-a","--filter","name=^/"+ctl.name+"$","--format","{{.ID}}"]:action="unique"
   elif requested[0:2]==[host.DOCKER,"create"] and requested==host.create_argv(ctl.expected):action="create"
   elif requested==[host.DOCKER,"inspect",ctl.cid]:action="inspect"
   elif requested==[host.DOCKER,"stop","--time","15",ctl.cid]:action="stop"
   elif requested==[host.H.SMI,"info"]:action="release"
   else:raise RuntimeError("test runner rejects create/start/work/foreign CLI")
   code=CREATE_FIXTURE_CLI if action in ("unique","create") else CLEANUP_FIXTURE_CLI
   actual=[sys.executable,"-B","-c",code,str(state),action]
   child=subprocess.run(actual,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=limit,check=False)
   if action=="create":
    # The stdlib stand-in's successful return precedes the real resource fault.
    value=json.loads(state.read_text());e=ctl.expected
    live=copy.deepcopy(f["proof"]["container_inspect"])
    live.update(Id=cid,Name="/"+ctl.name,Mounts=[dict(Type="bind",Source=p,Destination=g,RW=rw) for g,(p,rw) in e["mounts"].items()])
    live["Config"].update(Labels=host.labels(e),Env=[k+"="+v for k,v in host.environment().items()])
    live["HostConfig"]["Devices"]=[];live["State"].update(Running=False,Pid=0);live["ExecIDs"]=None
    value["inspect"]=live;state.write_text(json.dumps(value))
    if mode in ("old-rss","new-rss"):actual_peak.update(raise_actual_peak())
    if mode=="new-expiry":ctl.deadline=time.monotonic()-1
   return dict(argv=list(wrapped),exit_code=child.returncode,stdout=child.stdout,stderr=child.stderr,
    observed_utc=host.utc().isoformat(),fixture_only=True,actual_test_subprocess_argv=actual)
  ctl.h=SimpleNamespace(run=run,protected=lambda text:"fixture-protected",idle_one=lambda text,card:None)
  if mode=="new-preexpiry":ctl.deadline=time.monotonic()-1
  if mode=="new-preRSS":actual_peak.update(raise_actual_peak())
  error=None
  try:ctl.create({},f["source"],f["files"])
  except BaseException as e:error=e;ctl.primary=e
  assert error is not None and "torch" not in sys.modules
  value=json.loads(state.read_text());commands=value["commands"]
  owns=(mode in ("new-rss","new-expiry"))
  if owns:
   assert ctl.cid==cid and ctl.expected["cid"]==cid and (ctl.out/"OWNED.json").is_file()
   owned=json.loads((ctl.out/"OWNED.json").read_bytes());raw=receipt.load(owned["create_receipt"])
   assert owned["cid"]==cid and raw["exit_code"]==0 and raw["stdout"].strip()==cid
   assert raw["requested_argv"]==host.create_argv(ctl.expected) and raw["fixture_only"]
   assert owned["source"]==f["source"] and owned["sources"]==f["files"]
   if mode=="new-rss":assert "cumulative peak RSS" in str(error)
   else:assert "phase/cutoff" in str(error)
   # Already-created identity is not a retry or a successful admission.
   try:ctl.create_owned(f["files"])
   except ValueError:pass
   else:raise AssertionError("second creation admitted")
  else:
   assert ctl.cid is None and not (ctl.out/"OWNED.json").exists(),(mode,ctl.cid)
  cleanup=receipt.load(ctl.cleanup())
  commands=json.loads(state.read_text())["commands"]
  assert "start" not in commands
  if owns:
   assert cleanup["stopped"] and cleanup["retained"] and cleanup["primary_error"]==repr(error)
   assert commands==["unique","create","inspect","stop","inspect","release"],commands
  elif mode in ("new-preexpiry","new-preRSS"):assert "create" not in commands
  else:
   assert commands==["unique","create"] and not cleanup["stopped"],(mode,commands)
   retained=list(ctl.out.glob("create-*.json"));assert len(retained)==1
   raw=json.loads(retained[0].read_bytes())
   if mode=="old-rss":assert raw["stdout"].strip()==cid and raw["exit_code"]==0
   else:assert not (ctl.out/"OWNED.json").exists()
  return dict(mode=mode,actual_stdlib_subprocess=True,successful_exact_CID_latched_before_post_guard=owns,
   OWNED_before_post_guard=owns,formal_create_admission_failed=True,exact_stop_retained=bool(cleanup["stopped"]),
   actual_commands=commands,original_error=repr(error),actual_peak=actual_peak,
   no_create_retry=True,no_start_after_failed_guard=True,Docker_executed=False,Torch_imported=False,NPU_executed=False,numerical_PASS=False)
class CreateLinkage(unittest.TestCase):
 def test_actual_completed_create_then_resource_or_time_failure_retains_only_exact_CID(self):
  summaries=[]
  for mode in ("old-rss","new-rss","new-expiry","new-malformed","new-failed","new-preexpiry","new-preRSS"):
   child=subprocess.run([sys.executable,"-B",str(receipt.ROOT/"test_launch_linkage.py"),"--create-regression",mode],
    capture_output=True,text=True,check=False,timeout=4)
   self.assertEqual(child.returncode,0,mode+"\n"+child.stdout+"\n"+child.stderr)
   value=json.loads(child.stdout);self.assertFalse(value["Docker_executed"]);self.assertFalse(value["numerical_PASS"])
   summaries.append(value)
  print("SPARQ_V6_004_REAL_CREATE_REGRESSION "+json.dumps(summaries,sort_keys=True),flush=True)
 def test_actual_source_owned_persistence_precedes_post_create_RSS_and_time(self):
  tree=ast.parse(Path(host.__file__).read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="Controller")
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="create_owned")
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
  run=next(n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=="run")
  writes=[n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id=="write_new" and
   any(isinstance(x,ast.Constant) and x.value=="OWNED.json" for x in ast.walk(n))]
  rss=[n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=="rss"]
  remaining=[n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=="remaining"]
  cid=[n.lineno for n in ast.walk(fn) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=="cid" for t in n.targets)]
  self.assertEqual(len(writes),1);self.assertEqual(len(rss),2)
  self.assertLess(min(rss),run);self.assertLess(run,min(cid));self.assertLess(min(cid),writes[0])
  self.assertLess(writes[0],max(rss));self.assertLess(writes[0],max(remaining))
  create=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="create")
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="create_owned" for n in ast.walk(create)))
  self.assertNotIn('self.call("create"',ast.unparse(create))
  self.assertEqual(receipt.OWNER,"sparq-token-v6")

if __name__=="__main__":
 if sys.argv[1:]==["--cleanup-regression"]:print(json.dumps(cleanup_regression(),sort_keys=True),flush=True)
 elif len(sys.argv)==3 and sys.argv[1]=="--create-regression":print(json.dumps(create_regression(sys.argv[2]),sort_keys=True),flush=True)
 else:unittest.main(verbosity=2)
