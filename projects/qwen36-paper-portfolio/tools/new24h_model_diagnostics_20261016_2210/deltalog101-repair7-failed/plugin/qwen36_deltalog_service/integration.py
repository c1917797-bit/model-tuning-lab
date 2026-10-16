"""Actual runner/model-layer wiring, no separate scheduler/controller."""
import functools
from . import builder_mirror as M
_RUNNERS={}

def runner_for(layer):
 r=_RUNNERS.get(id(layer));M.need(r is not None,'actual layer registered by real runner prepare')
 M.need(r._deltalog018_state['layers'][layer.prefix]['layer']is layer,'same strong actual registered layer')
 return r

def rows_from_native(r,target):
 rows=[];ctx=r.compilation_config.static_forward_context
 for gid,table in enumerate(r.input_batch.block_table.block_tables):
  if not table.is_mamba_group:continue
  for name in r.kv_cache_config.kv_cache_groups[gid].layer_names:
   M.need(name in ctx,'actual config prefix exists in static framework context')
   layer=ctx[name];M.need(isinstance(layer,target)and layer.prefix==name,'actual source-resolved Qwen object, not invented prefix')
   rows.append((layer,gid))
 return rows

def install(R,target,emit):
 prepare=R._prepare_inputs;forward=R._model_forward
 M.need(not getattr(R,'_deltalog023_wired',False),'no duplicate actual wiring')
 @functools.wraps(prepare)
 def wrapped_prepare(r,*a,**kw):
  M.guard(r);state=getattr(r,'_deltalog018_state',None)
  if state is None or not state['layers']:
   rows=rows_from_native(r,target);receipt=M.register_layers(r,rows,target)
   for layer,gid in rows:
    M.need(id(layer)not in _RUNNERS,'actual layer cannot be owned by two runners');_RUNNERS[id(layer)]=r
   emit('actual_cpu_metadata_registered',prefix=None,registered=receipt['registered_prefixes'],groups={layer.prefix:gid for layer,gid in rows},framework_mapping=True)
  return prepare(r,*a,**kw)
 @functools.wraps(forward)
 def wrapped_forward(r,*a,**kw):
  if M._DUMMY.get():return forward(r,*a,**kw)
  state=getattr(r,'_deltalog018_state',None)
  if state is None or state['current']is None:
   M.need(state is None or not any(state['owners'].values()),'no unqualified native fallback after live state')
   return forward(r,*a,**kw)
  step=state['current'];M.need(not step.get('forward_complete',False),'one real model forward per scheduler epoch')
  result=forward(r,*a,**kw) # actual native forward context remains active here
  M.finish_step(r);step['forward_complete']=True
  r._deltalog023_finished_steps=getattr(r,'_deltalog023_finished_steps',0)+1
  emit('actual_model_step_complete',prefix=None,first_epoch=step['epoch'],all48_core=True,all48_decode=all(not m.num_decodes or len([k for k in m._deltalog018_cpu_receipt['seen']if k[1]=='decode'])==len([x for x in state['layers'].values()if x['group']==gid])for gid,m in step['metadata'].items()),qualification=False)
  return result
 R._prepare_inputs=wrapped_prepare;R._model_forward=wrapped_forward;R._deltalog023_wired=True
 return dict(installed=True,actual_forward_completed=False,NPU_qualified=False)

def snapshot(layer):
 r=runner_for(layer);s=r._deltalog018_state;step=s['current']
 return dict(epoch=s['epoch'],registered_prefixes=tuple(sorted(s['layers'])),finished_steps=getattr(r,'_deltalog023_finished_steps',0),last_forward_complete=step is not None and step.get('forward_complete',False),model_qualified=False)
