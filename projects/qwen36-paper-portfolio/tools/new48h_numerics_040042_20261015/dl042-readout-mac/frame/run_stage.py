"""One original owned stage, no automatic sequence or new controller."""
import argparse,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-sha256',required=True);p.add_argument('--stage',choices=('audit','cpu','numeric'),required=True);p.add_argument('--host-cpu',type=int,required=True);p.add_argument('--guest-cpu',type=int,required=True);a=p.parse_args()
 sr=C.ref(P/'SOURCE_MANIFEST.json');C.need(sr['sha256']==a.source_sha256,'actual reviewed040 source');m=C.source(sr)
 argv=['/usr/bin/python3','-I','-B',str(P/'host.py'),'--owner-ref',json.dumps(sr),'--target-source-ref',json.dumps(sr),'--authority-ref',json.dumps(m['authority_ref']),'--stage','cpu'if a.stage=='audit'else a.stage,'--host-cpu',str(a.host_cpu),'--guest-cpu',str(a.guest_cpu),'--physical-device','4','--output',m['outputs']['numeric'if a.stage=='numeric'else'cpu']]
 argv+=['--source-audit-only'if a.stage=='audit'else'--execute']
 if a.stage=='numeric':
  owner=C.obj(C.ref(Path(m['outputs']['cpu'])/'RESULT.json'));C.need(owner['schema']=='deltalog.single-frame-sidecar-owned/v040'and owner['source']==sr and owner['primary']is None and owner['secondary']==[]and owner['stopped_retained']is True and owner['NPU']is False,'actual same-sourceCPU terminal/release')
  cr=owner['result'];cpu=C.obj(cr);dm=C.obj(cpu['debug_meta_ref']);C.need(cpu['source']==sr and cpu['authority']==m['authority_ref']and cpu['pass_gate']is True and cpu['NPU']is False and cpu['software_cases']==m['software_cases']and dm['source']==sr and dm['debug_build']==m['debug_build_ref']and dm['library']==m['debug_library']and dm['pass_gate']is True,'actual same-sourceMeta frontdoor, no template PASS')
  argv+=['--cpu-preflight-ref',json.dumps(cr)]
 os.execv(argv[0],argv)
if __name__=='__main__':raise SystemExit(main())
