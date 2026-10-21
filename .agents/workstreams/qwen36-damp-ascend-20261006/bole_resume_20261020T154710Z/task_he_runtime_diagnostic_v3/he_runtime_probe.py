"""Only two env values and network-view diagnostics; no evaluator/generated code."""
import argparse
import hashlib
import inspect
import types
import json
import os
from pathlib import Path
import stat
import sys
import time
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
MARKER='BOLE_HE_RUNTIME_DIAGNOSTIC_V3 '
INTERPRETER_MARKER='BOLE_HE_RUNTIME_INTERPRETER_V3 '


def read_detail(path,limit):
    try:
        with path.open('rb')as f:data=f.read(limit+1)
        if len(data)>limit:raise ValueError('bounded actual network-details file')
        return dict(ok=True,text=data.decode('ascii'),error=None)
    except OSError as error:
        return dict(ok=False,text=None,error=dict(type=type(error).__name__,errno=error.errno))


def network_details(names):
    rows=[]
    for name in names:
        path=Path('/sys/class/net')/name;before=path.lstat()
        row=dict(name=name,lstat=dict(mode=before.st_mode,device=before.st_dev,inode=before.st_ino),
            is_symlink=path.is_symlink(),is_dir=path.is_dir(),
            symlink_target=os.readlink(path)if stat.S_ISLNK(before.st_mode)else None,
            attributes={key:read_detail(path/key,4096)for key in('flags','operstate','type','carrier','ifindex','iflink')})
        after=path.lstat()
        if(before.st_mode,before.st_dev,before.st_ino)!=(after.st_mode,after.st_dev,after.st_ino):
            raise ValueError('same actual sys network entry throughout read-only detail capture')
        rows.append(row)
    process=Path('/proc/self/stat').read_text();fields=process[process.rfind(')')+2:].split()
    return dict(schema='bole.actual-HE-readonly-network-details/v1',sys_entries=rows,
        proc_routes={name:read_detail(Path('/proc/self/net')/name,65536)for name in('route','ipv6_route','if_inet6')},
        guest_process=dict(pid=os.getpid(),start_ticks=int(fields[19])),
        interpretation_performed=False,network_safety_accepted=False)


def observations():
    names=sorted(p.name for p in Path('/sys/class/net').iterdir())
    text=Path('/proc/self/net/dev').read_text();netns=os.readlink('/proc/self/ns/net')
    if len(names)>64 or len(text.encode())>65536 or len(netns)>256:raise ValueError('bounded actual network-view diagnostic')
    env={k:os.environ.get(k)for k in('ASCEND_VISIBLE_DEVICES','HOME')}
    details=network_details(names)
    if sorted(p.name for p in Path('/sys/class/net').iterdir())!=names:raise ValueError('stable actual network entry inventory')
    return dict(environment=env,conditions=dict(ASCEND_VISIBLE_DEVICES_empty=env['ASCEND_VISIBLE_DEVICES']=='',
        HOME_tmp=env['HOME']=='/tmp',sys_class_interfaces_loopback_only=set(names)<={'lo'}),
        sys_class_net_names=names,proc_self_net_dev=text,net_namespace_link=netns,network_details=details)



def original_guard(function,path,name):
    if not inspect.isfunction(function)or function.__qualname__!=name or Path(function.__code__.co_filename)!=path:
        raise ValueError('actual original runtime guard callable/source')
    # Both frozen guards are direct module-level definitions. co_qualname was
    # added only in Python3.11; do not require it or project away code fields.
    module=compile(path.read_bytes(),str(path),'exec')
    found=[code for code in module.co_consts if isinstance(code,types.CodeType)and code.co_name==name]
    if len(found)!=1 or function.__code__!=found[0]:raise ValueError('loaded guard equals unchanged actual public source')


def interpreter():
    value=dict(version=sys.version,version_info=list(sys.version_info),implementation=sys.implementation.name,
        executable=sys.executable)
    if any(len(value[k].encode())>2048 for k in('version','implementation','executable')):
        raise ValueError('bounded actual interpreter receipt')
    return value


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--controls',action='store_true');p.add_argument('--capsule-sha256');a=p.parse_args()
    if not a.controls:print('{"enabled":false,"generated_code_executed":false,"NPU":false}');return 0
    if P!=Path('/source')or os.getuid()!=65534 or os.geteuid()!=65534 or not a.capsule_sha256:raise ValueError('explicit actual nonprivileged probe capsule')
    raw=(P/'HE_CAPSULE.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=a.capsule_sha256:raise ValueError('whole exact new diagnostic capsule')
    cap=json.loads(raw)
    if cap['schema']!='bole.HE-runtime-isolation-diagnostic-capsule/v1':raise ValueError('diagnostic source only')
    for row in cap['files']:
        relative=Path(row['relative'])
        if relative.is_absolute()or'..'in relative.parts:raise ValueError('ordinary public source')
        data=(P/relative).read_bytes()
        if(len(data),hashlib.sha256(data).hexdigest())!=(row['bytes'],row['sha256']):raise ValueError('unchanged public source bytes')
    auth=json.loads((P/'AUTHORITY.json').read_bytes())
    if not(auth['start_epoch']<=time.time()and time.time()+10<auth['cutoff_epoch']):raise ValueError('new current finite diagnostic authority')
    actual_interpreter=interpreter()
    print(INTERPRETER_MARKER+json.dumps(actual_interpreter,sort_keys=True,separators=(',',':'),allow_nan=False),flush=True)
    value=observations()
    import he_worker as W
    if Path(W.__file__)!=P/'he_worker.py'or Path(W.C.__file__)!=P/'task_contract.py':raise ValueError('actual original public worker/helper modules')
    original_guard(W.runtime,P/'he_worker.py','runtime')
    original_guard(W.C.cpu_runtime,P/'task_contract.py','cpu_runtime')
    # Original whole-byte worker and runtime guard execute unchanged; no run()
    # call, official imports, evaluator or generated task/control code follows.
    try:W.runtime();guard=dict(called=True,passed=True,error=None)
    except Exception as e:guard=dict(called=True,passed=False,error=type(e).__name__+': '+str(e))
    value.update(schema='bole.actual-HE-runtime-isolation-diagnostic/v3',capsule_sha256=a.capsule_sha256,interpreter=actual_interpreter,
        original_runtime_guard=guard,diagnostic_only=True,evaluator_executed=False,generated_code_executed=False,
        task_score_produced=False,full_software_qualification_accepted=False,network_safety_accepted=False,NPU=False)
    print(MARKER+json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False),flush=True)
    # Fixed source-bound window allows the actual host lifetime/UID/cgroup proof.
    time.sleep(5)
    return 0


if __name__=='__main__':raise SystemExit(main())
