"""079 diagnostic on the exact069 Lane/scope/cleanup; no model qualification."""
import argparse,ast,hashlib,importlib.util,inspect,json,os,shutil,stat,sys,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-tree-fa-owned-new24h-v1-116-repair5'
OUTROOT=Path('/opt/host/vnf/austinov/run-bole-tree-fa116repair5-MAIN-20261016-001')
OWNER='bole-tree-MAIN-116R5'
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
def receive(v,sr,ar,pr):
 need(v['schema']=='bole.tree-stage/v116'and v['source']==sr and v['authority']==ar and v['plan']==pr and v['primary']is None and v['NPU']is True and v['qualified']is False,'actual116 complete outer stage')
 inner=obj(v['result']);need(inner['schema']=='bole.FIA-stage/v115'and inner['source']==sr and len(inner['rows'])==6,'actual six FIA matrix calls')
 for row in inner['rows']:checked(row['raw'])
 return v


def closure(own):
 m=obj(own['donor_source']);need(own['donor_host']==m['files']['host.py'],'exact actual069 donor')
 refs=[own['donor_source'],own['authority_ref'],own['cann_helper_ref'],own['prepared_template'],m['observer_ref'],*[m['files'][n]for n in('scope_adapter.py','patch_scope.py','top_guard.py','terminal_fence.py')],*own['dependencies'].values(),*own.get('smoke_prerequisite_refs',[])]
 for r in refs:checked(r)
 return own,m,refs

