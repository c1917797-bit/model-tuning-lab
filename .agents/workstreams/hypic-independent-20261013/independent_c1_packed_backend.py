"""Independent packed convolution/shared-WY C1 backend, no runtime activation."""
import hashlib,inspect
from pathlib import Path
import torch
from independent_c1_prefix_seeds import prefix_initial_seeds,suffix_seeds_from_terminals
from independent_c1_window_pack import pack_windows
from independent_c1_shared_wy import prepare_shared_wy
from independent_c1_packed_metadata import PackedMetadataCache

def source_verified_backend(layer):
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    import vllm_ascend.ops.triton.fla.chunk as native
    from vllm_ascend.ops.gdn_attn_builder import _build_non_spec_chunked_prefill_metadata as builder
    from vllm_ascend.device.device_op import DeviceOperator
    if type(layer)is not QwenGatedDeltaNetAttention:raise ValueError("exact official GDN class required")
    expected=[
        (inspect.unwrap(type(layer)._forward_core),'d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816'),
        (native,'6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'),
        (builder,'42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16')]
    for obj,digest in expected:
        if hashlib.sha256(Path(inspect.getfile(obj)).read_bytes()).hexdigest()!=digest:
            raise ValueError("official packed C1 source drift")
    return (native,torch.ops._C_ascend.npu_causal_conv1d_custom,
        DeviceOperator.fused_gdn_gating,torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h,
        torch.ops._C_ascend.chunk_fwd_o,PackedMetadataCache(builder))

def run_packed_c1(layer,layout,projected,b,a,initial_states,incoming_conv,materials,
                  *,backends,finite_check=None,geometry_observer=None,stage_probe=None,
                  short_prefix_policy="chunk64",prefix_route_observer=None):
    """Return only private tensors. Caller owns leases and all-request commit."""
    if short_prefix_policy not in ("chunk64","canonical_recurrent_le64"):
        raise ValueError("explicit short-prefix policy required")
    native,conv_op,gating,state_op,output_op,metadata_cache=backends
    cached={key:body.affine for key,body in materials.items()}
    tails={key:body.conv_tail for key,body in materials.items()}
    packed=pack_windows(layout,projected,b,a,incoming_conv,tails)
    conv=packed.conv.clone();conv_output=torch.empty_like(packed.projected)
    n=len(layout.windows);device=projected.device
    conv_op(conv_output,packed.projected,
        layer.conv1d.weight.view(projected.shape[1],4).transpose(0,1),
        conv_state=conv,bias_opt=layer.conv1d.bias,
        query_start_loc_opt=packed.starts,
        cache_indices_opt=torch.arange(n,dtype=torch.int32,device=device),
        initial_state_mode_opt=torch.ones(n,dtype=torch.bool,device=device),
        num_accepted_tokens_opt=None,activation_mode=1 if layer.activation else 0,
        pad_slot_id=-1,run_mode=0)
    q,k,v=layer.rearrange_mixed_qkv(conv_output)
    g,beta=gating(layer.A_log,packed.a,packed.b,layer.dt_bias)
    if (q.ndim!=4 or q.shape!=k.shape or v.ndim!=4 or k.shape[2]<=0
            or v.shape[2]<=0 or v.shape[2]%k.shape[2]):
        raise ValueError("integral grouped key/value heads required")
    meta=metadata_cache.get(packed.host_starts,total_value_heads=layer.num_v_heads,
                           tp_size=layer.tp_size,device=device)
    shared=prepare_shared_wy(q,k,v,g,beta,meta=meta,native=native,
                            state_op=state_op,output_op=output_op)
    if geometry_observer is not None:
        geometry_observer(dict(key_heads=int(shared.k.shape[1]),
            query_heads=int(shared.q.shape[1]),value_heads=int(shared.u.shape[1]),
            wy_heads=int(shared.w.shape[1]),gate_heads=int(shared.g.shape[1]),
            key_width=int(shared.k.shape[-1]),value_width=int(shared.u.shape[-1]),
            head_layout="native_grouped"))
    initial_seeds=prefix_initial_seeds(layout,initial_states)
    # Use actual incoming H, not a zero/identity-derived approximation of a
    # finite-precision native live-prefix kernel. Dummy suffix states are zero.
    _,_,prefix_terminals=shared.state(initial_seeds.clone())
    if short_prefix_policy=="canonical_recurrent_le64":
        from independent_c1_short_prefix import align_short_prefix_terminals
        observer=stage_probe.packed_recurrent_inputs if stage_probe is not None else None
        prefix_terminals,routes=align_short_prefix_terminals(layout,q,k,v,g,beta,
            initial_seeds,prefix_terminals,input_observer=observer)
        if prefix_route_observer is not None:
            for route in routes:prefix_route_observer(route)
    seeds=suffix_seeds_from_terminals(layout,initial_seeds,prefix_terminals,cached)
    if stage_probe is not None:
        stage_probe.packed_inputs(shared,v,g,beta,initial_seeds,seeds)
        stage_probe.packed_states(prefix_terminals,seeds,materials)
    output,terminal=shared.render(seeds)
    wanted=(1,layout.packed_tokens,initial_states.shape[1],initial_states.shape[-1])
    if tuple(output.shape)!=wanted or terminal.shape!=(n,*initial_states.shape[1:]):
        raise ValueError("packed official output/state coverage mismatch")
    result={}
    for row,chain in enumerate(layout.chains):
        if not chain:continue
        jobs=[key for kind,key in chain if kind=='live'];last=jobs[-1]
        pieces=[output[0,layout.windows[j].packed_start:layout.windows[j].packed_end] for j in jobs]
        state=terminal[last];tail=conv[last].clone()
        if (short_prefix_policy=="canonical_recurrent_le64" and chain[0][0]=="live"
                and last==jobs[0]
                and layout.windows[last].packed_end-layout.windows[last].packed_start<=64):
            # With no live suffix, the real carried terminal is the aligned
            # prefix state, not the separate packed prefix-output rendering.
            state=prefix_terminals[last]
        if chain[-1][0]=='cached':
            body=materials[chain[-1][1]]
            state=body.affine.transition@state+body.affine.zero_state
            tail=body.conv_tail.clone()
        y=torch.cat(pieces,dim=0)
        if finite_check is None:
            if not all(torch.isfinite(x).all().item() for x in (y,state,tail)):
                raise ValueError("nonfinite packed private output")
        else:finite_check(y,state,tail)
        result[layout.request_ids[row]]=(y,state,tail)
        if stage_probe is not None:stage_probe.final("packed",layout.request_ids[row],(y,state,tail))
    return result
