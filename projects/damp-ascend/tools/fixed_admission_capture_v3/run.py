"""Private reuse of byte-frozen v2 controller; only v3 plugin/overlay differs."""
from __future__ import annotations
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from v3_contract import HERE,V1,V2,ROOT,file_sha,inventory,private_run,require,source_contract
PREVIOUS_ROOT=Path("/cache/cch/qwen36-damp-20261006/fixed-admission-c1-v2")
PREVIOUS_ID="2e3f31a6b470aa747504746f6a4c55706be391136d8e021ed0ea32dcf8a33f0c"
PREVIOUS_NAME="qwen36_damp_fixed_c1_fixed-admission-c1-v2-off-a"
PREVIOUS_INSPECT_SHA="89ab16e9a88dbb70b86c761f81a6ee5a7f59c5f6abf5102aef2d6697edb659af"
PREVIOUS_STOP_SHA="2eddb8cadf88e3159f2a14f9afeb61993aa21f74272bdd484cabe3fc83b0ded6"
def install(root):
 packet=source_contract();d=private_run().D;root=Path(root)
 root.mkdir(parents=True,exist_ok=False)
 (root/"damp_capture").symlink_to(d.COLLECTOR/"damp_capture",target_is_directory=True)
 (root/"damp_admission_diagnostic").symlink_to(V1/"damp_admission_diagnostic",target_is_directory=True)
 for name in ("v2_contract.py","v2_bindings.py","v2_observer.py","damp_fixed_v2.py"):
  (root/name).symlink_to(V2/name)
 for name in ("v3_contract.py","v3_before.py","damp_fixed_v3.py"):
  (root/name).symlink_to(HERE/name)
 meta=root/"damp_fixed_admission_v3-0.3.0.dist-info";meta.mkdir()
 with (meta/"METADATA").open("x") as out:
  out.write("Metadata-Version: 2.1\nName: damp-fixed-admission-v3\nVersion: 0.3.0\n")
 with (meta/"entry_points.txt").open("x") as out:
  out.write("[vllm.general_plugins]\ndamp_capture = damp_fixed_v3:register\n")
 return inventory([e for d in importlib.metadata.distributions(path=[str(root)]) for e in d.entry_points])
def target_preflight(report):
 from v3_contract import RUNTIME
 d=private_run().D;packet=source_contract()
 environment=d.runtime_environment(Path(report).parent)
 require(sys.version_info[:2]==(3,12) and callable(getattr(threading,"getprofile",None)),
         "target3.12 public profile API required")
 require(sys.getprofile() is None and threading.getprofile() is None,"foreign profile hook")
 require(not Path("/dev/davinci0").exists() and not Path("/dev/davinci4").exists(),"unexpected devices")
 require(os.environ.get("DAMP_ADMISSION_TRACE_ENABLE")!="1","preflight must defaultOFF")
 entry=inventory(importlib.metadata.entry_points())
 import damp_fixed_v3
 require(Path(damp_fixed_v3.__file__).resolve()==HERE/"damp_fixed_v3.py","wrong v3 plugin source")
 before=set(sys.modules);require(damp_fixed_v3.register() is None,"defaultOFF changed behavior")
 require(not any(n=="torch" or n.startswith("torch.") for n in sys.modules),"defaultOFF imported Torch")
 from damp_capture import run as collector_run
 require(Path(collector_run.__file__).resolve()==d.COLLECTOR/"damp_capture/run.py","frozen runner mismatch")
 for path,digest in dict(d.RUNTIME,**RUNTIME).items():require(file_sha(path)==digest,"actual image source drift")
 suite=unittest.defaultTestLoader.discover(str(HERE/"tests"),pattern="test_before.py")
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 require(result.wasSuccessful(),"v3 source/software preflight failed")
 require("torch" not in sys.modules,"software tests loaded Torch")
 d.write_new(report,{"schema":"damp-fixed-admission-preflight/v3","status":"source_import_pass",
  "packet":packet,"entrypoint":entry,"actual_environment":environment,
  "tests":result.testsRun,"npu_executed":False,"native_time_axis_observed":False,
  "source_lock_issued":False})
def previous_released(inspect):
 archived=PREVIOUS_ROOT/(PREVIOUS_NAME+"-inspect.json")
 stopped=PREVIOUS_ROOT/(PREVIOUS_NAME+"-stop.json")
 require(file_sha(archived)==PREVIOUS_INSPECT_SHA and file_sha(stopped)==PREVIOUS_STOP_SHA,
         "previous real C1 identity/stop bytes drift")
 prior=json.loads(archived.read_text());stop=json.loads(stopped.read_text())
 require(stop["id"]==PREVIOUS_ID and stop["exit_code"]==0 and stop["retained"] is True
         and stop["running_after"] is False,"previous C1 stop was not successful")
 actual=inspect(PREVIOUS_ID)
 require(actual is not None and actual["Id"]==prior["Id"]==PREVIOUS_ID
         and actual["Name"]==prior["Name"]=="/"+PREVIOUS_NAME
         and actual["Image"]==prior["Image"],"previous C1 fresh immutable identity differs")
 for key in ("Labels","Entrypoint","Cmd"):require(actual["Config"][key]==prior["Config"][key],
         "previous C1 config identity differs: "+key)
 for key in ("Devices","Privileged","Memory","MemorySwap","NanoCpus","SecurityOpt","CapDrop","NetworkMode"):
  require(actual["HostConfig"][key]==prior["HostConfig"][key],"previous C1 config drift: "+key)
 require(actual["Mounts"]==prior["Mounts"],"previous C1 mounts differ")
 state=actual["State"]
 require(state["Running"] is False and state["Pid"]==0 and state["Paused"] is False
         and state["Restarting"] is False and state["OOMKilled"] is False,
         "previous C1 is not stopped/Pid0/noOOM")
 require(not actual.get("ExecIDs"),"previous C1 has pending exec IDs")
 return {"id":PREVIOUS_ID,"name":actual["Name"],"image":actual["Image"],
  "stop":{"path":str(stopped),"sha256":PREVIOUS_STOP_SHA},
  "archived_identity":{"path":str(archived),"sha256":PREVIOUS_INSPECT_SHA},
  "fresh_state":state,"fresh_exec_ids":actual.get("ExecIDs"),
  "original_failure_preserved":True,"numerical_pass_claimed":False}
def main():
 base=private_run();original_plan=base.plan;parent_controller=base.Controller
 class Controller(parent_controller):
  def admit_prior_release(self,*args,**kwargs):
   super().admit_prior_release(*args,**kwargs)
   prior=previous_released(self.inspect)
   base.D.write_new(self.root/"prior-c1-v2-release.json",prior)
  def fresh_idle(self,arm):
   previous_released(self.inspect)
   return super().fresh_idle(arm)
 def plan(root,source):
  p=original_plan(root,source);p.update(schema="damp-fixed-admission-plan/v3",
    before_guard_independent_receipt=True,guard_unchanged=True,source_lock_issued=False,
    original_v2_controller_reused=True,not_proven=["native time-axis","short parity","full36",
      "192 plans","compressed model","E2E","task accuracy"])
  return p
 base.HERE=HERE;base.source_contract=source_contract;base.inventory=inventory
 base.install=install;base.target_preflight=target_preflight;base.Controller=Controller;base.plan=plan
 if "--output" not in sys.argv:
  sys.argv.extend(["--output",str(base.D.RESULT_ROOT/"fixed-admission-c1-v3")])
 return base.main()
if __name__=="__main__":main()
