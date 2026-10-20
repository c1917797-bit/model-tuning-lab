"""Only the first completed native pure-prefill SD tail, never spec history.

Installed causal_conv1d.h WriteBackState writes positions [0,K-1), using
stateLen solely as the slot stride. WriteBackStateSpec is a different path.
We therefore retain the complete real arena and expose only its leading
three positions to the already calibrated private width3 tree convolution.
No real arena bytes, including extra speculation bytes, are modified here.
"""
from dataclasses import dataclass
from model_entry import need, tensor_id
import functools, types


@dataclass(frozen=True)
class Tail:
 arena: object
 view: object
 slot: int
 metadata: object
 request: object
 request_id: str
 length: int
 arena_identity: tuple
 selected_before: object


def install_capture(worker, torch, C, *, get_forward_context, gdn_ref,
                    context_ref):
 """Observe the REAL original prefill write, not a simulated kernel result."""
 from model_entry import code_source
 code_source(C,get_forward_context,context_ref)
 saved=[]
 for layer in worker._bole_model_objects['inner'].layers:
  if layer.layer_type!='linear_attention':continue
  obj=layer.linear_attn;old=obj._forward_core;code_source(C,old,gdn_ref)
  native_module=__import__('inspect').getmodule(old.__func__)
  def core(this,mixed_qkv,b,a,core_attn_out,_old=old,_module=native_module):
   ctx=get_forward_context();mapping=ctx.attn_metadata
   if getattr(ctx,'in_profile_run',False)is True:
    return _old(mixed_qkv=mixed_qkv,b=b,a=a,core_attn_out=core_attn_out)
   meta=None if mapping is None else mapping[this.prefix]
   selected=(meta is not None and meta.num_prefills==1 and meta.num_decodes==0 and meta.num_spec_decodes==0 and meta.spec_sequence_masks is None)
   if not selected:return _old(mixed_qkv=mixed_qkv,b=b,a=a,core_attn_out=core_attn_out)
   need(type(meta)is _module.GDNAttentionMetadata,'real original native metadata')
   need(meta.num_actual_tokens>=3 and meta.prefill_query_start_loc.cpu().tolist()==[0,meta.num_actual_tokens]and
        meta.prefill_has_initial_state.cpu().tolist()==[False],
        'only first unchunked native pure prefill, no resumed state')
   runner=worker.model_runner;ids=[r for r in runner.input_batch.req_ids if r is not None]
   need(len(ids)==1 and runner.input_batch.req_id_to_index[ids[0]]==0 and ids[0]in runner.requests,'actual unique C1 request')
   slotids=meta.prefill_state_indices.cpu().tolist();need(len(slotids)==1,'one real recurrent slot')
   slot=slotids[0];arena=this.kv_cache[0]
   raw_tail=mixed_qkv[:meta.num_actual_tokens][-3:].clone()
   extra=arena[slot,3:].clone()
   result=_old(mixed_qkv=mixed_qkv,b=b,a=a,core_attn_out=core_attn_out)
   need(torch.equal(arena[slot,:3].contiguous().view(torch.uint8),raw_tail.contiguous().view(torch.uint8)),
        'actual native prefill leading chronology equals genuine projected last3 inputs')
   need(torch.equal(arena[slot,3:].contiguous().view(torch.uint8),extra.contiguous().view(torch.uint8)),
        'original native prefill did not modify extra speculative entries')
   this._bole_pure_prefill_observation=dict(metadata=meta,request=runner.requests[ids[0]],request_id=ids[0],
      slot=slot,length=meta.num_actual_tokens,arena_identity=tensor_id(arena),
      native_gdn_source=gdn_ref,raw_last3=raw_tail,extra_before=extra,
      actual_native_forward_returned=True)
   return result
  had='_forward_core'in obj.__dict__;prior=obj.__dict__.get('_forward_core')
  wrapped=types.MethodType(core,obj);obj._forward_core=wrapped;saved.append((obj,wrapped,had,prior))
 need(len(saved)==48,'installed exactly48 genuine native prefill observers')
 def restore():
  for obj,wrapped,had,prior in reversed(saved):
   need(obj._forward_core is wrapped,'native tail observer ownership')
   if had:obj._forward_core=prior
   else:delattr(obj,'_forward_core')
 return restore


