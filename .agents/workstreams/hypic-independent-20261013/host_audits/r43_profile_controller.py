"""Renew authority/storage only, delegate unchanged reviewed R42 runtime owner."""
import argparse,json,threading
from pathlib import Path
from host_audits import r42_profile_controller as retained
from host_audits import r43_renewal_policy as policy
W=policy.W
_LOCK=threading.Lock()
check_contract=policy.check
def receipt(c):
 return {"authority":c["r43_authority"],"source_sha256":c["r43_host_source_sha256"],
 "outer_host_controller_sha256":c["r43_controller_sha256"],"raw_root":c["raw_root"],
 "original_r42_controller_sha256":c["r42_controller_sha256"],"diagnostic_only":True}
def run_contract(c,*,source_root=W):
 checked=check_contract(c,root=source_root);policy.require_budget(c)
 if not _LOCK.acquire(blocking=False):raise RuntimeError("one R43 controller")
 oldcheck=retained.check_contract;oldbudget=retained.policy.require_budget
 oldrewrite=retained.retained.rewrite_launch;oldsnapshot=retained.retained.base.snapshot
 def check(candidate,**kw):
  if candidate!=c:raise ValueError("one frozen renewal contract")
  return checked
 def rewrite(data,contract,proof):
  oldrewrite(data,contract,proof);data["r43_launch_identity"]=receipt(c);return data
 def snapshot(cid=None):
  result=oldsnapshot(cid)
  if cid:
   import os
   st=os.statvfs(policy.RAW_PARENT)
   if st.f_bavail*st.f_frsize<c["cache_free_floor"]:
    retained.retained.base.stop_owned_on_foreign(cid,image=c["image"])
    raise RuntimeError("dedicated raw-volume floor stopped exact owned service")
  return result
 retained.check_contract=check;retained.policy.require_budget=policy.require_budget
 retained.retained.rewrite_launch=rewrite;retained.retained.base.snapshot=snapshot
 try:return retained.run_contract(c,source_root=source_root)
 finally:
  retained.check_contract=oldcheck;retained.policy.require_budget=oldbudget
  retained.retained.rewrite_launch=oldrewrite;retained.retained.base.snapshot=oldsnapshot;_LOCK.release()
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--run",action="store_true");a=p.parse_args()
 c=json.loads(Path(a.contract).read_bytes())
 if a.run:run_contract(c)
 else:print(json.dumps(check_contract(c)))
