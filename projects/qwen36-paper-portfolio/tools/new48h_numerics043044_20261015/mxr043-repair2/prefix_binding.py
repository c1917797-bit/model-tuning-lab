"""Real copied-method binding, not a guessed prefix; no backend imports."""
import contextvars,functools,hashlib,importlib,inspect,json
from pathlib import Path
SOFTWARE_CASES=16
RUNTIME_PINS={
 'vllm_ascend.ops.gdn':'d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816',
 'vllm_ascend.patch.worker.patch_qwen3_5':'21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3',
 'vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn':'885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0'}
def need(v,m):
 if not v:raise ValueError(m)
def owner(cls,name):
 for item in cls.__mro__:
  if name in item.__dict__:return item,item.__dict__[name]
 raise ValueError('unbound method')
def bind(target,algorithm_core,prefix,get_context,associated,after=None):
 prior_owner,prior=owner(target,'_forward_core')
 @functools.wraps(algorithm_core)
 def core(self,*a,**kw):
  resolved,method=owner(type(self),'_forward_core')
  need(isinstance(self,target)and method is core,'actual model MRO binding drift/override')
  layer=self.prefix;need(type(layer)is str and bool(layer),'actual model instance prefix')
  context=get_context();need(context.no_compile_layers.get(layer)is self,'actual custom-op static layer identity')
  associated(self,layer,resolved)
  token=prefix.set(layer)
  try:
   result=algorithm_core(self,*a,**kw)
   if after is not None:after(self,layer,result)
   return result
  finally:prefix.reset(token)
 target._forward_core=core
 return core,prior_owner,prior
def actual(gdn,runtime,prefix,worker_root,source,run_id,after=None):
 # Normal module import ensures the real framework patch target is resolved.
 modules={};sources={}
 for name,digest in RUNTIME_PINS.items():
  mod=importlib.import_module(name);path=Path(inspect.getsourcefile(mod)).resolve();wire=path.read_bytes()
  need(hashlib.sha256(wire).hexdigest()==digest,'actual installed binding source '+name)
  modules[name]=mod;sources[name]=dict(path=str(path),bytes=len(wire),sha256=digest)
 patch=modules['vllm_ascend.patch.worker.patch_qwen3_5'];model=modules['vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn']
 target=model.QwenGatedDeltaNetAttention
 need(patch._GDN_PATCH_TARGET is target,'actual Qwen3.5 class alias identity')
 algorithm_core=gdn.AscendGatedDeltaNetAttention._forward_core
 closure=inspect.getclosurevars(algorithm_core).nonlocals
 need(closure.get('counts')is runtime['counts']and isinstance(closure.get('prefix'),contextvars.ContextVar)and callable(closure.get('original_core')),'actual004 algorithm core wrapper, not direct native fallback')
 native=closure['original_core']
 need(inspect.unwrap(algorithm_core)is native and native.__qualname__=='AscendGatedDeltaNetAttention._forward_core','exact actual004 -> original native core chain')
 need(inspect.getsourcefile(native)==str(Path(gdn.__file__).resolve()),'native core genuine pinned gdn module')
 before_owner,before=owner(target,'_forward_core')
 need(inspect.unwrap(before)is native,'copied actual target must originate in native core, not unknown override')
 associations={};core_box={}
 def associated(instance,layer,resolved):
  need(gdn.AscendGatedDeltaNetAttention._forward_core is algorithm_core,'actual004 owner binding intact')
  if layer in associations:
   need(associations[layer]['instance_id']==id(instance),'same frozen prefix must retain actual model instance')
   return
  need(len(associations)<48,'no extra model prefixes beyond frozen48')
  value=dict(schema='mxr.actual-qwen-instance-binding/v010',source=source,run_id=run_id,prefix=layer,
   ordinal=len(associations),instance_id=id(instance),class_module=type(instance).__module__,class_name=type(instance).__qualname__,
   mro=[c.__module__+'.'+c.__qualname__ for c in type(instance).__mro__],
   resolved_owner=resolved.__module__+'.'+resolved.__qualname__,resolved_method_id=id(core_box['core']),
   actual_no_compile_layer_is_self=True,algorithm_counts_id=id(runtime['counts']),algorithm_core_id=id(algorithm_core),
   both_native_chunk_and_recurrent_within_original_core_scope=True,performance=False)
  with(worker_root/('core-binding-%03d.json'%len(associations))).open('x')as f:json.dump(value,f,sort_keys=True)
  associations[layer]=value
 after_ref=None
 if after is not None:
  need(callable(after),'explicit after callback callable')
  path=Path(inspect.getsourcefile(after)).resolve();wire=path.read_bytes();after_ref=dict(path=str(path),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
  need(after_ref in json.loads(Path(source['path']).read_bytes())['files'].values(),'after callback belongs to actual frozen caller source')
 core,previous_owner,previous=bind(target,algorithm_core,prefix,gdn.get_forward_context,associated,after);core_box['core']=core
 proof=dict(schema='mxr.actual-qwen-copied-core-binding/v010',source=source,run_id=run_id,sources=sources,
  target=target.__module__+'.'+target.__qualname__,target_mro=[c.__module__+'.'+c.__qualname__ for c in target.__mro__],
  previous_owner=previous_owner.__module__+'.'+previous_owner.__qualname__,previous_method_id=id(previous),previous_is_algorithm_core=previous is algorithm_core,
  native_id=id(native),algorithm_core_id=id(algorithm_core),algorithm_counts_id=id(runtime['counts']),bound_core_id=id(core),actual004_counts_identity=True,
  actual_target_bound=target._forward_core is core,Ascend_algorithm_binding_preserved=gdn.AscendGatedDeltaNetAttention._forward_core is algorithm_core,
  native_scope_methods=['chunk_gated_delta_rule','torch.ops._C_ascend.npu_recurrent_gated_delta_rule'],after_callback_ref=after_ref,hardware_prefix_validation_pending=True)
 with(worker_root/'CORE_BINDING.json').open('x')as f:json.dump(proof,f,sort_keys=True)
 return dict(core=core,target=target,algorithm_core=algorithm_core,associations=associations,proof=proof)
