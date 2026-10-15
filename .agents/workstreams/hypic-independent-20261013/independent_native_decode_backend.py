"""Batched ordinary native decode on PRIVATE buffers; not a HYPIC math kernel."""
from pathlib import Path
import hashlib,inspect
import torch
from independent_native_decode_pack import unpack_native_decode

GDN_SHA="d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"

def official_backends(layer):
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    if type(layer) is not QwenGatedDeltaNetAttention:
        raise ValueError("unexpected native decode layer")
    path=Path(inspect.getfile(inspect.unwrap(type(layer)._forward_core)))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=GDN_SHA:
        raise ValueError("native GDN source drift")
    from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd
    from vllm_ascend.device.device_op import DeviceOperator
    return (torch.ops._C_ascend.npu_causal_conv1d_custom,
            torch.ops._C_ascend.npu_recurrent_gated_delta_rule,
            l2norm_fwd,DeviceOperator.fused_gdn_gating)

def run_private_native_decode(layer,packed,*,ssm_index_dtype,backends=None,finite_check=None):
    """No real cache tensor is passed. Index dtype comes from live metadata."""
    if ssm_index_dtype not in (torch.int32,torch.int64):
        raise ValueError("native state-index dtype required")
    conv_op,recurrent_op,norm,gating=official_backends(layer) if backends is None else backends
    n=len(packed.rows);device=packed.projected.device
    if packed.state.dtype!=torch.float32:
        raise ValueError("selected native float32 state required")
    # Extra clones preserve packed initial inputs for independent full-path shadow.
    conv=packed.conv.clone();state=packed.state.clone()
    conv_output=torch.empty_like(packed.projected)
    conv_op(conv_output,packed.projected,
        layer.conv1d.weight.view(packed.projected.shape[1],4).transpose(0,1),
        conv_state=conv,bias_opt=layer.conv1d.bias,
        query_start_loc_opt=packed.conv_starts,
        cache_indices_opt=torch.arange(n,dtype=torch.int32,device=device),
        initial_state_mode_opt=torch.ones(n,dtype=torch.bool,device=device),
        num_accepted_tokens_opt=None,activation_mode=1 if layer.activation else 0,
        pad_slot_id=-1,run_mode=0)
    q,k,v=layer.rearrange_mixed_qkv(conv_output)
    g,beta=gating(layer.A_log,packed.a,packed.b,layer.dt_bias)
    if q.ndim!=4 or q.shape[:2]!=(1,n) or q.shape!=k.shape or v.shape[:2]!=(1,n):
        raise ValueError("native decode projected heads mismatch")
    if state.shape!=(n,v.shape[2],v.shape[3],k.shape[-1]):
        raise ValueError("native decode value-major state mismatch")
    output=recurrent_op(query=norm(q).squeeze(0),key=norm(k).squeeze(0),
        value=v.squeeze(0),g=g.squeeze(0),beta=beta.squeeze(0),state=state,
        scale=k.shape[-1]**-.5,actual_seq_lengths=packed.actual_seq_lengths,
        ssm_state_indices=torch.arange(n,dtype=ssm_index_dtype,device=device))
    return unpack_native_decode(packed,output,state,conv,finite_check=finite_check)
