"""Finite single-NPU owner; never touches foreign containers or NPU0-3."""
from pathlib import Path
import hashlib,json,os,re,signal,subprocess,time,traceback
P=Path(__file__).resolve().parent
OUT=Path('/opt/host/vnf/austinov/run-bole-native-ar-fia-20261020T154710Z-v1')
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
D='/usr/bin/docker';SMI='/usr/local/sbin/npu-smi'
def ref(p):
 p=Path(p);h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def write(p,value):
 with p.open('x')as f:json.dump(value,f,sort_keys=True);f.write('\n')
def main():
 assert not OUT.exists();OUT.mkdir(mode=0o700)
 cid=None;primary=None;secondary=[];start=time.monotonic()
 owner_source=ref(__file__);source=ref(P/'replay.py');data=json.loads((P/'INPUTS.json').read_bytes());frames=data['frames']
 assert ref(frames['path'])==frames
 before=Path('/proc/meminfo').read_text()
 mem=next(int(x.split()[1])*1024 for x in before.splitlines()if x.startswith('MemAvailable:'))
 assert mem>=17*2**30 and os.statvfs(OUT).f_bavail*os.statvfs(OUT).f_frsize>=10*2**30
 def call(label,args,timeout=20):
  r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
  record=dict(argv=args,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed=time.monotonic()-start)
  write(OUT/(label+'-'+str(time.time_ns())+'.json'),record)
  if r.returncode:raise RuntimeError(label+' '+r.stderr[-2000:])
  return r.stdout
 def smi(label):
  text=call(label,[SMI,'info'])
  rows=[tuple(map(int,m.groups()))for m in re.finditer(r'^\|\s*(\d+)\s+(\d+)\s*\|\s*(\d+)\s*\|',text,re.M)]
  for physical,chip,pid in rows:
   if physical==4:
    proc=Path('/proc')/str(pid)
    if not proc.exists():
     fresh=call(label+'-fresh',[SMI,'info'])
     assert not re.search(r'^\|\s*4\s+\d+\s*\|\s*'+str(pid)+r'\s*\|',fresh,re.M),'unresolved target PID disappearance'
     continue
    assert cid is not None and cid in(proc/'cgroup').read_text(),'foreign physicalNPU4 process'
    assert chip==0,'actual physical4 chip0'
   if physical in(0,1,2,3):
    proc=Path('/proc')/str(pid)
    try:cgroup=(proc/'cgroup').read_text()
    except FileNotFoundError:cgroup=''
    assert cid is None or cid not in cgroup,'own process on protected card'
  return text
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('finite unit deadline')))
 try:
  text=smi('NPU-BEFORE');assert 'No running processes found in NPU 4'in text
  # Match the device by character major/minor, including container aliases.
  dev=Path('/dev/davinci4').stat().st_rdev
  holders=[]
  for proc in Path('/proc').iterdir():
   if not proc.name.isdigit():continue
   try:
    for fd in(proc/'fd').iterdir():
     try:
      if fd.stat().st_rdev==dev:holders.append(int(proc.name));break
     except(FileNotFoundError,PermissionError):pass
   except(FileNotFoundError,PermissionError,ProcessLookupError):pass
  assert not holders,'unadmitted actual physical4 device FD holders'
  write(OUT/'ADMISSION.json',dict(owner_source=owner_source,source=source,inputs=ref(P/'INPUTS.json'),frames=frames,mem_available=mem,
   physical=[4],protected=[0,1,2,3],device_fd_holders=holders,phase_seconds=180,cleanup_seconds=60))
  args=[D,'create','--name','bole-native-ar-fia-20261020t154710z-v1','--label','model-tuning-lab.owner=bole-native-ar-fia-20261020T154710Z-v1',
   '--network=none','--memory=8g','--memory-swap=8g','--cpus=4','--cpuset-cpus=0,1,2,3','--pids-limit=512',
   '--read-only','--tmpfs=/tmp:rw,size=1073741824','--shm-size=1g','--cap-drop=ALL','--security-opt=no-new-privileges',
   '--env','TORCH_DEVICE_BACKEND_AUTOLOAD=0','--env','OMP_NUM_THREADS=4','--env','MKL_NUM_THREADS=4',
   '--env','ASCEND_RT_VISIBLE_DEVICES=0','--env','ASCEND_PROCESS_LOG_PATH=/tmp/ascend/log',
   '--mount','type=bind,src='+str(P)+',dst='+str(P)+',readonly',
   '--mount','type=bind,src='+frames['path']+',dst='+frames['path']+',readonly',
   '--mount','type=bind,src='+str(OUT)+',dst='+str(OUT),
   '--mount','type=bind,src=/usr/local/Ascend/driver,dst=/usr/local/Ascend/driver,readonly']
  for host,guest in(('/dev/davinci4','/dev/davinci0'),('/dev/davinci_manager','/dev/davinci_manager'),('/dev/devmm_svm','/dev/devmm_svm'),('/dev/hisi_hdc','/dev/hisi_hdc')):args+=['--device',host+':'+guest]
  args+=['--entrypoint','/bin/bash',IMAGE,'-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"','bole-native-ar-fia',
   '/usr/local/python3.12.13/bin/python3','-I','-B',str(P/'replay.py'),'--execute','--frames-ref',json.dumps(frames),'--output',str(OUT/'data')]
  cid=call('CREATE',args).strip();assert len(cid)==64
  write(OUT/'OWNED.json',dict(cid=cid,source=source,image=IMAGE))
  x=json.loads(call('INSPECT',[D,'inspect',cid]))[0];hc=x['HostConfig']
  assert x['Image']==IMAGE and not hc['Privileged']and hc['NetworkMode']=='none'
  assert {(d['PathOnHost'],d['PathInContainer'])for d in hc['Devices']}=={('/dev/davinci4','/dev/davinci0'),('/dev/davinci_manager','/dev/davinci_manager'),('/dev/devmm_svm','/dev/devmm_svm'),('/dev/hisi_hdc','/dev/hisi_hdc')}
  smi('PRESTART')
  with (OUT/'stdout.txt').open('x')as so,(OUT/'stderr.txt').open('x')as se:
   child=subprocess.Popen([D,'start','-a',cid],stdout=so,stderr=se)
   while child.poll()is None:
    assert time.monotonic()-start<180,'single finite phase deadline'
    smi('LIVE')
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:pass
   assert child.returncode==0,'actual replay child failed'
  assert ref(__file__)==owner_source and ref(P/'replay.py')==source and ref(frames['path'])==frames
 except BaseException as e:primary=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  if cid:
   try:
    x=json.loads(call('CLEANUP_INSPECT',[D,'inspect',cid]))[0]
    if x['State']['Running']:call('STOP',[D,'stop','--time','10',cid],25)
    x=json.loads(call('FINAL_INSPECT',[D,'inspect',cid]))[0]
    assert not x['State']['Running']and x['State']['Pid']==0 and not x.get('ExecIDs')
    write(OUT/'CLEANUP.json',dict(cid=cid,stopped=True,retained=True,deleted=False))
   except BaseException as e:secondary.append(repr(e))
  try:smi('NPU-AFTER')
  except BaseException as e:secondary.append(repr(e))
  result=dict(schema='bole.native-ar-fia-bounded-owner/v1',owner_source=owner_source,source=source,frames=frames,cid=cid,primary=primary,secondary=secondary,
   elapsed=time.monotonic()-start,physical=[4],protected=[0,1,2,3],final_success=False)
  write(OUT/'RESULT.json',result);print(json.dumps(result))
 return 0 if primary is None and not secondary else 3
if __name__=='__main__':raise SystemExit(main())
