"""Opt-in compact C2 paged KV repair and split causal query dispatch."""
from contextlib import ExitStack
from functools import wraps
from pathlib import Path
import hashlib,inspect


def install_compact_c2(stage,*,enabled=False,emit=None):
    if not enabled:return lambda:None
    if not callable(emit):raise ValueError('C2 evidence sink required')
    import torch
    from vllm_ascend.attention.attention_v1 import AscendAttentionBackendImpl as cls,AscendAttentionState
    from independent_compact_model_hook import CURRENT_COMPACT_MODEL
    from independent_runner_context import CURRENT_REQUEST_SLICES,CURRENT_PROMPT_TOKENS
    from independent_linear_material_pool import identity_key
    from independent_c2_cache_binding import bind_c2_cache
    from independent_c2_metadata import window_metadata
    from independent_c2_reference import relocate_keys
    from independent_kv_slots import install_private_kv_parts
    from independent_mixed_query_plan import NativeQueryPlan
    from independent_plan_material_identity import identity_for_plan
    original=cls.forward
    public_chunks={}
    if hashlib.sha256(Path(inspect.getfile(inspect.unwrap(original))).read_bytes()).hexdigest()!='80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390':
        raise ValueError('official C2 backend source drift')
    if getattr(original,'_independent_c2_owned',False) or getattr(original,'_independent_compact_c2_owned',False):
        raise RuntimeError('conflicting C2 hook')
    @wraps(original)
    def wrapped(self,layer,query,key,value,kv_cache,attn_metadata,output=None,
                output_scale=None,output_block_scale=None):
        selected=CURRENT_COMPACT_MODEL.get()
        requests=CURRENT_REQUEST_SLICES.get();prompts=CURRENT_PROMPT_TOKENS.get()
        def native():return original(self,layer,query,key,value,kv_cache,attn_metadata,output,output_scale,output_block_scale)
        if selected is None:
            if requests and len(requests)==1 and prompts and key is not None:
                req=requests[0]
                public_prompt=prompts.get(req.request_id)
                identity=stage.public_identity_for_request(layer.layer_name,req,public_prompt)
                if identity is not None:
                    cache_key=identity_key(identity)
                    with stage.compact_kv_store.lock:present=cache_key in stage.compact_kv_store.entries
                    if not present:
                        cut=stage.boundary
                        if stage.allow_public_chunks:
                            from independent_public_chunk_plan import public_chunk
                            from independent_public_chunk_kv import PublicChunkKV
                            chunk=public_chunk(req.computed_tokens,req.scheduled_tokens,
                                identity.length,boundary=identity.boundary_tokens)
                            assembly_key=(req.request_id,cache_key)
                            if assembly_key not in public_chunks:
                                if req.computed_tokens!=0 or len(public_chunks)>=64:
                                    raise ValueError("bounded zero-start KV producer required")
                                public_chunks[assembly_key]=PublicChunkKV(req.request_id,identity)
                            data=public_chunks[assembly_key].accept(req.request_id,identity,chunk,
                                key.reshape(key.shape[0],1,256),value.reshape(value.shape[0],1,256))
                            if data is not None:
                                generation=stage.compact_kv_store.publish(cache_key,data)
                                emit({'event':'compact_public_kv_published','rank':req.rank,
                                    'layer':layer.layer_name,'body_tokens':identity.length-cut,
                                    'tokens_sha256':identity.tokens_sha256,
                                    'producer_request_id':req.request_id,'chunked':True,
                                    'key':cache_key,'pool':'kv','generation':generation})
                                del public_chunks[assembly_key]
                            return native()
                        generation=stage.compact_kv_store.publish(cache_key,{
                            'keys':key.reshape(key.shape[0],1,256)[cut:identity.length].detach().to('cpu'),
                            'values':value.reshape(value.shape[0],1,256)[cut:identity.length].detach().to('cpu'),
                            'positions':torch.arange(cut,identity.length,dtype=torch.int64)})
                        emit({'event':'compact_public_kv_published','rank':req.rank,'layer':layer.layer_name,
                              'body_tokens':identity.length-cut,'tokens_sha256':identity.tokens_sha256,
                              'key':cache_key,'pool':'kv','generation':generation})
            return native()
        if key is None or value is None or output is None or attn_metadata is None:
            raise ValueError('compact C2 query/KV/output metadata absent')
        if output_scale is not None or output_block_scale is not None or self.num_kv_heads!=1 or self.head_size!=256:
            raise ValueError('selected BF16 compact C2 ABI mismatch')
        groups=[gid for gid,names in selected.attention_groups if layer.layer_name in names]
        if len(groups)!=1:raise ValueError('full-attention group association missing')
        group=groups[0];prepared=[];offset=0;all_slots=set()
        mixed=any(isinstance(p,NativeQueryPlan) for p in selected.plans)
        with ExitStack() as leases:
            for plan in selected.plans:
                caches=[c for c in selected.cache_slices if c.request_id==plan.request_id and c.group==group]
                owned=[slots for rid,gid,slots in selected.writable_kv_slots if rid==plan.request_id and gid==group]
                if len(caches)!=1 or len(owned)!=1:raise ValueError('request KV map/write lease absent')
                cache=caches[0]
                if all_slots.intersection(cache.slots):raise ValueError('cross-request scheduled KV alias')
                all_slots.update(cache.slots)
                binding=bind_c2_cache(plan,cache,writable_slots=owned[0])
                if isinstance(plan,NativeQueryPlan):
                    metas=tuple(window_metadata(attn_metadata,w,request_row=cache.row,
                        cache_hit_state=AscendAttentionState.PrefillCacheHit,
                        allow_mixed=mixed) for w in binding.windows)
                    prepared.append((plan,binding,None,offset,None,None,metas))
                    offset+=len(plan.retained_offsets)
                    continue
                generation,data=leases.enter_context(stage.compact_kv_store.acquire_private(
                    identity_key(identity_for_plan(stage,layer.layer_name,plan))))
                body_len=plan.skipped_tokens
                if data['keys'].shape!=(body_len,1,256) or data['values'].shape!=data['keys'].shape:
                    raise ValueError('cached body KV shape mismatch')
                positions=torch.arange(plan.computed_tokens+plan.body_start,
                    plan.computed_tokens+plan.body_end,device=query.device)
                inv=1.0/(10000000.0**(torch.arange(0,64,2,device=query.device).float()/64))
                k=relocate_keys(data['keys'].to(query.device),data['positions'].to(query.device),positions,inv)
                v=data['values'].to(query.device)
                if not torch.isfinite(k).all().item() or not torch.isfinite(v).all().item():
                    raise ValueError('nonfinite compact public KV')
                metas=tuple(window_metadata(attn_metadata,w,request_row=cache.row,
                    cache_hit_state=AscendAttentionState.PrefillCacheHit,
                    allow_mixed=mixed) for w in binding.windows)
                prepared.append((plan,binding,generation,offset,k,v,metas));offset+=len(plan.retained_offsets)
            if any(t.shape[0]!=offset for t in (query,key,value,output)):
                raise ValueError('compact C2 projected row coverage mismatch')
            if kv_cache is None or len(kv_cache)!=2:raise ValueError('native paged KV parts absent')
            for plan,binding,generation,base,k,v,metas in prepared:
                if not isinstance(plan,NativeQueryPlan):
                    install_private_kv_parts(kv_cache[0],kv_cache[1],k,v,
                        binding.body_slots,set(binding.body_slots))
                for w,meta in zip(binding.windows,metas):
                    span=slice(base+w.compact_start,base+w.compact_end)
                    original(self,layer,query[span],key[span],value[span],kv_cache,meta,output[span],None,None)
                torch.npu.synchronize()
                emit({'event':('mixed_native_c2_completed' if isinstance(plan,NativeQueryPlan)
                               else 'compact_c2_queries_completed'),'request_id':plan.request_id,
                    'rank':plan.rank,'step':plan.step,'layer':layer.layer_name,
                    'generation':generation,'retained_rows':len(plan.retained_offsets),
                    'skipped_body_queries':plan.skipped_tokens,'query_windows':len(binding.windows)})
        return output
    wrapped._independent_compact_c2_owned=True;cls.forward=wrapped
    def stop():
        if cls.forward is not wrapped:raise RuntimeError('compact C2 hook ownership changed')
        cls.forward=original
        public_chunks.clear()
    return stop
