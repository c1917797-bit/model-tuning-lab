"""Read only an explicitly bound owned PID; retain framework settings, never credentials."""
import argparse
import json
import os
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C

PREFIXES=('VLLM_','ASCEND_','HCCL_','TORCH_','CANN_','MXR_','MST_MXR_','QWEN36_','DLOG_')
SECRET=('TOKEN','SECRET','PASSWORD','API_KEY','CREDENTIAL','PRIVATE_KEY')


def process(pid):
    stat=Path('/proc/%d/stat'%pid).read_text();rest=stat[stat.rfind(')')+2:].split()
    return dict(pid=pid,start_ticks=int(rest[19]),cgroup=Path('/proc/%d/cgroup'%pid).read_text())


def filtered(environment):
    common={};excluded=[]
    for key,value in environment.items():
        if key=='VLLM_PLUGINS':continue
        if key.startswith(('BOLE_','BOLE111_','DENSE_OPPORTUNITY090_')):
            excluded.append(key);continue
        if key.startswith(PREFIXES):
            if any(word in key.upper()for word in SECRET):continue
            C.need(len(value.encode())<=65536,'bounded public framework environment value')
            common[key]=value
    return dict(common_environment=common,plugins=environment.get('VLLM_PLUGINS','').split(','),
                declared_algorithm_or_observer_environment_keys=sorted(excluded),
                credential_values_retained=False,plugin_effect_classification_performed=False)


def collect(sr,variant,expected,output):
    m=C.source(sr);C.need(C.ref(__file__)==m['files']['launch_profile.py'],'exact launch collector source')
    C.need(variant in('native_AR','BOLE')and set(expected)=={'pid','start_ticks','cgroup'}
           and type(expected['pid'])is int and expected['pid']>0,'explicit actually owned process binding')
    C.need(process(expected['pid'])==expected,'actual owned PID/start/cgroup before read')
    with Path('/proc/%d/environ'%expected['pid']).open('rb')as f:raw=f.read(2**20+1)
    C.need(len(raw)<=2**20,'bounded actual process environment')
    environment={}
    for row in raw.split(b'\0'):
        if row:
            key,sep,value=row.partition(b'=');C.need(sep,'actual environment entry')
            key=key.decode('utf8','strict')
            # Decode only values which may be retained; credential values are never decoded/output.
            if key=='VLLM_PLUGINS'or(key.startswith(PREFIXES)and not any(s in key.upper()for s in SECRET)):
                environment[key]=value.decode('utf8','strict')
            elif key.startswith(('BOLE_','BOLE111_','DENSE_OPPORTUNITY090_')):
                environment[key]=''  # Names only: these are explicit algorithm/observer deltas.
    C.need(process(expected['pid'])==expected,'same actual process after bounded read')
    return C.write(output,dict(schema='bole.actual-pair-launch-profile/v1',source=sr,variant=variant,
                              identity=expected,collector=m['files']['launch_profile.py'],**filtered(environment)))


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--variant',choices=('native_AR','BOLE'))
    p.add_argument('--owned-process-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    C.need(a.source_ref and a.variant and a.owned_process_ref and a.output,'explicit owned launch capture')
    result=collect(json.loads(a.source_ref),a.variant,C.obj(json.loads(a.owned_process_ref)),a.output)
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
