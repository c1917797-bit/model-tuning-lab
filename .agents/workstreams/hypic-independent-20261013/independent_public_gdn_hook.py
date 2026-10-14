"""Disabled-by-default canonical public GDN material producer hook."""
from contextvars import ContextVar
from pathlib import Path
import hashlib,inspect
from functools import wraps
_context=ContextVar("independent_public_gdn_context",default=None)
GDN_SHA256="d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"

def install_public_gdn_producer(*,enabled=False,select_public=None,publish=None):
    if not enabled:return lambda:None
    if not callable(select_public) or not callable(publish):
        raise ValueError("explicit public request selector and material sink required")
    import vllm_ascend.ops
    import vllm_ascend.ops.gdn as module
    from independent_runner_context import CURRENT_REQUEST_SLICES
    from independent_linear_public_builder import build_native_linear_public_body
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    cls=QwenGatedDeltaNetAttention
    if hashlib.sha256(Path(inspect.getfile(inspect.unwrap(cls._forward_core))).read_bytes()).hexdigest()!=GDN_SHA256:
        raise ValueError("official GDN source drift")
    original_core=cls._forward_core;original_chunk=module.chunk_gated_delta_rule
    if getattr(original_core,"_independent_public_owned",False):
        raise RuntimeError("public producer already installed")
    @wraps(original_core)
    def wrapped_core(self,mixed_qkv,b,a,core_attn_out):
        requests=CURRENT_REQUEST_SLICES.get()
        identity=select_public(self,requests) if requests else None
        if identity is None:return original_core(self,mixed_qkv,b,a,core_attn_out)
        if len(requests)!=1 or requests[0].computed_tokens!=0 or requests[0].scheduled_tokens!=identity.length:
            raise ValueError("canonical public request must be one complete zero-prefix prefill")
        if identity.layer!=self.prefix or identity.rank!=requests[0].rank:
            raise ValueError("canonical layer/rank mismatch")
        token=_context.set((identity,mixed_qkv))
        try:return original_core(self,mixed_qkv,b,a,core_attn_out)
        finally:_context.reset(token)
    def wrapped_chunk(*args,**kwargs):
        output=original_chunk(*args,**kwargs)
        context=_context.get()
        if context is not None:
            identity,projected=context
            # Official source invokes chunk with named q/k/v/g/beta fields.
            material=build_native_linear_public_body(
                identity,kwargs["k"],kwargs["v"],kwargs["g"],kwargs["beta"],
                output[0],projected)
            import torch
            torch.npu.synchronize()
            publish(material)
        return output
    wrapped_core._independent_public_owned=True
    cls._forward_core=wrapped_core;module.chunk_gated_delta_rule=wrapped_chunk
    def stop():
        if cls._forward_core is not wrapped_core or module.chunk_gated_delta_rule is not wrapped_chunk:
            raise RuntimeError("producer hook ownership changed")
        cls._forward_core=original_core;module.chunk_gated_delta_rule=original_chunk
    return stop
