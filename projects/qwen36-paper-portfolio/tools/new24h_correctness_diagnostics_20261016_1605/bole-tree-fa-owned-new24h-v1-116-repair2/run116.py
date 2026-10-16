"""Typed stage argv, not a controller or scheduler."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C


def command(a):
    prefix=['/usr/bin/python3','-I','-B']
    if a.stage=='bind':
        C.need(a.reviewed_template_ref is not None,'actual reviewed template Ref')
        return prefix+[str(P/'bind116.py'),'--execute','--reviewed-template-ref',a.reviewed_template_ref]
    C.need(a.source_ref is not None,'actual bound source');sr=json.loads(a.source_ref);m=C.source(sr);out=Path(m['output_root'])
    if a.stage=='sourceaudit':return prefix+[str(P/'owner116.py'),'--source-audit','--source-ref',a.source_ref]
    if a.stage=='ticket':
        C.need(a.cpu_owner_ref is not None,'actual released ABI CPU owner')
        return prefix+[str(P/'ticket116.py'),'--execute','--source-ref',a.source_ref,'--cpu-owner-ref',a.cpu_owner_ref,'--output',str(out/'NPU_TICKET.json')]
    C.need(a.host_cpu is not None and a.guest_cpu is not None and a.host_cpu!=a.guest_cpu,'MAIN explicit distinct CPUs')
    args=['--execute','--source-ref',a.source_ref,'--host-cpu',str(a.host_cpu),'--guest-cpu',str(a.guest_cpu)]
    if a.stage=='numeric':
        C.need(a.cpu_owner_ref is not None and a.abi_ticket_ref is not None,'released ABI owner and independent actual ticket required')
        return prefix+[str(P/'owner116.py'),*args,'--cpu-owner-ref',a.cpu_owner_ref,'--abi-ticket-ref',a.abi_ticket_ref,'--output',str(out/'numeric')]
    if a.stage=='consumer':
        C.need(a.numeric_owner_ref is not None,'actual released numeric owner');owner=C.obj(json.loads(a.numeric_owner_ref));C.need(owner['source']==sr and owner['result']is not None,'actual same-source numeric result')
        return prefix+[str(P/'owned_cpu116.py'),*args,'--numeric-owner-ref',a.numeric_owner_ref,'--stage-ref',json.dumps(owner['result'],separators=(',',':')),'--output',str(out/'consumer')]
    return prefix+[str(P/'owned_cpu116.py'),*args,'--output',str(out/'cpu')]


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--stage',choices=['bind','sourceaudit','cpu','ticket','numeric','consumer']);p.add_argument('--reviewed-template-ref');p.add_argument('--source-ref');p.add_argument('--cpu-owner-ref');p.add_argument('--numeric-owner-ref');p.add_argument('--abi-ticket-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    C.need(a.stage is not None,'explicit stage');argv=command(a);print(json.dumps(dict(actual_argv=argv)),flush=True);return subprocess.run(argv).returncode

if __name__=='__main__':raise SystemExit(main())
