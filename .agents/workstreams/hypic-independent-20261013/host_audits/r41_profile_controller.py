"""R41 outer HOST diagnostic adapter; unchanged R40/base own service and guards."""
import argparse,json,os,sys,time,threading,urllib.request
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r40_formal_controller as retained
from host_audits import r41_profile_policy as policy
from host_audits.r41_profile_trace import inventory,info_records
_LOCK=threading.Lock()
check_contract=policy.check
def control(port,path,guard):
 if path not in("/start_profile","/stop_profile"):raise ValueError("exact profiler control route required")
 guard();req=urllib.request.Request("http://127.0.0.1:"+str(port)+path,data=b"",method="POST")
 with urllib.request.urlopen(req,timeout=300)as r:
  if r.status!=200:raise ValueError("profiler control HTTP failure")
 guard();return 200
def run_profile_unit(original,spec,*,send_warmup,send_measured,guard,record,require_material_ready,
 expected_warm_descriptors,port,state):
 started=False
 def observe(e):
  nonlocal started
  record(e)
  if e.get("event")=="r40-begin":
   if started:raise ValueError("one profile window required")
   started=True;record({"event":"r41-profile-start-begin","scored":False})
   state["started"]=time.monotonic()
   status=control(port,"/start_profile",guard)
   record({"event":"r41-profile-start","scored":False,"status":status,"monotonic":time.monotonic()})
 try:
  result=original(spec,send_warmup=send_warmup,send_measured=send_measured,guard=guard,
   record=observe,require_material_ready=require_material_ready,expected_warm_descriptors=expected_warm_descriptors)
 finally:
  if started:
   record({"event":"r41-profile-stop-begin","scored":False})
   try:
    status=control(port,"/stop_profile",guard)
    record({"event":"r41-profile-stop","scored":False,"status":status,"monotonic":time.monotonic()})
   except Exception as e:
    record({"event":"r41-profile-control-failed","error":{"type":type(e).__name__,"message":str(e)},"scored":False})
    raise
 if not started:raise ValueError("profile trigger absent")
 result["r41_diagnostic_only"]=True
 return result
def run_contract(c,*,source_root=W):
 checked=check_contract(c,root=source_root);policy.require_budget(c)
 if not _LOCK.acquire(blocking=False):raise RuntimeError("one exact R41 owner")
 oldcheck=retained.check_contract;oldrewrite=retained.rewrite_launch;oldunit=retained.run_unit
 original_snapshot=retained.base.snapshot;raw=Path(c["raw_root"]);state={"started":None}
 def check(candidate,**kw):
  if candidate!=c:raise ValueError("one immutable diagnostic contract")
  return checked
 def rewrite(data,contract,proof):
  oldrewrite(data,contract,proof);argv=data["argv"]
  (raw/"profiles").mkdir(exist_ok=False)
  if "--profiler-config"in argv:raise ValueError("duplicate profiler configuration")
  argv.extend(["--profiler-config",json.dumps(policy.PROFILE,sort_keys=True,separators=(",",":"))])
  data["r41_launch_identity"]={"diagnostic_only":True,"profiler":policy.PROFILE,
   "source_sha256":c["r41_host_source_sha256"],"outer_host_controller_sha256":c["r41_controller_sha256"],
   "retained_host_controller_sha256":c["host_controller_sha256"],"captured_phase":"First bounded worker steps after actual4cachepreps+2targetwarm; phase classified from trace only"}
  return data
 def snapshot(cid=None):
  snap=original_snapshot(cid)
  if cid:
   try:
    inventory(raw/"profiles")
    if state["started"]is not None and time.monotonic()-state["started"]>300 and len(info_records(raw/"profiles"))!=4:
     raise TimeoutError("bounded all-rank profile closure deadline")
   except Exception:
    retained.base.stop_owned_on_foreign(cid,image=c["image"]);raise
  return snap
 def unit(*a,**kw):return run_profile_unit(oldunit,*a,**kw,port=c["port"],state=state)
 retained.check_contract=check;retained.rewrite_launch=rewrite;retained.run_unit=unit;retained.base.snapshot=snapshot
 try:return retained.run_contract(c,source_root=source_root)
 finally:
  retained.check_contract=oldcheck;retained.rewrite_launch=oldrewrite;retained.run_unit=oldunit
  retained.base.snapshot=original_snapshot;_LOCK.release()
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--run",action="store_true");a=p.parse_args()
 c=json.loads(Path(a.contract).read_bytes())
 if a.run:run_contract(c)
 else:print(json.dumps(check_contract(c)))
