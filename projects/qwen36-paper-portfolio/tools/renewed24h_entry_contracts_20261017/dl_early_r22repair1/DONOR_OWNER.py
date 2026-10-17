"""MAIN-only one retained-raw CPU child; existing069 ledger is never advanced."""
import argparse,hashlib,importlib.util,json,os,shutil,stat,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-measurement-only-renew24h-v1-22')
OUTROOT=Path('/opt/host/vnf/austinov/run-dl-measurement22-MAIN-RENEW24H_001')
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
PY='/usr/local/python3.12.13/bin/python3';DOCKER='/usr/bin/docker';GIB=2**30;START=1792226600;CUT=1792313000
CANN_WRAPPER='exec "$@"'
SOURCE={'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-model-three-node-entry-new24h-v1-131-repair17/SOURCE_BOUND.json', 'bytes': 59418, 'sha256': '1a6a1e1b6be6afa5ca91bd2909bcdc5fe3a821b4968b5cf04f9e2b2752977552'}
PRODUCER=dict(path='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-numeric160-MAIN-20261016-NEW24H-069-repair1-001/numeric/result/RESULT.json',bytes=100542,sha256='4a5b125780618a6020e2d2bf619be1e4258dbafd9b7699bfe52aabc16fa12caa')
OWNER='deltalog-measurement22';CAP=4*2**20
def storage_check():
 p=OUTROOT;need(p.is_dir()and all(not x.is_symlink()for x in(p,*p.parents)),'exact ordinary MXR authorized parent')
 v=os.statvfs(p);free=v.f_bavail*v.f_frsize;need(free>=8.5*GIB,'live8.5GiB MXR disk reserve, no DL ledger')
 return dict(schema='mxr.explicit-untracked-output-budget/v086',parent=str(p),filesystem_free_bytes=free,live_reserve_bytes=int(8.5*GIB),new_leaf_cap_bytes=CAP,shared_DL_ledger_used=False,ledger_advanced=False)
class Storage086:
 def check(self):return storage_check()
def source_verify(refs):
 for r in refs:checked(r)

def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'Ref3');p=Path(r['path']);need(p.is_absolute()and p.is_file()and all(not x.is_symlink()for x in(p,*p.parents)),'ordinary exact file')
 a=p.stat();need(ref(p)==r,'immutable bytes');b=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns),'stable read');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def docker_argv(args):
 # Host retains512MiB softAS. Only the actual Go Docker client is exec'd under
 # unlimitedAS (the parent hardlimit is independently required unlimited).
 need(type(args)is list and args and args[0]==DOCKER,'only exact absolute Docker child may receive AS wrapper')
 return ['/usr/bin/prlimit','--as=unlimited','--',*args]
def output_scan(p):
 total=0;dev=p.stat().st_dev
 for root,dirs,files in os.walk(p,followlinks=False):
  for n in dirs+files:
   q=Path(root)/n;s=q.lstat();need(not stat.S_ISLNK(s.st_mode)and s.st_dev==dev,'sole RW tree cannot escape')
   if stat.S_ISREG(s.st_mode):total+=s.st_size
   else:need(stat.S_ISDIR(s.st_mode),'ordinary CPU evidence only')
 need(total<=CAP,'complete output exceeds1GiB; do not truncate');return total
def create_argv(cpu,mounts,env,name,child):
 args=[DOCKER,'create','--name',name,'--label','qwen36.owner='+OWNER,'--label','qwen36.stage=math-recovery','--network','none','--ipc','private','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory',str(GIB),'--memory-swap',str(GIB),'--cpus','1','--cpuset-cpus',str(cpu),'--pids-limit','256','--shm-size',str(256*2**20),'--log-driver','none','--entrypoint','/bin/bash']
 for src,(dst,rw)in sorted(mounts.items()):args+=['--mount','type=bind,src='+src+',dst='+dst+(',readonly'if not rw else'')]
 for k,v in sorted(env.items()):args+=['-e',k+'='+v]
 return args+[IMAGE,'-c',CANN_WRAPPER,'boletree116',PY,*child]
