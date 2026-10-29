"""Source-bound CPU clock proof and exact pre-Docker constructor interception."""
import argparse,contextlib,copy,hashlib,io,json,os,subprocess,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r45_diagnostic_controller as owner
from host_audits import r45_diagnostic_policy as policy
CLOCK_CODE=r'''
import inspect,json,os,time
assert inspect.isbuiltin(time.monotonic)and inspect.isbuiltin(time.perf_counter_ns)
clocks={n:{"implementation":v.implementation,"monotonic":v.monotonic,"adjustable":v.adjustable,"resolution":v.resolution}
 for n in("monotonic","perf_counter")for v in(time.get_clock_info(n),)}
a=time.monotonic_ns();b=time.perf_counter_ns();c=time.monotonic_ns()
assert a<=b<=c
print(json.dumps({"clocks":clocks,"time_namespace":os.readlink("/proc/self/ns/time"),
 "bracket_monotonic_ns":str(a),"perf_counter_ns":str(b),"bracket_monotonic_end_ns":str(c),
 "no_inference_imports":True}))
'''
CLOCK_NAME="hypic-r45-clock-source-proof-20261029"
def clock_probe():
 root=policy.CPU_CLOCK.parent;image=policy.reference()["image"]
 if root.exists()or root.is_symlink():raise ValueError("new immutable CPU clock-proof root")
 if subprocess.check_output(["docker","ps","-a","--filter","name=^/"+CLOCK_NAME+"$","--format","{{.ID}}"],text=True).strip():
  raise ValueError("fresh exact CPU proof name required")
 root.mkdir()
 argv=["docker","create","--name",CLOCK_NAME,"--label","hypic.attempt=r45-clock-source-proof-20261029",
  "--network","none","--cpuset-cpus","112-119","--memory","128m","--pids-limit","64",
  image,"python3","-B","-c",CLOCK_CODE]
 created=subprocess.run(argv,capture_output=True,text=True,check=True)
 cid=created.stdout.strip()
 if len(cid)!=64 or any(ch not in"0123456789abcdef"for ch in cid):raise ValueError("exact CPU CID")
 declared=json.loads(subprocess.check_output(["docker","inspect",cid]))[0]
 raw={"helper_sha256":policy.sha(__file__),"code_sha256":hashlib.sha256(CLOCK_CODE.encode()).hexdigest(),
  "argv":argv,"cid":cid,"image":image,"declaration":declared,"host_clock":owner.clock_sources(),
  "host_time_namespace":os.readlink("/proc/self/ns/time"),"no_devices":not bool(declared["HostConfig"].get("Devices"))}
 error=None
 try:
  if(declared["Id"]!=cid or declared["Image"]!=image or declared["HostConfig"].get("Privileged")
     or declared["HostConfig"].get("Devices")or declared["HostConfig"].get("NetworkMode")!="none"):
   raise ValueError("sameimage no-device/no-network CPU declaration")
  r=subprocess.run(["docker","start","-a",cid],capture_output=True,text=True,timeout=60)
  raw.update(exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
 except BaseException as e:
  error=e;raw["controller_error"]={"type":type(e).__name__,"message":str(e)}
 finally:
  actual=json.loads(subprocess.check_output(["docker","inspect",cid]))[0]
  if(actual["Id"]!=cid or actual["Config"].get("Labels",{}).get("hypic.attempt")!="r45-clock-source-proof-20261029"):
   raise ValueError("exact CPU proof cleanup ownership")
  raw["terminal_state_before_cleanup"]=actual["State"]
  subprocess.run(["docker","rm","-f",cid],capture_output=True,text=True,check=True)
  q=subprocess.run(["docker","inspect",cid],capture_output=True,text=True)
  raw["exact_cpu_container_absent"]=q.returncode!=0 and q.stdout.strip()=="[]"and("No such object"in q.stderr or"No such container"in q.stderr)
  data=(json.dumps(raw,sort_keys=True)+"\n").encode()
  with policy.CPU_CLOCK.open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
  print(json.dumps({"path":str(policy.CPU_CLOCK),"sha256":hashlib.sha256(data).hexdigest(),
    "exit":raw.get("exit"),"exact_cpu_container_absent":raw["exact_cpu_container_absent"]}))
 if error:raise error
 if raw.get("exit")!=0 or not raw["exact_cpu_container_absent"]:raise ValueError("actual CPU clock proof failed")
 return {"path":str(policy.CPU_CLOCK),"sha256":policy.sha(policy.CPU_CLOCK)}
class CaptureOnly(RuntimeError):pass
def capture_contract(contract):
 checked=owner.check_contract(contract,source_root=W,require_new_root=True)
 live=copy.deepcopy(contract);original_command=owner.base.command;captured=[]
 empty={"utc":"rehearsal-not-telemetry","raw":"","processes":[],"owners":[],"foreign":[]}
 callbacks=(owner.base.write,owner.base.snapshot,owner.workload_slot.run_formal_workload,owner.check_contract)
 def command(argv,**kwargs):
  if argv==["docker","image","inspect",contract["image"]]:return original_command(argv,**kwargs)
  if argv==["git","rev-parse","HEAD"]:return original_command(argv,**kwargs)
  if argv[:3]==["ss","-H","-ltn"]:return ""
  if argv[:2]==["docker","run"]:
   captured.append(list(argv));raise CaptureOnly("actual base allocation boundary intercepted")
  raise AssertionError("external action forbidden in constructor rehearsal: "+str(argv))
 with tempfile.TemporaryDirectory(prefix="hypic-r45-launch-rehearsal-",dir="/cache/cch")as tmp:
  live["raw_root"]=str(Path(tmp)/"raw")
  def rehearsal_check(c,*,source_root=W,require_new_root=True):
   if c!=live or dict(c,raw_root=contract["raw_root"])!=contract or Path(source_root).resolve()!=W:
    raise ValueError("only explicit scratch raw-root override in no-device constructor")
   return checked
  with patch.object(owner,"check_contract",rehearsal_check),patch.object(owner.base,"snapshot",lambda cid=None:copy.deepcopy(empty)),\
       patch.object(owner.base,"port_free",lambda port:None),patch.object(owner.base,"command",command),contextlib.redirect_stdout(io.StringIO()):
   try:owner.run_contract(live,source_root=W)
   except SystemExit as stopped:
    if stopped.code!=1:raise
   else:raise AssertionError("rehearsal may never execute a device unit")
  terminal=json.loads((Path(live["raw_root"])/"result.json").read_bytes())
  launch=json.loads((Path(live["raw_root"])/"launch.json").read_bytes())
  if(len(captured)!=1 or terminal["error"]["type"]!="CaptureOnly"or terminal["release"]["owned_container"]is not None
     or launch["r45_launch_identity"]!=owner.identity(live)):
   raise AssertionError("exact actual constructor allocation boundary missing")
 if callbacks!=(owner.base.write,owner.base.snapshot,owner.workload_slot.run_formal_workload,owner.check_contract):
  raise AssertionError("constructor rehearsal callbacks not restored")
 return {"schema":"hypic-r45-actual-launch-capsule/v1","role":contract["r45_role"],
  "checked_contract_root":contract["raw_root"],"consumed_scratch_root_override":True,
  "checked_manifest":contract["successor_manifest"],"source_bindings":checked["source_bindings"],
  "image":contract["image"],"argv":captured[0],"r45_launch_identity":owner.identity(contract),
  "callbacks_restored":True,"new_device_allocation":False,"physical_admission_proven":False,
  "scope":"Real unchanged formal_r15 builder and new R45 wrapper, intercepted before Docker run. Scratch raw-root override and physical/port mocks are rehearsal-only; fresh real admission mandatory."}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--clock-probe",action="store_true");p.add_argument("--contract");p.add_argument("--output")
 a=p.parse_args()
 if a.clock_probe:clock_probe()
 else:
  if not a.contract or not a.output:p.error("contract/output required")
  d=capture_contract(json.loads(Path(a.contract).read_bytes()));data=(json.dumps(d,sort_keys=True)+"\n").encode()
  with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
  print(json.dumps({"path":a.output,"sha256":hashlib.sha256(data).hexdigest(),"new_device_allocation":False}))
