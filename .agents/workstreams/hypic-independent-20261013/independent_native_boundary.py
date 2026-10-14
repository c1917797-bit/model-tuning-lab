"""Current-request C1 boundary evaluation on private native state buffers."""
import torch
def private_conv_buffer(incoming_conv,projected):
    if incoming_conv.device!=projected.device:
        raise ValueError("conv/input device mismatch")
    return incoming_conv.detach().to(projected.dtype).clone().unsqueeze(0).contiguous()

def make_boundary_runner(layer,projected,b,a,incoming_conv,*,return_conv=False):
    """Caller passes ONLY the current request's live boundary, not public body.
    Official primitive calls are unchanged; conv/SSM input caches stay private.
    Must execute inside the real forward context on the request's device.
    """
    from pathlib import Path
    import hashlib,inspect
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    if type(layer) is not QwenGatedDeltaNetAttention:
        raise ValueError("unexpected boundary layer")
    if hashlib.sha256(Path(inspect.getfile(inspect.unwrap(type(layer)._forward_core))).read_bytes()).hexdigest()!="d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816":
        raise ValueError("GDN source drift")
    length=projected.shape[0]
    if length<1 or projected.ndim!=2 or b.shape[0]!=length or a.shape[0]!=length:
        raise ValueError("live boundary coverage mismatch")
    if incoming_conv.shape!=(3,projected.shape[1]):
        raise ValueError("selected width4 conv-state layout mismatch")
    # Independent producer may wrap the official module alias; import the
    # unchanged primitive directly so private boundary isn't published.
    from vllm_ascend.ops.triton.fla.chunk import chunk_gated_delta_rule
    from vllm_ascend.device.device_op import DeviceOperator
    def run(initial_state):
        conv_state=private_conv_buffer(incoming_conv,projected)
        conv_output=torch.empty_like(projected)
        starts=torch.tensor([0,length],dtype=torch.int32,device=projected.device)
        indices=torch.zeros(1,dtype=torch.int32,device=projected.device)
        torch.ops._C_ascend.npu_causal_conv1d_custom(
            conv_output,projected,layer.conv1d.weight.view(projected.shape[1],4).transpose(0,1),
            conv_state=conv_state,bias_opt=layer.conv1d.bias,
            query_start_loc_opt=starts,cache_indices_opt=indices,
            initial_state_mode_opt=torch.ones(1,dtype=torch.bool,device=projected.device),
            num_accepted_tokens_opt=None,activation_mode=1 if layer.activation else 0,
            pad_slot_id=-1,run_mode=0)
        torch.npu.synchronize()
        q,k,v=layer.rearrange_mixed_qkv(conv_output)
        g,beta=DeviceOperator.fused_gdn_gating(layer.A_log,a,b,layer.dt_bias)
        if length<=64:
            from independent_recurrent_boundary import recurrent_boundary
            output,state=recurrent_boundary(q,k,v,g,beta,initial_state.unsqueeze(0).contiguous())
        else:
            from independent_boundary_metadata import build_boundary_metadata
            meta=build_boundary_metadata(layer,length,projected.device)
            output,state=chunk_gated_delta_rule(
                q=q,k=k,v=v,g=g,beta=beta,initial_state=initial_state.unsqueeze(0).contiguous(),
                output_final_state=True,cu_seqlens=starts,prebuilt_meta=meta,
                head_first=False,use_qk_l2norm_in_kernel=True)
        torch.npu.synchronize()
        if state is None:raise ValueError("native boundary final state missing")
        if return_conv:return output[0],state[0],conv_state[0].clone()
        return output[0],state[0]
    return run
