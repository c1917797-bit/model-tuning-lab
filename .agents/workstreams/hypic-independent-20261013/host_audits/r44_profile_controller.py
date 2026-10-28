"""Only official observation count changes; original R43 runtime owns resources."""
import argparse,json
from pathlib import Path
from host_audits import r43_profile_controller as transport
from host_audits import r44_profile_policy as policy
from host_audits.r44_scope import scope
W=policy.W
retained=transport.retained
check_contract=policy.check
def run_contract(c,*,source_root=W):
 checked=check_contract(c,root=source_root);policy.require_budget(c)
 with scope(c,checker=check_contract):return transport.run_contract(c,source_root=source_root)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--contract",required=True);p.add_argument("--run",action="store_true");a=p.parse_args();c=json.loads(Path(a.contract).read_bytes())
 if a.run:run_contract(c)
 else:print(json.dumps(check_contract(c)))
