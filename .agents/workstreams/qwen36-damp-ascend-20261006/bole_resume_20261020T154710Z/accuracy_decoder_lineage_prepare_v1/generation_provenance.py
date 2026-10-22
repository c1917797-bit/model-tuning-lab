"""Assemble generation provenance from actual retained host operations. No HTTP or clock fabrication."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import decoder_replay_contract as R
PEER='lgw_a6109c51076a4a2c9d2674ca5a8704a0'

def record(value):
    if 'structuredContent'in value:value=value['structuredContent']
    if 'operation'in value:value=value['operation']
    R.need(value['routeDecision']=='peer_direct'and value['targetPeerId']==PEER,'actual retained chicaihong01 host operation route')
    v=value['result']['record']
    R.need(v['state']=='completed'and v['exitCode']==0 and not v.get('timedOut')and not v.get('cancelled')and
        re.fullmatch(r'exec-[0-9a-f]+',v['id'])and v['stderr']=='','actual complete zero-exit host operation')
    return v

def clock(v):
    r=record(v)
    R.need(r['command']=='/usr/bin/date'and r['args']==['+%s.%N']and
        re.fullmatch(r'[0-9]+\.[0-9]{9}\n',r['stdout']),'actual host date stdout, never operator-supplied epoch')
    return float(Decimal(r['stdout'].strip())),int(r['id'][5:],16)

def provenance(before_ref,dispatch_ref,after_ref,owner_ref,HTTP_source_ref,plan_ref):
    before,bi=clock(R.obj(before_ref));after,ai=clock(R.obj(after_ref));dispatch=record(R.obj(dispatch_ref))
    R.need(bi<int(dispatch['id'][5:],16)<ai and before<=after,'retained host operation ordering brackets complete generation owner')
    owner=R.obj(owner_ref);client_ref=owner['summary']['client_ref'];client=R.obj(client_ref)
    release_ref=owner['summary']['model_release_ref'];release=R.obj(release_ref)
    raw_ref=client['raw_ref'];raw=R.obj(raw_ref);plan=R.obj(plan_ref);HTTP_source=R.obj(HTTP_source_ref)
    source=R.obj(owner['source_ref']);argv=[dispatch['command'],*dispatch['args']]
    entries=[v for v in argv if v.endswith('.py')]
    R.need(source['task_normalEOS_smoke_source_ref']==HTTP_source_ref and owner['actual_argv']==argv and
        len(argv)>=4 and argv[0]in('/usr/bin/env','/usr/bin/python3')and '/usr/bin/python3'in argv and
        '-I'in argv and '-B'in argv and '--execute'in argv and len(entries)==1 and
        entries[0]in{r['path']for r in source['files'].values()},
        'actual exact owned generation entry/source/host argv, not a planned launch')
    outputs=[]
    for line in dispatch['stdout'].splitlines():
        try:v=json.loads(line)
        except ValueError:continue
        if type(v)is dict and (v.get('result_ref')==owner_ref or v.get('owner_ref')==owner_ref):outputs.append(v)
    R.need(len(outputs)==1,'actual foreground terminal host operation emitted this exact completed owner Ref')
    producer=R.ref(__file__)
    value=dict(schema='bole.actual-task-generation-provenance/v1',producer_ref=producer,
        plan_ref=plan_ref,raw_ref=raw_ref,HTTP_source_ref=HTTP_source_ref,
        authority_ref=HTTP_source['authority_ref'],owner_ref=owner_ref,client_ref=client_ref,release_ref=release_ref,
        started_epoch=before,finished_epoch=after,
        host_clock_before_ref=before_ref,host_execution_ref=dispatch_ref,host_clock_after_ref=after_ref,
        timing_scope='conservative host-clock bracket includes foreground owner startup/request/stop-retain',
        operator_epochs_accepted=False,HTTP_executed_by_producer=False,NPU_dispatched_by_producer=False)
    binding=dict(schema='bole.current-CPU-replay-binding/v1',phase=plan['phase'],arm=plan['arm'],
        historical_task_source_ref=plan['source_ref'],effective_inputs_ref=plan['effective_inputs_ref'],
        plan_ref=plan_ref,raw_ref=raw_ref,generation_producer_ref=producer)
    R.generation_policy(binding,plan,raw,value,HTTP_source,R.obj(value['authority_ref']),owner,client,release)
    return value

def assemble(before_ref,dispatch_ref,after_ref,owner_ref,HTTP_source_ref,plan_ref,output):
    value=provenance(before_ref,dispatch_ref,after_ref,owner_ref,HTTP_source_ref,plan_ref)
    R.need(output.is_absolute()and output.parent.is_dir()and not output.exists()and
        not any(p.is_symlink()for p in output.parents),'fresh provenance-only output')
    with output.open('xb')as stream:
        stream.write(R.canonical(value)+b'\n');stream.flush();__import__('os').fsync(stream.fileno())
    return R.ref(output)

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--assemble',action='store_true')
    names=('before-clock-ref','dispatch-ref','after-clock-ref','owner-ref','HTTP-source-ref','plan-ref')
    for n in names:p.add_argument('--'+n)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.assemble:
        R.need(not any(getattr(a,n.replace('-','_'))for n in names)and a.output is None,'explicit mode')
        print('{"enabled":false,"HTTP":false,"NPU":false,"authority_created":false}');return
    R.need(a.output and all(getattr(a,n.replace('-','_'))for n in names),'all actual host operations/owner/source/plan references')
    refs=[json.loads(getattr(a,n.replace('-','_')))for n in names]
    print(json.dumps(dict(provenance_ref=assemble(*refs,a.output),HTTP=False,NPU=False,authority_created=False)))
if __name__=='__main__':main()
