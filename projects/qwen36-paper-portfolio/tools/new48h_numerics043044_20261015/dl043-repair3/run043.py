"""Exact typed caller over inherited owner. Disabled unless MAIN opts in."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
ROOT='/opt/host/vnf/austinov/deltalog-mixed-precast-new48h-043-repair3'
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--phase',choices=('bind','sourceaudit','cpu','numeric16','numeric160'),required=True);p.add_argument('--template-ref',required=True);p.add_argument('--original035-source-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);p.add_argument('--cpu-owner-ref');p.add_argument('--smoke-owner-ref');a=p.parse_args();tr=json.loads(a.template_ref)
 C.need(C.ref(P/'SOURCE_TEMPLATE.json')==tr,'reviewed exact template Ref3')
 if a.phase=='bind':
  m=C.obj(json.loads(a.original035_source_ref));C.need(m['library_ref']==C.obj(tr)['library_ref']and m['prepared_only']is False,'real B010 unchanged; 035 oldFAIL is not numerical admission')
  argv=[sys.executable,'-I','-B',str(P/'run031.py'),'--execute','--phase','bind','--template-ref',json.dumps(tr),'--composite-source-ref',json.dumps(m['composite_source_ref']),'--composite-cpu-owner-ref',json.dumps(m['composite_cpu_owner_ref'])]
 else:
  C.need(a.host_cpu is not None and a.guest_cpu is not None,'fresh actual CPU assignment')
  output=Path(ROOT)/('run-'+a.phase+'-MAIN-20261015-001');C.need(not output.exists()and output.parent.is_dir()and not output.parent.is_symlink(),'MAIN-created exact new opt root and fresh phase output')
  argv=[sys.executable,'-I','-B',str(P/'run031.py'),'--execute','--phase',a.phase,'--template-ref',json.dumps(tr),'--host-cpu',str(a.host_cpu),'--guest-cpu',str(a.guest_cpu),'--output',str(output)]
  if a.phase.startswith('numeric'):argv+=['--cpu-owner-ref',a.cpu_owner_ref]
  if a.phase=='numeric160':argv+=['--smoke-owner-ref',a.smoke_owner_ref]
 return subprocess.call(argv)
if __name__=='__main__':raise SystemExit(main())
