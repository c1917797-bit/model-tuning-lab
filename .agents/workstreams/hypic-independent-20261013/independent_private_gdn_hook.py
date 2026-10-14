"""Disabled-by-default request-local C1 GDN serving reuse. C2 is not enabled."""
from functools import wraps
from contextlib import ExitStack
import hashlib,inspect
from pathlib import Path

def install_private_c1(stage,*,enabled=False,emit=None):
    if not enabled:return lambda:None
    if not callable(emit):raise ValueError("private C1 evidence sink required")
    import torch
    from vllm.forward_context import get_forward_context
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention as cls
    from independent_runner_context import CURRENT_REQUEST_SLICES,CURRENT_PROMPT_TOKENS
    from independent_segment_selection import select_segment,require_full_scheduled_segment
    from independent_runtime_adapter import associate_native_linear
    from independent_native_boundary import make_boundary_runner
    from independent_private_linear import execute_private_linear
    from independent_linear_material_pool import identity_key
    from independent_prefill_batch import plan_prefill_batch,stage_prefill_batch
    original=cls._forward_core
    if hashlib.sha256(Path(inspect.getfile(inspect.unwrap(original))).read_bytes()).hexdigest()!="d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816":
        raise ValueError("private GDN source drift")
    if getattr(original,"_independent_private_owned",False):
        raise RuntimeError("private C1 already installed")
    @wraps(original)
    def wrapped(self,mixed_qkv,b,a,core_attn_out):
        requests=CURRENT_REQUEST_SLICES.get();prompts=CURRENT_PROMPT_TOKENS.get()
        if not requests or prompts is None:
            return original(self,mixed_qkv,b,a,core_attn_out)
        metadata=get_forward_context().attn_metadata
        if metadata is None:return original(self,mixed_qkv,b,a,core_attn_out)
        meta=metadata[self.prefix]
        if meta.num_prefills!=len(requests) or meta.num_decodes or meta.spec_sequence_masks is not None:
            return original(self,mixed_qkv,b,a,core_attn_out)
        def present(identity):
            with stage.store.pool.lock:return identity_key(identity) in stage.store.pool.entries
        plans=plan_prefill_batch(requests,prompts,stage.tokens,
            lambda req:stage.identity(self.prefix,req.rank),present)
        if plans is None:
            return original(self,mixed_qkv,b,a,core_attn_out)
        associations=associate_native_linear(self,requests,meta)
        conv_cache,state_cache=self.kv_cache[:2]
        with ExitStack() as leases:
            def prepare(plan,association):
                req,selected,expected=plan;slot=association.state_slot
                state=state_cache[slot].transpose(-1,-2).contiguous().clone()
                conv=conv_cache[slot].clone()
                if not association.has_initial_state:state.zero_();conv.zero_()
                def live(lo,hi,incoming,tail):
                    span=slice(req.token_start+lo,req.token_start+hi)
                    return make_boundary_runner(self,mixed_qkv[span],b[span],a[span],tail,
                                                return_conv=True)(incoming)
                generation,material=leases.enter_context(stage.store.acquire_private(expected))
                output,final,tail=execute_private_linear(
                    material,expected,selected,req,state,conv,run_live=live)
                native=final.transpose(-1,-2).contiguous()
                target=core_attn_out[req.token_start:req.token_end]
                if native.shape!=state_cache[slot].shape or tail.shape!=conv_cache[slot].shape or output.shape!=target.shape:
                    raise ValueError('private commit layout mismatch')
                if not all(torch.isfinite(t).all().item() for t in (output,native,tail)):
                    raise ValueError('nonfinite private C1 result')
                return req,selected,expected,slot,generation,output,native,tail
            # All requests finish and validate before ANY native slot is written.
            prepared=stage_prefill_batch(plans,associations,prepare)
            if CURRENT_REQUEST_SLICES.get() is not requests:
                raise RuntimeError("request step context changed before commit")
            for req,selected,expected,slot,generation,output,native,tail in prepared:
                state_cache[slot].copy_(native.to(state_cache.dtype))
                conv_cache[slot].copy_(tail.to(conv_cache.dtype))
                core_attn_out[req.token_start:req.token_end].copy_(output.to(core_attn_out.dtype))
            torch.npu.synchronize()
            for req,selected,expected,slot,generation,output,native,tail in prepared:
                emit({"event":"private_c1_reused","request_id":req.request_id,
                      "rank":req.rank,"step":req.step,"layer":self.prefix,
                      "slot":slot,"generation":generation,"segment_start":selected.start,
                      "segment_end":selected.end,"skipped_body_tokens":expected.length-expected.boundary_tokens,
                      "batch_size":len(prepared),"finite":True,
                      "c2_enabled":bool(getattr(stage,"c2_enabled",False))})
        return None
    wrapped._independent_private_owned=True
    cls._forward_core=wrapped
    def stop():
        if cls._forward_core is not wrapped:raise RuntimeError("private hook ownership changed")
        cls._forward_core=original
    return stop
