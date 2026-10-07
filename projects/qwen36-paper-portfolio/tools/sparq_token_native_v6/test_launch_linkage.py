"""Stdlib-only host-generated proof/actual ABI-argv contract regression. No native/NPU authority."""
import ast,copy,hashlib,json,sys,tempfile,types,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import host,receipt,preflight,consume_numeric
from sparq_token_v4 import proof as gate
OLD=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-token-native-v5-002")
# Test output ownership is independent of canonical or private source placement.
TEST_TMP_PARENT=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-token-native-v6-002")
class CrossModule(unittest.TestCase):
 def test_explicit_owned_temporary_parent_independent_of_source_placement(self):
  self.assertEqual(TEST_TMP_PARENT,Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-token-native-v6-002"))
  self.assertTrue(TEST_TMP_PARENT.is_dir());self.assertFalse(TEST_TMP_PARENT.is_symlink())
  self.assertEqual(TEST_TMP_PARENT.resolve(),TEST_TMP_PARENT)
  self.assertIn(Path("/cache/cch"),TEST_TMP_PARENT.parents)
  tree=ast.parse(Path(receipt.ROOT/"test_launch_linkage.py").read_text())
  dirs=[k.value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
   n.func.attr=="TemporaryDirectory" for k in n.keywords if k.arg=="dir"]
  self.assertEqual(len(dirs),5)
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
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-002-linkage-") as td:
   root=Path(td);f=self.fixture(root)
   got=self.validate(f,root)
   self.assertEqual(got["container_inspect"]["Config"]["Labels"]["model-tuning-lab.owner"],receipt.OWNER)
   self.assertEqual(got["cpu_host_output_root"],str(f["cpu_root"]))
   self.assertEqual(receipt.load(got["native_no_device_abi"])["actual_argv"],f["args"])
   self.assertNotIn("torch",sys.modules)
 def test_old_owner_source_rejected_without_union(self):
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-002-linkage-") as td:
   root=Path(td);f=self.fixture(root)
   for owner in ("sparq-token-v4","sparq-token-v5","other"):
    value=copy.deepcopy(f["proof"]);value["container_inspect"]["Config"]["Labels"]["model-tuning-lab.owner"]=owner
    with self.subTest(owner=owner),self.assertRaisesRegex(ValueError,"owned numeric container"):
     self.validate(f,root,value)
 def test_actual_predecessor_two_rejections_reproduced_without_device(self):
  module=types.ModuleType("sparq_token_v4._original_frozen_proof");module.__package__="sparq_token_v4"
  exec(compile((OLD/"sparq_token_v4/proof.py").read_bytes(),str(OLD/"sparq_token_v4/proof.py"),"exec"),module.__dict__)
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-002-linkage-") as td:
   root=Path(td);f=self.fixture(root)
   with self.assertRaisesRegex(ValueError,"owned numeric container"):
    self.validate(f,root,validator=module.validate_proof)
   value=copy.deepcopy(f["proof"]);value["container_inspect"]["Config"]["Labels"]["model-tuning-lab.owner"]="sparq-token-v4"
   with self.assertRaisesRegex(ValueError,"original Docker child"):
    self.validate(f,root,value,validator=module.validate_proof)
 def test_complete_ABI_command_negatives_before_NPU_and_again_in_proof(self):
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-002-linkage-") as td:
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
  with tempfile.TemporaryDirectory(dir=TEST_TMP_PARENT,prefix="sparq-v6-002-linkage-") as td:
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
   "preflight.py":"85e2b0aa2632cfc36df378aaa53f50dbcf06bc4ffbe176b0bbe14115c30b1463"}.items():
   self.assertEqual(receipt.sha(receipt.ROOT/n),s)
  self.assertNotEqual(receipt.sha(Path(gate.__file__)),"70eed04080d4a3e8c6a81871d3da81aa1bed6fcde3c06b32d0e04d37d89c539c")
  self.assertEqual(receipt.OWNER,"sparq-token-v6");self.assertNotIn("torch",sys.modules)
if __name__=="__main__":unittest.main(verbosity=2)
