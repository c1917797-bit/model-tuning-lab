"""v12 differences: real isolated whole-component replay, strict cache negatives.
Foreign modules below are rejected metadata fixtures, NOT runtime substitutes.
"""
import hashlib,json,os,subprocess,sys,types,unittest
from pathlib import Path
import source_contract as c,component_bootstrap as b
COMPONENT=dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-sparq005-consumer-mounts-whole-user72h-20261009-001.json",
 sha256="5614469e833ada86ad9f2f5869d084752a7262d0ac1f3701b7246e9701df7a74")
class ComponentBootstrap(unittest.TestCase):
 def reject(self,name,path):
  previous=sys.modules.get(name);bad=types.ModuleType(name)
  if path is not None:bad.__file__=path
  sys.modules[name]=bad
  try:
   with self.assertRaisesRegex(ValueError,"cached"):b.verify_cached(c)
   self.assertIs(sys.modules[name],bad) # production guard must NOT delete/rebind it
  finally:
   if previous is None:sys.modules.pop(name,None)
   else:sys.modules[name]=previous
 def test_foreign_contract_rejected(self):self.reject("contract",str(c.ROOT/"source_contract.py"))
 def test_foreign_receipt_rejected(self):self.reject("receipt",str(c.ROOT/"source_contract.py"))
 def test_foreign_shard_rows_rejected(self):self.reject("shard_rows",str(c.ROOT/"source_contract.py"))
 def test_foreign_native_package_rejected(self):self.reject("sparq_token_v4",str(c.ROOT/"source_contract.py"))
 def test_missing_cached_source_rejected(self):self.reject("contract",None)
 def test_different_whole_reader_rejected(self):self.reject("original_terminal",str(c.ROOT/"source_contract.py"))
 def test_identical_full_whole_reader_allowed(self):
  import original_terminal
  self.assertIn(Path(original_terminal.__file__).resolve(),(c.ROOT/"original_terminal.py",c.KERNEL/"original_terminal.py"))
  self.assertIn("original_terminal",b.verify_cached(c))
 def test_complete_native_and_shard_explicit_choices(self):
  wants=b.expected(c)
  for name in (*b.NATIVE_NAMES,"shard_contract","shard_rows","shard_proof","shard_host"):
   self.assertIn(name,wants);self.assertEqual(len(wants[name]),1)
  self.assertEqual(len(wants["original_terminal"]),2)
 def test_actual_clean_I_whole_component_replay(self):
  source_sha=c.sha(c.ROOT/"SOURCE_MANIFEST.json");env=dict(os.environ,PYTHONPATH="",PYTHONDONTWRITEBYTECODE="1",TORCH_DEVICE_BACKEND_AUTOLOAD="0")
  argv=[sys.executable,"-I","-B",str(c.ROOT/"component_bootstrap.py"),"--execute","--source-manifest-sha256",source_sha,
   "--component",COMPONENT["path"],"--component-sha256",COMPONENT["sha256"]]
  r=subprocess.run(argv,cwd="/",env=env,capture_output=True,text=True,timeout=180)
  self.assertEqual(r.returncode,0,r.stdout+"\n"+r.stderr)
  lines=[x for x in r.stdout.splitlines() if x.startswith("SPARQ_COMPONENT_BOOTSTRAP ")]
  self.assertEqual(len(lines),1);p=json.loads(lines[0].split(" ",1)[1])
  source=dict(path=str(c.ROOT/"SOURCE_MANIFEST.json"),sha256=source_sha)
  self.assertTrue(b.verify_probe(c,dict(component_bootstrap=p),source,COMPONENT))
  self.assertFalse(p["npu_rerun"]);self.assertFalse(p["model_executed"])
 def test_actual_clean_I_default_OFF(self):
  r=subprocess.run([sys.executable,"-I","-B",str(c.ROOT/"component_bootstrap.py")],cwd="/",
   env=dict(os.environ,PYTHONPATH=""),capture_output=True,text=True,timeout=10)
  self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),
   dict(status="disabled",ready=False,npu_executed=False))

class ExactOwnedWorkdir(unittest.TestCase):
 def fixture(self,root):
  import host_run as h,service_contract as service,consume_model
  source=c.bound(c.ROOT/"SOURCE_MANIFEST.json",c.sha(c.ROOT/"SOURCE_MANIFEST.json"))
  files=c.obj(source)["files"];cid="a"*64;arm="cpu-preflight"
  e=dict(cid=cid,name="source-workdir-positive",image=service.IMAGE,arm=arm,source=source,host_sha256=files["host_run.py"],
   guest_cpus=[0],mounts={str(c.ROOT):(str(c.ROOT),False),str(root):(str(root),True)})
  argv=h.create_argv(e)
  created=c.write(root/"create.json",dict(exit_code=0,stdout=cid+"\n",requested_argv=argv))
  owned=c.write(root/"OWNED.json",dict(e,sources=files,create_receipt=created))
  x=dict(Id=cid,Image=service.IMAGE,Name="/"+e["name"],ExecIDs=None,
   State=dict(Running=False,Pid=0,OOMKilled=False),HostConfig=dict(Privileged=False,Memory=8*1024**3,MemorySwap=8*1024**3,
    NanoCpus=10**9,CpusetCpus="0",IpcMode="private",NetworkMode="none",ShmSize=4*1024**3,PidsLimit=2048,
    DeviceRequests=None,DeviceCgroupRules=None,CapDrop=["ALL"],SecurityOpt=["no-new-privileges"],Devices=[]),
   Config=dict(Image=service.IMAGE,Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],
    Labels=h.labels(e),Env=[k+"="+v for k,v in h.environment(True).items()],WorkingDir=argv[argv.index("--workdir")+1]),
   Mounts=[dict(Type="bind",Destination=n,Source=p,RW=rw) for n,(p,rw) in e["mounts"].items()])
  return h,consume_model,source,files,cid,e,owned,x
 def check(self,mutation=None):
  import tempfile
  with tempfile.TemporaryDirectory(prefix="full-v12-exact-workdir-") as folder:
   root=Path(folder);h,m,source,files,cid,e,owned,x=self.fixture(root)
   h.validate_inspect(x,e) # Real unchanged complete producer predicate first.
   if mutation is not None:mutation(x)
   observed=c.write(root/"inspect.json",dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",cid],
    stdout=json.dumps([x])))
   if mutation is None:
    self.assertEqual(m.stopped(observed,cid,owned,source,files,True),x)
   else:
    with self.assertRaises(ValueError):h.validate_inspect(x,e)
    with self.assertRaises(ValueError):m.stopped(observed,cid,owned,source,files,True)
 def test_real_complete_producer_to_consumer_workdir(self):self.check()
 def test_wrong_workdir_hard_rejected(self):self.check(lambda x:x["Config"].update(WorkingDir=str(c.ROOT)))
 def test_foreign_CID_hard_rejected(self):self.check(lambda x:x.update(Id="b"*64))

if __name__=="__main__":unittest.main()
