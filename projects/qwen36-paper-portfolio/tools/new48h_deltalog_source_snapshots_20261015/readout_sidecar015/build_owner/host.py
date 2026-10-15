"""MAIN-only Devices[] KDMA isolated compilation; original Joint/Owned."""
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);need(p.is_absolute()and p.resolve()==p and p.is_file()and not p.is_symlink(),'ordinary stable input');a=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_mtime_ns,a.st_size)==(z.st_dev,z.st_ino,z.st_mtime_ns,z.st_size),'whole data stability');return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>=0 and ref(r['path'])==r,'exact Ref3');return Path(r['path']).read_bytes()
def load(name,r):
 need(name not in sys.modules,'no foreign/partial source module');s=importlib.util.spec_from_file_location(name,r['path']);v=importlib.util.module_from_spec(s);sys.modules[name]=v
 try:exec(compile(checked(r),r['path'],'exec',dont_inherit=True),v.__dict__)
 except BaseException:sys.modules.pop(name,None);raise
 return v
def prepare(a,started):
 own=ref(a.source);need(own['sha256']==a.source_sha256 and a.source==P/'SOURCE_MANIFEST.json','current own source');m=json.loads(checked(own));need(m['schema']=='deltalog.owned-kdma-build-source/v1'and m['root']==str(P)and m['default_enabled']is False and(m['start_epoch'],m['cutoff'])==(1791962297,1792135097),'frozen CPU-only source')
 for r in [*m['files'].values(),*m['dependencies']]:checked(r)
 W=load('_input_window',m['window']);W.validate(checked(m['authority']));R=load('_input_shared_cohort',m['cohort_runtime']);binding=R.static_binding(m,own,a,checked,load)
 b=load('_input_actual_binding',m['owner_binding']);B=b.base();bm=json.loads(checked(m['base_source']));build=json.loads(checked(m['build_source_manifest']));data=[m['build_script_ref'],m['build_source_manifest'],*m['build_host_refs']]
 rows=[own,*m['files'].values(),*m['dependencies'],*data,*bm['files'],*bm['dependencies'],bm['clock'],binding['ref'],*binding['policy_manifest']['files'].values(),*[r['source']for r in binding['plan']['members']]];refs={}
 for r in rows:checked(r);need(r['path']not in refs or refs[r['path']]==r,'exact source/data closure');refs[r['path']]=r
 A=load('_input_actual_adapter',m['controller_adapter']);C=A.private_contract(B,checked(m['donor_contract']),P,list(refs.values()),binding['policy'].devices);C.PHASE=900;C.CLEANUP=90
 def environment(service,leaf):
  value=B.environment(service,leaf);value.update(ASCEND_RT_VISIBLE_DEVICES='',TORCH_DEVICE_BACKEND_AUTOLOAD='0',MST_DASC_BOUNDARY_DIAGNOSTIC='0',USE_TORCH='1',USE_TF='0',USE_FLAX='0',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false');return value
 C.environment=environment;C.create_argv.__globals__['environment']=environment
 store=load('_input_inspect_storage',m['inspect_store']);store.install(C,B);L=load('_input_actual_safety',m['donor_safety']);E=A.bind(B,L,m['donor_host'],checked(m['donor_host']),C,started)
 def closure(model,material,output,leaf):
  need(type(model)is dict and model['numeric_script']==m['files']['guest.py']and material is None,'actual inherited cache manifest, not model material')
  mounts={r['path']:(r['path'],False)for r in refs.values()}
  need(not any(src.startswith('/cache/efim/Qwen3.6-27B/')or src=='/cache/efim/Qwen3.6-27B'for src,rw in mounts.values()),'no checkpoint source/weight mount')
  need(str(leaf)not in mounts,'no RO/output collision')
  mounts[str(leaf)]=(str(leaf),True)
  return mounts
 E['closure_mounts']=closure
 return own,m,bm,B,C,E,R,binding,list(refs.values())
def main():
 started=time.monotonic();epoch=time.time();p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-audit-only',action='store_true');p.add_argument('--source',type=Path);p.add_argument('--source-sha256');p.add_argument('--cohort',type=Path);p.add_argument('--cohort-sha256');p.add_argument('--run-id');p.add_argument('--physical',type=int);p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit_only):print(json.dumps(dict(enabled=False,NPU=False)));return 0
 own,m,bm,B,C,E,R,binding,refs=prepare(a,started)
 if a.source_audit_only:print(json.dumps(dict(source=own,RO_refs=refs,NPU=False,tokenized=False,ready=False)));return 0
 need(1791962297<=epoch and epoch+900<1792135097 and [sys.executable,'-B',*sys.argv]==R.exact_host_argv(own,binding['ref'],binding['row']),'actual exact R156 cohort CLI/900phase')
 out=B.ordinary(a.output);need(str(out)==binding['row']['output_root']and out.parent==B.OUTPUT_PARENT and not out.exists(),'absent actual cohort output')
 bm=dict(bm,cache_accountant=m['files']['cache_scan.py'],numeric_script=m['files']['guest.py']);H=E['helper'](bm);load('_input_idle',m['idle_policy']).install(H,m['idle_helper']);E['COHORT_SHARED']=R.install(E,C,E['L'],H,binding,m,checked)
 host_cpu=H.cpu_view(os.getpid());daemon_cpu=H.daemon_view();admission=H.cpu_admission(host_cpu,daemon_cpu)
 out.mkdir(mode=0o700);admission_ref=C.write(out/'PRE_OUTPUT_CPU_ADMISSION.json',dict(source=own,cohort=binding['ref'],host=host_cpu,daemon=daemon_cpu,plan=admission,observed_epoch=time.time()))
 co=E['Joint'](a,own,bm,None,dict(source=own,input_files=refs),H,started);need(co.cpu==admission,'same original fresh CPU admission before/after output creation');load('_input_protected',m['protected_observer']).install(H,m['idle_helper'],out,C.write,lambda:([os.getpid()],[x.cid for x in co.controllers if x.cid]));Owned=E['controller'](H);ctl=None;primary=None;child=None;result=None;cleanup=None
 try:
  leaf=out/'cpu-preflight';leaf.mkdir();(leaf/'tmp').mkdir();ctl=Owned(co,leaf,None,P);co.controllers.append(ctl);co.observe(ctl,'input-cpu',initial=True);ctl.create();x,_=ctl.inspect();need(x['HostConfig']['Devices']==[],'actual no devices')
  cap=int(ctl.remaining(cap=810));args=[str(P/'guest.py'),'--execute','--source',own['path'],'--source-sha256',own['sha256'],'--expected-cid',ctl.cid,'--remaining-seconds',str(cap),'--output',str(leaf/'producer')];ctl.begin('cpu-prerequisite',args,cap);child=ctl.wait(False);result=C.ref(leaf/'producer'/'RESULT.json');v=C.load(result)
  need(v['source']==own and v['primary']is None and v['actual_cid']==ctl.cid and v['NPU']is False and v['result']['build_complete']is True and v['result']['NPU']is False,'actual source/API CPU preflight only')
  actual=C.load(v['result']['build_result_ref']);need(actual['source_manifest']==m['build_source_manifest']and actual['authority']==m['authority']and actual['primary']is None and actual['Devices']==[]and actual['NPU']is False and actual['numeric_qualified']is False and actual['model_ready']is False,'independent host build verdict')
  need([r['arm']for r in actual['artifacts']]==['readout_sidecar_v015']and all(r['exit_code']==0 and r['error']is None for r in actual['commands']),'independent both build commands')
  for row in actual['artifacts']:
   for key in('library','cache','compile_commands'):
    if row[key]is not None:checked(row[key])
  need(len(v['safety'])>=3 and all(s['forbidden_modules']==[] and s['no_device_nodes']and s['no_device_fds']and s['no_npu_runtime_maps']for s in v['safety']),'actual CPU safety receipts')
  for r in refs:checked(r)
  cleanup=ctl.cleanup();cl=C.load(cleanup);need(cl['stopped']is cl['retained']is True and cl['errors']==[]and not ctl.secondary,'actual CPU stop/retain');co.resources()
 except BaseException as e:primary=e
 finally:
  if ctl and ctl.cid and cleanup is None:
   ctl.primary=primary
   try:cleanup=ctl.cleanup()
   except BaseException as e:co.secondary.append(repr(e))
  if ctl:co.secondary.extend(ctl.secondary)
  co.secondary.extend(co.time_failures());rr=C.write(out/'RESULT.json',dict(schema='deltalog.owned-kdma-build-host/v1',source=own,admitted_epoch=epoch,cohort=binding['ref'],run_id=a.run_id,pre_output_cpu_admission=admission_ref,phase_seconds=900,cleanup_seconds=90,child=result,child_operation=child,cleanup=cleanup,primary=repr(primary)if primary else None,secondary=co.secondary,actual_host_argv=[sys.executable,'-B',*sys.argv],NPU=False,model_ready=False,task_ready=False,elapsed_seconds=time.monotonic()-started));print('MAIN_KDMA_OWNED_BUILD '+json.dumps(rr),flush=True)
 if primary:raise primary
 need(not co.secondary,'whole original CPU budget/cleanup');return 0
if __name__=='__main__':raise SystemExit(main())
