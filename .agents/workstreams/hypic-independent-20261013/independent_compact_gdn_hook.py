"""Source-bound compact C1 core hook. Defaults disabled; model selection required."""
from contextlib import ExitStack
from functools import wraps
from pathlib import Path
import hashlib,inspect


def install_compact_gdn(stage,*,enabled=False,emit=None):
    if not enabled:return lambda:None
    if not callable(emit):raise ValueError('compact evidence sink required')
    import torch
    from vllm.forward_context import get_forward_context
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention as cls
    from independent_runner_context import CURRENT_REQUEST_SLICES
    from independent_compact_model_hook import CURRENT_COMPACT_MODEL
    from independent_runtime_adapter import associate_native_linear
    from independent_native_boundary import make_boundary_runner
    from independent_compact_linear import execute_compact_linear
    from independent_compact_material_pool import CompactLinearMaterialPool
    if not isinstance(stage.compact_store,CompactLinearMaterialPool):
        raise ValueError('compact CPU material store required')
    original=cls._forward_core
    if hashlib.sha256(Path(inspect.getfile(inspect.unwrap(original))).read_bytes()).hexdigest()!='d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816':
        raise ValueError('official GDN source drift')
    if getattr(original,'_independent_private_owned',False) or getattr(original,'_independent_compact_gdn_owned',False):
        raise RuntimeError('conflicting C1 core hook')
    @wraps(original)
    def wrapped(self,mixed_qkv,b,a,core_attn_out):
        selected=CURRENT_COMPACT_MODEL.get()
        if selected is None:return original(self,mixed_qkv,b,a,core_attn_out)
        requests=CURRENT_REQUEST_SLICES.get();plans=selected.plans
        if not requests or len(requests)!=len(plans):
            raise ValueError('compact/native request coverage missing')
        for req,plan in zip(requests,plans):
            if (req.request_id,req.rank,req.step,req.token_start,req.scheduled_tokens)!=(plan.request_id,plan.rank,plan.step,plan.token_start,plan.scheduled_tokens):
                raise ValueError('compact/native request identity drift')
        raw=get_forward_context().attn_metadata
        if not isinstance(raw,dict) or self.prefix not in raw:
            raise ValueError('native linear metadata absent')
        associations=associate_native_linear(self,requests,raw[self.prefix])
        total=sum(len(p.retained_offsets) for p in plans)
        if any(x.shape[0]!=total for x in (mixed_qkv,b,a,core_attn_out)):
            raise ValueError('compact GDN projected row coverage mismatch')
        conv_cache,state_cache=self.kv_cache[:2];prepared=[];offset=0
        with ExitStack() as leases:
            for plan,assoc in zip(plans,associations):
                expected=stage.identity(self.prefix,plan.rank)
                generation,material=leases.enter_context(
                    stage.compact_store.acquire_private(expected,device=mixed_qkv.device))
                slot=assoc.state_slot
                state=state_cache[slot].transpose(-1,-2).contiguous().clone()
                tail=conv_cache[slot].clone()
                if not assoc.has_initial_state:state.zero_();tail.zero_()
                base=offset
                def live(lo,hi,incoming,conv):
                    span=slice(base+lo,base+hi)
                    return make_boundary_runner(self,mixed_qkv[span],b[span],a[span],conv,
                                                return_conv=True)(incoming)
                output,final,tail=execute_compact_linear(material,expected,plan,state,tail,run_live=live)
                native=final.transpose(-1,-2).contiguous()
                end=offset+len(plan.retained_offsets)
                if native.shape!=state_cache[slot].shape or tail.shape!=conv_cache[slot].shape or output.shape!=core_attn_out[offset:end].shape:
                    raise ValueError('compact GDN native commit layout mismatch')
                prepared.append((plan,slot,generation,offset,end,output,native,tail));offset=end
            if CURRENT_COMPACT_MODEL.get() is not selected or CURRENT_REQUEST_SLICES.get() is not requests:
                raise RuntimeError('request context changed before compact commit')
            # Every request is prepared before the first native state write.
            for plan,slot,generation,start,end,output,native,tail in prepared:
                state_cache[slot].copy_(native.to(state_cache.dtype))
                conv_cache[slot].copy_(tail.to(conv_cache.dtype))
                core_attn_out[start:end].copy_(output.to(core_attn_out.dtype))
            torch.npu.synchronize()
            for plan,slot,generation,start,end,output,native,tail in prepared:
                emit({'event':'compact_gdn_body_composed','request_id':plan.request_id,
                    'rank':plan.rank,'step':plan.step,'layer':self.prefix,'slot':slot,
                    'generation':generation,'retained_rows':end-start,
                    'skipped_body_tokens':plan.skipped_tokens,'finite':True})
        return None
    wrapped._independent_compact_gdn_owned=True;cls._forward_core=wrapped
    def stop():
        if cls._forward_core is not wrapped:raise RuntimeError('compact GDN hook ownership changed')
        cls._forward_core=original
    return stop
