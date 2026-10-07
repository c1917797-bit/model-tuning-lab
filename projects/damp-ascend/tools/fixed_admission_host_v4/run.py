"""HOST-only v4: exact unordered mounts + stricter20min; runtime v3 unchanged."""
from __future__ import annotations
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/damp-ascend/tools/fixed_admission_host_v4"
V3=ROOT/"projects/damp-ascend/tools/fixed_admission_capture_v3"
V3_RUN_SHA="dcc4b9ec2ab6b9c65f96a0277fb4a6c8113ab57bed31001dafa77fc42d93c221"
V3_MANIFEST_SHA="de2cc8a9c520c4d1698dfe717f5d684587708d66b56554cddcafbe2a3f885a86"
PREVIOUS_ROOT=Path("/cache/cch/qwen36-damp-20261006/fixed-admission-c1-v2")
PREVIOUS_ID="2e3f31a6b470aa747504746f6a4c55706be391136d8e021ed0ea32dcf8a33f0c"
PREVIOUS_NAME="qwen36_damp_fixed_c1_fixed-admission-c1-v2-off-a"
PREVIOUS_INSPECT_SHA="89ab16e9a88dbb70b86c761f81a6ee5a7f59c5f6abf5102aef2d6697edb659af"
PREVIOUS_STOP_SHA="2eddb8cadf88e3159f2a14f9afeb61993aa21f74272bdd484cabe3fc83b0ded6"
CAP_SECONDS=20*60
CLEANUP_RESERVE=90
ABSOLUTE_DEADLINE_UTC="2026-10-07T08:48:03Z"
ABSOLUTE_DEADLINE_EPOCH=1791362883
def require(ok,message):
 if not ok:raise ValueError(message)
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()
def canonical(value):
 return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def mounts_multiset(rows):
 require(isinstance(rows,list),"Mounts must remain the raw array")
 for row in rows:require(isinstance(row,dict) and isinstance(row.get("Destination"),str),
                        "invalid actual mount row")
 # Every field/type/value and duplicate count are kept; only array order is ignored.
 return Counter(canonical(row) for row in rows)
def raw_mounts_before_predicates(inspect,actual,prior):
 owner=getattr(inspect,"__self__",None)
 require(owner is not None and isinstance(owner.root,Path),"actual owned Controller bound inspect required")
 owner._v4_mount_receipt_count=getattr(owner,"_v4_mount_receipt_count",0)+1
 path=owner.root/("prior-c1-mounts-raw-%04d.json"%owner._v4_mount_receipt_count)
 record={"schema":"damp-prior-c1-mounts-raw/v4","phase":"before-actual-identity-and-mount-predicates",
  "previous_id":PREVIOUS_ID,"actual_id":actual.get("Id") if isinstance(actual,dict) else None,
  "actual_mounts":actual.get("Mounts") if isinstance(actual,dict) else None,
  "archived_mounts":prior["Mounts"],"normalized_snapshot":False,
  "archived_identity_sha256":PREVIOUS_INSPECT_SHA,"not_release_authority":True}
 data=canonical(record)+b"\n"
 require(len(data)<=1024*1024,"raw mounts receipt exceeds1MiB")
 with path.open("xb",buffering=0) as f:f.write(data);os.fsync(f.fileno())
def previous_released(inspect):
 archived=PREVIOUS_ROOT/(PREVIOUS_NAME+"-inspect.json")
 stopped=PREVIOUS_ROOT/(PREVIOUS_NAME+"-stop.json")
 require(file_sha(archived)==PREVIOUS_INSPECT_SHA and file_sha(stopped)==PREVIOUS_STOP_SHA,
         "previous real C1 identity/stop bytes drift")
 prior=json.loads(archived.read_text());stop=json.loads(stopped.read_text())
 require(stop["id"]==PREVIOUS_ID and stop["exit_code"]==0 and stop["retained"] is True
         and stop["running_after"] is False,"previous C1 stop was not successful")
 actual=inspect(PREVIOUS_ID)
 raw_mounts_before_predicates(inspect,actual,prior)
 require(actual is not None and actual["Id"]==prior["Id"]==PREVIOUS_ID
         and actual["Name"]==prior["Name"]=="/"+PREVIOUS_NAME
         and actual["Image"]==prior["Image"],"previous C1 fresh immutable identity differs")
 for key in ("Labels","Entrypoint","Cmd"):require(actual["Config"][key]==prior["Config"][key],
         "previous C1 config identity differs: "+key)
 for key in ("Devices","Privileged","Memory","MemorySwap","NanoCpus","SecurityOpt","CapDrop","NetworkMode"):
  require(actual["HostConfig"][key]==prior["HostConfig"][key],"previous C1 config drift: "+key)
 require(mounts_multiset(actual["Mounts"])==mounts_multiset(prior["Mounts"]),
         "previous C1 mounts multiset differs")
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

def private_v3():
 require(file_sha(V3/"run.py")==V3_RUN_SHA and file_sha(V3/"SOURCE_MANIFEST.json")==V3_MANIFEST_SHA,
         "frozen v3 source drift")
 if str(V3) not in sys.path:sys.path.insert(0,str(V3))
 name="_damp_host_v4_private_v3_controller"
 if name not in sys.modules:
  spec=importlib.util.spec_from_file_location(name,V3/"run.py")
  module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
 return sys.modules[name]
def source_contract():
 m=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
 require(m["schema"]=="damp-fixed-admission-host-sources/v4","wrong HOST packet")
 for name,digest in m["files"].items():require(file_sha(HERE/name)==digest,"HOST source drift: "+name)
 frozen=private_v3().source_contract()
 return {"schema":m["schema"],"manifest_sha256":file_sha(HERE/"SOURCE_MANIFEST.json"),
         "runtime_v3_unchanged":frozen,"source_prepared":True,"npu_executed":False}
def tightened_deadline(start,existing,*,monotonic,wall_time):
 # Identical cleanup reserve remains in remaining(); no deadline extension.
 return min(existing,start+CAP_SECONDS,monotonic+ABSOLUTE_DEADLINE_EPOCH-wall_time)
def main():
 packet=source_contract();v3=private_v3();base=v3.private_run()
 parent=base.Controller;original_plan=base.plan
 class Capped(parent):
  def __init__(self,root):
   start=time.monotonic();super().__init__(root)
   self.deadline=tightened_deadline(start,self.deadline,monotonic=time.monotonic(),wall_time=time.time())
   self.remaining()
  def remaining(self):
   remaining=self.deadline-time.monotonic()-CLEANUP_RESERVE
   require(remaining>0,"HOST v4 20min/absolute08:48:03 deadline reached; retainpartial/no retry")
   return remaining
 def plan(root,source):
  p=original_plan(root,source);p.update(host_driver_packet=packet,host_only_revision=4,
   seconds_including_cold_starts=CAP_SECONDS,cleanup_reserve_seconds=CLEANUP_RESERVE,
   absolute_deadline_utc=ABSOLUTE_DEADLINE_UTC,mounts_comparison="allfields-canonical-exact-multiset",
   mounts_raw_before_predicates=True)
  return p
 # Only private HOST modules are adapted. No original runtime/source edits.
 base.Controller=Capped;base.plan=plan;v3.previous_released=previous_released
 if "--output" not in sys.argv:
  sys.argv.extend(["--output","/cache/cch/qwen36-damp-20261006/fixed-admission-c1-v4"])
 return v3.main()
if __name__=="__main__":main()
