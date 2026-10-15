"""MAIN-only read-only admission and new immutable CPU cohort publication."""
import argparse,hashlib,importlib.util,json,os,re,selectors,shutil,subprocess,sys,time
from pathlib import Path
START,CUT=1791962297,1792135097
READ_RECEIPTS=[]
READ_RECEIPT_PATH=None
BIND_STARTED=time.monotonic()
def need(v,m):
 if not v:raise ValueError(m)
def ref(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not p.is_symlink(),'ordinary immutable source')
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def checked(r):need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact actual Ref3');return Path(r['path']).read_bytes()
def load(name,r):
 need(name not in sys.modules,'no partial source module');s=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(s);sys.modules[name]=m
 try:exec(compile(checked(r),r['path'],'exec'),m.__dict__)
 except BaseException:sys.modules.pop(name,None);raise
 return m
def cli_snapshot(pid):
 try:
  text=Path('/proc/'+str(pid)+'/stat').read_text();fields=text[text.rfind(')')+2:].split()
  status=Path('/proc/'+str(pid)+'/status').read_text()
  rss={line.split(':')[0]:int(line.split()[1])*1024 for line in status.splitlines()if line.startswith(('VmRSS:','VmHWM:'))}
  return {'status':'live','pid':pid,'start_ticks':int(fields[19]),'state':fields[0],**rss}
 except(FileNotFoundError,ProcessLookupError):return {'status':'departed','pid':pid}
def docker(args):
 import resource
 need(args==['ps','-q','--no-trunc']or len(args)==2 and args[0]=='inspect'and re.fullmatch('[0-9a-f]{64}',args[1]),'exact readonly Docker args')
 need(resource.getrlimit(resource.RLIMIT_AS)==(536870912,resource.RLIM_INFINITY),'parent soft512/hardunlimited remains, no global relaxation')
 need(time.monotonic()-BIND_STARTED<120,'whole binder clock before CLI launch')
 argv=['/usr/bin/prlimit','--as=unlimited','--','/usr/bin/docker',*args]
 try:p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 except BaseException as e:
  READ_RECEIPTS.append({'argv':argv,'requested_argv':['/usr/bin/docker',*args],'pid':None,'returncode':None,'stderr':repr(e),'primary':repr(e),'capture_complete':False,'child_terminal':None,'parent_AS_limit':[536870912,'unlimited'],'RSS_observation':'spawn failed before PID'})
  raise
 receipt={'argv':argv,'requested_argv':['/usr/bin/docker',*args],'pid':p.pid,'started_epoch':time.time(),'snapshots':[],'parent_AS_limit':[536870912,'unlimited'],'child_AS_only':'unlimited','RSS_budget_bytes':536870912}
 start=time.monotonic();buffers={'stdout':bytearray(),'stderr':bytearray()};sel=selectors.DefaultSelector();primary=None;child_peak=0
 try:
  for name,pipe in(('stdout',p.stdout),('stderr',p.stderr)):
   os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,name)
  while sel.get_map():
   need(time.monotonic()-start<20 and time.monotonic()-BIND_STARTED<120,'20s read/whole120 binder clock')
   snap=cli_snapshot(p.pid)
   if snap['status']=='live':
    child_peak=max(child_peak,snap.get('VmHWM',snap.get('VmRSS',0)))
    if len(receipt['snapshots'])<400:receipt['snapshots'].append(snap)
   parent_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
   need(parent_peak+max(child_peak,resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024)<=536870912,'actual parent plus owned CLI peak RSS512')
   for key,mask in sel.select(.05):
    data=os.read(key.fileobj.fileno(),65536)
    if not data:sel.unregister(key.fileobj);key.fileobj.close();continue
    need(sum(len(v)for v in buffers.values())+len(data)<=4*1024**2,'bounded stdout/stderr, no accepted truncation')
    buffers[key.data].extend(data)
  p.wait(timeout=max(.01,20-(time.monotonic()-start)))
 except BaseException as e:
  primary=repr(e)
  if p.poll()is None:p.kill()
  p.wait(timeout=3)
 finally:
  sel.close()
  for pipe in(p.stdout,p.stderr):
   if not pipe.closed:pipe.close()
  receipt.update(returncode=p.returncode,primary=primary,elapsed_seconds=time.monotonic()-start,stdout_bytes=len(buffers['stdout']),stdout_sha256=hashlib.sha256(buffers['stdout']).hexdigest(),stderr_bytes=len(buffers['stderr']),stderr=bytes(buffers['stderr']).decode(errors='replace'),child_peak_RSS_bytes=max(child_peak,resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024),parent_peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,capture_complete=primary is None,child_terminal=p.poll()is not None)
  READ_RECEIPTS.append(receipt)
 need(receipt['child_peak_RSS_bytes']+receipt['parent_peak_RSS_bytes']<=536870912,'actual terminal parent plus CLI RSS512')
 need(primary is None and p.returncode==0,'actual readonly Docker failure recorded; not RAM attribution')
 return bytes(buffers['stdout']).decode()
