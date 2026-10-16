"""Typed sequential frontdoor; existing owners retain sole resource authority."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common095 as C
def commands(a):
 if a.phase=='bind':
  C.need(C.ref(P/'SOURCE_TEMPLATE.json')==json.loads(a.template_ref),'actual reviewed template');return [[sys.executable,'-I','-B',str(P/'bind095.py'),'--execute','--template-ref',a.template_ref]]
 sr=json.loads(a.source_ref);m=C.source(sr)
 if a.phase=='sourceaudit':return [[sys.executable,'-I','-B',str(P/n),'--source-audit','--source-ref',a.source_ref]for n in('owned_cpu095.py','owner095.py')]
 out=Path(m['output_root'])/a.phase;C.need(out.parent.is_dir()and not out.exists(),'MAIN explicit parent prerequisite; new stage output')
 argv=[sys.executable,'-I','-B',str(P/('owner095.py'if a.phase=='numeric'else'owned_cpu095.py')),'--execute','--source-ref',a.source_ref,'--host-cpu',a.host_cpu,'--guest-cpu',a.guest_cpu,'--output',str(out)]
 if a.phase=='numeric':C.need(a.cpu_owner_ref is not None,'actualCPUowner missing');argv+=['--cpu-owner-ref',a.cpu_owner_ref]
 if a.phase=='consumer':
  nr=json.loads(a.numeric_owner_ref);v=C.obj(nr);C.need(v['schema']=='deltalog.graph-owned/v095'and v['source']==sr and v['primary']is None and v['secondary']==[]and v['stopped_retained']is True,'actual same-source NPU release first');argv+=['--numeric-owner-ref',a.numeric_owner_ref,'--stage-ref',json.dumps(v['result'],separators=(',',':'))]
 return [argv]
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--phase',choices=('bind','sourceaudit','cpu','numeric','consumer'));p.add_argument('--template-ref');p.add_argument('--source-ref');p.add_argument('--host-cpu');p.add_argument('--guest-cpu');p.add_argument('--cpu-owner-ref');p.add_argument('--numeric-owner-ref');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 for argv in commands(a):
  r=subprocess.run(argv);C.need(r.returncode==0,'existing owned phase failed; stop, retain, do not run next')
 return 0
if __name__=='__main__':raise SystemExit(main())
