"""Read-only live /proc/namespace collector for explicitly owned smoke journals.
Does not search services, call Docker/systemd, import models, stop or signal.
MAIN supplies a fresh exact owned Docker inspect receipt and original helper Ref.
"""
import argparse
import json
import os
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import http_common as C


def start(proc):
    text=(proc/'stat').read_text();f=text[text.rfind(')')+2:].split();C.need(f[0]!='Z','actual live nonzombie process');return int(f[19])


def collect(source_ref,journals_ref,owned_ref,inspect_ref,helper_ref,G1_source_ref,out):
    m=C.source(source_ref,native_runtime=False);decl=C.obj(journals_ref)
    C.need(decl['source_ref']==source_ref and set(decl['journals'])=={'scheduler','frontend','worker0','worker1','worker2','worker3'},'all six explicit role journals')
    g1=C.obj(G1_source_ref);C.need(helper_ref==g1['files']['frontend_namespace131r18.py'],'same qualified original full namespace interpreter helper')
    F=C.load(helper_ref,'_task_http_exact_original_namespace_helper')
    e,x=C.owned_inspect(owned_ref,inspect_ref)
    C.need(x['State']['Running']is True and x['State']['Pid']>0,'actual same-image live owned container')
    owner_source=C.obj(e['source']);C.need(owner_source['task_normalEOS_smoke_source_ref']==source_ref,'actual new model owner source explicitly binds this exact smoke packet')
    init=Path('/proc')/str(x['State']['Pid']);init_start=start(init);C.need(e['cid']in(init/'cgroup').read_text(),'actual inspected live owned init cgroup')
    processes=[p for p in Path('/proc').iterdir()if p.name.isdigit()];C.need(len(processes)<=16384,'bounded current process inventory')
    result=[];seen=set()
    for role,r in decl['journals'].items():
        p=C.checked(r);C.need(p.stat().st_size<=16*2**20,'bounded actual complete role journal')
        with p.open('rb')as stream:line=stream.readline(2**20+1)
        C.need(len(line)<=2**20 and line.endswith(b'\n'),'complete bounded native journal header');header=C.parse(line)
        C.need(header['event']=='header'and header['payload']['source_ref']==source_ref and header['payload']['role']==role,'actual source/role journal header')
        h=header['payload']['process'];matches=[]
        for proc in processes:
            try:
                cg=(proc/'cgroup').read_text()
                if e['cid']not in cg:continue
                status=(proc/'status').read_text();ns=[int(v)for ln in status.splitlines()if ln.startswith('NSpid:')for v in ln.split()[1:]]
                if ns and ns[-1]==h['pid']:matches.append((proc,cg,status,ns))
            except(FileNotFoundError,ProcessLookupError):continue
        C.need(len(matches)==1,'one actual namespace host process for observer role')
        proc,cg,status,ns=matches[0];tick=start(proc);uids=[int(v)for ln in status.splitlines()if ln.startswith('Uid:')for v in ln.split()[1:]]
        argv=[s.decode()for s in(proc/'cmdline').read_bytes().split(b'\0')if s]
        C.need(tick==h['start_ticks']and uids==[h['uid']]*4 and argv==h['argv']and os.readlink(proc/'exe')==h['executable'], 'same actual role lifetime/UID/loaded executable/argv')
        identity=(int(proc.name),tick);C.need(identity not in seen,'six distinct actual role processes');seen.add(identity)
        program=F.verify(proc,init,'/usr/local/python3.12.13/bin/python3')
        C.need(start(proc)==tick and(proc/'cgroup').read_text()==cg and start(init)==init_start,'same current process/init across namespace binary proof')
        result.append(dict(role=role,journal_ref=r,header=h,host_pid=int(proc.name),host_start_ticks=tick,host_cgroup=cg,
            NSpid=ns,UID=uids,argv=argv,namespace_program=program))
    C.source(source_ref,native_runtime=False)
    return C.write(out,dict(schema='bole.actual-task-normalEOS-process-bindings/v1',collector_ref=m['files']['bind_processes.py'],source_ref=source_ref,journals_ref=journals_ref,
        owned_ref=owned_ref,owned_inspect_ref=inspect_ref,namespace_helper_ref=helper_ref,G1_source_ref=G1_source_ref,
        init_host_pid=int(init.name),init_start_ticks=init_start,processes=result,actual_live_six_roles_same_owned_container=True,
        NPU_dispatch=False,model_ready=False,performance_ready=False,formal_accuracy_accepted=False))


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--collect',action='store_true')
    for n in('source-ref','journals-ref','owned-ref','inspect-ref','namespace-helper-ref','G1-source-ref'):p.add_argument('--'+n)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.collect:print('{"enabled":false,"NPU_dispatch":false}');return 0
    C.need(all(v is not None for v in vars(a).values()),'all exact actual role/owned/helper evidence refs')
    args=[C.parse(v)for v in(a.source_ref,a.journals_ref,a.owned_ref,a.inspect_ref,a.namespace_helper_ref,a.G1_source_ref)]
    print(json.dumps(dict(result_ref=collect(*args,a.output),model_ready=False)));return 0


if __name__=='__main__':raise SystemExit(main())
