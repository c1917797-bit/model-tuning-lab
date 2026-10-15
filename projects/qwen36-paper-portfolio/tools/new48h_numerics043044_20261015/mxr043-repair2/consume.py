"""Complete raw once-candidate GDN CPU reference, unchanged original metrics."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parent
ORIGINAL={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-r118-capture-20261013-001/consume_capture.py','bytes':10097,'sha256':'7c31e87b409ef095e5789a2bc1b71a987a69dc237789c125ad749a69fecec6c3'}
def need(v,s):
 if not v:raise ValueError(s)
def checked(r):
 p=Path(r['path']);need(type(r['bytes'])is int and 0<r['bytes']<=768*1024**2 and p.stat().st_size==r['bytes'],'bounded full raw Ref3');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'full raw source SHA');return b
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);exec(compile(checked(r),r['path'],'exec'),m.__dict__);return m
def fingerprint(torch,t):
 b=t.contiguous().view(torch.uint8).numpy().tobytes();return dict(dtype=str(t.dtype),shape=list(t.shape),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def consume(worker,source,output,run_id):
 m=json.loads(checked(source));need(m['schema']=='mxr.diag16.full-gdn-frame-bridge-source/v1','new source, not061')
 module(m['files']['admit042.py'],'_043_actual042_consumer').gate(m['actual042_owner_ref'])
 oracle=module(ORIGINAL,'_actual_original_FP64metrics')
 ref=module(m['files']['independent_reference.py'],'_independent_GDN_recurrence')
 import torch
 torch.set_num_threads(1)
 notes=[json.loads(p.read_text())for p in sorted(worker.glob('frame-*/FRAME.json'))]
 need(notes and len(notes)==(48 if m['stage']=='short129'else 1),'declared short48 or full longshape representative')
 runtime=json.loads((worker/'RUNTIME.json').read_bytes());need(runtime['source']==source and runtime['plugin_source']==m['plugin_source']and runtime['run_id']==run_id and runtime['mode']=='correctness','actual current runtime identity')
 binding=module(m['files']['prefix_binding.py'],'_043_exact_prefix_binding');RUNTIME_PINS=binding.RUNTIME_PINS
 boundary=module(m['files']['boundary_oracle.py'],'_043_independent_working_reference')
 core_proof=None;associations={};rows=[]
 for n in notes:
  need(n['pid']==runtime['pid']and n['run_id']==run_id and n['source']==source and n['plugin_source']==m['plugin_source']and n['candidate_delta']==1 and n['graph']is False,'actual004 candidate once, not fallback/shadow')
  proof=json.loads(checked(n['core_binding']));association=json.loads(checked(n['instance_binding']))
  need(proof['schema']=='mxr.actual-qwen-copied-core-binding/v010'and proof['source']==source and proof['run_id']==run_id and proof['actual_target_bound']is proof['Ascend_algorithm_binding_preserved']is proof['actual004_counts_identity']is True,'actual004 + realQwen target binding')
  need({k:v['sha256']for k,v in proof['sources'].items()}==RUNTIME_PINS,'actual installed binding source pins')
  need(association['schema']=='mxr.actual-qwen-instance-binding/v010'and association['source']==source and association['run_id']==run_id and association['prefix']==n['prefix']and association['actual_no_compile_layer_is_self']is True,'actual static-forward instance/prefix identity')
  need(association['resolved_owner']==proof['target']and association['resolved_method_id']==proof['bound_core_id']and association['algorithm_core_id']==proof['algorithm_core_id']and association['algorithm_counts_id']==proof['algorithm_counts_id'],'same MRO method and algorithm counts consumed')
  need(core_proof is None or core_proof==proof,'one immutable worker binding chain');core_proof=proof;associations[n['prefix']]=association
  raw=n['raw'];checked(raw);payload=torch.load(raw['path'],map_location='cpu',weights_only=True)
  need(set(payload)=={'inputs','inputs_after','normalized_inputs','normalized_inputs_after','output','final_state','solve','refinement','FP32_policy'},'complete actual once-pipeline payload')
  x=payload['inputs'];need(set(x)==set(payload['inputs_after']),'same actual input keys')
  for k,v in x.items():
   if torch.is_tensor(v):need(fingerprint(torch,v)==payload['inputs_after'][k],'unchanged entire input byte fingerprint '+k)
  nx=payload['normalized_inputs'];need(nx['already_normalized']is True,'actual post-native-normalizer boundary, no guessed epsilon')
  for k,v in nx.items():
   if torch.is_tensor(v):need(fingerprint(torch,v)==payload['normalized_inputs_after'][k],'whole normalized boundary unchanged '+k)
  canonical=boundary.evaluate(torch,nx)
  expected,final=ref.recurrence(torch,nx);om=oracle.metrics(torch,payload['output'],expected);sm=oracle.metrics(torch,payload['final_state'],final)
  sv=payload['solve'];need(fingerprint(torch,sv['A'])==sv['A_after']and fingerprint(torch,sv['cu'])==sv['cu_after'],'whole solve original input immutability')
  e,res=oracle.fp64_reference(torch,sv['A'],sv['cu'].tolist());am=oracle.metrics(torch,sv['output'],e)
  need(payload['FP32_policy']['allow_hf32']is False and payload['FP32_policy']['common_to_all_arms']is True,'same042 FP32 precision policy')
  trace=payload['refinement'];need(torch.equal(trace['X1_FP32'].bfloat16(),sv['output']),'actual042 refined result consumed by fullGDN')
  workout=oracle.metrics(torch,payload['output'],canonical['output']);workstate=oracle.metrics(torch,payload['final_state'],canonical['state'])
  rows.append(dict(working_output=workout,working_state=workstate,original_ideal_gate_pass=om['pass']and sm['pass']and am['pass'],reference_contract='mxr.independent-canonical-working-storage/v043',prefix=n['prefix'],tokens=x['q'].shape[1],output=om,state=sm,solve=am,pass_gate=workout['pass']and workstate['pass']and am['pass'],raw=raw))
 need(len({r['prefix']for r in rows})==len(rows),'unique actual GDN prefixes')
 value=dict(original_ideal_metrics_retained=True,reference_contract='mxr.independent-canonical-working-storage/v043',actual042_owner_ref=m['actual042_owner_ref'],binary_provenance_granted=False,schema='mxr.observerless-once-GDN-independent/v1',plugin_source_ref=m['plugin_source'],capture_source=source,run_id=run_id,pid=runtime['pid'],worker_root=str(worker),layer_prefixes=[r['prefix']for r in rows],gdn_frame_gate_pass=all(r['pass_gate']for r in rows),model_logits_qualified=False,rows=rows,pass_stage=all(r['pass_gate']for r in rows),full_GDN=True,multistep_state=False,inference_metadata_lifecycle_pass=False,graph_candidate=False,performance_ready=False,task_ready=False,qualification_not_yet_promotable=True)
 need(output.is_absolute()and not output.exists(),'new independent result directory')
 output.mkdir();output=output/'BRIDGE_RESULT.json'
 with output.open('x')as f:json.dump(value,f,sort_keys=True);f.write('\n')
 return 0 if value['pass_stage']else 3
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--worker-root',type=Path);p.add_argument('--source-ref');p.add_argument('--prerequisite-ref');p.add_argument('--run-id');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 need(a.prerequisite_ref and a.run_id and a.source_ref,'explicit actual039/source/run')
 module(dict(path=str(P/'prerequisite.py'),bytes=(P/'prerequisite.py').stat().st_size,sha256=hashlib.sha256((P/'prerequisite.py').read_bytes()).hexdigest()),'_once_prerequisite').gate(json.loads(a.prerequisite_ref))
 return consume(a.worker_root,json.loads(a.source_ref),a.output,a.run_id)
if __name__=='__main__':raise SystemExit(main())
