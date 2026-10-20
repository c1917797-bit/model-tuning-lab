"""Bounded primitive/tensor export; never pickle a model, pool or runtime class."""
import dataclasses

def export(t,value,*,cap_bytes):
 if type(cap_bytes)is not int or not 0<cap_bytes<=2**30:raise ValueError('explicit at-most1GiB per-rank capture budget')
 used=0
 def walk(x):
  nonlocal used
  if isinstance(x,t.Tensor):
   used+=x.numel()*x.element_size()
   if used>cap_bytes:raise ValueError('capture logical bytes exceed budget before next D2H')
   return x.detach().cpu().contiguous()
  if x is None or type(x)in(str,int,float,bool):return x
  if type(x)in(tuple,list):return [walk(v)for v in x]
  if type(x)is dict:
   if not all(type(k)in(str,int)for k in x):raise ValueError('primitive metadata keys only')
   return {k:walk(v)for k,v in x.items()}
  if dataclasses.is_dataclass(x)and type(x).__module__ in('model_entry','treeconv118','tree_metadata111','acceptance','adapter'):
   return {f.name:walk(getattr(x,f.name))for f in dataclasses.fields(x)}
  raise ValueError('opaque runtime/model metadata forbidden: '+type(x).__name__)
 result=walk(value)
 return dict(schema='bole.model-diagnostic-primitives/v1',payload=result,logical_tensor_bytes=used,cap_bytes=cap_bytes,model_ready=False)

def export_staged(t,proposal,*,cap_bytes):
 """Explicitly omit live destination tensors, never an entire engine cache pool."""
 if proposal.get('schema')!='bole.actual-model-selected-path-staging/v1'or proposal.get('published')is not False:raise ValueError('unpublished actual staged proposal only')
 writes=[]
 for r in proposal['writes']:
  if not {'layer','kind','arena','arena_identity','before','after'}<=set(r):raise ValueError('complete staged write record')
  writes.append({k:v for k,v in r.items()if k not in('arena','slot_binding')})
 raw={k:v for k,v in proposal.items()if k!='writes'};raw['writes']=writes;raw['serialized_plan_is_not_publishable']=True
 return export(t,raw,cap_bytes=cap_bytes)
