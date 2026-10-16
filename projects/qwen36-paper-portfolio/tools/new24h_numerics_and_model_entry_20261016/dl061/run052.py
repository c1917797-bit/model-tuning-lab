"""Reuse exact original043 owner; source binding and new output identity only."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
OUT='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061'
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--phase',choices=('bind','sourceaudit','cpu','numeric16','numeric160'),required=True);p.add_argument('--template-ref',required=True)
 for n in('original035-source-ref','build-ref','host-cpu','guest-cpu','cpu-owner-ref','smoke-owner-ref'):p.add_argument('--'+n)
 p.add_argument('--storage-authority-ref');a=p.parse_args();tr=json.loads(a.template_ref);C.need(C.ref(P/'SOURCE_TEMPLATE.json')==tr,'reviewed052 template')
 if a.phase=='bind':argv=[sys.executable,'-I','-B',str(P/'bind052.py'),'--execute','--template-ref',a.template_ref,'--original035-source-ref',a.original035_source_ref,'--build-ref',a.build_ref,'--storage-authority-ref',a.storage_authority_ref]
 else:
  output=Path(OUT)/('run-'+a.phase+'-MAIN-20261016-NEW24H-001');C.need(not output.exists()and output.parent.is_dir()and not output.parent.is_symlink(),'new explicit opt output root')
  argv=[sys.executable,'-I','-B',str(P/'run031.py'),'--execute','--phase',a.phase,'--template-ref',a.template_ref,'--host-cpu',a.host_cpu,'--guest-cpu',a.guest_cpu,'--output',str(output)]
  if a.phase.startswith('numeric'):argv+=['--cpu-owner-ref',a.cpu_owner_ref]
  if a.phase=='numeric160':argv+=['--smoke-owner-ref',a.smoke_owner_ref]
 return subprocess.call(argv)
if __name__=='__main__':raise SystemExit(main())
