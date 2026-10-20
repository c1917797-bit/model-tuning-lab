"""MAIN-owned finite Devices[] checks of frozen timing bytes; no NPU access."""
import hashlib
import json
from pathlib import Path
import subprocess
import time
import traceback

T = Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SRC = T / 'gdn_timing_v1'
OUT = Path('/opt/host/vnf/austinov/run-bole-gdn-timing-cpu-20261020T154710Z-v1')
NAME = 'bole-gdn3-timing-cold-20261020t154710z-v1'
IMAGE = 'sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
D = '/usr/bin/docker'
PY = '/usr/local/python3.12.13/bin/python3'

GUEST = r'''
import ast,hashlib,json,pathlib,shutil,subprocess,sys
T=pathlib.Path(__TASK__); S=T/'gdn_timing_v1'
p=pathlib.Path('/tmp/packet/gdn_timing_owner');p.mkdir(parents=True)
for x in (S/'gdn_timing_owner').glob('*.py'):shutil.copyfile(x,p/x.name)
r=pathlib.Path('/tmp/bole_service_reference/installed');r.mkdir(parents=True)
for name in ['triton_jit.py','triton_compiled.py','triton_ascend_compiler.py']:
 shutil.copyfile(T/'kernel_v1/evidence'/name,r/name)
checks=[]
for x in sorted(S.rglob('*.py')):
 ast.parse(x.read_text());compile(x.read_text(),str(x),'exec')
checks.append('all_frozen_AST_compile')
q=subprocess.run([sys.executable,'-I','-B',str(p/'test_pure.py')],capture_output=True,text=True,timeout=60)
print(q.stdout,end='');print(q.stderr,file=sys.stderr,end='');assert q.returncode==0
checks.append('all8_offline_controls_in_actual_sameimage')
for x in [S/'gdn_timing/time_gdn.py']:
 for args in ([],['--help']):
  z=subprocess.run([sys.executable,'-I','-B',str(x),*args],capture_output=True,text=True,timeout=10)
  assert z.returncode==0,(str(x),args,z.stderr)
  if not args:assert json.loads(z.stdout)['enabled'] is False
checks.append('frozen_timing_defaultOFF_help')
runtime={'/usr/local/python3.12.13/lib/python3.12/site-packages/triton/runtime/jit.py':(36630,'8f170a849331e9ce75b0d2d05e0bcd6ad2f9de838bfb277e823617982d672aad'),'/usr/local/python3.12.13/lib/python3.12/site-packages/triton/compiler/compiler.py':(18714,'4e432986cb567b94d282f9a2c2f9911a6c3718337289fa936f240282a6a5d54b'),'/usr/local/python3.12.13/lib/python3.12/site-packages/triton/backends/ascend/compiler.py':(53431,'253bdb0d9bf2d092c8c1ae40cc610b2d00c534b127f9d258e9e8e1a221934002')}
for name,pin in runtime.items():
 b=pathlib.Path(name).read_bytes();assert(len(b),hashlib.sha256(b).hexdigest())==pin
assert not any(n.split('.')[0] in ['torch','torch_npu','triton','vllm'] for n in sys.modules)
print(json.dumps(dict(schema='bole.gdn3-timing-sameimage-cold/v1',pass_gate=True,checks=checks,installed_runtime_exact=True,NPU=False,tensor_runtime_imported=False,actual_timing=False,formal_success=False)))
'''.replace('__TASK__', repr(str(T)))


def ref(p):
    b = Path(p).read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def main():
    OUT.mkdir(mode=0o700)
    before = {str(p): ref(p) for p in SRC.rglob('*') if p.is_file()}
    (OUT/'guest.py').write_text(GUEST)
    cid = None; primary = None; secondary = []; start = time.monotonic()
    def call(args, timeout=25):
        r = subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        if len(r.stdout.encode())+len(r.stderr.encode()) > 2**20:
            raise RuntimeError('bounded preflight output')
        if r.returncode: raise RuntimeError(dict(argv=args,exit_code=r.returncode,stderr=r.stderr))
        return r.stdout
    def inspect(label):
        s=call([D,'inspect',cid]);(OUT/(label+'.json')).write_text(s)
        x=json.loads(s)[0];assert x['Id']==cid and x['Image']==IMAGE
        assert x['Config']['Labels']['model-tuning-lab.owner']==NAME
        assert not x['HostConfig']['Privileged'] and not x['HostConfig']['Devices']
        assert x['HostConfig']['CpusetCpus']=='145' and x['HostConfig']['NetworkMode']=='none'
        assert all('Ascend/driver' not in v['Source'] for v in x['Mounts'])
        return x
    try:
        args=[D,'create','--name',NAME,'--label','model-tuning-lab.owner='+NAME,'--network=none','--memory=1g','--memory-swap=1g','--cpus=1','--cpuset-cpus=145','--pids-limit=128','--read-only','--tmpfs=/tmp:rw,exec,size=268435456','--shm-size=64m','--cap-drop=ALL','--security-opt=no-new-privileges','--env','TORCH_DEVICE_BACKEND_AUTOLOAD=0','--env','ASCEND_RT_VISIBLE_DEVICES=','--env','OMP_NUM_THREADS=1','--mount','type=bind,src='+str(T)+',dst='+str(T)+',readonly','--mount','type=bind,src='+str(OUT)+',dst='+str(OUT)+',readonly','--entrypoint',PY,IMAGE,'-I','-B',str(OUT/'guest.py')]
        cid=call(args).strip();assert len(cid)==64
        inspect('CREATED');call([D,'start',cid])
        s=call([D,'wait',cid],110);assert s.strip()=='0',s
        logs=subprocess.run([D,'logs',cid],capture_output=True,text=True,timeout=20)
        (OUT/'stdout').write_text(logs.stdout);(OUT/'stderr').write_text(logs.stderr)
        assert logs.returncode==0
        x=inspect('EXITED');assert not x['State']['Running'] and x['State']['ExitCode']==0
    except BaseException as e:
        primary=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if cid:
            try:
                x=inspect('CLEANUP-PRE')
                if x['State']['Running']:call([D,'stop','--time','10',cid])
                x=inspect('CLEANUP-FINAL');assert not x['State']['Running'] and not x.get('ExecIDs')
                call([D,'logs',cid])
            except BaseException as e:secondary.append(repr(e))
        after={p:ref(p) for p in before}
        if before!=after:secondary.append('source bytes changed')
        result=dict(schema='bole.gdn3-timing-actual-sameimage-preflight/v1',source_before=before,source_after=after,cid=cid,primary=primary,secondary=secondary,pass_gate=primary is None and not secondary,elapsed=time.monotonic()-start,all_owned_stopped_retained=not secondary,NPU=False,actual_timing=False,formal_success=False)
        (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('source_before','source_after')}))
    return 0 if primary is None and not secondary else 3


if __name__=='__main__':
    raise SystemExit(main())
