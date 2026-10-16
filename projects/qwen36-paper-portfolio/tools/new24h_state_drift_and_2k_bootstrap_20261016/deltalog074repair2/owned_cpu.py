"""MAIN-only one retained-raw CPU child; existing069 ledger is never advanced."""
import argparse,hashlib,importlib.util,json,os,shutil,stat,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-state-drift-cpu-new24h-v1-074-repair2')
OUTROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
PY='/usr/local/python3.12.13/bin/python3';DOCKER='/usr/bin/docker';GIB=2**30;START=1792134133;CUT=1792220533
SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-069-repair1/SOURCE_MANIFEST.json',bytes=52969,sha256='b9cb456d960072d8e6730bb5307dcabfc83b3ad7bffd9d3476d9b92220048f21')
PRODUCER=dict(path='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-numeric160-MAIN-20261016-NEW24H-069-repair1-001/numeric/result/RESULT.json',bytes=100542,sha256='4a5b125780618a6020e2d2bf619be1e4258dbafd9b7699bfe52aabc16fa12caa')
OWNER='deltalog-retained-drift-CPU074R2';CAP=GIB
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
 args=[DOCKER,'create','--name',name,'--label','qwen36.owner='+OWNER,'--label','qwen36.stage=cpu074','--network','none','--ipc','private','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory',str(8*GIB),'--memory-swap',str(8*GIB),'--cpus','1','--cpuset-cpus',str(cpu),'--pids-limit','256','--shm-size',str(256*2**20),'--log-driver','none','--entrypoint',PY]
 for src,(dst,rw)in sorted(mounts.items()):args+=['--mount','type=bind,src='+src+',dst='+dst+(',readonly'if not rw else'')]
 for k,v in sorted(env.items()):args+=['-e',k+'='+v]
 return args+[IMAGE,*child]
def inspect_owned(x,cid,mounts,env,guest,name,child):
 h=x['HostConfig'];cfg=x['Config'];need(x['Id']==cid and x['Image']==IMAGE and x['Name']=='/'+name and cfg['Labels'].get('qwen36.owner')==OWNER,'exact created CID/name/image/owner')
 need(not x.get('ExecIDs')and h['Privileged']is False and h['ReadonlyRootfs']is True and 'ALL'in h['CapDrop']and any('no-new-privileges'in s for s in h['SecurityOpt']),'owned private restricted container')
 need(h['Memory']==h['MemorySwap']==8*GIB and h['NanoCpus']==10**9 and h['CpusetCpus']==str(guest)and h['PidsLimit']==256 and h['IpcMode']=='private'and h['NetworkMode']=='none'and h['LogConfig']['Type']=='none','exact CPU/RAM/network/log budgets')
 need(not h.get('Devices')and not h.get('DeviceRequests')and not h.get('DeviceCgroupRules')and not h.get('PortBindings'),'actual Devices[] no exposed NPU/network')
 actual={v['Source']:(v['Destination'],v['RW'])for v in x['Mounts']};need(actual==mounts,'exact RO closure and sole RWout')
 actualenv=dict(v.split('=',1)for v in cfg['Env']);need(all(actualenv.get(k)==v for k,v in env.items())and cfg['Entrypoint']==[PY]and cfg['Cmd']==child,'actual guest Python3.12 command/env')
 need(not x['State'].get('OOMKilled'),'OOM hard failure');return x
