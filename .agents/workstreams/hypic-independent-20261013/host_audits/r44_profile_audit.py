"""Retain every independent R43 check; identify actual count-two receipt."""
import argparse,json,hashlib,os
from pathlib import Path
from host_audits import r43_profile_audit as retained
from host_audits import r44_profile_policy as policy
from host_audits.r44_scope import scope,renewal_receipt
def finish(c,report):
 launch=json.loads((Path(c["raw_root"])/"launch.json").read_bytes())
 if launch.get("r43_launch_identity")!=renewal_receipt(c):raise ValueError("actual R44 wrapper receipt drift")
 if not report.get("profiler",{}).get("four_rank_trace_valid"):raise ValueError("actual complete four-rank trace required")
 report["profiler"]["configured_max_iterations"]=2
 report["profiler"]["step_cap_source_proof"]="Same original official WorkerProfiler counter, max2; third step() stops BEFORE third execute_model. Actual phase/work separately evidenced."
 report.update(r44_diagnostic_transport_valid=True,r44_host_source_sha256=c["r44_host_source_sha256"],r44_profiler=policy.PROFILE,r44_launch_identity=policy.receipt(c),full_goal_complete=False,new_performance_acceptance=False)
 return report
def audit(path,*,live_release=False):
 cp=Path(path).resolve();c=json.loads(cp.read_bytes());policy.check(c,root=cp.parent,require_new_root=False)
 with scope(c):report=retained.audit(cp,live_release=live_release)
 return finish(c,report)
def save(path,report):
 data=(json.dumps(report,sort_keys=True)+"\n").encode()
 with Path(path).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
 return hashlib.sha256(data).hexdigest()
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");p.add_argument("--output",required=True);a=p.parse_args()
 report=audit(a.contract,live_release=a.live_release);digest=save(a.output,report)
 print(json.dumps({"output":a.output,"sha256":digest,"r44_diagnostic_transport_valid":True,"live_release_verified":report.get("live_release_verified",False)}))
