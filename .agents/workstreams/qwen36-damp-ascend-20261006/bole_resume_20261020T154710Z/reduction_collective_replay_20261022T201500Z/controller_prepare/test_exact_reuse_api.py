"""Exact original runtime APIs in a fresh CPU process; command/Torch tripwires."""
import subprocess
import sys
import unittest

CONTROL = r'''
from pathlib import Path
import importlib.util,json,subprocess,builtins,sys,copy,os
w=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
C=load("_controller_review_common",w/"native_ar_fsum_oracle_v1/ar_owner_common.py")
NS=load("_controller_review_namespace",w/"native_ar_fsum_oracle_v1/ar_saved_namespace.py")
on=json.loads((w/"bound-boundary-ON-v4-textonly_20261022T171000Z/SOURCE_BOUND.json").read_bytes())
def forbidden(*a,**k):raise AssertionError("source control must not run commands")
for k in ("run","Popen","check_output","check_call","call"):setattr(subprocess,k,forbidden)
real_import=builtins.__import__
def guarded(n,*a,**k):
 if n.split(".")[0] in ("torch","torch_npu"):raise AssertionError("no tensor import")
 return real_import(n,*a,**k)
builtins.__import__=guarded
os.environ["DENSE090_EXTERNAL_OUTPUT_ENABLE"]="1"
output="/opt/host/vnf/austinov/run-bole-native-ar-collective-replay-source-api-control-no-owner"
with NS.open_namespace(C,dict(output_root=output,authority=on["authority_ref"]),on) as (c,S,H,proof):
 assert S.MEM==32*c.GIB and S.WORKSPACE==32*c.GIB and S.RESERVE==8*c.GIB
 leaf=Path(output)/"dense"
 e=dict(cid="a"*64,name="bole-collective-source-api",image=c.IMAGE,arm="collective-replay",source={"sha256":"b"*64},
        host_sha256=c.sha(S.__file__),guest_cpus=[145,146,147,148],
        mounts={"/adakv-results":(str(leaf),True),str(leaf):(str(leaf),True)})
 argv=S.create_argv(e)
 assert argv[argv.index("--network")+1]=="none" and "--read-only" in argv
 assert argv[argv.index("--memory")+1]==str(32*c.GIB) and argv[argv.index("--cpus")+1]=="4"
 import external025
 env=dict(S.environment(False),**external025.environment(e))
 x=dict(Id=e["cid"],Image=e["image"],Name="/"+e["name"],
   Config=dict(Image=e["image"],Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],
               WorkingDir=str(c.ROOT),Labels=S.labels(e),Env=[k+"="+v for k,v in env.items()]),
   HostConfig=dict(Privileged=False,Memory=32*c.GIB,MemorySwap=32*c.GIB,NanoCpus=4*10**9,
      CpusetCpus="145,146,147,148",IpcMode="private",NetworkMode="none",ShmSize=4*c.GIB,
      PidsLimit=2048,DeviceRequests=[],DeviceCgroupRules=[],CapDrop=["ALL"],SecurityOpt=["no-new-privileges"],
      Devices=[dict(PathOnHost=p,PathInContainer=n,CgroupPermissions="rwm") for p,n in S.device_map().items()],
      ReadonlyRootfs=True,LogConfig=external025.LOG,Tmpfs=None),
   Mounts=[dict(Type="bind",Destination=n,Source=p,RW=rw) for n,(p,rw) in e["mounts"].items()])
 S.validate_inspect(x,e)
 for mutation in ("protected_device","foreign_cid","extra_RW","writable_root"):
  bad=copy.deepcopy(x)
  if mutation=="protected_device":bad["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci0"
  elif mutation=="foreign_cid":bad["Id"]="c"*64
  elif mutation=="extra_RW":bad["Mounts"].append(dict(Type="bind",Destination="/extra",Source="/tmp",RW=True))
  else:bad["HostConfig"]["ReadonlyRootfs"]=False
  try:S.validate_inspect(bad,e);raise AssertionError("accepted "+mutation)
  except ValueError:pass
 assert all(callable(getattr(S.Controller,n)) for n in ("observe","resources","create_owned","inspect","cleanup"))
 print(json.dumps(dict(real_source_API=True,new_arm_accepted=True,negatives=4,NPU=False,Docker=False,
                       output_created=Path(output).exists())))
assert not Path(output).exists()
'''


class ExactReuseTests(unittest.TestCase):
    def test_actual_new_arm_create_inspect_and_negative_profiles(self):
        r=subprocess.run([sys.executable,"-B","-c",CONTROL],capture_output=True,text=True,timeout=20)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('"new_arm_accepted": true',r.stdout)
        self.assertIn('"output_created": false',r.stdout)


if __name__=="__main__":unittest.main()
