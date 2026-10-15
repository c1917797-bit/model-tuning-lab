"""Typed existing Devices[] owner CLI; MAIN alone provides fresh CPU IDs."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import host as H
AUTH=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW48H_AUTHORITY_20261014.json',bytes=3591,sha256=H.AUTH_SHA)
OUTPUT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl043r3-sidecar-cpu-new48h-MAIN-20261015-001-repair3'
def argv(phase,sr,m,host_cpu,guest_cpu):
 a=['/usr/bin/python3','-I','-B',str(P/'host.py'),'--source-audit-only'if phase=='sourceaudit'else'--execute','--owner-ref',json.dumps(sr),'--target-source-ref',json.dumps(sr),'--authority-ref',json.dumps(AUTH),'--lifecycle-ref',json.dumps(m['lifecycle_source_ref']),'--stage','cpu','--steps','16','--output',OUTPUT,'--host-cpu',str(host_cpu),'--guest-cpu',str(guest_cpu)]
 return a
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--template-ref',required=True);p.add_argument('--phase',choices=('bind','sourceaudit','cpu'),required=True);p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);a=p.parse_args()
 if not a.execute:print('disabled');return
 tr=json.loads(a.template_ref);t=H.obj(tr);H.need(tr['path']==str(P/'SOURCE_TEMPLATE.json')and t['root']==str(P),'sourcebound actual template')
 for r in t['files'].values():H.validate_ref_streamed(r)
 if a.phase=='bind':
  import bind_recovery;return bind_recovery.bind(tr)
 H.need(a.host_cpu is not None and a.guest_cpu is not None and a.host_cpu!=a.guest_cpu,'fresh disjoint actual CPU IDs')
 sr=H.ref(P/'SOURCE_MANIFEST.json');m=H.obj(sr);return subprocess.call(argv(a.phase,sr,m,a.host_cpu,a.guest_cpu))
if __name__=='__main__':raise SystemExit(main())
