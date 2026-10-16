import ast,copy,importlib.util,os,re,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location("policy",P/"external_output_policy.py");M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
SAFETY=Path("C:/Users/Huawei/AppData/Local/Temp/model036-controller-exact011-review/safety_host.py")
DONOR=Path("C:/Users/Huawei/AppData/Local/Temp/mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py")
if not SAFETY.is_file():SAFETY=P/"actual_loader/safety_host.py"
if not DONOR.is_file():DONOR=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py")
class T(unittest.TestCase):
 def setUp(self):
  body,pairs=M.derive_safety(SAFETY.read_bytes());self.assertEqual(len(pairs),4)
  tree=ast.parse(body);names={"environment","labels","device_map","create_argv","validate_inspect"};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
  c=types.SimpleNamespace(GIB=2**30,ROOT=Path("/repo"),IMAGE="sha256:image",require=M.need)
  self.ns=dict(c=c,_EXTERNAL=M,MEM=48*2**30,OWNER="owner",PHYSICAL=(4,5,6,7),DOCKER="/usr/bin/docker",re=re)
  exec(compile(ast.Module(body=nodes,type_ignores=[]),"actual-derived-safety","exec"),self.ns)
  self.e=dict(arm="cpu-preflight",algorithm_arm="capture",name="own",cid="a"*64,source={"sha256":"x"},host_sha256="h",guest_cpus=[2],external_output_policy=True,external_output_root="/opt/host/vnf/austinov/new",mounts={"/adakv-results":("/opt/host/vnf/austinov/new/cpu-preflight",True),"/source":("/source",False)})
  # Actual008 narrows generic algorithm environment to capture, unchanged.
  self.ns["environment"]=lambda cpu,arm:{"TMPDIR":"/adakv-results","ASCEND_RT_VISIBLE_DEVICES":""}
 def inspect(self):
  e=self.e;n=self.ns
  env=dict(n["environment"](True,"capture"),**M.environment(e))
  return dict(Id=e["cid"],Image="sha256:image",Name="/own",Config=dict(Image="sha256:image",Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],WorkingDir=str(n["c"].ROOT),Labels=n["labels"](e),Env=[k+"="+v for k,v in env.items()]),HostConfig=dict(ReadonlyRootfs=True,LogConfig=copy.deepcopy(M.LOG),Privileged=False,Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=10**9,CpusetCpus="2",IpcMode="private",NetworkMode="none",ShmSize=4*2**30,PidsLimit=2048,CapDrop=["ALL"],SecurityOpt=["no-new-privileges"],Devices=[]),Mounts=[dict(Type="bind",Destination=d,Source=p,RW=w)for d,(p,w)in e["mounts"].items()])
 def test_actual_create_inspect(self):
  a=self.ns["create_argv"](self.e);self.assertIn("--read-only",a);self.assertIn("max-size=16m",a);self.assertIn("HOME=/adakv-results/.runtime/home",a)
  self.ns["validate_inspect"](self.inspect(),self.e)
 def test_inspect_drift(self):
  for key,value in(("ReadonlyRootfs",False),("LogConfig",{"Type":"json-file","Config":{}}),("Tmpfs",{"/tmp":"size=1g"})):
   x=self.inspect();x["HostConfig"][key]=value
   with self.assertRaises(ValueError):self.ns["validate_inspect"](x,self.e)
  x=self.inspect();x["Config"]["Env"].append("HOME=/escape")
  with self.assertRaises(ValueError):self.ns["validate_inspect"](x,self.e)
 def test_rw_escape(self):
  self.e["mounts"]["/escape"]=("/cache/foreign",True)
  with self.assertRaises(ValueError):M.environment(self.e)
 def test_docker_split_gate_still_failclosed(self):
  S=types.SimpleNamespace(RESERVE=int(8.5*2**30),WORKSPACE=32*2**30,_external_output_enabled=True)
  ctl=types.SimpleNamespace(expected=self.e,_external_output_expected=self.e,cid=None)
  M.docker_gate(ctl,S,16551014400,True)
  with self.assertRaises(ValueError):M.docker_gate(ctl,S,8*2**30,True)
  ctl.cid="a";ctl.inspect=lambda:(_ for _ in()).throw(ValueError("actual inspect failed"))
  with self.assertRaises(ValueError):M.docker_gate(ctl,S,16551014400,True)
 def test_source_inverse_defaultOFF(self):
  M.derive_donor(DONOR.read_bytes())
  with self.assertRaises(ValueError):M.derive_donor(DONOR.read_bytes()+b"\n")
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(ValueError):M.enable(types.SimpleNamespace(),"/opt/host/vnf/austinov/new")
 def test_real_install_precreate_to_actual_create(self):
  from pathlib import PurePosixPath
  from unittest.mock import Mock
  S=types.SimpleNamespace(**self.ns);S.__dict__.update(RESERVE=int(8.5*2**30),WORKSPACE=32*2**30)
  class Owned:
   def __init__(self,leaf):self.name="own";self.out=leaf;self.cid=None
  rr=dict(path=str(SAFETY),bytes=22569,sha256=M.SAFETY_SHA)
  with patch.dict(os.environ,{M.ENABLE:"1"}):
   M.install(S,Owned,None,PurePosixPath("/opt/host/vnf/austinov/new"),rr)
   ctl=Owned(PurePosixPath("/opt/host/vnf/austinov/new/cpu-preflight"))
   M.docker_gate(ctl,S,16551014400,True)
   e=copy.deepcopy(self.e);e.pop("external_output_policy");e.pop("external_output_root")
   with patch.object(M,"prepare",return_value={})as prep:
    argv=S.create_argv(e);prep.assert_called_once_with(e)
   self.assertIn("--read-only",argv);self.assertTrue(e["external_output_policy"])
   S.validate_inspect(self.inspect(),e)
   bad=copy.deepcopy(e);bad["mounts"]["/adakv-results"]=("/opt/host/vnf/austinov/new/candidate",True)
   with self.assertRaises(ValueError):S.create_argv(bad)
if __name__=="__main__":unittest.main()
