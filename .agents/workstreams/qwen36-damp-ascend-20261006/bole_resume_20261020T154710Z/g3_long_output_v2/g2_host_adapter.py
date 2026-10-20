"""Explicit untimed TP4/3CPU diagnostic plus independent CPU145 consumer.

The original two reserved CPUs, RAM/disk/resource/protected-device checks and
cleanup owner proof remain. This profile is forbidden as formal timing evidence.
"""
import ast
from pathlib import Path
import types
import g2_contract as G2

CPU_PROFILE=dict(schema='bole.untimed-stream-CPU-budget/v1',host=[166],model=[0,1,2],
    consumer=[145],reserve=[3,144],host_budget=1,model_budget=3,consumer_budget=1,
    reserve_budget=2,total_budget=7,TP_world_size=4,formal_timing=False)


def derive(body,external):
    text,prior=external.derive(body)
    pairs=[('cpu=e["arm"]=="cpu-preflight";mem=8*c.GIB if cpu else MEM;cores=1 if cpu else 4',
        'cpu=e["arm"] in ("cpu-preflight","stream-consumer");mem=8*c.GIB if cpu else MEM;cores=1 if cpu else 3')]
    before=text
    for old,new in pairs:
        if text.count(old)!=2:raise ValueError('exact original two create/inspect CPU classifications')
        text=text.replace(old,new)
    inverse=text
    for old,new in reversed(pairs):inverse=inverse.replace(new,old)
    if inverse!=before:raise ValueError('exact whole new CPU delta inverse')
    return text,pairs


def cpu_admission(original,host,daemon):
    baseline=original(host,daemon) # Original reserve2/shared7 checks remain.
    if host['effective_cpus']!=[166]or host['effective_capacity']<1:
        raise ValueError('actual pinned host166/1CPU')
    if not set(range(4))|{144,145,166}<=set(daemon['effective_cpus']):
        raise ValueError('actual daemon model3/consumer1/host1/reserve2 cpuset')
    groups=[CPU_PROFILE[k]for k in('host','model','consumer','reserve')]
    if len(set(sum(groups,[])))!=sum(map(len,groups)):
        raise ValueError('no CPU borrowing or reserve double count')
    return dict(baseline,guest_cpus=[0,1,2],reserve_cpus=[3,144],guest_cpu_budget=3,
        stream_consumer_cpus=[145],stream_consumer_cpu_budget=1,diagnostic_only=True)


def install(C,c,S,H,m):
    import external025 as external
    C.need(C.ref(__file__)==m['files']['g2_host_adapter.py']and
        m['stream_resource_profile']==CPU_PROFILE and S.MEM==32*c.GIB and
        S.HOST_MEM==512*2**20 and S.RESERVE==8*c.GIB and S.WORKSPACE==32*c.GIB,
        'exact new diagnostic profile after unchanged cap32/025 admission')
    text,pairs=derive(Path(S.__file__).read_bytes(),external)
    channel=Path(m['stream_channel_root']);receipt=Path(m['model_receipt_root'])
    C.need(channel==receipt/'STREAM','exact nested stream capability')
    def environment(e):
        if e['arm']!='stream-consumer':return external.environment(e)
        mounts=e['mounts'];C.need(Path(mounts['/adakv-results'][0])==channel and
            all(not rw or Path(src)==channel for src,rw in mounts.values())and
            mounts[str(receipt)]==(str(receipt),False)and
            mounts[m['root']]==(m['root'],False),
            'consumer sole owned nested RW leaf; whole source/receipt parent RO')
        return dict(HOME='/adakv-results/.runtime/home',TMPDIR='/adakv-results',
            XDG_CACHE_HOME='/adakv-results/.runtime/xdg',TORCH_HOME='/adakv-results/.runtime/torch',
            TORCH_EXTENSIONS_DIR='/adakv-results/.runtime/extensions',TRITON_CACHE_DIR='/adakv-results/.runtime/triton',
            HF_HOME='/adakv-results/.runtime/hf',HF_HUB_CACHE='/adakv-results/.runtime/hf/hub',
            VLLM_CACHE_ROOT='/adakv-results/.runtime/vllm',TORCHINDUCTOR_CACHE_DIR='/adakv-results/.runtime/inductor')
    tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in('create_argv','validate_inspect')]
    C.need(len(nodes)==2,'only exact original create/inspect helpers derived')
    scope=dict(S.__dict__,_EXTERNAL=types.SimpleNamespace(environment=environment,LOG=external.LOG))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),S.__file__+'#G2-explicit-CPU-profile','exec'),scope)
    S._EXTERNAL=scope['_EXTERNAL']
    for name in('create_argv','validate_inspect'):S.__dict__[name]=types.FunctionType(scope[name].__code__,S.__dict__,name)
    original=S.cpu_admission
    S.cpu_admission=lambda host,daemon:cpu_admission(original,host,daemon)
    return dict(profile=CPU_PROFILE,delta=pairs,common_model_GiB=32,consumer_GiB=8,
        host_GiB=.5,RAM_reserve_GiB=8,concurrent_budget_GiB=48.5,
        original_resource_admission_unchanged=True,formal_timing=False)
