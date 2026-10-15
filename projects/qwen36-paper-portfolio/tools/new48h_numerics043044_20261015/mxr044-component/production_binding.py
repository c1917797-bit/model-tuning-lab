"""Untimed actual target binding; timed path is the exact algorithm core object."""
import contextvars,hashlib,importlib,inspect
from pathlib import Path
SOFTWARE_CASES=28
PINS={
 'vllm_ascend.ops.gdn':'d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816',
 'vllm_ascend.patch.worker.patch_qwen3_5':'21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3',
 'vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn':'885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0'}
def need(v,m):
 if not v:raise ValueError(m)
def bind_target(target,ascend,algorithm,counts):
 closure=inspect.getclosurevars(algorithm).nonlocals
 need(closure.get('counts')is counts and isinstance(closure.get('prefix'),contextvars.ContextVar),'actual algorithm core counts/context identity')
 native=closure.get('original_core')
 need(callable(native)and inspect.unwrap(algorithm)is native,'algorithm -> original core chain')
 need(inspect.unwrap(target._forward_core)is native and ascend._forward_core is algorithm,'actual target prior native origin + Ascend algorithm owner')
 target._forward_core=algorithm
 return dict(target=target,ascend=ascend,algorithm=algorithm,counts=counts,native=native)
def bind_actual(gdn,counts,algorithm):
 modules={};sources={}
 for name,digest in PINS.items():
  mod=importlib.import_module(name);path=Path(inspect.getsourcefile(mod)).resolve();wire=path.read_bytes()
  need(hashlib.sha256(wire).hexdigest()==digest,'actual installed production source '+name)
  modules[name]=mod;sources[name]=dict(path=str(path),bytes=len(wire),sha256=digest)
 model=modules['vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn'];patch=modules['vllm_ascend.patch.worker.patch_qwen3_5'];target=model.QwenGatedDeltaNetAttention
 need(patch._GDN_PATCH_TARGET is target,'real copied-method target alias')
 state=bind_target(target,gdn.AscendGatedDeltaNetAttention,algorithm,counts);state['sources']=sources
 return state
def snapshot(state):
 # Called only by the pre-existing outside-timing SIGUSR1 worker receipt.
 target,algorithm=state['target'],state['algorithm']
 return dict(schema='mxr.production-real-target-binding/v005',target=target.__module__+'.'+target.__qualname__,
  sources=state['sources'],target_is_algorithm_core=target._forward_core is algorithm,
  Ascend_is_algorithm_core=state['ascend']._forward_core is algorithm,
  algorithm_counts_same=inspect.getclosurevars(algorithm).nonlocals.get('counts')is state['counts'],
  target_method_id=id(target._forward_core),algorithm_method_id=id(algorithm),native_method_id=id(state['native']),
  timed_extra_wrapper=False,diagnostic_capture=False,per_layer_file_writes=False,extra_synchronization=False)
def startup_gate(rows,source,qualification):
 need(len(rows)==4 and len({x['pid']for x in rows})==4,'four actual workers before measured interval')
 for row in rows:
  b=row['real_target_binding']
  need(row['source_ref']==source and row['qualification_ref']==qualification and row['mode']=='performance'and row['bindings_intact']is True,'actual same production worker/source/qualification')
  need(b['schema']=='mxr.production-real-target-binding/v005'and b['target_is_algorithm_core']is b['Ascend_is_algorithm_core']is b['algorithm_counts_same']is True and b['target_method_id']==b['algorithm_method_id'],'actual target uses exact algorithm core')
  need({k:v['sha256']for k,v in b['sources'].items()}==PINS,'actual target full source pins')
  need(len(row['prefix_counts'])==48 and all(v['candidate']>0 for v in row['prefix_counts'].values()),'real untimed warmup candidate hit all48, not allfallback')
  need(row['candidate_instances']and row['mapped_libraries'],'actual initialized candidate/kernel map after warmup')
 return True
