"""MAIN-only frozen Joint/Owned reuse for new vector writer. DEFAULT OFF."""
import argparse,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common as J
def prepare(a):
 own,m=J.boot(a.source,a.source_sha256);R=J.load('_vector_cohort_runtime',m['cohort_runtime']);binding=R.static_binding(m,own,a,J.checked,J.load)
 B,A,C=J.contract(m,[]);bm=J.obj(m['base_source']);rows=[own,*m['files'].values(),*m['dependencies'],binding['ref'],*binding['policy_manifest']['files'].values(),*[r['source']for r in binding['plan']['members']],*bm['files'],*bm['dependencies'],bm['clock']]
 refs={}
 for r in rows:J.checked(r);J.need(r['path']not in refs or refs[r['path']]==r,'no conflicting readset');refs[r['path']]=r
 C.input_refs=lambda unused:list(refs.values())
 L=J.load('_vector_original_safety',m['donor_safety']);E=A.bind(B,L,m['donor_host'],J.checked(m['donor_host']),C,time.monotonic())
 return own,m,bm,B,C,E,R,binding,list(refs.values())
def main():
 started=time.monotonic();epoch=time.time();p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-audit-only',action='store_true');p.add_argument('--source',type=Path);p.add_argument('--source-sha256');p.add_argument('--cohort',type=Path);p.add_argument('--cohort-sha256');p.add_argument('--run-id');p.add_argument('--physical',type=int);p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit_only):print(json.dumps(dict(default_enabled=False,NPU=False)));return 0
 own,m,bm,B,C,E,R,binding,refs=prepare(a)
 if a.source_audit_only:print(json.dumps(dict(source=own,readset=refs,cohort=binding['ref'],ready=False,NPU=False)));return 0
 J.need(J.START<=epoch and epoch+180<J.CUT,'original180 phase includes60 cleanup and fits fixed window')
 J.need([sys.executable,'-B',*sys.argv]==R.exact_host_argv(own,binding['ref'],binding['row']),'actual exact cohort host CLI')
 out=B.ordinary(a.output);J.need(str(out)==binding['row']['output_root']and out.parent==B.OUTPUT_PARENT and out.name.startswith('run-kivi-direct-fp32-graph-owner-r156-main-')and not out.exists(),'new exact cohort output');out.mkdir(mode=0o700)
 bm=dict(bm,cache_accountant=m['files']['cache_scan.py'],numeric_script=m['files']['guest.py']);H=E['helper'](bm);idle=J.load('_vector_idle_policy',m['idle_policy']);idle.install(H,m['idle_helper']);E['COHORT_SHARED']=R.install(E,C,E['L'],H,binding,m,J.checked)
 co=E['Joint'](a,own,bm,None,dict(source=own,input_files=refs),H,started);Owned=E['controller'](H);observer=J.load('_vector_protected_observer',m['protected_observer']);observer.install(H,m['idle_helper'],out,C.write,lambda:([os.getpid()],[c.cid for c in co.controllers if c.cid]));stages=[];cleanups=[];primary=None
 try:
  for mode,label,card,cap in [('software','cpu-preflight',None,25),(m['stage'],'physical-single',a.physical,120)]:
   leaf=out/label;leaf.mkdir();(leaf/'tmp').mkdir();ctl=Owned(co,leaf,card,J.P);co.controllers.append(ctl);_,initial=co.observe(ctl,label,initial=True);ctl.create();remaining=int(ctl.remaining(cap=cap));J.need(remaining>0,'actual remaining budget')
   args=[str(J.P/'guest.py'),'--execute','--source',own['path'],'--source-sha256',own['sha256'],'--mode',mode,'--output',str(leaf/'producer'),'--expected-cid',ctl.cid,'--remaining-seconds',str(remaining)]
   inspection=None
   if card is not None:
    _,ir=ctl.inspect();inspection=C.write(leaf/'VECTOR_INSPECTION.json',dict(schema='skvq.vector256-owned-inspection/v1',source=own,owned_ref=C.ref(leaf/'OWNED.json'),raw_inspect_ref=ir));C.write(leaf/'VECTOR_INSPECTION_REF.json',inspection)
    args+=['--physical',str(card),'--inspection-ref-json',str(leaf/'VECTOR_INSPECTION_REF.json')]
   ctl.begin('matrix'if card is not None else'cpu-prerequisite',args,remaining);child=ctl.wait(card is not None);rr=C.ref(leaf/'producer'/'RESULT.json');v=C.load(rr)
   J.need(v['schema']=='skvq.vector256-owned-child/v1'and v['source']==own and v['mode']==mode and v['primary']is None and v['actual_cid']==ctl.cid and v['python_version'][:2]==[3,12]and v['actual_argv']==ctl.expected_child_argv,'actual same660/source-bound child')
   if card is not None:B.validate_process(v,ctl.gate_proofs,ctl.expected_child_argv);raw=C.load(v['raw_ref']);J.need(raw['primary']is None and raw['status']=='WRITER_COMPONENT_RAW_AND_SELF_CHECK_COMPLETE'and raw['stage']==m['stage'],'complete raw, independent consumption still required')
   stages.append(dict(mode=mode,label=label,result=rr,child=child,owned=C.ref(leaf/'OWNED.json'),inspection=inspection,argv=ctl.expected_child_argv,initial=initial,process_proofs=ctl.gate_proofs));cr=ctl.cleanup();cleanups.append(cr);cl=C.load(cr);J.need(cl['stopped']is cl['retained']is True and cl['errors']==[]and not ctl.secondary,'exact own stop-retain before next stage')
  for r in refs:J.checked(r)
  co.resources()
 except BaseException as e:primary=e
 finally:
  for ctl in co.controllers:
   if ctl.cid and not any(C.load(r)['container']==ctl.cid for r in cleanups):
    ctl.primary=primary
    try:cleanups.append(ctl.cleanup())
    except BaseException as e:co.secondary.append(repr(e))
   co.secondary.extend(ctl.secondary)
  co.secondary.extend(co.time_failures())
  if co.cleanup_used>60:co.secondary.append('original cumulative60 cleanup exceeded')
  result=dict(schema='skvq.vector256-cohort-host/v1',source=own,admitted_epoch=epoch,status='RAW_PENDING_INDEPENDENT'if primary is None and not co.secondary and len(stages)==2 else'FAILED',primary=repr(primary)if primary else None,secondary=co.secondary,stages=stages,cleanups=cleanups,cohort=binding['ref'],run_id=a.run_id,physical=a.physical,phase_seconds=180,cleanup_seconds=60,cumulative_cleanup_seconds=co.cleanup_used,elapsed_seconds=time.monotonic()-started,start_epoch=J.START,cutoff=J.CUT,authority=m['authority'],actual_host_argv=[sys.executable,'-B',*sys.argv],model_ready=False,performance_ready=False,task_ready=False,run_authority=False)
  rr=C.write(out/'RESULT.json',result);print('MAIN_SKVQ_VECTOR256_R156 '+json.dumps(rr),flush=True)
 if primary:raise primary
 J.need(not co.secondary and len(stages)==2,'complete actual CPU/NPU and release');return 0
if __name__=='__main__':raise SystemExit(main())
