"""Fixed R6 FIA replay, derived from exact executed paged owner116.

The run/cleanup/CPU observer and complete scoped NPU ownership controller are
preserved. New-source CPU/ABI/guest/result interfaces are explicit below; the
whole-model PHASE3600 contract is never used or modified.
"""
import argparse,ast,hashlib,importlib.util,inspect,json,os,shutil,stat,sys,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));import common as C
ROOT=C.ROOT
OUTROOT=Path(C.OUTROOT)
OWNER='bole-fia-fixed-frame-MAIN-CONTINUE-20261018T192427Z-v1'
GIB=2**30
def storage_check():
 p=OUTROOT;need(p.is_dir()and all(not x.is_symlink()for x in(p,*p.parents)),'exact ordinary MXR authorized parent')
 v=os.statvfs(p);free=v.f_bavail*v.f_frsize;need(free>=8.5*GIB,'live8.5GiB MXR disk reserve, no DL ledger')
 return dict(schema='mxr.explicit-untracked-output-budget/v086',parent=str(p),filesystem_free_bytes=free,live_reserve_bytes=int(8.5*GIB),new_leaf_cap_bytes=GIB,shared_DL_ledger_used=False,ledger_advanced=False)
class Storage086:
 def check(self):return storage_check()
def source_verify(refs):
 for r in refs:checked(r)

def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3');p=Path(r['path']);s=p.stat()
 need(p.is_absolute()and p.is_file()and all(not x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'ordinary stable exact input')
 t=p.stat();need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns),'stable read');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def scan(root):
 total=0;dev=root.stat().st_dev
 for directory,dirs,files in os.walk(root,followlinks=False):
  for name in dirs+files:
   s=(Path(directory)/name).lstat();need(s.st_dev==dev and not stat.S_ISLNK(s.st_mode),'owned output no link/FS escape')
   if stat.S_ISREG(s.st_mode):total+=s.st_size
   else:need(stat.S_ISDIR(s.st_mode),'ordinary diagnostic files only')
 need(total<=GIB,'whole1GiB hard output bound');return total
