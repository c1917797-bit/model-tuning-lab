"""MAIN-only source-bound real-frame graph plus active128 gate, default OFF."""
import argparse,hashlib,importlib.util,json,sys,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def checked(r):
 p=Path(r['path']);need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and p.is_absolute()and p.resolve()==p and not p.is_symlink()and p.is_file(),'strict3 ordinary source/input');before=p.stat();wire=p.read_bytes();after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and len(wire)==r['bytes']and hashlib.sha256(wire).hexdigest()==r['sha256'],'complete stable source/input bytes');return wire
def load(name,r):
 s=importlib.util.spec_from_file_location(name,r['path']);M=importlib.util.module_from_spec(s);sys.modules[name]=M;exec(compile(checked(r),r['path'],'exec',dont_inherit=True),M.__dict__);return M
def prepare(a):
 own=dict(path=str(a.source),bytes=a.source.stat().st_size,sha256=a.source_sha256);m=json.loads(checked(own));need(m['root']==str(P)and m['schema']=='kivi.direct-fp32.graph-single4-owner-sources/v3'and m['default_enabled']is False and m['cutoff']==1792002456,'new graph owner source/window')
 for r in m['files'].values():checked(r)
 R=load('_graph_cohort_runtime',m['files']['cohort_runtime.py']);binding=R.static_binding(m,own,a,checked,load);m=dict(m,_cohort=binding,_runtime=R)
 W=load('_graph_r156_window',m['files']['window.py']);W.validate(checked(m['authority']));need(m['start_epoch']==W.START and m['cutoff']==W.CUT,'frozen R156 clock not donor clock')
 b=load('_graph_original_owner_binding',m['owner_binding']);B=b.base();bm=json.loads(checked(m['base_source']));g=json.loads(checked(m['graph_source']));numeric=json.loads(checked(g['standalone_import_roles']['numeric_manifest']));repair=json.loads(checked(m['writer_repair']));zero=json.loads(checked(m['zero_source']));active=json.loads(checked(m['active_source']))
 need(m['graph_source']['sha256']=='d0eed41cbda770c59e4fdb6ef2ed648362a5d074928c254df2307c291cfc3f82'and g['software_tests']==36,'exact frozen graph source, no borrowed PASS')
 S=load('_graph_original_standalone',g['files']['standalone_graph.py']);frame=json.loads(checked(S.FRAME))
 need((m['phase_seconds'],m['cleanup_seconds'],m['guest_bytes'],m['host_bytes'],m['reserve_bytes'],m['CPU_total'],m['physical_allowed'],m['logical'])==(1800,90,8*1024**3,512*1024**2,8*1024**3,4,[4,5,6,7],0),'original phase/resource/physical scope unchanged')
 rows=[m['observer'],m['prefix_source'],m['active_source'],m['active_original_source'],active['author'],*active['files'].values(),*json.loads(checked(m['prefix_source']))['files'].values(),m['original008_source'],*m['original008_files'].values(),m['zero_source'],*zero['files'].values(),own,binding['ref'],m['cohort_policy'],*binding['policy_manifest']['files'].values(),*[r['source']for r in binding['plan']['members']],m['original006_source'],*m['original006_files'].values(),m['writer_repair'],*repair['files'].values(),m['original004_source'],*m['original004_files'].values(),m['predecessor_source'],*m['predecessor_files'].values(),m['graph_source'],m['base_source'],m['owner_binding'],m['donor_contract'],m['donor_host'],m['donor_safety'],m['inspect_store'],m['authority'],m['oracle'],m['output_budget'],m['idle_policy'],m['idle_helper'],*m['files'].values(),*g['files'].values(),*g['software_dependencies'],*numeric['sources'].values(),*numeric['dependencies'],*bm['files'],*bm['dependencies'],bm['clock'],S.FRAME,frame['rows'][0]['query_ref'],*frame['pool_fields'].values(),*frame['whole_prewrite_input_refs'].values()]
 refs={}
 for r in rows:
  checked(r);need(r['path']not in refs or refs[r['path']]==r,'no conflicting source/input identity');refs[r['path']]=r
 need(not {'torch','torch_npu','triton','numpy'}.intersection(n.split('.')[0]for n in sys.modules),'host cold source-only')
 return own,m,bm,B,list(refs.values())
def runtime(own,m,bm,B,refs,started):
 A=load('_graph_controller_private_adapter',m['files']['controller_adapter.py']);C=A.private_contract(B,checked(m['donor_contract']),P,refs,m['_cohort']['policy'].devices)
 store=load('_graph_lossless_original_inspect',m['inspect_store']);store.install(C,B)
 L=load('_graph_actual_original_safety',m['donor_safety']);env=A.bind(B,L,m['donor_host'],checked(m['donor_host']),C,started)
 return C,env
