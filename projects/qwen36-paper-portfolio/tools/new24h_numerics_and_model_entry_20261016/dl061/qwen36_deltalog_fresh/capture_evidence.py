"""Diagnosis-only native-call/initial-input evidence. No changed arithmetic."""
import hashlib
import inspect
import os
import dataclasses
from pathlib import Path

CHUNK_SHA='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'

def need(x,message):
 if not x:raise RuntimeError(message)

def file_ref(path):
 p=Path(path).resolve();data=p.read_bytes()
 return dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

def tensor_fingerprint(torch,tensor):
 cpu=tensor.detach().cpu().contiguous()
 return dict(dtype=str(cpu.dtype),shape=list(cpu.shape),
             sha256=hashlib.sha256(cpu.view(torch.uint8).numpy().tobytes()).hexdigest())

def controls(torch,kwargs):
 need(set(kwargs)=={'q','k','v','g','beta','initial_state','cu_seqlens','use_qk_l2norm_in_kernel','output_final_state','head_first','prebuilt_meta'},'actual pinned GDN402 keyword inventory')
 need(kwargs['output_final_state'] is True and kwargs['head_first'] is False,'actual full-state/non-head-first GDN controls')
 meta=kwargs['prebuilt_meta'];need(dataclasses.is_dataclass(meta) and type(meta).__name__=='GDNChunkedPrefillMetadata','real official chunk metadata class')
 module=inspect.getmodule(type(meta));source=file_ref(module.__file__)
 need(source['sha256']=='42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16','actual official metadata class source')
 names=('cu_seqlens_host','chunk_indices_chunk64_host','chunk_indices_chunk64','chunk_offsets_chunk64','update_chunk_offsets_chunk64','final_chunk_indices_chunk64','chunk_indices_large_block','block_indices_cumsum','num_decodes','cu_seqlens_kern','keep_meta')
 need({f.name for f in dataclasses.fields(meta)}==set(names),'bounded official metadata fields')
 def value(v):
  if v is None:return dict(kind='none')
  if type(v) in (bool,int):return dict(kind=type(v).__name__,value=v)
  if isinstance(v,torch.Tensor):
   need(v.numel()<=1024 and v.dtype in (torch.int32,torch.int64,torch.bool),'bounded chunk index metadata tensor')
   return dict(kind='tensor',fingerprint=tensor_fingerprint(torch,v),values=v.cpu().tolist(),device=str(v.device),data_ptr=v.data_ptr())
  if type(v) is tuple:
   need(len(v)<=1024 and all(type(x) is int for x in v),'bounded native host index tuple')
   return dict(kind='tuple',values=list(v))
  raise RuntimeError('unknown native metadata value')
 return dict(output_final_state=True,head_first=False,metadata_class=type(meta).__module__+'.'+type(meta).__qualname__,metadata_source=source,metadata={n:value(getattr(meta,n)) for n in names})

def callable_proof(original,gdn,chunk,count):
 need(original is gdn.chunk_gated_delta_rule is chunk.chunk_gated_delta_rule,'actual native chunk aliases changed')
 source=file_ref(chunk.__file__);need(source['sha256']==CHUNK_SHA,'actual native chunk source drift')
 chain=[];seen=set();current=original
 for unused in range(16):
  need(id(current) not in seen,'native wrapper cycle');seen.add(id(current))
  code=getattr(current,'__code__',None)
  chain.append(dict(object_id=id(current),module=getattr(current,'__module__',None),
                    qualname=getattr(current,'__qualname__',None),
                    code_file=None if code is None else str(Path(code.co_filename).resolve()),
                    first_line=None if code is None else code.co_firstlineno))
  if not hasattr(current,'__wrapped__'):break
  current=current.__wrapped__
 else:raise RuntimeError('native unwrap chain >16')
 unwrapped=inspect.unwrap(original)
 need(current is unwrapped and getattr(unwrapped,'__code__',None) is not None,'actual native callable code required')
 need(Path(unwrapped.__code__.co_filename).resolve()==Path(source['path']),'unwrapped native chunk not actual source')
 return dict(schema='deltalog.native-chunk-callable/v030',pid=os.getpid(),counter=count,
             original_id=id(original),gdn_alias_id=id(gdn.chunk_gated_delta_rule),chunk_alias_id=id(chunk.chunk_gated_delta_rule),
             original_module=getattr(original,'__module__',None),module_file=source,
             unwrapped_id=id(unwrapped),unwrap_chain=chain)

def begin(torch,original,gdn,chunk,count,args,kwargs,raw_inputs):
 need(not args,'reviewed chunk keyword ABI only')
 proof=callable_proof(original,gdn,chunk,count)
 names=('q','k','v','g','beta','initial_state','cu_seqlens','use_qk_l2norm_in_kernel')
 need(set(raw_inputs)==set(names),'complete actual chunk operand capture')
 operands={}
 for name in names:
  value=kwargs[name]
  if isinstance(value,torch.Tensor):
   need(value.device.type=='npu','real native chunk device operand')
   operands[name]=dict(device=str(value.device),data_ptr=value.data_ptr(),storage_offset=value.storage_offset(),
    stride=list(value.stride()),actual=tensor_fingerprint(torch,value),captured=tensor_fingerprint(torch,raw_inputs[name]))
   need(operands[name]['actual']==operands[name]['captured'],'captured chunk input differs from actual argument')
  else:
   need(value is raw_inputs[name] and type(value) is bool,'actual chunk non-tensor operand')
   operands[name]=dict(value=value)
 proof['operands']=operands;proof['controls']=controls(torch,kwargs);return proof

def finish(torch,original,gdn,chunk,count,before,value,kwargs):
 after=callable_proof(original,gdn,chunk,count)
 need(after['counter']==before['counter']+1 and after['pid']==before['pid'],'native dispatch counter')
 need(all(after[key]==before[key] for key in ('original_id','gdn_alias_id','chunk_alias_id','module_file','unwrapped_id','unwrap_chain')),'native callable changed across actual invocation')
 after['controls']=controls(torch,kwargs);need(after['controls']==before['controls'],'actual native control metadata mutated across call')
 after['input_fingerprints']={name:tensor_fingerprint(torch,kwargs[name]) for name,op in before['operands'].items() if 'actual' in op}
 need(all(value==before['operands'][name]['actual'] for name,value in after['input_fingerprints'].items()),'actual native tensor input mutated across call')
 need(isinstance(value,(list,tuple)) and len(value)==2,'native chunk output/state pair')
 return dict(schema='deltalog.native-chunk-dispatch/v030',before=before,after=after,
             returned_output=tensor_fingerprint(torch,value[0]),returned_state=tensor_fingerprint(torch,value[1]),
             actual_original_call_returned=True)

def initial(torch,initial,conv_initial,state,native,pointers,batch,fixture_file,config_file):
 # CPU inputs were generated before candidate allocation/dispatch, and never
 # derived by reversing candidate state. Record both inputs and actual loading.
 return dict(schema='deltalog.independent-initial-anchor/v030',batch=batch,seed=2610165101+batch,
             fixture_source=file_ref(fixture_file),config_source=file_ref(config_file),
             geometry=dict(slots=2*batch+4,key_heads=4,value_heads=12,key_dim=128,value_dim=128,conv_dim=2560),
             generated_base=initial.clone(),generated_conv=conv_initial.clone(),
             candidate_state={k:v.cpu().clone() for k,v in state.items()},native_initial=native.cpu().clone(),
             pointer_identity=dict(pointers),pid=os.getpid(),before_any_candidate_dispatch=True)
