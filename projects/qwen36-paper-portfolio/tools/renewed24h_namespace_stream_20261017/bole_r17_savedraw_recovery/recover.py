"""Devices[] original tensor math only; never reconstructs a worker snapshot."""
import argparse,json,os,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import recovery_io as C,plan as R

def run(t,own_source,plan_ref,out):
 own=C.obj(own_source);C.need(own['prepared_only']is False and own['recovery_plan_ref']==plan_ref,'same bound recovery plan')
 proof=R.consume(C,plan_ref);m,mods=R.parent_modules(C);I=mods['independent_model'];MC=mods['model_calibration131r12'];K=mods['consume_model'];O=mods['identity_oracle'];oracle=mods['oracle112']
 http=C.obj(proof['http']);response=C.obj(http['rows'][0]['response']);events=[C.obj(r)for r in proof['journals']]
 assignments=[e['event']for e in events if e['role']=='frontend'and e['kind']=='assignment'and e['event']['before_request_id']==response['id']+'-0'];C.need(len(assignments)==1,'actual one original frontend assignment')
 _,assigned=O.validate_assignment(response['id'],K.PROFILE,assignments[0]);C.need(response['id']==O.expected_server_id(http['rows'][0]['header'],None),'HTTP assigned identity source join')
 reports=[];rows=[];vocabulary=[];calibrations=[];traces=[];bindings={}
 oldabi=C.obj(m['actual118c']['capture'])['actual_device_abi_ref']
 for expected,pair in enumerate(proof['ranks']):
  receipt=C.obj(pair['receipt']);C.need(receipt['rank']==expected and receipt['primary']is None and receipt['raw']==pair['raw'],'unchanged original rank capture')
  fields=receipt['stat'][receipt['stat'].rfind(')')+2:].split();identity=dict(pid=receipt['pid'],start_ticks=int(fields[19]),cgroup=receipt['cgroup']);bindings[expected]=identity
  journal=[e['event']for e in events if e['role']=='rank%d'%expected and e['kind']=='worker_update'];C.need(journal and all(e['identity']==identity and e['rank']==expected for e in journal),'all actual journal/capture identities')
  traces.append(dict(schema='vllm023.actual-worker-retirement/v1',rank=expected,identity=identity,events=journal))
  exported=t.load(C.checked(pair['raw']),map_location='cpu',weights_only=False)
  C.need(exported['schema']=='bole.model-diagnostic-primitives/v1'and 0<=exported['logical_tensor_bytes']<=exported['cap_bytes']==2**30,'original full bounded primitive raw')
  raw=exported['payload'];C.need(raw['source']==R.SOURCE and raw['rank']==expected and raw['request']['request']==assigned,'source/rank/actual assigned request join')
  C.need(raw['same_model_conv_calibration']==pair['calibration']==receipt['model_calibration_ref'],'same original per-rank calibration raw')
  calibrations.append(MC.consume(t,C,pair['calibration'],oldabi,R.SOURCE,expected))
  C.need(pair['raw']['bytes']+calibrations[-1]['raw_bytes']+pair['calibration']['bytes']<=2**30+2**20,'original combined1GiB raw gate')
  observation=raw['actual_native_prefill_input'];C.need(observation['sources']=={k:m['runtime_sources'][k]for k in('runner','base_runner','qwen35','qwen_next')},'original actual native input source join')
  vocabulary.append(dict(policy=raw['native_logits_policy'],local=raw['genuine_MTP']['first_local_logits'].clone(),global_logits=raw['genuine_MTP']['first_logits'].clone(),children=raw['genuine_MTP']['children'].clone(),tokens=raw['tree_context']['tokens'],target=raw['staged']['actual_target_logits'].clone()))
  report,vectors=I.consume(t,raw,oracle) # actual original complete reference/gates
  path=out/('VECTORS-rank%d.pt'%expected)
  with path.open('xb')as f:t.save(vectors,f);f.flush();os.fsync(f.fileno())
  C.need(path.stat().st_size<=2**30,'original complete difference-vector1GiB perrank')
  rr=C.write(out/('RANK-%d.json'%expected),dict(source=own_source,original_source=R.SOURCE,receipt=pair['receipt'],raw=pair['raw'],report=report,vectors=C.ref(path)))
  reports.append(rr);rows.append(report);del raw,vectors,exported
 K.vocabulary_join(t,vocabulary) # exact original independent assembly function
 O.validate_worker_retirement(assigned,traces,bindings)
 result=dict(schema='bole.r17-independent-savedraw-math/v1',source=own_source,recovery_plan=plan_ref,original_source=R.SOURCE,original_failed_owner=R.OWNER,ranks=reports,independently_recomputed_same_model_conv_calibrations=calibrations,tensor_math_complete=True,component_checks_pass=all(x['component_checks_pass']for x in rows),independent_actual_MTP_TP4_vocabulary_join=True,recorded_retirement_journals_consistent=True,native_snapshot_status=proof['native_snapshot_status'],actual_original_snapshots=proof['snapshots'],live_frontend_binding_status='missing-not-reconstructed',native_restored_snapshot_qualified=False,lifecycle_qualified=False,original_owner_pass=False,whole_numerical_qualified=False,model_ready=False,scheduler_committed=False,performance_ready=False,task_ready=False,qualified=False)
 C.write(out/'ATTRIBUTION.json',result)
 C.need(result['component_checks_pass'],'original component mathematical gate FAIL; complete reports/vectors preserved')
 return result

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 C.need(a.source_ref and a.plan_ref and a.output,'explicit bound source/plan/output')
 sr=json.loads(a.source_ref);pr=json.loads(a.plan_ref);own=C.obj(sr)
 C.need(own['files']['recover.py']==C.ref(__file__)and own['root']==str(P),'exact own actual consumer source')
 C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci[0-9]*')),'actual Devices[] CPU only')
 C.need(str(a.output)==own['output_root']+'/consumer'and a.output.is_dir(),'sole owned exact physical guest output, no dangling alias Refs')
 try:
  import torch
  torch.set_num_threads(1);C.need(not hasattr(torch,'npu')or not torch.npu.is_initialized(),'no native device initialization')
  run(torch,sr,pr,a.output);return 0
 except BaseException as e:
  C.write(a.output/'FAILURE.json',dict(source=sr,recovery_plan=pr,primary=repr(e),traceback=traceback.format_exc(),qualified=False,original_owner_pass=False));raise
if __name__=='__main__':raise SystemExit(main())
