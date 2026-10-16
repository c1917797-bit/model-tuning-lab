"""079 diagnostic on the exact069 Lane/scope/cleanup; no model qualification."""
import argparse,ast,hashlib,importlib.util,inspect,json,os,shutil,stat,sys,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-native-prefill-owned-new24h-v1-081'
OUTROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
OWNER='deltalog-native-prefill-counterfactual-MAIN-081'
GIB=2**30
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
 need(dv['logical']==0 and dv['physical_declared_by_plan']==5 and dv['plan']==plan and dv['canary']==[4.,5.]and dv['physical_proof_must_be_host_owned']is True and cid in dv['cgroup'],'079 device/plan/self report, not physical proof')
 ticks=int(dv['stat'][dv['stat'].rfind(')')+2:].split()[19])
 proofs=[p for p in record['owned_process_proofs']if p['physical']==5 and p['namespace_pids'][-1]==dv['pid']and p['start_ticks']==ticks and cid in p['cgroup']]
 if not proofs:need(not record['owned_process_proofs'],'actual nonempty ownership mismatch');return None
 need(len(proofs)==1 and proofs[0]['argv']==argv,'unique host SMI/PID/start/ns/cgroup/fullargv proof');return proofs[0]
def receive(v,sr,ar,pr):
 need(v['schema']=='deltalog.native-prefill-counterfactual-stage/v079'and v['source']==sr and v['authority']==ar and v['plan']==pr and v['primary']is None and v['NPU']is True,'actual079 successful stage, not a qualification')
 need(v['qualified']is False and v['old160_failure_unchanged']is True and len(v['result']['rows'])==6 and v['result']['raw_bytes']<=256*2**20,'six full bounded raw diagnostic calls')
 need(v['result']['whole_correctness_qualified']is False and v['result']['native_baseline_postconv_inputs_were_captured']is False,'scope cannot be promoted')
 for r in v['result']['rows']:checked(r['raw'])
 return v
def closure(own):
 gm=obj(own['guest_source']);m=obj(gm['retained_source']);producer=obj(gm['retained_failed_producer'])
 need(gm['schema']=='deltalog.native-prefill-counterfactual-source/v079'and gm['default_enabled']is False,'sealed079 defaultOFF')
 g=load(gm['files']['guest_core.py'],'_079_source_only');rows=g.select_records(producer)
 refs=[own['guest_source'],*gm['files'].values(),gm['retained_source'],gm['retained_failed_producer'],gm['authority_ref'],gm['cann_helper_ref'],m['config_ref'],*[m['files'][n]for n in('raw_codec.py','qwen36_deltalog_fresh/native_fixture.py','qwen36_deltalog_fresh/capture_evidence.py','host.py','scope_adapter.py','patch_scope.py','top_guard.py','terminal_fence.py','storage061.py','sealed_storage069.py')],m['observer_ref'],m['storage_authority_ref'],m['storage_seal_evidence_ref'],*[r['raw']for r in rows],*own['dependencies'].values()]
 def nested(v):
  if type(v)is dict:
   if set(v)=={'path','bytes','sha256'}:refs.append(v)
   else:
    for x in v.values():nested(x)
  elif type(v)is list:
   for x in v:nested(x)
 nested(obj(m['storage_seal_evidence_ref']))
 for r in refs:checked(r)
 need(own['donor_host']==m['files']['host.py'],'only actual069 bound donor, no analogous controller')
 return gm,m,refs
