"""Typed commands only. Existing donor owners retain all resource scheduling."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common112 as C


def command(a):
    if a.stage=='bind':
        C.need(a.reviewed_template_ref is not None and a.profile is not None,'explicit reviewed template/profile')
        return ['/usr/bin/python3','-I','-B',str(P/'bind112.py'),'--execute','--reviewed-template-ref',a.reviewed_template_ref,'--profile',a.profile]+(['--smoke-consumer-owner-ref',a.smoke_consumer_owner_ref]if a.smoke_consumer_owner_ref else[])
    C.need(a.source_ref is not None,'actual bound source ref, never a template')
    sr=json.loads(a.source_ref);m=C.source(sr);output=Path(m['output_root'])
    if a.stage=='sourceaudit':return ['/usr/bin/python3','-I','-B',str(P/'owner112.py'),'--source-audit','--source-ref',a.source_ref]
    C.need(a.host_cpu is not None and a.guest_cpu is not None and a.host_cpu!=a.guest_cpu,'explicit distinct CPU IDs')
    common=['--execute','--source-ref',a.source_ref,'--host-cpu',str(a.host_cpu),'--guest-cpu',str(a.guest_cpu)]
    if a.stage=='numeric':
        C.need(a.cpu_owner_ref is not None,'actual CPU owner required')
        return ['/usr/bin/python3','-I','-B',str(P/'owner112.py'),*common,'--cpu-owner-ref',a.cpu_owner_ref,'--output',str(output/'numeric')]
    if a.stage=='consumer':
        C.need(a.numeric_owner_ref is not None,'actual numeric owner required');owner=C.obj(json.loads(a.numeric_owner_ref));C.need(owner['source']==sr and owner['result']is not None,'same source actual numeric result')
        return ['/usr/bin/python3','-I','-B',str(P/'owned_cpu112.py'),*common,'--numeric-owner-ref',a.numeric_owner_ref,'--stage-ref',json.dumps(owner['result'],separators=(',',':')),'--output',str(output/'consumer')]
    return ['/usr/bin/python3','-I','-B',str(P/'owned_cpu112.py'),*common,'--output',str(output/'cpu')]


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--stage',choices=['bind','sourceaudit','cpu','numeric','consumer']);p.add_argument('--profile',choices=['smoke','full']);p.add_argument('--reviewed-template-ref');p.add_argument('--source-ref');p.add_argument('--cpu-owner-ref');p.add_argument('--numeric-owner-ref');p.add_argument('--smoke-consumer-owner-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    C.need(a.stage is not None,'explicit stage');cmd=command(a);print(json.dumps(dict(actual_argv=cmd)),flush=True);return subprocess.run(cmd).returncode

if __name__=='__main__':raise SystemExit(main())
