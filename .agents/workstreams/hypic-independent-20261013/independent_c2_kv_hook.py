"""Disabled C2 canonical KV capture and private text-position relocation."""
from functools import wraps
from pathlib import Path
import hashlib,inspect
def install_c2_kv(stage,*,enabled=False,emit=None):
    if not enabled:return lambda:None
    if not callable(emit):raise ValueError("C2 evidence sink required")
    import torch
    from vllm_ascend.attention.attention_v1 import AscendAttentionBackendImpl as cls
    from independent_runner_context import CURRENT_REQUEST_SLICES,CURRENT_PROMPT_TOKENS
    from independent_segment_selection import select_segment,require_full_scheduled_segment
    from independent_linear_material_pool import identity_key
    from independent_c2_reference import relocate_keys
    from independent_public_pool import PublicPool
    if hashlib.sha256(Path(inspect.getfile(cls)).read_bytes()).hexdigest()!="80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390":
        raise ValueError("official full-attention source drift")
    pool=PublicPool(stage.store.pool.capacity//4)
    original=cls.forward
    if getattr(original,"_independent_c2_owned",False):raise RuntimeError("C2 already installed")
    @wraps(original)
    def wrapped(self,layer,query,key,value,kv_cache,attn_metadata,output=None,
                output_scale=None,output_block_scale=None):
        def native(k=key,v=value):
            return original(self,layer,query,k,v,kv_cache,attn_metadata,output,
                            output_scale,output_block_scale)
        reqs=CURRENT_REQUEST_SLICES.get();prompts=CURRENT_PROMPT_TOKENS.get()
        if key is None or value is None or not reqs or len(reqs)!=1 or prompts is None or attn_metadata is None:
            return native()
        req=reqs[0];tokens=prompts.get(req.request_id)
        if tokens is None or req.computed_tokens or req.scheduled_tokens!=len(tokens):
            return native()
        # Selected27B text-only model: local KV head1, head256, rotary64.
        keys=key.reshape(key.shape[0],-1,256);values=value.reshape(value.shape[0],-1,256)
        if keys.shape[1:]!=(1,256) or keys.dtype!=torch.bfloat16:
            raise ValueError("selected model C2 KV shape/dtype mismatch")
        identity=stage.identity(layer.layer_name,req.rank);cache_key=identity_key(identity)
        if tokens==stage.tokens:
            with pool.lock:present=cache_key in pool.entries
            if not present:
                cut=stage.boundary
                pool.publish(cache_key,{"keys":keys[cut:len(tokens)],
                    "values":values[cut:len(tokens)],
                    "positions":torch.arange(cut,len(tokens),device=key.device)})
                emit({"event":"public_c2_kv_published","rank":req.rank,"layer":layer.layer_name,
                      "body_tokens":len(tokens)-cut,"tokens_sha256":identity.tokens_sha256})
            return native()
        try:
            selected=select_segment(tokens,stage.tokens)
            require_full_scheduled_segment(selected,req)
        except ValueError:return native()
        with pool.lock:present=cache_key in pool.entries
        if not present:return native()
        lo=selected.start+stage.boundary;hi=selected.end
        with pool.acquire_private(cache_key) as (generation,data):
            inv=1.0/(10000000.0**(torch.arange(0,64,2,device=key.device).float()/64))
            positions=torch.arange(lo,hi,device=key.device)
            relocated=relocate_keys(data["keys"],data["positions"],positions,inv)
            private_k=keys.clone();private_v=values.clone()
            private_k[lo:hi]=relocated;private_v[lo:hi]=data["values"]
            if not torch.isfinite(private_k).all().item() or not torch.isfinite(private_v).all().item():
                raise ValueError("nonfinite C2 relocation")
            result=native(private_k.reshape_as(key),private_v.reshape_as(value))
            torch.npu.synchronize()
            emit({"event":"private_c2_kv_reused","request_id":req.request_id,
                  "rank":req.rank,"step":req.step,"layer":layer.layer_name,
                  "generation":generation,"body_tokens":hi-lo,"finite":True,
                  "projection_skipped":False,"attention_queries_skipped":False})
            return result
    wrapped._independent_c2_owned=True;cls.forward=wrapped
    def stop():
        if cls.forward is not wrapped:raise RuntimeError("C2 hook ownership changed")
        cls.forward=original
    return stop