def publish_reads(primary=None):
 if READ_RECEIPT_PATH is None:return
 need(not READ_RECEIPT_PATH.exists(),'new readonly CLI receipt')
 with READ_RECEIPT_PATH.open('x',encoding='utf-8')as f:json.dump({'schema':'ascend.cpu-cohort-read-diagnostic/v1','source':ref(__file__),'primary':primary,'reads':READ_RECEIPTS,'NPU':False,'Docker_mutation':False},f,sort_keys=True,allow_nan=False);f.write('\n')
def running():
 cids=docker(['ps','-q','--no-trunc']).split();need(len(cids)<=128,'bounded actual running inventory')
 rows=[]
 for cid in cids:
  values=json.loads(docker(['inspect',cid]));need(len(values)==1 and values[0]['Id']==cid,'exact running inspect')
  x=values[0];labels=x['Config'].get('Labels')or{}
  owned=labels.get('model-tuning-lab.owner')or labels.get('qwen36.owner')
  rows.append({'cid':cid,'name':x['Name'],'running':x['State']['Running'],'pid':x['State']['Pid'],'memory_limit':x['HostConfig']['Memory'],'owned_label':owned,'devices':x['HostConfig'].get('Devices')or[]})
 need(docker(['ps','-q','--no-trunc']).split()==cids,'running inventory changed during admission')
 need(not any(r['owned_label']and r['running']for r in rows),'other running owned budgets are unbound: stop/release or use a separately audited multi-owner cohort')
 return rows
