"""One original owned stage; no build/binder/controller or automatic NPU."""
import argparse,hashlib,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-sha256');p.add_argument('--stage',choices=('audit','cpu','numeric'));p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);a=p.parse_args()
 if not a.execute:print('disabled');return
 import io_contract as C
 sr=ref(P/'BOUND_NUMERIC_SOURCE.json');C.need(sr['sha256']==a.source_sha256,'MAIN reviewed source');m=C.source(sr)
 C.need(a.stage and a.host_cpu is not None and a.guest_cpu is not None,'explicit fresh actual CPUs and stage')
 argv=['/usr/bin/python3','-I','-B',str(P/'host.py'),'--owner-ref',json.dumps(sr),'--target-source-ref',json.dumps(sr),'--authority-ref',json.dumps(m['authority_ref']),'--stage','cpu'if a.stage=='audit'else a.stage,'--host-cpu',str(a.host_cpu),'--guest-cpu',str(a.guest_cpu),'--physical-device','4','--output',m['outputs']['numeric'if a.stage=='numeric'else'cpu']]
 if a.stage=='audit':argv+=['--source-audit-only']
 else:argv+=['--execute']
 if a.stage=='numeric':
  own=C.obj(ref(Path(m['outputs']['cpu'])/'RESULT.json'));C.need(own['source']==sr and own['primary']is None and own['secondary']==[]and own['stopped_retained']is True and own['NPU']is False,'actual same-source CPU owner/release')
  cr=own['result'];v=C.obj(cr);C.need(v['source']==sr and v['pass_gate']is True and v['direct_round_controls']['direct_RNE']is True and len(v['actual_new_library_registration'])==1,'actual same-image directRNE/Meta success')
  dm=C.obj(v['debug_meta_ref']);C.need(dm['source']==sr and dm['debug_build']==m['debug_build_ref']and dm['library']==m['debug_library']and dm['pass_gate']is True and dm['NPU']is False,'actual same-source real debug Meta')
  argv+=['--cpu-preflight-ref',json.dumps(cr)]
 os.execv(argv[0],argv)
if __name__=='__main__':main()