def main():
 started=time.monotonic();admitted_epoch=time.time();p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-audit-only',action='store_true');p.add_argument('--source',type=Path);p.add_argument('--source-sha256');p.add_argument('--output',type=Path);p.add_argument('--cohort',type=Path);p.add_argument('--cohort-sha256');p.add_argument('--run-id');p.add_argument('--physical',type=int);a=p.parse_args()
 if not(a.execute or a.source_audit_only):print(json.dumps(dict(default_enabled=False,NPU=False)));return 0
 own,m,bm,B,refs=prepare(a);C,E=runtime(own,m,bm,B,refs,started)
 if a.source_audit_only:print(json.dumps(dict(source=own,refs=len(refs),NPU=False,ready=False)));return 0
 need(1791916056<=time.time()and time.time()+1800<=1792002456,'single original phase1800 fits authorized R156 cutoff')
 need([sys.executable,'-B',*sys.argv]==m['_runtime'].exact_host_argv(own,m['_cohort']['ref'],m['_cohort']['row']),'actual exact cohort CLI');out=B.ordinary(a.output);need(str(out)==m['_cohort']['row']['output_root']and out.parent==B.OUTPUT_PARENT and out.name.startswith('run-kivi-direct-fp32-graph-owner-r156-main-')and not out.exists(),'new owned output no retry/overwrite');out.mkdir(mode=0o700)
 bm=dict(bm,cache_accountant=m['files']['cache_scan.py'],numeric_script=m['files']['guest.py']);H=E['helper'](bm);policy=load('_graph_r156_idle_policy',m['idle_policy']);policy.install(H,m['idle_helper']);E['COHORT_SHARED']=m['_runtime'].install(E,C,E['L'],H,m['_cohort'],m,checked);co=E['Joint'](a,own,bm,None,dict(source=own,input_files=refs),H,started);Observer=load('_r162_protected_actual',m['observer']);observer_receipt=Observer.install(H,m['idle_helper'],out,C.write,lambda:([__import__('os').getpid()],[x.cid for x in co.controllers if x.cid]));Owned=E['controller'](H)
 stages=[];cleanups=[];primary=None;raw_refs={}
 try:
  for mode,label,card,cap in [('software','cpu-preflight',None,180),('graph','physical-single',a.physical,600),('active','physical-active',a.physical,600),('independent','cpu-independent',None,180)]:
   leaf=out/label;leaf.mkdir();(leaf/'tmp').mkdir();ctl=Owned(co,leaf,card,Path(m['graph_source']['path']).parent);co.controllers.append(ctl)
   _,initial=co.observe(ctl,label,initial=True);ctl.create();remaining=int(ctl.remaining(cap=cap));need(remaining>0,'actual same phase remaining')
   args=[str(P/'guest.py'),'--execute','--source',own['path'],'--source-sha256',own['sha256'],'--mode',mode,'--output',str(leaf/'producer'),'--expected-cid',ctl.cid,'--remaining-seconds',str(remaining)]
   if mode=='independent':args+=['--raw-ref-json',str(out/'RAW_REFS.json')]
   ctl.begin('matrix'if card is not None else('cpu-prerequisite'if mode=='software'else'independent'),args,remaining);child=ctl.wait(card is not None);rr=C.ref(leaf/'producer'/'RESULT.json');v=C.load(rr)
   need(v['schema']=='kivi.r156.dual-domain-child/v1'and v['source']==own and v['mode']==mode and v['primary']is None and v['actual_cid']==ctl.cid and v['writer_repair']==m['writer_repair']and v['python_version'][:2]==[3,12],'actual new source-specific child contract')
   if card is not None:
    B.validate_process(v,ctl.gate_proofs,ctl.expected_child_argv);raw_refs[mode]=v['raw_ref']
    if mode=='active':C.write(out/'RAW_REFS.json',raw_refs)
   stages.append(dict(mode=mode,result=rr,child=child,owned=C.ref(leaf/'OWNED.json'),argv=ctl.expected_child_argv,initial=initial,process_proofs=ctl.gate_proofs));cr=ctl.cleanup();cleanups.append(cr);cl=C.load(cr);need(cl['stopped']is cl['retained']is True and cl['errors']==[]and not ctl.secondary,'own exact stop-retain before next actual stage')
  for r in refs:checked(r)
  co.resources()
 except BaseException as e:
  primary=e;C.write(out/'FIRST_FAULT.json',dict(primary=repr(e),traceback=traceback.format_exc(),filename=getattr(e,'filename',None),errno=getattr(e,'errno',None)))
 finally:
  for ctl in co.controllers:
   if ctl.cid and not any(C.load(r)['container']==ctl.cid for r in cleanups):
    ctl.primary=primary
    try:cleanups.append(ctl.cleanup())
    except BaseException as e:co.secondary.append(repr(e))
   co.secondary.extend(ctl.secondary)
  co.secondary.extend(co.time_failures())
  if co.cleanup_used>90:co.secondary.append('cumulative original90 cleanup exceeded')
  rr=C.write(out/'RESULT.json',dict(schema='kivi.r156.dual-domain-host/v1',source=own,admitted_epoch=admitted_epoch,status='DUAL_DOMAIN_PENDING_ORIGINAL_CONSUMPTION'if primary is None and not co.secondary and len(stages)==4 else'FAILED',primary=repr(primary)if primary else None,secondary=co.secondary,stages=stages,cleanups=cleanups,raw_refs=raw_refs,observer_receipt=observer_receipt,started_monotonic=started,created_monotonic=co.created,deadline_monotonic=co.deadline,cumulative_cleanup_seconds=co.cleanup_used,phase_seconds=1800,cleanup_seconds=90,cutoff=1792002456,start_epoch=1791916056,authority=m['authority'],cohort=m['_cohort']['ref'],run_id=a.run_id,physical=a.physical,writer_repair=m['writer_repair'],actual_host_argv=[sys.executable,'-B',*sys.argv],model_ready=False,performance_ready=False,run_authority=False,multistep_qualified=False,numerical_qualified=False,active_source=m['active_source'],actual_writer=m['actual_writer']))
  print('MAIN_KIVI_DUAL_DOMAIN_R156 '+json.dumps(rr),flush=True)
 if primary:raise primary
 need(not co.secondary and len(stages)==4,'complete source/saved32769/active128/independent stages')
 return 0
if __name__=='__main__':raise SystemExit(main())
