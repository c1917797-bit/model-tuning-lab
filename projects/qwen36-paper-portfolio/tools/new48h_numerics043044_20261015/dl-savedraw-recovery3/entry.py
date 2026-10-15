"""Devices[]: original031 consume_pair over saved40raw+2anchors; no NPU rerun."""
import argparse,json,os,pathlib,subprocess,sys,time
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
def diagnostic_argv(m,out):
 consumer=m['files']['diagnose.py'];C.checked(consumer)
 return[sys.executable,'-I','-B',consumer['path'],'--execute','--source-ref',json.dumps(m['original_source_ref']),'--producer-ref',json.dumps(m['original_producer_ref']),'--output',str(out/'sidecar-predicates')]
def validate_diagnosis(m,v):
 C.need(v['schema']=='deltalog.saved-sidecar-predicate-diagnostic/v1'and v['source']==m['original_source_ref']and v['producer']==m['original_producer_ref']and v['diagnostic_complete']is True and len(v['rows'])==57,'actual57 original predicate source/raw join')
 C.need(all(v[k]is False for k in('NPU_reexecuted','numeric16_qualified','numeric160_qualified','model_ready','performance_ready','task_ready')),'diagnostic only, never gate promotion')
def main():
 if '--execute'not in sys.argv:print('disabled');return
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--stage',choices=('cpu-preflight',),required=True)
 for n in('source-ref','authority-ref','lifecycle-ref','output'):p.add_argument('--'+n,required=True)
 p.add_argument('--steps',type=int,choices=(16,),default=16);a=p.parse_args();sr=json.loads(a.source_ref);ar=json.loads(a.authority_ref);m=C.source(sr);C.window(ar)
 C.need(not list(pathlib.Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','actual no-device CPU environment')
 original=C.obj(m['original_source_ref']);producer=C.obj(m['original_producer_ref']);failed=C.obj(m['original_failed_owner_ref']);cleanup=C.obj(m['original_cleanup_ref'])
 cpu_failure=C.obj(m['original_CPU_failure_ref']);old_strict=C.obj(m['original_strict_failure_ref']);C.checked(m['original_domain_child_failure_ref'])
 C.need(cpu_failure['primary']is not None and cpu_failure['result']is None and cpu_failure['stopped_retained']is True and cpu_failure['NPU']is False and old_strict['pass_gate']is False and old_strict['source']==m['original_source_ref']and old_strict['producer']==m['original_producer_ref'],'old0928 failure and old strict FAIL unchanged')
 # Installed guest source identities are not host files or mounted tensor data.
 # Verify their actual original paths inside this same660 Devices[] image.
 import bind_recovery
 bind_recovery.validate_runtime_identities(m['guest_runtime_identity_evidence'],producer)
 seen_guest={}
 for item in m['guest_runtime_identity_evidence']:
  r=item['identity'];C.need(bind_recovery.runtime_identity(r,tuple(item['record_json_path'])),'exact original raw-schema guest identity')
  C.need(r['path']not in seen_guest or seen_guest[r['path']]==r,'no guest identity conflict');seen_guest[r['path']]=r
 for r in seen_guest.values():C.checked(r)
 import provenance
 exit_proof=provenance.validate(failed,producer,C.obj(m['original_stage_ref']),cleanup,*[C.obj(m['original_exit_evidence'][k])for k in('verdict','arm','before','after')],m['original_source_ref'],m['original_producer_ref'])
 C.need(failed['schema']=='deltalog.diagnostic-owned-host/v035'and failed['target_source']==m['original_source_ref']and failed['primary']is not None and failed['bridge_primitive_gate_pass']is False,'old043R3 owned FAIL remains unchanged')
 C.need(cleanup['resource_release_verified']is cleanup['stopped']is cleanup['retained']is True and cleanup['errors']==[]and cleanup['secondary_guard_cleanup']==[]and cleanup['unresolved_active_cid']is None,'actual saved031 stop-retain-release proof')
 C.need(producer['source']==m['original_source_ref']and producer['steps']==16 and producer['primary']is None and producer['NPU']is True and len(producer['records'])==40,'actual complete031 saved40 raw')
 out=pathlib.Path(a.output);C.need(not out.exists()and out.parent.is_dir(),'new CPU-only leaf');out.mkdir()
 argv=diagnostic_argv(m,out)
 with(out/'consumer.stdout').open('x')as so,(out/'consumer.stderr').open('x')as se:r=subprocess.run(argv,stdout=so,stderr=se,timeout=min(600,1792135097-time.time()-90))
 C.write(out/'CONSUMER_EXEC.json',dict(argv=argv,exit_code=r.returncode,stdout=C.ref(out/'consumer.stdout'),stderr=C.ref(out/'consumer.stderr')));C.need(r.returncode==0,'actual031 pair CPU execution failed; preserve outputs')
 ir=C.ref(out/'sidecar-predicates/DIAGNOSIS.json');v=C.obj(ir)
 validate_diagnosis(m,v)
 C.write(out/'STAGE_RESULT.json',dict(schema='deltalog.saved043R3-sidecar-diagnostic/v3',source=sr,authority=ar,pass_gate=True,NPU=False,model_ready=False,diagnostic_complete=True,original_source=m['original_source_ref'],original_producer=m['original_producer_ref'],actual_original_NPU_provenance=exit_proof,diagnosis=ir,failed_indices=v['failed_indices'],original_numerical_pass=False,original_failed_owner=m['original_failed_owner_ref'],original_CPU_failure=m['original_CPU_failure_ref'],old_host_failure_unchanged=True,numeric16_qualified=False,numeric160_qualified=False))
if __name__=='__main__':main()
