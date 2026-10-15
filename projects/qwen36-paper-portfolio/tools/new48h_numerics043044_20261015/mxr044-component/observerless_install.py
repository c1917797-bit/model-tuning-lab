"""Source-bound actual chunk/solve monkeypatch; defaultOFF; no observer tensors."""
import atexit,contextvars,functools,hashlib,importlib,inspect,json,os
from pathlib import Path
PINS={
 'vllm_ascend.ops.gdn':'d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816',
 'vllm_ascend.ops.triton.fla.chunk':'6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5',
 'vllm_ascend.ops.triton.fla.solve_tril':'2d8cd5d3bd365fa5894c7ee0cddc106d1d2b34dd3f3e05f4dbf15e8010d89fc0',
 'vllm_ascend.ops.gdn_attn_builder':'42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16'}
_installed=None
EVENT_GATE={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-mxr-event-single6-owned-main-NEW48H_053_NPU_001/physical6/numeric/RESULT.json','bytes':2116,'sha256':'91cf2b49724681a4c4a095c5ed3d6ee8e2570f8f88c5bb046790d6edfb2c021e'}
def need(v,m):
 if not v:raise ValueError(m)
def checked(ref):
 need(type(ref)is dict and set(ref)=={'path','bytes','sha256'},'complete exact reference')
 p=Path(ref['path']);need(p.is_absolute()and p.is_file()and not p.is_symlink(),'ordinary source/reference')
 b=p.read_bytes();need(len(b)==ref['bytes']and hashlib.sha256(b).hexdigest()==ref['sha256'],'whole exact bytes')
 return b
def load(ref,name):
 checked(ref);s=importlib.util.spec_from_file_location(name,ref['path']);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def qualification(ref):
 q=json.loads(checked(ref))
 own=json.loads(os.environ['MXR_OBSERVERLESS_SOURCE_REF']);mf=json.loads(checked(own))
 need(mf.get('schema')=='mxr.observerless-source/v1'and mf.get('root')==str(Path(__file__).resolve().parent)and mf.get('default_enabled')is False,'actual own plugin source')
 for name,item in mf['files'].items():
  need(item['path']==str(Path(__file__).resolve().parent/name),'own complete leaf identity');checked(item)
 need(q.get('plugin_source_ref')==own,'qualification is for this exact plugin source')
 need(q.get('schema')=='mxr.observerless-qualification/v1'and q.get('source_pins')==PINS,'actual source-bound qualification contract')
 need(q.get('mode')in('correctness','performance')and q.get('physical')==[4,5,6,7],'MAIN actual TP4 scope')
 # Event receipt itself is produced by real independent child, not software.
 need(q['event_numeric_ref']==EVENT_GATE,'actual053 immutable Event result identity')
 ev=json.loads(checked(q['event_numeric_ref']))
 need(ev.get('schema')=='mxr.event-single6-qualified/v1'and ev.get('NPU')is True
      and ev.get('lifecycle_gate_pass')is True and ev.get('independent_gate_pass')is True,'actual Event+independent qualified output')
 need(type(q.get('lengths'))is list and q['lengths']and all(type(t)is int and 1<t<=40960 for t in q['lengths']),'bounded lengths')
 need(q.get('pool_bytes')==512*1024**2 and q.get('pool_entries')==2,'frozen512MiB/2 pressure bound')
 if q['mode']=='performance':
  from admission import verify_derived
  verify_derived(q['full_numeric_ref'],own)
  full=json.loads(checked(q['full_numeric_ref']))
  need(full.get('schema')=='mxr.observerless-full-gdn-independent/v1'
       and full.get('full_GDN')is full.get('multistep_state')is full.get('source_qualified')is full.get('pass')is True
       and full.get('source_pins')==PINS and set(q['lengths'])<=set(full.get('lengths',[]))
       and full.get('plugin_source_ref')==own
       and full.get('graph_candidate')is False and full.get('inference_metadata_lifecycle_pass')is True,'actual fullGDN/state/length independent gate before performance')
 need(q.get('prefixes')is None if q['mode']=='correctness'else type(q.get('prefixes'))is list and len(set(q['prefixes']))==48,'actual48layer declaration for performance')
 return q
def install():
 global _installed
 if os.environ.get('MXR_OBSERVERLESS_ENABLE')!='1':return None
 if _installed is not None:return _installed
 q=qualification(json.loads(os.environ['MXR_OBSERVERLESS_QUALIFICATION_REF']))
 modules={}
 for name,digest in PINS.items():
  module=importlib.import_module(name);p=Path(inspect.getsourcefile(module)).resolve()
  need(hashlib.sha256(p.read_bytes()).hexdigest()==digest,'actual installed source '+name);modules[name]=module
 import torch
 import torch_npu
 from metadata_association import Associations
 from metadata_certificate import certificate,consume
 from eager_receiver import make_receiver
 from event_backend import EventBackend
 from lifetime import KeepalivePool
 for name in('metadata_association','metadata_certificate','eager_receiver','event_backend','lifetime','block_refine','production_binding'):
  support=importlib.import_module(name);need(Path(support.__file__).resolve()==Path(__file__).resolve().parent/(name+'.py'),'exact current runtime module, no stale sibling '+name)
 gdn=modules['vllm_ascend.ops.gdn'];chunk=modules['vllm_ascend.ops.triton.fla.chunk'];sm=modules['vllm_ascend.ops.triton.fla.solve_tril'];builder=modules['vllm_ascend.ops.gdn_attn_builder']
 original_solve=chunk.solve_tril;original_fwd=chunk.chunk_gated_delta_rule_fwd
 original_core=gdn.AscendGatedDeltaNetAttention._forward_core
 original_attach=builder.AscendGDNAttentionMetadataBuilder._attach_non_spec_prefill_metadata
 original_producer=builder._build_non_spec_chunked_prefill_metadata
 need(original_solve is sm.solve_tril and original_fwd.__globals__ is vars(chunk),'real unpatched chunk solve seam')
 for fn,name in ((original_solve,'vllm_ascend.ops.triton.fla.solve_tril'),(original_fwd,'vllm_ascend.ops.triton.fla.chunk'),(original_core,'vllm_ascend.ops.gdn'),(original_attach,'vllm_ascend.ops.gdn_attn_builder'),(original_producer,'vllm_ascend.ops.gdn_attn_builder')):
  need(inspect.getsourcefile(inspect.unwrap(fn))==inspect.getsourcefile(modules[name]),'genuine pinned callable before patch')
 # Same actual039 compensated9arg loader, source/build validated independently.
 prerequisite=load(q['prerequisite_source_ref'],'_mxr_observerless_prerequisite')
 passed=prerequisite.gate(q['prerequisite_ref'])
 component=json.loads(checked(passed['source']))
 adapter=load(component['files']['adapter.py'],'_mxr_observerless_actual037_adapter')
 solvers={};pools={};backends={};assoc=Associations();prefixes_seen=set();prefix_counts={}
 prefix=contextvars.ContextVar('mxr_actual_gdn_prefix',default=None);cert=contextvars.ContextVar('mxr_actual_metadata',default=None)
 def solver_for(device):
  if device not in solvers:
   _,_,candidate=adapter.instances(torch,passed['source'],passed['build'],torch.device(device))
   solvers[device]=candidate
  return solvers[device]
 def pool_for(device):
  if device not in pools:pools[device]=KeepalivePool(q['pool_bytes'],q['pool_entries'])
  return pools[device]
 def backend_for(device):
  if device not in backends:backends[device]=EventBackend(torch,torch_npu)
  return backends[device]
 query=getattr(torch.npu,'is_current_stream_capturing',None);need(callable(query),'actual graphquery')
 def metadata(A,cu,indices,dtype):return consume(cert.get(),A,cu,indices,dtype)
 solve,counts=make_receiver(original_solve,torch,solver_for,pool_for,backend_for,
                           lambda:prefix.get()is not None,metadata,query,enabled=True)
 attach_sig=inspect.signature(original_attach);fwd_sig=inspect.signature(original_fwd)
 @functools.wraps(original_producer)
 def producer(*a,**kw):
  out=original_producer(*a,**kw);assoc.produced(out);return out
 @functools.wraps(original_attach)
 def attach(*a,**kw):
  bound=attach_sig.bind(*a,**kw);bound.apply_defaults();out=original_attach(*a,**kw)
  x=bound.arguments;assoc.attach(x['chunk_metadata'],out.prefill_query_start_loc)
  return out
 @functools.wraps(original_core)
 def core(self,*a,**kw):
  prefixes_seen.add(self.prefix)
  token=prefix.set(self.prefix if q['prefixes']is None or self.prefix in q['prefixes']else None)
  before=dict(counts)
  try:return original_core(self,*a,**kw)
  finally:
   row=prefix_counts.setdefault(self.prefix,dict(candidate=0,native=0,core=0));row['core']+=1
   for name in ('candidate','native'):row[name]+=counts[name]-before[name]
   prefix.reset(token)
 @functools.wraps(original_fwd)
 def fwd(*a,**kw):
  need(chunk.solve_tril is solve,'worker solve binding drift')
  x=fwd_sig.bind(*a,**kw);x.apply_defaults();v=x.arguments;meta=v.get('prebuilt_meta');cu=v.get('cu_seqlens')
  c=None
  from vllm.distributed import get_pcp_group
  if prefix.get()is not None and not query()and get_pcp_group().world_size==1 and assoc.verified(meta,cu,prefix.get()):
   c=certificate(meta,cu,v['q'].shape[1],prefix.get(),q['lengths'])
  token=cert.set(c)
  try:return original_fwd(*a,**kw)
  finally:cert.reset(token)
 def drain():
  # Outside timed requests; failure must stay failure, no forced buffer release.
  return {device:pool.finish()for device,pool in pools.items()}
 builder._build_non_spec_chunked_prefill_metadata=producer
 builder.AscendGDNAttentionMetadataBuilder._attach_non_spec_prefill_metadata=attach
 gdn.AscendGatedDeltaNetAttention._forward_core=core
 chunk.chunk_gated_delta_rule_fwd=fwd
 chunk.solve_tril=sm.solve_tril=solve
 from production_binding import bind_actual,snapshot as binding_snapshot
 real_target=bind_actual(gdn,counts,core)
 from worker_receipt import install as install_receipt
 def snapshot():
  return dict(real_target_binding=binding_snapshot(real_target),counts=dict(counts),prefix_counts={k:dict(v)for k,v in prefix_counts.items()},prefixes_seen=sorted(prefixes_seen),mode=q['mode'],source_pins=PINS,graph_candidate=False,
   bindings_intact=chunk.solve_tril is solve and sm.solve_tril is solve and chunk.chunk_gated_delta_rule_fwd is fwd and gdn.AscendGatedDeltaNetAttention._forward_core is core,
   candidate_instances=[v.experiment_identity for v in solvers.values()],mapped_libraries=[line for line in Path('/proc/self/maps').read_text().splitlines()if 'libmxr_diag16_defect_MEMORY_BASE.so'in line],source_component=passed['source'],source_build=passed['build'])
 install_receipt(snapshot)
 atexit.register(drain)
 _installed=dict(counts=counts,drain=drain,mode=q['mode'],source_pins=PINS,pools=pools,prefixes_seen=prefixes_seen,
                 formal_performance_qualified=q['mode']=='performance',graph_candidate=False,real_target_binding=real_target)
 return _installed