def exact_methods(donor):
 """Only these three unchanged donor methods, not its numerical main/gates."""
 tree=ast.parse(checked(donor).read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
 ge=next(n for n in main.body if isinstance(n,ast.ClassDef)and n.name=='GE')
 selected=[n for n in ge.body if isinstance(n,ast.FunctionDef)and n.name in('run','cleanup','cpu_observe')]
 need({n.name for n in selected}=={'run','cleanup','cpu_observe'},'exact donor method set')
 return selected
def device_proof(dv,record,plan,cid,argv):
 need(dv['logical']==0 and dv['physical_declared_by_plan']==4 and dv['plan']==plan and dv['canary']==[4.,5.]and dv['physical_proof_must_be_host_owned']is True and cid in dv['cgroup'],'079 device/plan/self report, not physical proof')
 ticks=int(dv['stat'][dv['stat'].rfind(')')+2:].split()[19])
 proofs=[p for p in record['owned_process_proofs']if p['physical']==4 and p['namespace_pids'][-1]==dv['pid']and p['start_ticks']==ticks and cid in p['cgroup']]
 if not proofs:need(not record['owned_process_proofs'],'actual nonempty ownership mismatch');return None
 need(len(proofs)==1 and proofs[0]['argv']==argv,'unique host SMI/PID/start/ns/cgroup/fullargv proof');return proofs[0]
def own_abi_module_ref(sr):return obj(sr)['files']['abi_device118.py']

def receive(v,sr,ar,pr):
 need(v['schema']=='bole.fia-replay-stage/v1'and v['source']==sr and v['authority']==ar and v['plan']==pr and v['primary']is None and v['NPU']is True and v['qualified']is False,'complete source-bound actual replay outer stage')
 inner=obj(v['result'])
 need(inner['schema']=='bole.fia-original-replay-and-parameter-probe/v1'and inner['source']==sr and inner['qualified']is False and inner['diagnostic_complete']is True,'complete original FIA replay diagnostic, never qualification')
 need(type(inner['baseline_gate_pass'])is bool and type(inner['intervention_executed'])is bool,'explicit baseline/intervention outcomes')
 if inner['baseline_gate_pass']is False:
  need(inner['intervention_executed']is False and inner['replay_qualified']is False,'original-call mismatch must stop all intervention attribution')
 need(inner['runtime_plan']==pr and inner['actual_abi_ref']==v['actual_abi_ref']and
      inner['NPU']is True and inner['whole_model_qualified']is False and inner['primary']is None
      and inner['original_numeric_failures_unchanged']is True,'actual ABI/runtime plan and original failure provenance')
 baselines=inner['baselines'];variants=inner['interventions']
 need([row['branch']for row in baselines]==['tree','native']and
      [row['role']for row in baselines]==['baseline','baseline'], 'both original branch measurements')
 need([row['whole_output']['elements']for row in baselines]==[4608,1536], 'full original tree and native outputs')
 if inner['baseline_gate_pass']:
  need([row['branch']for row in variants]==['tree','native']and
       all(row['role']=='intervention'for row in variants),'both sole-parameter variants')
 else:need(variants==[],'no variant after failed baseline')
 for row in baselines+variants:
  need(row['primary']is None and row['operator_completed']is True,'complete actual FIA calls')
  checked(row['raw']);need(obj(row['receipt'])=={k:value for k,value in row.items()if k!='receipt'},'quiescent exact call receipt')
 br=obj(inner['baselines_ref'])
 need(br['source']==sr and br['rows']==baselines and br['baseline_gate_pass']==inner['baseline_gate_pass']
      and br['intervention_executed']is False and br['qualified']is False,'frozen baseline evidence precedes variants')
 return v

def closure(own):
 m=obj(own['donor_source']);need(own['donor_host']==m['files']['host.py'],'exact actual069 donor')
 return own,m,C.readset(own)


def controller(own,a,gm,m,refs):
 d=load(own['donor_host'],'_081_exact069_host');d.OWNER=OWNER;d.START=C.START;d.CUT=C.CUT
 Base,cpu=d.base_lane();terminal=load(m['files']['terminal_fence.py'],'_081_same_terminal')
 adapter=load(own['controller_files']['scope_adapter112.py'],'_081_same_scope');patch=load(m['files']['patch_scope.py'],'_081_same_patch');guard=load(own['controller_files']['top_guard116.py'],'_092_bounded_same_top_tree');composition=load(own['controller_files']['patch_scope112.py'],'_116R1_exact_composition');composition.install(adapter,guard,patch)
 ns=Base.observe.__globals__;module=types.SimpleNamespace(**dict(ns,c=types.SimpleNamespace(sha=d.sha),_adapter_ref=a.owner_ref));adapter._MODULE=module
 ns.update(_adapter_scope=adapter.scoped_cards,_adapter_ref=a.owner_ref,_adapter_checked=d.checked,_adapter_protected=adapter.protected_observation,_adapter_nonselected=adapter.nonselected_identity)
 transformed=adapter.transform_observe(inspect.getsource(Base.observe));new={};exec(compile(transformed,str(HERE/'owner.py')+':unchanged069scope','exec'),ns,new);Base.observe=new['observe']
 oldinit=Base.__init__
 def init(self,*args):
  oldinit(self,*args);self._adapter_module=module
  obs=load(m['observer_ref'],'_081_actual_protected_observer');obs.install(types.SimpleNamespace(frozen=lambda:self.h),d.ref(d.HOST),a.output,write,lambda:([os.getpid()]+[p['pid']for p in self.pid_proofs.values()],[self.active]if self.active else[]))
 Base.__init__=init
 scope=dict(d.__dict__,Base=Base,a=a,cpu=cpu)
 cls=ast.ClassDef(name='GE',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=exact_methods(own['donor_host']),decorator_list=[])
 code=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]));exec(compile(code,str(HERE/'owner.py')+':unchanged069methods','exec'),scope);GE=scope['GE']
 def create(self,stage):
  self.stage=stage;self.secondary=[];self.output=a.output/stage;self.output.mkdir();self.cards=[4]
  self.observe('numeric',require_idle=True)
  roots={gm['root'],str(HERE)}
  # Exact source roots and the one historical blob tree only. config.json is
  # mounted as a FILE, never its weight-bearing model directory.
  paths={r['path']for r in refs}|roots;paths={q for q in paths if not any(v!=q and Path(v)in Path(q).parents for v in roots)}
  mounts={q:(q,False)for q in paths};mounts['/usr/local/Ascend/driver']=('/usr/local/Ascend/driver',False);mounts[str(self.output)]=(str(self.output),True);a.current_mounts=mounts
  need(sum(rw for _,rw in mounts.values())==1,'sole fresh stage RW')
  env=dict(BOLE_FIA_FIXED_FRAME_ENABLE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',TORCH_DEVICE_BACKEND_AUTOLOAD='0',ASCEND_RT_VISIBLE_DEVICES='0',VLLM_PLUGINS='ascend',ASCEND_CUSTOM_OPP_PATH='/vllm-workspace/vllm-ascend/vllm_ascend/_cann_ops_custom/vendors/custom_transformer')
  childout=self.output/'result';plan=self.output/'PLAN.json';write(plan,dict(schema='bole.fia-replay-plan/v1',source=a.owner_ref,cpu_stage=a.cpu_stage_ref,physical=4,logical=0,profile=own['profile'],abi_ticket_ref=a.abi_ticket_ref,qualification=False,work_deadline=min(C.CUT-180,time.time()+560,a.whole_epoch_deadline-180)));self.plan_ref=ref(plan)
  args=[d.PY,'-I','-B',own['files']['guest.py']['path'],'--execute','--source-ref',json.dumps(own['guest_source'],separators=(',',':')),'--plan-ref',json.dumps(self.plan_ref,separators=(',',':')),'--output',str(childout)]
  cmd=[d.DOCKER,'create','--name','bole-fia-fixed-'+str(time.time_ns()),'--label','qwen36.owner='+OWNER,'--label','qwen36.stage='+stage,'--label','deltalog-fresh-bridge.owner-source-sha256='+a.owner_ref['sha256'],'--cpus=1','--cpuset-cpus='+str(a.guest_cpu),'--memory=8g','--memory-swap=8g','--ipc=private','--shm-size=2g','--pids-limit=512','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none']
  for dst,(src,rw)in mounts.items():cmd+=['--mount','type=bind,src='+src+',dst='+dst+(''if rw else',readonly')]
  # Same proven069 host5 -> guest0 contract; actual physical identity still
  # must be independently seen by SMI/proc before ARM. No guessed alias.
  cmd+=['--device=/dev/davinci4:/dev/davinci0']
  for dev in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc'):need(Path(dev).exists(),'actual control node');cmd+=['--device='+dev]
  for k,v in env.items():cmd+=['-e',k+'='+v]
  a.current_env=env;self.expected_child_argv=args;a.current_cmd=['/bin/bash','-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"','dldeadbridge024']+args;cmd+=[d.IMAGE]+a.current_cmd
  write(self.output/'create-argv.json',dict(argv=cmd,owner=a.owner_ref,guest=own['guest_source']));r=self.call(cmd,60);write(self.output/'create-receipt.json',r);cid=r['stdout'].strip();need(len(cid)==64 and all(c in'0123456789abcdef'for c in cid),'created exact CID');self.active=cid
  r,x=self.inspect(cid);write(self.output/'inspect-created.json',r);need(not x['State']['Running']and x['State']['Pid']==0,'cold inspected created state');write(self.output/'start-receipt.json',self.call([d.DOCKER,'start',cid],60));return childout
 def wait(self):
  childout=self.create('numeric');end=min(time.monotonic()+600,a.whole_deadline-180);bound=None
  while True:
   r,x=self.inspect(self.active)
   if not x['State']['Running']:r,x=terminal.postexit(self,r,x,bound,lambda v:write(self.output/('terminal-'+str(time.time_ns())+'.json'),v),end)
   else:
    before=terminal.files(a.run_root)
    try:record=self.observe('numeric')
    except BaseException as original:
     try:r,x=terminal.recover(self,original,bound,x,before,lambda v:write(self.output/('terminal-'+str(time.time_ns())+'.json'),v),end)
     except BaseException as failure:
      write(self.output/('terminal-refused-'+str(time.time_ns())+'.json'),dict(original=repr(original),fence=repr(failure)));raise original
     record=None
    device=childout/'DEVICE.json'
    if record is not None and device.is_file()and bound is None:
     dv=obj(ref(device));proof=device_proof(dv,record,self.plan_ref,self.active,self.expected_child_argv)
     if proof is not None:
      bound=proof;write(self.output/'ACTUAL_OWNER.json',proof);write(childout/'MAIN_ARM.json',dict(schema='bole.fia-replay-arm/v1',pid=dv['pid'],plan_sha256=self.plan_ref['sha256'],physical=4))
   if not x['State']['Running']:
    write(self.output/'inspect-exited.json',r);need(x['State']['ExitCode']==0,'actual079 child exit; failure retained');need(bound is not None,'real host proof/ARM required')
    write(self.output/'QUIESCENT_REFS.json',terminal.quiescent(childout,False,ref,obj));rr=ref(childout/'STAGE_RESULT.json');receive(obj(rr),own['guest_source'],own['authority_ref'],self.plan_ref);return rr
   need(time.monotonic()<end,'guest600/whole900 charged startup deadline');time.sleep(.2 if bound is None else 1)
 GE.create=create;GE.wait079=wait
 observe=GE.observe
 def observed(self,*args,**kw):
  used=scan(OUTROOT);proof=storage.check()
  live=self.call([d.DOCKER,'ps','--no-trunc','--filter','label=qwen36.owner','--format','{{.ID}}']);need(set(live['stdout'].split())<=({self.active}if self.active else set()),'no unaccounted owned CPU/RAM overlap')
  return observe(self,*args,**kw)
 GE.observe=observed
 storage=Storage086();seal=None
 return GE,d,storage,seal


def main():
 global OUTROOT
 begun=time.monotonic();begun_epoch=time.time()
 p=argparse.ArgumentParser(allow_abbrev=False)
 p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true')
 p.add_argument('--source-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int)
 p.add_argument('--output',type=Path);p.add_argument('--cpu-owner-ref');p.add_argument('--abi-ticket-ref')
 a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);own=C.source(sr);OUTROOT=Path(own['output_root'])
 need(own['files']['owner.py']==ref(__file__),'actual new owner identity, never oldowner filename')
 gm,m,refs=closure(own);refs=C.dedup([sr,*refs]);ar=own['authority_ref'];own=dict(own,guest_source=sr)
 if a.source_audit:
  print(json.dumps(dict(source=sr,readset=refs,NPU=False,resource_admitted=False,component_source=own['component_source_ref'])));return 0
 need(a.execute and sys.platform=='linux','explicit MAIN Linux owner')
 C.window(own,whole=900)
 cpu_ref=json.loads(a.cpu_owner_ref);ticket_ref=json.loads(a.abi_ticket_ref)
 ticket_api=load(own['files']['ticket.py'],'_actual_fixed_frame_ticket')
 tv=ticket_api.consume(ticket_ref,sr,cpu_ref)
 cv=obj(cpu_ref);a.cpu_stage_ref=cv['stage_result'];a.abi_ticket_ref=ticket_ref
 need(cv['schema']=='bole.fia-replay-owned-CPU/v1'and cv['source']==sr and cv['primary']is None
      and cv['secondary']==[]and cv['resource_release_verified']is True and cv['stopped_retained']is True
      and cv['Devices']==[]and cv['NPU']is False and cv['stage_ref']is None,'released same-source actual CPU prerequisite')
 need(tv['source']==sr and tv['cpu_owner']==cpu_ref and tv['cpu_stage']==a.cpu_stage_ref
      and tv['image']==C.IMAGE and tv['admitted_for_microprobe_only']is True,'actual sameimage ABI ticket')
 refs=C.dedup([*refs,cpu_ref,a.cpu_stage_ref,ticket_ref,*tv['runtime_readset']])
 source_verify(refs)
 need(a.output is not None and a.output.parent==OUTROOT and a.output.name=='numeric'
      and not a.output.exists()and OUTROOT.is_dir()and all(not q.is_symlink()for q in(OUTROOT,*OUTROOT.parents)),
      'one fresh exact new output; source binder does not allocate experiment outputs')
 import resource,fcntl,signal
 affinity=os.sched_getaffinity(0)
 need(a.host_cpu in affinity and a.guest_cpu in affinity and a.host_cpu!=a.guest_cpu,'disjoint actual inherited CPU assignments')
 a.owner_ref=sr;a.lease_seconds=900;a.whole_deadline=begun+900;a.whole_epoch_deadline=begun_epoch+900
 a.run_root=a.output;a.stop_after_numerics=True;a.physical_device=4;a.host_original_affinity=sorted(affinity)
 need(time.monotonic()<a.whole_deadline-180 and a.whole_epoch_deadline<C.CUT,'all source/CPU ticket preparation charged to whole900')
 os.sched_setaffinity(0,{a.host_cpu});soft,hard=resource.getrlimit(resource.RLIMIT_AS)
 need(hard==resource.RLIM_INFINITY,'host hardAS unchanged');resource.setrlimit(resource.RLIMIT_AS,(GIB//2,hard))
 def deadline(signum,frame):raise RuntimeError('independent component whole900 or fixed renewed cutoff')
 signal.signal(signal.SIGALRM,deadline);signal.signal(signal.SIGTERM,deadline)
 signal.setitimer(signal.ITIMER_REAL,max(.001,a.whole_deadline-time.monotonic()))
 GE,d,storage,seal=controller(own,a,gm,m,refs)
 fd=os.open(OUTROOT/'.fia-fixed-frame.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
 fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  lane=GE(a,Path(gm['root']));lane.lease_deadline=a.whole_deadline
  r=lane.call([d.DOCKER,'ps','--no-trunc','--filter','label=qwen36.owner','--format','{{.ID}}'])
  need(not r['stdout'].strip(),'serialize with every existing owned load')
  proof=storage.check();need(proof['filesystem_free_bytes']>=9.5*GIB,'original component initial9.5GiB actual filesystem reserve')
  a.output.mkdir();write(a.output/'UNTRACKED_ALLOCATION.json',dict(source=sr,component_source=own['component_source_ref'],bytes=GIB,proof=proof,ledger_advanced=False,qualified=False))
  primary=None;secondary=[];result=None;release=False;inner=None
  try:
   result=lane.wait079();outer=obj(result);inner=obj(outer['result'])
   if inner['baseline_gate_pass']is False:primary='original FIA boundary replay mismatch; all interventions suppressed'
  except BaseException as error:primary=repr(error)
  finally:
   try:
    lane.cleanup()
    cleanup=obj(ref(lane.output/'cleanup-verdict.json'))
    release=cleanup['resource_release_verified']is True and cleanup['retained']is True and cleanup['stopped']is True and lane.active is None
    need(release,'exact retained CID and resource-release verification')
   except BaseException as error:secondary.append('cleanup '+repr(error))
  try:
   source_verify(refs);used=scan(OUTROOT);storage.check()
   need(used<=GIB-65536,'all CPU plus numeric outputs leave terminal receipt reserve')
  except BaseException as error:secondary.append('postverify '+repr(error));used=None
  value=dict(schema='bole.fia-replay-owned/v1',source=sr,abi_ticket_ref=ticket_ref,cpu_owner_ref=cpu_ref,
             component_source=own['component_source_ref'],component_owner=own['component_owner_ref'],
             donor_source=own['donor_source'],authority=ar,result=result,primary=primary,secondary=secondary,
             stopped_retained=lane.active is None,resource_release_verified=release and not secondary,
             physical=[4],logical=0,NPU=(a.output/'numeric/result/DEVICE.json').is_file(),NPU_requested=True,
             qualified=False,whole_model_qualified=False,old_failures_unchanged=True,
             baseline_gate_pass=None if inner is None else inner['baseline_gate_pass'],
             intervention_executed=False if inner is None else inner['intervention_executed'],
             diagnostic_complete=False if inner is None else inner['diagnostic_complete'],
             elapsed=time.monotonic()-begun,whole_seconds=900,cutoff=C.CUT,used_bytes=used)
  write(a.output/'RESULT.json',value);print(json.dumps(ref(a.output/'RESULT.json')))
  return 0 if primary is None and not secondary and release else 3
 finally:
  os.close(fd);signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':raise SystemExit(main())