def closure(sr):
 m=obj(sr);need(sr==SOURCE and m['prepared_only']is False,'exact actual069R1 bound source')
 refs=[sr,PRODUCER,*[m['files'][n]for n in('oracle.py','raw_codec.py','consume.py','bridge_io.py','storage061.py','sealed_storage069.py','window056.py')]]
 for r in refs:checked(r)
 need(obj(PRODUCER)['source']==sr,'failed producer source exact join')
 return m,refs
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 ar=json.loads(a.source_ref);own=obj(ar);need(own['schema']=='deltalog.retained-state-drift-owned-source/v074'and own['root']==str(HERE)and own['default_enabled']is False,'own source root/defaultOFF')
 for r in own['files'].values():checked(r)
 need(own['files']['owned_cpu.py']==ref(__file__),'actual own launcher source');m,refs=closure(SOURCE)
 authority=obj(own['authority_ref']);need(authority['schema']=='ascend.paper-portfolio.new24h-authority/v1'and authority['start_epoch']==START and authority['cutoff_epoch']==CUT,'exact actual24h authority unchanged')
 if a.source_audit:print(json.dumps(dict(source=ar,readset=refs,resources_admitted=False,NPU=False)));return 0
 need(sys.platform=='linux'and a.execute and START<=time.time()<CUT-1000,'fixed24h/whole1000s fit');need(a.output.parent==OUTROOT and a.output.name.startswith('run-drift074repair2-')and not a.output.exists()and all(not q.is_symlink()for q in(OUTROOT,*OUTROOT.parents)),'one new authorized leaf')
 affinity=os.sched_getaffinity(0);need(a.host_cpu in affinity and a.guest_cpu in affinity and a.host_cpu!=a.guest_cpu,'real disjoint inherited CPU assignments')
 import fcntl,resource,signal
 whole_start=time.monotonic()
 def interrupted(signum,frame):raise RuntimeError('MAIN-owned CPU074 signal/whole deadline '+str(signum))
 signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGALRM,interrupted);signal.alarm(1000)
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
  x=run([DOCKER,'ps','--no-trunc','--filter','label=qwen36.owner','--format','{{.ID}}']);need(x.returncode==0,'complete live owned list');ids=set(x.stdout.split());need(not(ids-({exclude}if exclude else set())),'no blind shared RAM/CPU overlap with any existing owned task')
 no_overlap();mem=dict(v.split(':',1)for v in Path('/proc/meminfo').read_text().splitlines());need(int(mem['MemAvailable'].split()[0])*1024>=16.5*GIB,'8guest+.5host+8reserve ordinary RAM')
 sys.path.insert(0,str(Path(SOURCE['path']).parent));storage=load(m['files']['storage061.py'],'_074_actual_storage');seal=load(m['files']['sealed_storage069.py'],'_074_actual_seal');storage.authority(m['storage_authority_ref'],obj)
 seal.install(storage,m['storage_seal_evidence_ref'],m['storage_authority_ref'],m['prepared_template'])
 fd=os.open(OUTROOT/'.storage061.lock',os.O_RDWR|os.O_NOFOLLOW);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  no_overlap();proof=storage.check();need(proof['committed_bytes']+CAP<=80*GIB and proof['filesystem_free_bytes']>=101*GIB,'sealed effective commitment plus untracked1GiB preserves80/100')
  a.output.mkdir();write(a.output/'UNTRACKED_ALLOCATION.json',dict(schema='deltalog.untracked-CPU-output/v074',source=ar,bytes=CAP,proof=proof,ledger_advanced=False,exclusive_existing_storage_lock=True,qualified=False))
  env=dict(ASCEND_RT_VISIBLE_DEVICES='',ASCEND_VISIBLE_DEVICES='',TORCH_DEVICE_BACKEND_AUTOLOAD='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR='/adakv-results',HOME='/adakv-results')
  mounts={str(checked(own['files'][n])):(str(checked(own['files'][n])),False)for n in('diagnose.py','cpu_entry.py')};mounts[str(checked(SOURCE))]=(SOURCE['path'],False)
  for n in('oracle.py','raw_codec.py','consume.py','bridge_io.py'):r=m['files'][n];mounts[str(checked(r))]=(r['path'],False)
  rawroot=str(Path(PRODUCER['path']).parent);mounts[rawroot]=(rawroot,False);mounts[str(a.output)]=('/adakv-results',True)
  child=['-I','-B',own['files']['cpu_entry.py']['path'],'--execute','--source-ref',json.dumps(SOURCE,separators=(',',':')),'--producer-ref',json.dumps(PRODUCER,separators=(',',':')),'--output','/adakv-results/DIAGNOSIS074.json'];name='dl-drift074-'+str(time.time_ns());cid=None;attach=None;primary=None;secondary=[];start=time.monotonic();released=False
  def inspect():
   z=run([DOCKER,'inspect',cid]);need(z.returncode==0,'own exact inspect readable');x=json.loads(z.stdout);need(len(x)==1,'one own inspect');inspect_owned(x[0],cid,mounts,env,a.guest_cpu,name,child);return x[0]
  try:
   need(time.monotonic()-whole_start<900,'whole preparation leaves cleanup reserve before create')
   argv=create_argv(a.guest_cpu,mounts,env,name,child);write(a.output/'CREATE_ARGV.json',argv);z=run(argv);write(a.output/'CREATE.json',dict(exit=z.returncode,stdout=z.stdout,stderr=z.stderr));need(z.returncode==0,'create success');cid=z.stdout.strip();need(len(cid)==64 and all(v in'0123456789abcdef'for v in cid),'created exact CID');write(a.output/'CID.json',dict(cid=cid,name=name));inspect()
   with(a.output/'child.stdout').open('xb')as out,(a.output/'child.stderr').open('xb')as err:
    attach_argv=docker_argv([DOCKER,'start','--attach',cid]);write(a.output/'ATTACH_ARGV.json',dict(requested_argv=[DOCKER,'start','--attach',cid],actual_argv=attach_argv))
    attach=subprocess.Popen(attach_argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
    while attach.poll()is None:
     need(time.monotonic()-start<600 and time.monotonic()-whole_start<900 and time.time()<CUT-100,'child600s/whole1000s incl cleanup90/fixed cutoff');no_overlap(cid);output_scan(a.output);storage.check();x=inspect();write(a.output/('inspect-%d.json'%time.time_ns()),x);time.sleep(1)
    need(attach.returncode==0,'actual child exit0')
   x=inspect();need(x['State']['Running']is False and x['State']['Pid']==0 and x['State']['ExitCode']==0,'actual CPUchild terminal success');d=json.loads((a.output/'DIAGNOSIS074.json').read_bytes());need(d['source']==SOURCE and d['producer']==PRODUCER and d['primary']is None and len(d['rows'])==91 and d['qualification']is False and d['NPU_reexecuted']is False,'complete diagnostic91 only, not qualification')
  except BaseException as e:primary=repr(e)
  finally:
   cleanup_seconds=max(1,min(90,int(1000-(time.monotonic()-whole_start)),int(CUT-time.time())))
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
    need(time.monotonic()<cleanup_deadline,'cleanup deadline before final readonly verification');used=output_scan(a.output);storage.check();seal.final_verify(m['storage_seal_evidence_ref'])
   except BaseException as e:secondary.append(repr(e));used=None
   write(a.output/'RESULT.json',dict(schema='deltalog.state-drift-owned-CPU/v074',source=ar,original_source=SOURCE,producer=PRODUCER,cid=cid,primary=primary,secondary=secondary,resource_release_verified=released,stopped_retained=released,Devices=[],NPU=False,qualified=False,used_bytes=used,elapsed=time.monotonic()-start))
   signal.alarm(0)
  return 0 if primary is None and not secondary and released else 3
 finally:os.close(fd)
if __name__=='__main__':raise SystemExit(main())
