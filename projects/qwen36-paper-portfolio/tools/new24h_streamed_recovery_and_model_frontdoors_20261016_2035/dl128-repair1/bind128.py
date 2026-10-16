"""Publish only a typed actual recovery input/permission, no model SOURCE claim."""
import argparse,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import io128 as C,receiver128 as R
def model_context(component_cpu_owner_ref):
 old=C.obj(R.OLD_TEMPLATE);fault=C.obj(R.FAULT);sr=fault['refs']['source'];s=C.obj(sr)
 old.update(admission_mode='actual052-split-scale-diagnostic-only',prepared_only=False,
  bridge024_source_ref=sr,bridge024_owner_ref=fault['refs']['owner'],component_cpu_owner_ref=component_cpu_owner_ref,
  production_build_ref=s['split_build_ref'],debug_build_ref=s['debug_build_ref'],split_kernel_source_ref=s['split_kernel_source_ref'],debug_kernel_source_ref=s['debug_kernel_source_ref'],library_ref=s['library_ref'],debug_library=s['debug_library'])
 return old
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for n in('receiver-source-ref','recovery-owner-ref','recovery-cleanup-ref','recovery-inspect-ref','component-cpu-owner-ref','output'):p.add_argument('--'+n)
 a=p.parse_args()
 if not a.execute:print('disabled');return 0
 for n in('receiver_source_ref','recovery_owner_ref','recovery_cleanup_ref','recovery_inspect_ref','component_cpu_owner_ref','output'):C.need(getattr(a,n)is not None,'actual required input pending: '+n)
 sr=json.loads(a.receiver_source_ref);R.source(C,sr);C.need(1792134133<=time.time()<1792220533,'fixed new24h cutoff, no extension')
 plan=dict(schema='deltalog.recovered-component-model-input/v128',receiver_source_ref=sr,old_model_template_ref=R.OLD_TEMPLATE,recovery_template_ref=R.R2_TEMPLATE,actual_fault_ref=R.FAULT)
 for n in('recovery_owner_ref','recovery_cleanup_ref','recovery_inspect_ref','component_cpu_owner_ref'):plan[n]=json.loads(getattr(a,n))
 out=Path(a.output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists()and not out.with_name(out.name+'.permission.json').exists(),'fresh explicit agentcontrol input/permission paths')
 # The candidate plan is never published until all real predicates pass.
 m=model_context(plan['component_cpu_owner_ref'])
 result=R.admit_plan(C,m,plan,sr)
 C.write(out,plan);C.write(out.with_name(out.name+'.permission.json'),dict(schema='deltalog.actual-recovery-component-permission/v128',current_reader_source=sr,input_plan=C.ref(out),result=result,model_source_bound=False,model_ready=False,performance_ready=False,task_ready=False));print(json.dumps(dict(input=C.ref(out),permission=C.ref(out.with_name(out.name+'.permission.json')))));return 0
if __name__=='__main__':raise SystemExit(main())