def inspect_owned(x,cid,mounts,env,guest,name,child):
 h=x['HostConfig'];cfg=x['Config'];need(x['Id']==cid and x['Image']==IMAGE and x['Name']=='/'+name and cfg['Labels'].get('qwen36.owner')==OWNER,'exact created CID/name/image/owner')
 need(not x.get('ExecIDs')and h['Privileged']is False and h.get('PidMode','')in('','private')and h['ReadonlyRootfs']is True and 'ALL'in h['CapDrop']and any('no-new-privileges'in s for s in h['SecurityOpt']),'owned private restricted container')
 need(h['Memory']==h['MemorySwap']==GIB and h['NanoCpus']==10**9 and h['CpusetCpus']==str(guest)and h['PidsLimit']==256 and h['IpcMode']=='private'and h['NetworkMode']=='none'and h['LogConfig']['Type']=='none','exact CPU/RAM/network/log budgets')
 need(not h.get('Devices')and not h.get('DeviceRequests')and not h.get('DeviceCgroupRules')and not h.get('PortBindings'),'actual Devices[] no exposed NPU/network')
 actual={v['Source']:(v['Destination'],v['RW'])for v in x['Mounts']};need(actual==mounts,'exact RO closure and sole RWout')
 actualenv=dict(v.split('=',1)for v in cfg['Env']);need(all(actualenv.get(k)==v for k,v in env.items())and cfg['Entrypoint']==['/bin/bash']and cfg['Cmd']==['-c',CANN_WRAPPER,'boletree116',PY,*child],'actual exact CANN -> absolute Python3.12 command/env')
 need(not x['State'].get('OOMKilled'),'OOM hard failure');return x
def closure(sr):
 return {},[]
def guest_closure(own):
 refs=[*own['files'].values(),own['authority_ref'],own['prepared_template']]
 for r in refs:checked(r)
 return refs

def receive_preflight(d,sr,guest,producer):
 need(d['schema']=='mxr.prefill-three-arm-stage/v084'and d['source']==guest and d['primary']is None and d['NPU']is False and d['qualified']is False and d['old_failures_unchanged']is True and d['result']['actual_saved_frame_extracted']is True,'actual084 mounted source/frame CPU extraction, not numerical qualification')