def main():
 global READ_RECEIPT_PATH
 import resource
 start=time.monotonic();ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true')
 for k in('self-sha256','owner-source-ref','run-id','output-root','cohort-output'):ap.add_argument('--'+k,required=True)
 a=ap.parse_args();need(resource.getrlimit(resource.RLIMIT_AS)==(536870912,resource.RLIM_INFINITY),'actual parent soft512 hardunlimited');need(ref(__file__)['sha256']==a.self_sha256,'binder own frozen bytes')
 if not a.execute:print(json.dumps({'enabled':False,'NPU':False}));return 0
 own=json.loads(a.owner_source_ref);m=json.loads(checked(own));need(m['schema']in('mst.dasc.owned-cpu-source/v1','good-enough.owned-cpu-attribution-source/v1','deltalog.owned-cpu-attribution-source/v1','deltalog.owned-kdma-build-source/v1')and m['default_enabled']is False,'known same owned CPU adapter')
 need(START<=time.time()and time.time()+900<CUT,'new48h full inherited lease fits')
 W=load('_bind_actual_window',m['window']);W.validate(checked(m['authority']))
 bm=json.loads(checked(m['base_source']));pins=[r for r in bm['safety_pins']if r['path'].endswith('short_horizon_h8_gate_v4/host_run.py')];need(len(pins)==1,'one original CPU helper')
 H=load('_bind_actual_h8',pins[0]);H.frozen();host=H.cpu_view(os.getpid());daemon=H.daemon_view()
 need(host['effective_cpus']and len(daemon['effective_cpus'])>=3,'actual host/guest/reserve CPU inventory')
 host_cpu=sorted(host['effective_cpus'])[-1];pool=sorted(set(daemon['effective_cpus'])-{host_cpu})
 need(len(pool)>=3,'three disjoint actual guest/reserve CPUs')
 admission={'host_cpu':host_cpu,'guest_cpu':pool[0],'reserve_cpus':pool[1:3]}
 need('torch'not in sys.modules and'torch_npu'not in sys.modules,'binder never imports framework')
 out=Path(a.output_root);target=Path(a.cohort_output)
 need(out.parent==Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit')and out.name.startswith('run-')and not out.exists(),'actual new owned output root')
 need(target.parent==out.parent and target.name.startswith('COHORT-')and target.parent.is_dir()and not target.exists()and not target.is_symlink(),'fresh bounded cohort publication')
 READ_RECEIPT_PATH=target.with_name(target.name+'.READ_DIAGNOSTIC.json');need(not READ_RECEIPT_PATH.exists(),'new immutable read diagnostic')
 pm=json.loads(checked(m['cohort_policy']));P=load('_bind_actual_policy',pm['files']['cohort_policy.py'])
 for r in pm['files'].values():checked(r)
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();owners=running()
 row={'source':own,'run_id':a.run_id,'cards':[4],'host_cpu':admission['host_cpu'],'guest_cpus':[admission['guest_cpu']],'guest_bytes':8589934592,'host_bytes':536870912,'output_bytes':268435456,'cache_bytes':536870912,'budget_held':True,'compatibility':'main-fixed-disjoint-diagnostic-v1','output_root':str(out)}
 cohort={'schema':'ascend.main-fixed-diagnostic-cohort/v1','allocator':'MAIN','policy_ref':m['cohort_policy'],'compatibility':'main-fixed-disjoint-diagnostic-v1','start_epoch':START,'cutoff_epoch':CUT,'mode':'diagnostic-disjoint','boot_id':boot,'members':[row],'reserve_bytes':8589934592,'reserve_cpus':admission['reserve_cpus']}
 P.cohort(cohort,m['cohort_policy'],boot=boot,now=time.time());P.qualified_sources(cohort,checked);P.cpu_plan(cohort,a.run_id,host,daemon)
 memory={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()if line.startswith(('MemAvailable:','SwapTotal:','SwapFree:'))}
 plan=P.resources(cohort,mem_available=memory['MemAvailable'],swap_total=memory['SwapTotal'],swap_free=memory['SwapFree'],disk_free=shutil.disk_usage(out.parent).free,used_by_run={a.run_id:{'output_bytes':0,'cache_bytes':0}})
 need(time.monotonic()-start<120 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=512*1024,'actual bounded host prelude')
 need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot,'same actual boot before publish')
 owners_after=running()  # External0-3 departure is not task interference.
 host_after=H.cpu_view(os.getpid());daemon_after=H.daemon_view();P.cpu_plan(cohort,a.run_id,host_after,daemon_after)
 memory_after={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()if line.startswith(('MemAvailable:','SwapTotal:','SwapFree:'))}
 P.resources(cohort,mem_available=memory_after['MemAvailable'],swap_total=memory_after['SwapTotal'],swap_free=memory_after['SwapFree'],disk_free=shutil.disk_usage(out.parent).free,used_by_run={a.run_id:{'output_bytes':0,'cache_bytes':0}})
 checked(own);need(time.monotonic()-start<120 and time.time()+900<CUT,'whole binding prelude and unchanged source')
 cohort['binding_observation']={'owner_source':own,'binder_source':ref(__file__),'observed_epoch':time.time(),'host_cpu':host_after,'daemon_cpu':daemon_after,'memory':memory_after,'resources':plan,'running_containers_before':owners,'running_containers_after':owners_after,'external_churn_not_interference':True,'devices':[],'NPU':False,'external_future_resources_guaranteed':False,'read_receipts':READ_RECEIPTS}
 with target.open('x',encoding='utf-8')as f:json.dump(cohort,f,sort_keys=True,allow_nan=False);f.write('\n')
 publish_reads()
 print(json.dumps({'cohort_ref':ref(target),'exact_run_id':a.run_id,'output_root':str(out),'host_cpu':row['host_cpu'],'guest_cpu':row['guest_cpus'][0],'NPU':False}))
 return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as error:
  publish_reads(repr(error));raise