def controller(own,a,gm,m,refs):
 d=load(own['donor_host'],'_081_exact069_host');d.OWNER=OWNER
 Base,cpu=d.base_lane();terminal=load(m['files']['terminal_fence.py'],'_081_same_terminal')
 adapter=load(own['files']['scope_adapter112.py'],'_081_same_scope');patch=load(m['files']['patch_scope.py'],'_081_same_patch');guard=load(own['files']['top_guard116.py'],'_092_bounded_same_top_tree');composition=load(own['files']['patch_scope112.py'],'_116R1_exact_composition');composition.install(adapter,guard,patch)
 ns=Base.observe.__globals__;module=types.SimpleNamespace(**dict(ns,c=types.SimpleNamespace(sha=d.sha),_adapter_ref=a.owner_ref));adapter._MODULE=module
 ns.update(_adapter_scope=adapter.scoped_cards,_adapter_ref=a.owner_ref,_adapter_checked=d.checked,_adapter_protected=adapter.protected_observation,_adapter_nonselected=adapter.nonselected_identity)
 transformed=adapter.transform_observe(inspect.getsource(Base.observe));new={};exec(compile(transformed,str(HERE/'owner116.py')+':unchanged069scope','exec'),ns,new);Base.observe=new['observe']
 oldinit=Base.__init__
 def init(self,*args):
  oldinit(self,*args);self._adapter_module=module
  obs=load(m['observer_ref'],'_081_actual_protected_observer');obs.install(types.SimpleNamespace(frozen=lambda:self.h),d.ref(d.HOST),a.output,write,lambda:([os.getpid()]+[p['pid']for p in self.pid_proofs.values()],[self.active]if self.active else[]))
 Base.__init__=init
 scope=dict(d.__dict__,Base=Base,a=a,cpu=cpu)
 cls=ast.ClassDef(name='GE',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=exact_methods(own['donor_host']),decorator_list=[])
 code=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]));exec(compile(code,str(HERE/'owner116.py')+':unchanged069methods','exec'),scope);GE=scope['GE']
 def create(self,stage):
  self.stage=stage;self.secondary=[];self.output=a.output/stage;self.output.mkdir();self.cards=[4]
  self.observe('numeric',require_idle=True)
  roots={gm['root'],str(HERE)}
  # Exact source roots and the one historical blob tree only. config.json is
  # mounted as a FILE, never its weight-bearing model directory.
  paths={r['path']for r in refs}|roots;paths={q for q in paths if not any(v!=q and Path(v)in Path(q).parents for v in roots)}
  mounts={q:(q,False)for q in paths};mounts['/usr/local/Ascend/driver']=('/usr/local/Ascend/driver',False);mounts[str(self.output)]=(str(self.output),True);a.current_mounts=mounts
  need(sum(rw for _,rw in mounts.values())==1,'sole fresh stage RW')
  env=dict(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',TORCH_DEVICE_BACKEND_AUTOLOAD='0',ASCEND_RT_VISIBLE_DEVICES='0',VLLM_PLUGINS='ascend',ASCEND_CUSTOM_OPP_PATH='/vllm-workspace/vllm-ascend/vllm_ascend/_cann_ops_custom/vendors/custom_transformer')
  childout=self.output/'result';plan=self.output/'PLAN.json';write(plan,dict(schema='bole.tree-plan/v116',source=a.owner_ref,cpu_stage=a.cpu_stage_ref,physical=4,logical=0,profile=own['profile'],abi_ticket_ref=a.abi_ticket_ref,qualification=False));self.plan_ref=ref(plan)
  args=[d.PY,'-I','-B',own['files']['guest116.py']['path'],'--execute','--source-ref',json.dumps(own['guest_source'],separators=(',',':')),'--plan-ref',json.dumps(self.plan_ref,separators=(',',':')),'--output',str(childout)]
  cmd=[d.DOCKER,'create','--name','boletree116-'+str(time.time_ns()),'--label','qwen36.owner='+OWNER,'--label','qwen36.stage='+stage,'--label','deltalog-fresh-bridge.owner-source-sha256='+a.owner_ref['sha256'],'--cpus=1','--cpuset-cpus='+str(a.guest_cpu),'--memory=8g','--memory-swap=8g','--ipc=private','--shm-size=2g','--pids-limit=512','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none']
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
      bound=proof;write(self.output/'ACTUAL_OWNER.json',proof);write(childout/'MAIN_ARM.json',dict(schema='bole.tree-arm/v116',pid=dv['pid'],plan_sha256=self.plan_ref['sha256'],physical=4))
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
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);p.add_argument('--output',type=Path);p.add_argument('--cpu-owner-ref');p.add_argument('--abi-ticket-ref');a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);own=obj(sr);need(own['output_root']==str(OUTROOT)+'/'+own['profile'],'exact frozen profile output');OUTROOT=Path(own['output_root']);need(own['schema']=='bole.tree-fa-owned-source/v116'and own['root']==str(HERE)and own['default_enabled']is False,'exact081 own source/defaultOFF')
 for r in own['files'].values():checked(r)
 need(own['prepared_only']is False and own['files']['owner116.py']==ref(__file__),'actual bound owner bytes');gm,m,refs=closure(own);refs=[sr,*own['files'].values(),*refs];own['guest_source']=sr;ar=own['authority_ref'];auth=obj(ar);need(ar==gm['authority_ref']and auth['start_epoch']==1792134133 and auth['cutoff_epoch']==1792220533,'unchanged new24h authority')
 if a.source_audit:print(json.dumps(dict(source=sr,readset=refs,NPU=False,resource_admitted=False)));return 0
 cpu_ref=json.loads(a.cpu_owner_ref);cv=obj(cpu_ref);need(cv['schema']=='bole.tree-owned-CPU/v116'and cv['source']==sr and cv['primary']is None and cv['secondary']==[]and cv['resource_release_verified']is True and cv['stage_ref']is None,'same-source stopped actual CPU preflight owner');a.cpu_stage_ref=cv['stage_result'];cpu_stage=obj(a.cpu_stage_ref);need(cpu_stage['schema']=='bole.tree-CPU-stage/v116'and cpu_stage['source']==sr and cpu_stage['actual_meta']['pass_gate']is True,'actual116 sameimage dualMeta preflight');refs.extend([cpu_ref,a.cpu_stage_ref])
 need(a.abi_ticket_ref,'actual releasedCPU ABI NPU ticket required');ticket_ref=json.loads(a.abi_ticket_ref);ticket_api=load(own['files']['ticket116.py'],'_actual116ticket');tv=ticket_api.consume(ticket_ref,sr,cpu_ref);a.abi_ticket_ref=ticket_ref;refs.extend([ticket_ref,tv['actual_abi_ref']])
 need(sys.platform=='linux'and 1792134133<=time.time()<1792220533-900,'Linux/current whole900 fits cutoff');need(a.output.parent==OUTROOT and a.output.name=='numeric'and not a.output.exists()and all(not q.is_symlink()for q in(OUTROOT,*OUTROOT.parents)),'unique absent authorized leaf')
 import resource,fcntl,signal
 affinity=os.sched_getaffinity(0);need(a.host_cpu in affinity and a.guest_cpu in affinity and a.host_cpu!=a.guest_cpu,'actual disjoint inherited CPUs');a.owner_ref=sr;a.lease_seconds=900;a.whole_deadline=time.monotonic()+900;a.run_root=a.output;a.stop_after_numerics=True;a.physical_device=4
 os.sched_setaffinity(0,{a.host_cpu});soft,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'host hardAS unchanged');resource.setrlimit(resource.RLIMIT_AS,(GIB//2,hard))
 def deadline(signum,frame):raise RuntimeError('original whole900/fixed authority deadline')
 signal.signal(signal.SIGALRM,deadline);signal.signal(signal.SIGTERM,deadline);signal.alarm(900)
 GE,d,storage,seal=controller(own,a,gm,m,refs)
 fd=os.open(OUTROOT/'.graph116R5.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  # New explicitly authorized MXR leaf; no DL storage ledger is read or mutated.
  lane=GE(a,Path(gm['root']));r=lane.call([d.DOCKER,'ps','--no-trunc','--filter','label=qwen36.owner','--format','{{.ID}}']);need(not r['stdout'].strip(),'serialize with every existing owned load')
  proof=storage.check();need(proof['filesystem_free_bytes']>=9.5*GIB,'fresh32GiB MXR samefilesystem admission; no DL space');a.output.mkdir();write(a.output/'UNTRACKED_ALLOCATION.json',dict(source=sr,bytes=GIB,proof=proof,ledger_advanced=False,exclusive_MXR084_lock=True,qualified=False))
  primary=None;secondary=[];result=None;start=time.monotonic()
  try:result=lane.wait079()
  except BaseException as e:primary=repr(e)
  finally:
   try:lane.cleanup()
   except BaseException as e:secondary.append('cleanup '+repr(e))
  for r in refs:checked(r)
  source_verify(refs);used=scan(OUTROOT);need(used<=GIB-65536,'reserve bounded final owner receipt within whole cap')
  v=dict(schema='bole.tree-owned/v116',source=sr,abi_ticket_ref=a.abi_ticket_ref,guest_source=own['guest_source'],donor_source=own['donor_source'],authority=ar,result=result,primary=primary,secondary=secondary,stopped_retained=lane.active is None,physical=[4],logical=0,NPU=(a.output/'numeric/result/DEVICE.json').is_file(),NPU_requested=True,qualified=False,old_failures_unchanged=True,elapsed=time.monotonic()-start,used_bytes=used)
  write(a.output/'RESULT.json',v);print(json.dumps(ref(a.output/'RESULT.json')));return 3 if primary or secondary else 0
 finally:os.close(fd);signal.alarm(0)
if __name__=='__main__':raise SystemExit(main())