def controller(own,a,gm,m,refs):
 d=load(own['donor_host'],'_081_exact069_host');d.OWNER=OWNER
 Base,cpu=d.base_lane();terminal=load(m['files']['terminal_fence.py'],'_081_same_terminal')
 adapter=load(m['files']['scope_adapter.py'],'_081_same_scope');patch=load(m['files']['patch_scope.py'],'_081_same_patch');guard=load(m['files']['top_guard.py'],'_081_same_tree');patch.install(adapter,guard)
 ns=Base.observe.__globals__;module=types.SimpleNamespace(**dict(ns,c=types.SimpleNamespace(sha=d.sha),_adapter_ref=a.owner_ref));adapter._MODULE=module
 ns.update(_adapter_scope=adapter.scoped_cards,_adapter_ref=a.owner_ref,_adapter_checked=d.checked,_adapter_protected=adapter.protected_observation,_adapter_nonselected=adapter.nonselected_identity)
 transformed=adapter.transform_observe(inspect.getsource(Base.observe));new={};exec(compile(transformed,str(HERE/'owner081.py')+':unchanged069scope','exec'),ns,new);Base.observe=new['observe']
 oldinit=Base.__init__
 def init(self,*args):
  oldinit(self,*args);self._adapter_module=module
  obs=load(m['observer_ref'],'_081_actual_protected_observer');obs.install(types.SimpleNamespace(frozen=lambda:self.h),d.ref(d.HOST),a.output,write,lambda:([os.getpid()]+[p['pid']for p in self.pid_proofs.values()],[self.active]if self.active else[]))
 Base.__init__=init
 scope=dict(d.__dict__,Base=Base,a=a,cpu=cpu)
 cls=ast.ClassDef(name='GE',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=exact_methods(own['donor_host']),decorator_list=[])
 code=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]));exec(compile(code,str(HERE/'owner081.py')+':unchanged069methods','exec'),scope);GE=scope['GE']
 def create(self,stage):
  self.stage=stage;self.secondary=[];self.output=a.output/stage;self.output.mkdir();self.cards=[5]
  self.observe('numeric',require_idle=True)
  roots={gm['root'],m['root'],str(HERE),str(Path(gm['retained_failed_producer']['path']).parent)}
  # Exact source roots and the one historical blob tree only. config.json is
  # mounted as a FILE, never its weight-bearing model directory.
  paths={r['path']for r in refs}|roots;paths={q for q in paths if not any(v!=q and Path(v)in Path(q).parents for v in roots)}
  mounts={q:(q,False)for q in paths};mounts['/usr/local/Ascend/driver']=('/usr/local/Ascend/driver',False);mounts[str(self.output)]=(str(self.output),True);a.current_mounts=mounts
  need(sum(rw for _,rw in mounts.values())==1,'sole fresh stage RW')
  env=dict(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',TORCH_DEVICE_BACKEND_AUTOLOAD='0',ASCEND_RT_VISIBLE_DEVICES='0',VLLM_PLUGINS='ascend',ASCEND_CUSTOM_OPP_PATH='/vllm-workspace/vllm-ascend/vllm_ascend/_cann_ops_custom/vendors/custom_transformer')
  childout=self.output/'result';plan=self.output/'PLAN.json';write(plan,dict(schema='deltalog.native-prefill-counterfactual-plan/v079',source=own['guest_source'],retained_source=gm['retained_source'],producer=gm['retained_failed_producer'],physical=5,logical=0,qualification=False));self.plan_ref=ref(plan)
  args=[d.PY,'-I','-B',gm['files']['guest_core.py']['path'],'--execute','--source-ref',json.dumps(own['guest_source'],separators=(',',':')),'--plan-ref',json.dumps(self.plan_ref,separators=(',',':')),'--output',str(childout)]
  cmd=[d.DOCKER,'create','--name','dl-native081-'+str(time.time_ns()),'--label','qwen36.owner='+OWNER,'--label','qwen36.stage='+stage,'--label','deltalog-fresh-bridge.owner-source-sha256='+a.owner_ref['sha256'],'--cpus=1','--cpuset-cpus='+str(a.guest_cpu),'--memory=8g','--memory-swap=8g','--ipc=private','--shm-size=2g','--pids-limit=512','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none']
  for dst,(src,rw)in mounts.items():cmd+=['--mount','type=bind,src='+src+',dst='+dst+(''if rw else',readonly')]
  # Same proven069 host5 -> guest0 contract; actual physical identity still
  # must be independently seen by SMI/proc before ARM. No guessed alias.
  cmd+=['--device=/dev/davinci5:/dev/davinci0']
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
      bound=proof;write(self.output/'ACTUAL_OWNER.json',proof);write(childout/'MAIN_ARM.json',dict(schema='deltalog.native-prefill-counterfactual-arm/v079',pid=dv['pid'],plan_sha256=self.plan_ref['sha256'],physical=5))
   if not x['State']['Running']:
    write(self.output/'inspect-exited.json',r);need(x['State']['ExitCode']==0,'actual079 child exit; failure retained');need(bound is not None,'real host proof/ARM required')
    write(self.output/'QUIESCENT_REFS.json',terminal.quiescent(childout,False,ref,obj));rr=ref(childout/'STAGE_RESULT.json');receive(obj(rr),own['guest_source'],own['authority_ref'],self.plan_ref);return rr
   need(time.monotonic()<end,'guest600/whole900 charged startup deadline');time.sleep(.2 if bound is None else 1)
 GE.create=create;GE.wait079=wait
 observe=GE.observe
 def observed(self,*args,**kw):
  used=scan(a.output);proof=storage.check();need(proof['committed_bytes']+GIB<=80*GIB and proof['filesystem_free_bytes']>=100*GIB,'untracked1GiB/80total/live100free')
  live=self.call([d.DOCKER,'ps','--no-trunc','--filter','label=qwen36.owner','--format','{{.ID}}']);need(set(live['stdout'].split())<=({self.active}if self.active else set()),'no unaccounted owned CPU/RAM overlap')
  return observe(self,*args,**kw)
 GE.observe=observed
 storage=load(m['files']['storage061.py'],'_081_exact_storage');seal=load(m['files']['sealed_storage069.py'],'_081_exact_seal');seal.install(storage,m['storage_seal_evidence_ref'],m['storage_authority_ref'],m['prepared_template'])
 return GE,d,storage,seal
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--host-cpu',type=int);p.add_argument('--guest-cpu',type=int);p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);own=obj(sr);need(own['schema']=='deltalog.native-prefill-owned-source/v081'and own['root']==str(HERE)and own['default_enabled']is False,'exact081 own source/defaultOFF')
 for r in own['files'].values():checked(r)
 need(own['files']['owner081.py']==ref(__file__),'actual owner bytes');gm,m,refs=closure(own);refs=[sr,*own['files'].values(),*refs];ar=own['authority_ref'];auth=obj(ar);need(ar==gm['authority_ref']and auth['start_epoch']==1792134133 and auth['cutoff_epoch']==1792220533,'unchanged new24h authority')
 if a.source_audit:print(json.dumps(dict(source=sr,readset=refs,NPU=False,resource_admitted=False)));return 0
 need(sys.platform=='linux'and 1792134133<=time.time()<1792220533-900,'Linux/current whole900 fits cutoff');need(a.output.parent==OUTROOT and a.output.name.startswith('run-native081-')and not a.output.exists()and all(not q.is_symlink()for q in(OUTROOT,*OUTROOT.parents)),'unique absent authorized leaf')
 import resource,fcntl,signal
 affinity=os.sched_getaffinity(0);need(a.host_cpu in affinity and a.guest_cpu in affinity and a.host_cpu!=a.guest_cpu,'actual disjoint inherited CPUs');a.owner_ref=sr;a.lease_seconds=900;a.whole_deadline=time.monotonic()+900;a.run_root=a.output;a.stop_after_numerics=True;a.physical_device=5
 os.sched_setaffinity(0,{a.host_cpu});soft,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'host hardAS unchanged');resource.setrlimit(resource.RLIMIT_AS,(GIB//2,hard))
 def deadline(signum,frame):raise RuntimeError('original whole900/fixed authority deadline')
 signal.signal(signal.SIGALRM,deadline);signal.signal(signal.SIGTERM,deadline);signal.alarm(900)
 GE,d,storage,seal=controller(own,a,gm,m,refs)
 fd=os.open(OUTROOT/'.storage061.lock',os.O_RDWR|os.O_NOFOLLOW);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  # Retain074's no-overlap and sealed/untracked output protocol; never advance
  # the historical ledger or infer that its prior FAIL was qualified.
  lane=GE(a,Path(gm['root']));r=lane.call([d.DOCKER,'ps','--no-trunc','--filter','label=qwen36.owner','--format','{{.ID}}']);need(not r['stdout'].strip(),'serialize with every existing owned load')
  proof=storage.check();need(proof['committed_bytes']+GIB<=80*GIB and proof['filesystem_free_bytes']>=101*GIB,'sealed80+new1/live100+new1');a.output.mkdir();write(a.output/'UNTRACKED_ALLOCATION.json',dict(source=sr,bytes=GIB,proof=proof,ledger_advanced=False,exclusive_existing_storage_lock=True,qualified=False))
  primary=None;secondary=[];result=None;start=time.monotonic()
  try:result=lane.wait079()
  except BaseException as e:primary=repr(e)
  finally:
   try:lane.cleanup()
   except BaseException as e:secondary.append('cleanup '+repr(e))
  for r in refs:checked(r)
  seal.final_verify(m['storage_seal_evidence_ref']);used=scan(a.output);need(used<=GIB-65536,'reserve bounded final owner receipt within whole cap')
  v=dict(schema='deltalog.native-prefill-owned/v081',source=sr,guest_source=own['guest_source'],retained_source=gm['retained_source'],producer=gm['retained_failed_producer'],authority=ar,result=result,primary=primary,secondary=secondary,stopped_retained=lane.active is None,physical=[5],logical=0,NPU=(a.output/'numeric/result/DEVICE.json').is_file(),NPU_requested=True,qualified=False,old160_failure_unchanged=True,elapsed=time.monotonic()-start,used_bytes=used)
  write(a.output/'RESULT.json',v);print(json.dumps(ref(a.output/'RESULT.json')));return 3 if primary or secondary else 0
 finally:os.close(fd);signal.alarm(0)
if __name__=='__main__':raise SystemExit(main())
