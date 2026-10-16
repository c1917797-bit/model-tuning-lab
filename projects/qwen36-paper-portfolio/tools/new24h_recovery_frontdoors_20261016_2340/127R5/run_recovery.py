"""One explicit new ownedCPU leaf. No numeric/NPU branch."""
import argparse,json,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import host as H
from window056 import AUTH
OUTPUT='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-anchor-recovery127repair5-MAIN-20261016-NEW24H-001'
def main():
 whole_start=time.monotonic()
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--phase',choices=('bind','sourceaudit','cpu'),required=True);ap.add_argument('--template-ref',required=True);ap.add_argument('--budget-profile-ref');ap.add_argument('--host-cpu',type=int);ap.add_argument('--guest-cpu',type=int);a=ap.parse_args()
 tr=json.loads(a.template_ref);H.need(H.ref(P/'SOURCE_TEMPLATE.json')==tr,'exact reviewed127R1 template')
 if not a.execute:print('disabled');return 0
 if a.phase=='bind':
  import bind127;return bind127.bind(tr,json.loads(a.budget_profile_ref)if a.budget_profile_ref else None)
 H.need(a.host_cpu is not None and a.guest_cpu is not None and a.host_cpu!=a.guest_cpu,'actual disjoint host/guest CPUs')
 sr=H.ref(P/'SOURCE_MANIFEST.json');m=H.obj(sr)
 argv=['/usr/bin/prlimit','--as=536870912:unlimited','--','/usr/bin/python3','-B',str(P/'host.py'),'--source-audit-only'if a.phase=='sourceaudit'else'--execute','--whole-start',str(whole_start),'--owner-ref',json.dumps(sr),'--target-source-ref',json.dumps(sr),'--authority-ref',json.dumps(AUTH),'--lifecycle-ref',json.dumps(m['lifecycle_source_ref']),'--stage','cpu','--steps','16','--output',OUTPUT,'--host-cpu',str(a.host_cpu),'--guest-cpu',str(a.guest_cpu)]
 return subprocess.call(argv)
if __name__=='__main__':raise SystemExit(main())
