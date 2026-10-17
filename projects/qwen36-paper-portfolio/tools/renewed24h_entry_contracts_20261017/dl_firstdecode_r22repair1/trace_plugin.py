"""Default-OFF actual forward dispatch trajectory, never numerical proof."""
import functools,json,os
from pathlib import Path
def register():
 if os.environ.get('QWEN36_DELTALOG_TRACE025_ENABLE')!='1':return
 import owner_overlay as O
 sr=json.loads(os.environ['QWEN36_DELTALOG_TRACE025_SOURCE_REF']);m=O.current(sr)
 import bootstrap101r9 as BOOT
 BOOT.install(m,Path(__file__).resolve().parent);print('DL101R9_WORKER_IMPORT '+json.dumps(BOOT.package_proof(m)),flush=True)
 O.need(O.obj_file(m['files']['trace_plugin.py'])==Path(__file__).resolve(),'actual trace source')
 from qwen36_deltalog_service import runtime as R,integration as W,builder_mirror as M
 O.need(R._OP is None,'trace025 is sole service entrypoint, no duplicate service023 invocation')
 import tensor_observer as T
 activate=T.install(R,W,M,sr,m)
 R.register();O.need(R._OP is not None and R._SOURCE==m['plugin_source'],'actual023 receiver registered')
 activate()
 import identity_events
 identity_events.install(R,sr,m)
 from vllm_ascend.worker.model_runner_v1 import NPUModelRunner
 from vllm.distributed import parallel_state as ps
 original=NPUModelRunner._model_forward
 O.need(not getattr(NPUModelRunner,'_dl025_trace',False),'no duplicate trajectory hook')
 @functools.wraps(original)
 def forward(r,*a,**kw):
  result=original(r,*a,**kw)
  if M._DUMMY.get():return result
  state=getattr(r,'_deltalog018_state',None);step=None if state is None else state['current']
  if step is None:return result
  O.need(step['forward_complete']is True and M.finish_step(r),'actual final023 forward finished')
  root=Path(os.environ['QWEN36_DELTALOG_SERVICE023_AUDIT'])/'dispatch-trajectory';root.mkdir(exist_ok=True)
  counts={prefix:R._COUNTS.get(prefix,0)for prefix in state['layers']}
  value=dict(schema='deltalog.actual-dispatch-trajectory/v025',source=sr,plugin_source=R._SOURCE,pid=os.getpid(),rank=ps.get_tensor_model_parallel_rank(),epoch=step['epoch'],request_ids=[k[0]for k in step['keys']],groups={str(gid):dict(decode=list(meta._deltalog018_cpu_receipt['cpu'].decode),prefill=list(meta._deltalog018_cpu_receipt['cpu'].prefill))for gid,meta in step['metadata'].items()},registered_prefixes=sorted(state['layers']),decode_calls=counts,all48_finished=True,numerical_qualified=False,actual_merge_observed=False)
  path=root/('worker-%d-epoch-%05d.json'%(os.getpid(),step['epoch']))
  with path.open('x',encoding='utf8')as f:json.dump(value,f,sort_keys=True);f.write('\n')
  return result
 NPUModelRunner._model_forward=forward;NPUModelRunner._dl025_trace=True
