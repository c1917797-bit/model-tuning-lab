"""Private output/CPU-resource namespace over exact registered025 helpers."""
from contextlib import contextmanager
from pathlib import Path
import sys
import time

NAMES=('sourceio','contract090','external025','cap48_provider','owned_substrate',
       'output_scan131r8','observer_race_repair')
ORIGINAL_ROOT='/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-tp4-model-once-v1-025'
ORIGINAL={
 'model_contract.py':(13660,'82243c277890aef7c24ea5eb5fbfa0658b314a39c01d7b2a7ddf34b2bf363e9f'),
 'safety_host.py':(22338,'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'),
 'host_once.py':(18170,'36844e41895b95e810b54ecae32994a96b21258ae8ad8d88fccaac19f035cf8c')}
HOST_ROOT='/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools'
HOST_HELPERS={
 'short_horizon_h8_gate_v4/host_run.py':'4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20',
 'full_matrix_host_v2/host.py':'ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86',
 'saved_step_native_order_v2/host_run.py':'86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc'}


def helper_refs(C,on):
    result=[on['files'][name+'.py']for name in(*NAMES,'frontend_namespace131r18')]
    for name,(size,sha)in ORIGINAL.items():
        r=C.ref(Path(ORIGINAL_ROOT)/name);C.need((r['bytes'],r['sha256'])==(size,sha),'whole genuine025 source')
        result.append(r)
    for relative,sha in HOST_HELPERS.items():
        r=C.ref(Path(HOST_ROOT)/relative);C.need(r['sha256']==sha,'whole original host CPU/process helper');result.append(r)
    # Exact protected0..3 lifecycle source used by025; not its old main/source admission.
    native=dict(path='/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-native-serial-once-v1-016/SOURCE_MANIFEST.json',
                sha256='201ad2395f3f2213cd8e8d5c5486d6d1f94633615b94f279c42a33db3e2e757d')
    result.append(C.ref(C.checked(native)));manifest=C.obj(native)
    wanted={'once_contract.py','safety_lifecycle.py'}
    matches=[r for r in manifest['files']if Path(r['path']).name in wanted]
    C.need({Path(r['path']).name for r in matches}==wanted,'complete exact protected lifecycle helper pair')
    result.extend(matches)
    for r in result:C.checked(r)
    return result


@contextmanager
def open_namespace(C,x,on):
    C.need(not any(name in sys.modules for name in(*NAMES,'model_contract','safety_host','_mxr_actual025_host_once')),
           'fresh private -I/-B owner; no foreign module mutation')
    old_path=list(sys.path);out=Path(x['output_root']);D=E=S=None;old={};old_external=None;old_mem=None;old_argv=None;old_inspect=None
    C.need(out.parent==Path('/opt/host/vnf/austinov')and out.name.startswith('run-bole-task-cpu-')and not out.exists(),
           'new registered task CPU output root')
    try:
        sys.path.insert(0,on['root'])
        C.load(on['files']['sourceio.py'],'sourceio');D=C.load(on['files']['contract090.py'],'contract090')
        old={key:getattr(D,key)for key in('OUT','CPU_OUT','OUTPUT_POSIX','CPU_OUTPUT_POSIX')}
        new=dict(OUT=out,OUTPUT_POSIX=str(out),CPU_OUT=out.with_name(out.name+'-unused'),
                 CPU_OUTPUT_POSIX=str(out.with_name(out.name+'-unused')))
        for key,value in new.items():setattr(D,key,value)
        E=C.load(on['files']['external025.py'],'external025');old_external=E.OUT
        substrate=C.load(on['files']['owned_substrate.py'],'owned_substrate');c,S,H,pairs=substrate.load(out)
        C.need(E.OUT==out and S.MEM==32*C.GIB and S.RESERVE==8*C.GIB and S.HOST_MEM==512*2**20
               and S.PHASE==3600 and S.CLEANUP==180 and S.WORKSPACE==32*C.GIB and S.PHYSICAL==(4,5,6,7),
               'exact registered025/cap32/window/output/cleanup safety before CPU-only profile')
        old_mem=S.MEM;S.MEM=8*C.GIB
        old_argv=S.create_argv;old_inspect=S.validate_inspect
        def cpu_argv(expected):
            C.need(expected['arm']=='cpu-preflight','CPU-only namespace never creates a model profile')
            args=old_argv(expected);C.need('--runtime'not in args and '--device'not in args,'original Devices[] CPU argv')
            return [*args[:2],'--runtime','runc',*args[2:]]
        def cpu_inspect(value,expected):
            C.need(expected['arm']=='cpu-preflight','CPU-only inspect profile')
            old_inspect(value,expected)
            C.need(value['HostConfig']['Runtime']=='runc','explicit plain CPU runtime, no Ascend injection')
        S.create_argv=cpu_argv;S.validate_inspect=cpu_inspect
        authority=C.authority(x['authority_ref'],C.PHASE)
        C.need(authority['cutoff_epoch']<=c.CUTOFF and time.time()+C.PHASE<c.CUTOFF,
               'new CPU authority within unchanged registered technical admission horizon')
        for name in NAMES:
            if name in sys.modules:C.need(C.ref(sys.modules[name].__file__)==on['files'][name+'.py'],'exact source-bound host helper '+name)
        proof=dict(schema='bole.task-CPU-private025-namespace/v1',source_global_deltas=[
            dict(module='contract090',name=k,before=str(old[k]),after=str(new[k]))for k in new],
            CPU_only_resource_delta=dict(name='safety_host.MEM',before=old_mem,after=S.MEM,
                reason='CPU-only8GiB guest; create/inspect CPU branch remains original8GiB'),
            original_joint_deltas=[dict(before=a.decode(),after=b.decode())for a,b in pairs],
            original025_safety_reimplemented=False,original_7CPU_admission_preserved=True,
            CPU_create_explicit_runtime_delta='append --runtime runc; require cpu-preflight/Devices[]; original argv/inspect execute unchanged',
            original_disk32GiB_plus8_5GiB_reserve_preserved=True,phase_seconds=3600,cleanup_seconds=180,
            no_model_dispatch=True,worker_signal_permitted=False)
        yield c,S,H,proof
    finally:
        if S is not None and old_argv is not None:
            C.need(S.create_argv is cpu_argv and S.validate_inspect is cpu_inspect,'no foreign CPU profile replacement')
            S.create_argv=old_argv;S.validate_inspect=old_inspect
        if S is not None and old_mem is not None:
            C.need(S.MEM==8*C.GIB,'no foreign CPU resource mutation');S.MEM=old_mem
        if D is not None:
            for key,value in old.items():
                C.need(getattr(D,key)==new[key],'no foreign output namespace mutation');setattr(D,key,value)
                C.need(getattr(D,key)is value,'exact original global object restored')
        if E is not None and old_external is not None:E.OUT=old_external
        sys.path[:]=old_path
