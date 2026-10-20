"""MAIN finite singleton replay and independent Devices[] consumption."""
import argparse,hashlib,json,os,re,signal,subprocess,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
D='/usr/bin/docker';SMI='/usr/local/sbin/npu-smi'
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
R23CID='0ebc2acfa84df1bb1cc8d0b7899d4b942320fc7d206104bbf6f002ce1d239df9'
PHASE=1800;CLEANUP=120

def ref(p):
    p=Path(p);h=hashlib.sha256();n=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def write(p,value):
    with p.open('x')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
    return ref(p)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--output',type=Path);a=ap.parse_args()
    if not a.execute:
        print(json.dumps(dict(enabled=False,NPU=False,formal_success=False)));return 0
    if os.environ.get('BOLE_GDN3_OWNER_ENABLE')!='1'or a.output is None:ap.error('explicit owner opt-in and fresh output required')
    OUT=a.output;assert OUT.is_absolute()and not OUT.exists();OUT.mkdir(mode=0o700)
    start=time.monotonic();cid=None;cpu_cid=None;primary=None;secondary=[];source_before={str(q):ref(q)for q in sorted(P.iterdir())if q.is_file()}
    inputs=json.loads((P/'INPUTS.json').read_bytes());template=inputs['manifest_template'];actual_source=template['actual_source']
    checked_paths=[actual_source,*template['references'].values(),*template['candidate'].values(),*template['files'].values()]
    for pair in template['receipts']:
        checked_paths.append(pair['receipt']);r=json.loads(Path(pair['receipt']['path']).read_bytes());checked_paths.append(r['raw'])
    assert all(ref(r['path'])==r for r in checked_paths)
    mem=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()if x.startswith('MemAvailable:'))
    assert mem>=17*2**30 and os.statvfs(OUT).f_bavail*os.statvfs(OUT).f_frsize>=10*2**30
    env=dict(TORCH_DEVICE_BACKEND_AUTOLOAD='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',ASCEND_RT_VISIBLE_DEVICES='0',BOLE_GDN3_REPLAY_ENABLE='1',BOLE_GDN3_TRITON_ENABLE='1',TRITON_CACHE_DIR='/tmp/triton',VLLM_CACHE_ROOT='/tmp/vllm',ASCEND_PROCESS_LOG_PATH='/tmp/ascend/log')
    def call(label,args,timeout=25):
        r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        value=dict(argv=args,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed=time.monotonic()-start)
        receipt=write(OUT/(label+'-'+str(time.time_ns())+'.json'),value)
        if r.returncode:raise RuntimeError(label+' '+r.stderr[-2000:])
        return r.stdout,receipt
    def inspect(label,identity):
        s,_=call(label,[D,'inspect',identity]);rows=json.loads(s);assert len(rows)==1
        raw_ref=write(OUT/(label+'-RAW-'+str(time.time_ns())+'.json'),rows)
        return rows[0],raw_ref
    def smi(label):
        text,_=call(label,[SMI,'info']);rows=[tuple(map(int,m.groups()))for m in re.finditer(r'^\|\s*(\d+)\s+(\d+)\s*\|\s*(\d+)\s*\|',text,re.M)]
        for physical,chip,pid in rows:
            if physical not in(0,1,2,3,4):continue
            proc=Path('/proc')/str(pid)
            if not proc.exists():
                fresh,_=call(label+'-fresh',[SMI,'info']);assert not re.search(r'^\|\s*'+str(physical)+r'\s+\d+\s*\|\s*'+str(pid)+r'\s*\|',fresh,re.M),'unresolved observed PID disappearance';continue
            try:cg=(proc/'cgroup').read_text()
            except FileNotFoundError:raise ValueError('observed process identity disappeared')
            if physical==4:assert cid is not None and cid in cg and chip==0,'foreign physical4 process'
            else:assert cid is None or cid not in cg,'own process on protected0..3'
        return text
    def holders():
        dev=Path('/dev/davinci4').stat().st_rdev;rows=[]
        for p in Path('/proc').iterdir():
            if not p.name.isdigit():continue
            try:
                for fd in(p/'fd').iterdir():
                    try:
                        if fd.stat().st_rdev==dev:rows.append(int(p.name));break
                    except(FileNotFoundError,PermissionError,ProcessLookupError):pass
            except(FileNotFoundError,PermissionError,ProcessLookupError):pass
        return rows
    def create_args(name,cpus):
        args=[D,'create','--name',name,'--label','model-tuning-lab.owner='+name,'--network=none','--memory=8g','--memory-swap=8g','--cpus='+str(len(cpus.split(','))),'--cpuset-cpus='+cpus,'--pids-limit=512','--read-only','--tmpfs=/tmp:rw,exec,size=1073741824','--shm-size=1g','--cap-drop=ALL','--security-opt=no-new-privileges']
        for k,v in env.items():args+=['--env',k+'='+v]
        mounts={str(P),str(Path(actual_source['path']).parent)}
        mounts.update(str(Path(r['path']).parent)for r in template['candidate'].values())
        mounts.update(str(Path(r['path']).parent)for r in template['references'].values())
        mounts.update(str(Path(x['receipt']['path']).parent)for x in template['receipts'])
        for path in sorted(mounts):args+=['--mount','type=bind,src='+path+',dst='+path+',readonly']
        args+=['--mount','type=bind,src='+str(OUT)+',dst='+str(OUT)]
        return args
    def run_child(identity,label,limit,*,observe=False):
        with(OUT/(label+'.stdout')).open('x')as so,(OUT/(label+'.stderr')).open('x')as se:
            child=subprocess.Popen([D,'start','-a',identity],stdout=so,stderr=se)
            end=time.monotonic()+limit
            while child.poll()is None:
                assert time.monotonic()<end and time.monotonic()-start<PHASE,'one finite whole replay/consumer phase'
                if observe:smi('LIVE')
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:pass
            write(OUT/(label+'-CHILD.json'),dict(exit_code=child.returncode,stdout=ref(OUT/(label+'.stdout')),stderr=ref(OUT/(label+'.stderr'))))
            assert child.returncode==0,'actual '+label+' child failed'
    def stop_owned(identity,label):
        x,_=inspect(label+'-PRE',identity)
        assert x['Id']==identity and x['Image']==IMAGE and x['Config']['Labels']['model-tuning-lab.owner'].startswith('bole-gdn3-')
        if x['State']['Running']:call(label+'-STOP',[D,'stop','--time','10',identity],25)
        x,r=inspect(label+'-FINAL',identity);assert not x['State']['Running']and x['State']['Pid']==0 and not x.get('ExecIDs')
        return r
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('finite unit deadline')))
    replay_result=None;manifest_ref=None;admission_ref=None;release_ref=None
    try:
        text=smi('NPU-BEFORE');assert 'No running processes found in NPU 4'in text
        assert not holders(),'unadmitted actual physical4 device FD holders'
        old,old_ref=inspect('R23-INSPECT',R23CID);assert old['Image']==IMAGE and old['State']['Running']is False
        write(OUT/'RESOURCE-ADMISSION.json',dict(owner_source=ref(__file__),source_before=source_before,inputs=ref(P/'INPUTS.json'),mem_available=mem,physical=[4],protected=[0,1,2,3],phase_seconds=PHASE,cleanup_seconds=CLEANUP,output_cap_bytes=2**30))
        name='bole-gdn3-replay-20261020t154710z-v2';args=create_args(name,'0,1,2,3')
        args+=['--mount','type=bind,src=/usr/local/Ascend/driver,dst=/usr/local/Ascend/driver,readonly']
        for host,guest in(('/dev/davinci4','/dev/davinci0'),('/dev/davinci_manager','/dev/davinci_manager'),('/dev/devmm_svm','/dev/devmm_svm'),('/dev/hisi_hdc','/dev/hisi_hdc')):args+=['--device',host+':'+guest]
        args+=['--entrypoint','/bin/bash',IMAGE,'-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"','bole-gdn3-bootstrap','/usr/local/python3.12.13/bin/python3','-I','-B',str(P/'boot.py'),'--execute','--root',str(OUT),'--source',str(P)]
        s,_=call('CREATE',args);cid=s.strip();assert re.fullmatch('[0-9a-f]{64}',cid)
        x,_=inspect('CREATED-INSPECT',cid);assert x['Image']==IMAGE and x['State']['Running']is False
        write(OUT/'OWNED.json',dict(cid=cid,image=IMAGE,owner_source=ref(__file__)))
        call('START',[D,'start',cid]);x,inspection_ref=inspect('RUNNING-INSPECT',cid);assert x['State']['Running']is True
        hc=x['HostConfig'];assert not hc['Privileged']and hc['NetworkMode']=='none'and hc['CpusetCpus']=='0,1,2,3'
        assert {(d['PathOnHost'],d['PathInContainer'])for d in hc['Devices']}=={('/dev/davinci4','/dev/davinci0'),('/dev/davinci_manager','/dev/davinci_manager'),('/dev/devmm_svm','/dev/devmm_svm'),('/dev/hisi_hdc','/dev/hisi_hdc')}
        admission_ref=write(OUT/'ADMISSION.json',dict(schema='bole.gdn3-replay-owned-admission/v1',authority='MAIN',actual_source=actual_source,physical_devices=[4],logical_devices=[0],guest_device_path='/dev/davinci0',allow_hf32=False,controller_inspection=inspection_ref,r23_controller_inspection=old_ref,image_digest=IMAGE,same_image_as_actual_r23=True,owned_container_id=cid,environment=env))
        template['admission']=admission_ref;manifest_ref=write(OUT/'MANIFEST.json',template);(OUT/'data').mkdir();write(OUT/'MANIFEST-REF.json',manifest_ref)
        # Container already runs the bounded handoff; attach logs without restarting.
        with(OUT/'REPLAY.stdout').open('x')as so,(OUT/'REPLAY.stderr').open('x')as se:
            log=subprocess.Popen([D,'logs','--follow',cid],stdout=so,stderr=se)
            while True:
                assert time.monotonic()-start<PHASE,'one finite replay deadline'
                x,_=inspect('LIVE-INSPECT',cid)
                if not x['State']['Running']:break
                smi('LIVE');time.sleep(2)
            log.wait(timeout=15)
        write(OUT/'REPLAY-CHILD.json',dict(exit_code=x['State']['ExitCode'],stdout=ref(OUT/'REPLAY.stdout'),stderr=ref(OUT/'REPLAY.stderr')))
        assert x['State']['ExitCode']==0,'actual replay child failed'
        replay_result=ref(OUT/'data/REPLAY-RESULT.json');stopped_ref=stop_owned(cid,'REPLAY-RELEASE')
        release_ref=write(OUT/'RELEASE.json',dict(schema='bole.gdn3-replay-owner-released/v1',authority='MAIN',replay_result=replay_result,admission=admission_ref,owner_stop_completed=True,controller_inspection=stopped_ref))
        smi('REPLAY-AFTER');assert not holders(),'owned physical4 FD remains after stop'
        env['ASCEND_RT_VISIBLE_DEVICES']='';env['BOLE_GDN3_REPLAY_ENABLE']='0';env['BOLE_GDN3_TRITON_ENABLE']='0';env['BOLE_GDN3_CONSUME_ENABLE']='1'
        name='bole-gdn3-consumer-20261020t154710z-v2';args=create_args(name,'145')
        args+=['--entrypoint','/usr/local/python3.12.13/bin/python3',IMAGE,'-I','-B',str(P/'consume_gdn.py'),'--execute','--manifest-ref',json.dumps(manifest_ref),'--result-ref',json.dumps(replay_result),'--owner-release-ref',json.dumps(release_ref),'--output',str(OUT/'consumer')]
        s,_=call('CPU-CREATE',args);cpu_cid=s.strip();assert re.fullmatch('[0-9a-f]{64}',cpu_cid)
        x,_=inspect('CPU-INSPECT',cpu_cid);assert not(x['HostConfig']['Devices']or[])and not x['HostConfig']['Privileged']and x['Image']==IMAGE and x['HostConfig']['CpusetCpus']=='145'
        (OUT/'consumer').mkdir();run_child(cpu_cid,'CONSUMER',900)
        assert all(ref(p)==r for p,r in source_before.items())and all(ref(r['path'])==r for r in checked_paths)
    except BaseException as e:primary=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        for identity,label in((cpu_cid,'CPU-CLEANUP'),(cid,'NPU-CLEANUP')):
            if identity:
                try:stop_owned(identity,label)
                except BaseException as e:secondary.append(repr(e))
        try:smi('NPU-AFTER')
        except BaseException as e:secondary.append(repr(e))
        result=dict(schema='bole.gdn3-finite-owner/v1',owner_source=ref(__file__),inputs=ref(P/'INPUTS.json'),source_before=source_before,source_after={p:ref(p)for p in source_before},cid=cid,cpu_cid=cpu_cid,manifest=manifest_ref,admission=admission_ref,replay_result=replay_result,release=release_ref,primary=primary,secondary=secondary,elapsed=time.monotonic()-start,physical=[4],protected=[0,1,2,3],E2E_measured=False,formal_success=False)
        write(OUT/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k not in('source_before','source_after')}))
    return 0 if primary is None and not secondary else 3
if __name__=='__main__':raise SystemExit(main())
