"""Typed thin commands over original binder/owner. Default OFF; MAIN alone runs."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
AUTH=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW48H_AUTHORITY_20261014.json',bytes=3591,sha256='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99')
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--phase',choices=('bind','sourceaudit','cpu','numeric16','numeric160'),required=True);p.add_argument('--template-ref',required=True);p.add_argument('--composite-source-ref');p.add_argument('--composite-cpu-owner-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);p.add_argument('--output',type=Path);p.add_argument('--cpu-owner-ref');p.add_argument('--smoke-owner-ref');a=p.parse_args()
 tr=json.loads(a.template_ref);C.need(C.ref(P/'SOURCE_TEMPLATE.json')==tr,'MAIN reviewed full template Ref3')
 if a.phase=='bind':
  C.need(a.composite_source_ref and a.composite_cpu_owner_ref,'actual022 source/owner required')
  argv=[sys.executable,'-I','-B',str(P/'bind_composite.py'),'--execute','--template-sha256',tr['sha256'],'--composite-source-ref',a.composite_source_ref,'--composite-cpu-owner-ref',a.composite_cpu_owner_ref]
 else:
  sr=C.ref(P/'SOURCE_MANIFEST.json');m=C.source(sr);C.need(m['prepared_template']==tr and m['prepared_only']is False,'actual binder must have run')
  C.need(a.host_cpu is not None and a.guest_cpu is not None and a.output is not None,'actual CPU assignment/new output mandatory')
  C.need(not a.output.exists(),'exclusive new output')
  argv=['/usr/bin/prlimit','--as=536870912:unlimited','--','/usr/bin/python3','-B',str(P/'host.py'),'--source-audit-only'if a.phase=='sourceaudit'else'--execute','--owner-ref',json.dumps(sr),'--target-source-ref',json.dumps(sr),'--authority-ref',json.dumps(AUTH),'--lifecycle-ref',json.dumps(m['composite_cpu_owner_ref']),'--stage','cpu'if a.phase in('cpu','sourceaudit')else'numeric','--steps','160'if a.phase=='numeric160'else'16','--physical-device','5','--host-cpu',str(a.host_cpu),'--guest-cpu',str(a.guest_cpu),'--output',str(a.output)]
  if a.phase.startswith('numeric'):
   own=C.obj(json.loads(a.cpu_owner_ref));C.need(own['target_source']==sr and own['stage']=='cpu'and own['primary']is None and not own['secondary']and own['stopped_retained']is True,'actual source-bound released CPU owner')
   argv+=['--cpu-preflight-ref',json.dumps(own['result'])]
  if a.phase=='numeric160':argv+=['--smoke-ref',a.smoke_owner_ref]
 return subprocess.call(argv)
if __name__=='__main__':raise SystemExit(main())
