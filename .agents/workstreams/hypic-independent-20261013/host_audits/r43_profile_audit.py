"""Retain independent R42 full transport/math/trace audit, then verify renewal receipt."""
import argparse,hashlib,json,os
from pathlib import Path
from host_audits import r42_profile_audit as retained
from host_audits import r43_renewal_policy as policy
from host_audits.r43_profile_controller import receipt
def audit(path,*,live_release=False):
 cp=Path(path).resolve();c=json.loads(cp.read_bytes())
 checked=policy.check(c,root=cp.parent,require_new_root=False)
 oldcheck=retained.policy.check
 def check(candidate,**kw):
  if candidate!=c:raise ValueError("one actual renewed audited contract")
  return checked
 retained.policy.check=check
 try:report=retained.audit(path,live_release=live_release)
 finally:retained.policy.check=oldcheck
 launch=json.loads((Path(c["raw_root"])/"launch.json").read_bytes())
 if launch.get("r43_launch_identity")!=receipt(c):raise ValueError("actual renewal owner receipt differs")
 report.update(r43_diagnostic_transport_valid=True,r43_host_source_sha256=c["r43_host_source_sha256"],
  r43_authority=c["r43_authority"],r43_launch_identity=launch["r43_launch_identity"],
  full_goal_complete=False,new_performance_acceptance=False)
 return report
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--live-release",action="store_true");p.add_argument("--output",required=True);a=p.parse_args()
 report=audit(a.contract,live_release=a.live_release);data=(json.dumps(report,sort_keys=True)+"\n").encode()
 with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
 print(json.dumps({"r43_diagnostic_transport_valid":True,"output":a.output,"sha256":hashlib.sha256(data).hexdigest(),"live_release_verified":report.get("live_release_verified",False)}))