def bind(torch, obj, meta, *, original_gdn_module, request, request_id,
         slot, length, native_prefill_returned):
 need(native_prefill_returned is True, 'only after original native forward returned')
 need(type(meta) is original_gdn_module.GDNAttentionMetadata,
      'actual GDNAttentionMetadata imported by frozen native GDN')
 need(meta.num_prefills == 1 and meta.num_decodes == 0 and
      meta.num_spec_decodes == 0 and meta.spec_sequence_masks is None,
      'C1 pure prefill, no speculative verification/accepted offset')
 need(type(slot) is int and slot >= 0 and type(length) is int and length > 0,
      'explicit real slot and completed prefix length')
 need(meta.num_actual_tokens == length and
      meta.prefill_query_start_loc.cpu().tolist() == [0,length] and
      meta.prefill_state_indices.cpu().tolist() == [slot] and
      meta.non_spec_state_indices_tensor.cpu().tolist() == [slot],
      'actual prefill token chronology and recurrent slot agree')
 convmeta=meta.non_spec_prefill_metadata.causal_conv1d
 indices=convmeta.cache_indices
 # Actual builder passes block_table_tensor for no-spec convolution. Kernel
 # ReadCacheIndexValue reads seq*cacheIndicesStride (the first column).
 need(indices.ndim in(1,2)and indices.shape[0]==1 and
      (indices.ndim==1 or indices.shape[1]>=1), 'actual one-row conv cache-index ABI')
 selected_indices=indices if indices.ndim==1 else indices[:,0]
 need(convmeta.query_start_loc.cpu().tolist() == [0,length] and
      selected_indices.cpu().tolist() == [slot],
      'actual native convolution and recurrent prefill selected same slot')
 arena=obj.kv_cache[0]
 observation=getattr(obj,'_bole_pure_prefill_observation',None)
 need(type(observation)is dict and observation['metadata']is meta and
      observation['request']is request and observation['request_id']==request_id and
      (observation['slot'],observation['length'])==(slot,length)and
      observation['actual_native_forward_returned']is True and
      observation['arena_identity']==tensor_id(arena),
      'actual original native prefill chronology observation required')
 need(torch.equal(arena[slot,:3].contiguous().view(torch.uint8),observation['raw_last3'].contiguous().view(torch.uint8))and
      torch.equal(arena[slot,3:].contiguous().view(torch.uint8),observation['extra_before'].contiguous().view(torch.uint8)),
      'observed native prefill chronology and extra bytes still current')
 need(arena.ndim == 3 and arena.shape[1] >= 3 and arena.shape[2] == 2560 and
      arena.dtype == torch.bfloat16 and 0 <= slot < arena.shape[0],
      'actual calibrated SD channels and sufficient full arena width')
 need(arena.stride(2)==1 and arena.stride(1)==2560 and
      arena.stride(0)>=arena.shape[1]*2560,
      'nonoverlapping actual SD arena, no DS or transposed alias')
 need(tuple(obj.conv1d.weight.shape)[-1] == 4 and obj.conv1d.bias is None,
      'actual native width4/no-bias family')
 view=arena[:,:3,:]
 return Tail(arena,view,slot,meta,request,request_id,length,
             tensor_id(arena),arena[slot:slot+1].clone())


def unchanged(torch, tail, *, obj, request, request_id, slot, length):
 need(type(tail) is Tail and tail.arena is obj.kv_cache[0] and
      tail.request is request and tail.request_id == request_id and
      (tail.slot,tail.length) == (slot,length), 'same genuine request/arena window')
 need(tensor_id(tail.arena)==tail.arena_identity and
      torch.equal(tail.arena[slot:slot+1].contiguous().view(torch.uint8),
                  tail.selected_before.contiguous().view(torch.uint8)),
      'entire selected native conv slot including extra spec bytes unchanged')
 return tail.view