def main():
 global OUTROOT
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);p.add_argument('--output',type=Path);p.add_argument('--stage-ref');p.add_argument('--numeric-owner-ref');a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 whole_start=time.monotonic()
 if a.execute and sys.platform=='linux':
  import signal
  def earliest_timeout(signum,frame):raise RuntimeError('original whole180/fixed cutoff includes source closure')
  signal.signal(signal.SIGALRM,earliest_timeout);signal.alarm(max(1,min(180,int(CUT-time.time()))))
 ar=json.loads(a.source_ref);own=obj(ar);need(own['output_root']==str(OUTROOT)+'/'+own['profile'],'exact frozen profile output');OUTROOT=Path(own['output_root']);need(own['schema']=='deltalog.measurement-source/v22'and own['root']==str(HERE)and own['default_enabled']is False,'own source root/defaultOFF')
 for r in own['files'].values():checked(r)
 sys.path.insert(0,str(HERE))
 need(own['prepared_only']is False and own['files']['owner.py']==ref(__file__),'actual bound own launcher source');checked(own['donor']);m,refs=closure(SOURCE);guest_refs=guest_closure(own);refs.extend([own['donor'],*guest_refs])
 need(a.stage_ref is None and a.numeric_owner_ref is None,'no new NPU stage or borrowed owner interface')
 authority=obj(own['authority_ref']);need(authority['schema']=='ascend.paper-portfolio.explicit-renewed24h/v1'and authority['start_epoch']==START and authority['cutoff_epoch']==CUT,'exact actual24h authority unchanged')
 if a.source_audit:print(json.dumps(dict(source=ar,readset=refs,resources_admitted=False,NPU=False)));return 0
 need(sys.platform=='linux'and a.execute and START<=time.time()<CUT-180,'fixed24h/whole180s fit');need(a.output.parent==OUTROOT and a.output.name in('cpu','consumer')and not a.output.exists()and all(not q.is_symlink()for q in(OUTROOT,*OUTROOT.parents)),'one new authorized leaf')
 affinity=os.sched_getaffinity(0);need(a.host_cpu in affinity and a.guest_cpu in affinity and a.host_cpu!=a.guest_cpu,'real disjoint inherited CPU assignments')
 import fcntl,resource,signal
 def interrupted(signum,frame):raise RuntimeError('MAIN-owned CPU074 signal/whole deadline '+str(signum))
 signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGALRM,interrupted);signal.alarm(max(1,int(180-(time.monotonic()-whole_start))))
 os.sched_setaffinity(0,{a.host_cpu});soft,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'host soft512MiB preserves original hard');resource.setrlimit(resource.RLIMIT_AS,(GIB//2,hard))
 def run(args,timeout=20):
  argv=docker_argv(args);called=time.monotonic()
  x=subprocess.run(argv,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=timeout)
  need(len(x.stdout.encode())+len(x.stderr.encode())<=2**20,'bounded Docker metadata')
  receipt=dict(schema='deltalog.actual-Docker-client-call/v074R2',requested_argv=args,actual_argv=argv,exit_code=x.returncode,stdout=x.stdout,stderr=x.stderr,elapsed=time.monotonic()-called)
  # BEFORE output admission there is intentionally no writable leaf. Preserve
  # failure in the original operation stderr instead of masking Go diagnostics.
  if a.output.is_dir():write(a.output/('DOCKER-CALL-%d.json'%time.time_ns()),receipt)
  if x.returncode:print('MAIN_DOCKER_CLIENT_FAILURE '+json.dumps(receipt,sort_keys=True,allow_nan=False),file=sys.stderr,flush=True)
  return x
 def no_overlap(exclude=None):
  x=run([DOCKER,'ps','--no-trunc','--filter','label=qwen36.owner','--format','{{.ID}}']);need(x.returncode==0,'complete live owned list');y=run([DOCKER,'ps','--no-trunc','--filter','label=model-tuning-lab.owner','--format','{{.ID}}']);need(y.returncode==0,'complete model owner live list');ids=set(x.stdout.split())|set(y.stdout.split());need(not(ids-({exclude}if exclude else set())),'no blind shared RAM/CPU overlap with any existing owned task')
 no_overlap();mem=dict(v.split(':',1)for v in Path('/proc/meminfo').read_text().splitlines());need(int(mem['MemAvailable'].split()[0])*1024>=9.5*GIB,'1guest+.5host+8reserve ordinary RAM')
 storage=Storage086();seal=None
 fd=os.open(OUTROOT/'.math-recovery.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  no_overlap();proof=storage.check();need(proof['filesystem_free_bytes']>=8.5*GIB+CAP,'fresh4MiB plus unchanged8.5GiB disk reserve')
  a.output.mkdir();write(a.output/'UNTRACKED_ALLOCATION.json',dict(schema='mxr.explicit-untracked-CPU-output/v086',source=ar,bytes=CAP,proof=proof,ledger_advanced=False,exclusive_MXR084_lock=True,qualified=False))
  env=dict(ASCEND_RT_VISIBLE_DEVICES='',ASCEND_VISIBLE_DEVICES='',TORCH_DEVICE_BACKEND_AUTOLOAD='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(a.output),HOME=str(a.output))
  mounts={str(checked(r)):(r['path'],False)for r in [ar,*own['files'].values(),*refs]}
  mounts[str(a.output)]=(str(a.output),True)

  child=['-I','-B',own['files']['recover.py']['path'],'--execute','--source-ref',json.dumps(ar,separators=(',',':')),'--output',str(a.output)];name='dl-measurement22-cpu-'+str(time.time_ns());cid=None;attach=None;primary=None;secondary=[];start=time.monotonic();released=False
  def inspect():
   z=run([DOCKER,'inspect',cid]);need(z.returncode==0,'own exact inspect readable');x=json.loads(z.stdout);need(len(x)==1,'one own inspect');inspect_owned(x[0],cid,mounts,env,a.guest_cpu,name,child);return x[0]
  try:
   need(time.monotonic()-whole_start<90,'whole preparation leaves cleanup reserve before create')
   argv=create_argv(a.guest_cpu,mounts,env,name,child);write(a.output/'CREATE_ARGV.json',argv);z=run(argv);write(a.output/'CREATE.json',dict(exit=z.returncode,stdout=z.stdout,stderr=z.stderr));need(z.returncode==0,'create success');cid=z.stdout.strip();need(len(cid)==64 and all(v in'0123456789abcdef'for v in cid),'created exact CID');write(a.output/'CID.json',dict(cid=cid,name=name));inspect()
   with(a.output/'child.stdout').open('xb')as out,(a.output/'child.stderr').open('xb')as err:
    attach_argv=docker_argv([DOCKER,'start','--attach',cid]);write(a.output/'ATTACH_ARGV.json',dict(requested_argv=[DOCKER,'start','--attach',cid],actual_argv=attach_argv))
    attach=subprocess.Popen(attach_argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
    while attach.poll()is None:
     need(time.monotonic()-start<90 and time.monotonic()-whole_start<90 and time.time()<CUT-100,'child within remaining90/whole180 incl cleanup30/fixed cutoff');no_overlap(cid);output_scan(OUTROOT);storage.check();x=inspect();write(a.output/('inspect-%d.json'%time.time_ns()),x)
     device=a.output/'CHILD_IDENTITY.json'
     if device.exists()and not(a.output/'MAIN_ARM.json').exists():
      dv=obj(ref(device));hp=x['State']['Pid'];need(x['State']['Running']and type(hp)is int and hp>0,'actual running exact CID before arm')
      proc=Path('/proc')/str(hp);before=(proc/'stat').read_text();start_ticks=before.rsplit(')',1)[1].split()[19];status=(proc/'status').read_text();nsp=[v for v in status.splitlines()if v.startswith('NSpid:')]
      need(dv['source']==ar and dv['start_ticks']==start_ticks and len(nsp)==1 and int(nsp[0].split()[-1])==dv['pid']and os.readlink(proc/'ns/pid')==dv['pid_namespace'],'source/CID/host PID/start/guest namespace join')
      need((proc/'stat').read_text().rsplit(')',1)[1].split()[19]==start_ticks,'stable host start before arm')
      write(a.output/'HOST_CHILD_IDENTITY.json',dict(source=ar,cid=cid,host_pid=hp,guest=dv,host_stat=before,host_status=status,host_cgroup=(proc/'cgroup').read_text()))
      write(a.output/'MAIN_ARM.json',dict(source=ar,guest_pid=dv['pid'],start_ticks=start_ticks))
     time.sleep(.2)
    need(attach.returncode==0,'actual child exit0')
   x=inspect();need(x['State']['Running']is False and x['State']['Pid']==0 and x['State']['ExitCode']==0,'actual CPUchild terminal success');d=json.loads((a.output/'ATTRIBUTION.json').read_bytes())
   need(d['schema']=='deltalog.measurement-only-complete/v22'and d['source']==ar and d['primary']is None and d['Devices']==[]and d['NPU']is False and d['qualified']is False and d['old_R21_failure_unchanged']is True and d['measurement_contract_changed']is False,'complete exact measurement child, no numerical qualification')
  except BaseException as e:primary=repr(e)
  finally:
   cleanup_seconds=max(1,min(30,int(180-(time.monotonic()-whole_start)),int(CUT-time.time())))
   cleanup_deadline=time.monotonic()+cleanup_seconds
   signal.alarm(cleanup_seconds)
   if cid:
    try:
     z=run([DOCKER,'stop','--time','10',cid],timeout=30);write(a.output/'STOP.json',dict(exit=z.returncode,stdout=z.stdout,stderr=z.stderr));x=inspect();write(a.output/'FINAL_INSPECT.json',x);need(x['State']['Running']is False and x['State']['Pid']==0 and not x.get('ExecIDs'),'exact owned stop/release');released=True
    except BaseException as e:secondary.append(repr(e))
   if attach is not None:
    try:
     need(time.monotonic()<cleanup_deadline,'cleanup deadline before attach wait');attach.wait(timeout=min(10,cleanup_deadline-time.monotonic()))
    except BaseException as e:secondary.append(repr(e))
   try:
    need(time.monotonic()<cleanup_deadline,'cleanup deadline before final readonly verification');used=output_scan(OUTROOT);storage.check();source_verify([ar,*own['files'].values(),*refs])
   except BaseException as e:secondary.append(repr(e));used=None
   write(a.output/'RESULT.json',dict(schema='deltalog.measurement-owned/v22',source=ar,stage_result=ref(a.output/'ATTRIBUTION.json')if(a.output/'ATTRIBUTION.json').is_file()else None,stage_ref=json.loads(a.stage_ref)if a.stage_ref else None,numeric_owner=json.loads(a.numeric_owner_ref)if a.stage_ref else None,cid=cid,primary=primary,secondary=secondary,resource_release_verified=released,stopped_retained=released,Devices=[],NPU=False,qualified=False,used_bytes=used,elapsed=time.monotonic()-start,whole_elapsed=time.monotonic()-whole_start))
   signal.alarm(0)
  return 0 if primary is None and not secondary and released else 3
 finally:os.close(fd)
if __name__=='__main__':raise SystemExit(main())
