"""Read true model-instance/core binding separately from tensor mathematics."""
import hashlib,json
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(ref(r['path'])==r,'actual binding Ref3');return json.loads(Path(r['path']).read_bytes())
def consume(worker,source,notes,run_id,worker_source):
 proof_ref=ref(worker/'CORE_BINDING.json');proof=obj(proof_ref)
 need(proof['schema']=='mxr.actual-qwen-copied-core-binding/v010'and proof['source']==source and proof['run_id']==run_id and proof['target']=='vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn.QwenGatedDeltaNetAttention','actual real Qwen target')
 need(proof['actual_target_bound']is proof['Ascend_algorithm_binding_preserved']is proof['actual004_counts_identity']is True and proof['after_callback_ref']==worker_source,'true receiver+after state-write source binding')
 need(proof['native_scope_methods']==['chunk_gated_delta_rule','torch.ops._C_ascend.npu_recurrent_gated_delta_rule'],'both real prefill/decode core domains')
 files=sorted(worker.glob('core-binding-*.json'));need(len(files)==48,'all48 actual model instance associations')
 associations={}
 for path in files:
  r=ref(path);v=obj(r);layer=v['prefix']
  need(v['schema']=='mxr.actual-qwen-instance-binding/v010'and v['source']==source and v['run_id']==run_id and v['actual_no_compile_layer_is_self']is True and v['both_native_chunk_and_recurrent_within_original_core_scope']is True,'actual static-layer instance witness')
  need(v['resolved_method_id']==proof['bound_core_id']and v['algorithm_core_id']==proof['algorithm_core_id']and v['algorithm_counts_id']==proof['algorithm_counts_id']and layer not in associations,'same actual receiver/counters/MRO')
  associations[layer]=r
 need({n['prefix']for n in notes}==set(associations),'frame-prefix cartesian actual associations')
 for n in notes:need(n['core_binding']==proof_ref and n['instance_binding']==associations[n['prefix']],'each actual frame source/instance proof')
 return dict(actual_target=True,instance_prefixes=48,frames=len(notes),performance=False)
