"""Disabled-by-default canonical public GDN material producer hook."""
from contextvars import ContextVar
from pathlib import Path
import hashlib,inspect
from functools import wraps
_context=ContextVar("independent_public_gdn_context",default=None)
GDN_SHA256="d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"

def prefix_material_inputs(length,projected,fields):
    if type(length) is not int or length<1 or projected.ndim!=2 or projected.shape[0]<length:
        raise ValueError("public prefix projected coverage mismatch")
    tensors=[]
    for name in ("k","v","g","beta"):
        value=fields[name]
        if value.ndim<2 or value.shape[0]!=1 or value.shape[1]<length:
            raise ValueError("public prefix field coverage mismatch")
        tensors.append(value[:,:length].contiguous())
    return (*tensors,projected[:length].contiguous())

def install_public_gdn_producer(*,enabled=False,select_public=None,publish=None,compact=False,allow_chunks=False):
    if not enabled:return lambda:None
    if not callable(select_public) or not callable(publish):
        raise ValueError("explicit public request selector and material sink required")
    if type(allow_chunks) is not bool or (allow_chunks and not compact):
        raise ValueError("chunk capture requires explicit compact mode")
    accumulators={}
    import vllm_ascend.ops
    import vllm_ascend.ops.gdn as module
    from independent_runner_context import CURRENT_REQUEST_SLICES
    from independent_linear_public_builder import build_native_linear_public_body
    from independent_linear_public_builder import build_native_compact_linear_public_body
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
        if len(requests)!=1 or (not allow_chunks and
                (requests[0].computed_tokens!=0 or requests[0].scheduled_tokens<identity.length)):
            raise ValueError("canonical public request must be one complete zero-prefix prefill")
        if identity.layer!=self.prefix or identity.rank!=requests[0].rank:
            raise ValueError("canonical layer/rank mismatch")
        token=_context.set((identity,mixed_qkv,requests[0]))
        try:return original_core(self,mixed_qkv,b,a,core_attn_out)
        finally:_context.reset(token)
    def wrapped_chunk(*args,**kwargs):
        output=original_chunk(*args,**kwargs)
        context=_context.get()
        if context is not None:
            identity,projected,request=context
            if allow_chunks:
                from independent_public_chunk_plan import public_chunk
                from independent_public_chunk_state import PublicChunkState
                from independent_c1_official_bridge import official_segment_affine
                from independent_c1_state_only import official_state_only
                from independent_linear_material_pool import identity_key
                chunk=public_chunk(request.computed_tokens,request.scheduled_tokens,
                    identity.length,boundary=identity.boundary_tokens)
                key=(request.request_id,identity_key(identity))
                if key not in accumulators:
                    if request.computed_tokens!=0 or len(accumulators)>=64:
                        raise ValueError("bounded zero-start chunk producer required")
                    accumulators[key]=PublicChunkState(request.request_id,identity)
                affine=None
                if chunk.body_end>chunk.body_start:
                    span=slice(chunk.body_start,chunk.body_end)
                    fields=[kwargs[name][:,span].contiguous() for name in ("k","v","g","beta")]
                    affine=official_segment_affine(official_state_only,*fields)
                tail=(projected[chunk.conv_tail_start:chunk.conv_tail_end].contiguous()
                      if chunk.completes_public else None)
                material=accumulators[key].accept(request.request_id,identity,chunk,affine,tail)
                if material is not None:
                    import torch
                    torch.npu.synchronize()
                    publish(material);del accumulators[key]
                return output
            length=identity.length
            k,v,g,beta,projected=prefix_material_inputs(length,projected,kwargs)
            # Official source invokes chunk with named q/k/v/g/beta fields.
            if compact:
                material=build_native_compact_linear_public_body(
                    identity,k,v,g,beta,projected)
            else:
                material=build_native_linear_public_body(
                    identity,k,v,g,beta,
                    output[0][:,:length].contiguous(),projected)
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
        accumulators.clear()
    return stop
