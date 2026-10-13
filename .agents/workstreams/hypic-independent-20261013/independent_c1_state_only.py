"""Independent C1 state-only runner built from official unchanged primitives.
No serving attention output is replaced. Only public-material S/T construction.
"""
def official_state_only(q,k,v,g,beta,*,initial_state,output_final_state,
                        cu_seqlens,prebuilt_meta=None,head_first=False,
                        use_qk_l2norm_in_kernel=True):
    import torch
    import vllm_ascend.ops.triton.fla.chunk as native
    if head_first or not output_final_state or prebuilt_meta is not None:
        raise ValueError("single-segment state-only ABI required")
    if k.shape[2]!=v.shape[2] or cu_seqlens.numel()!=2:
        raise ValueError("equal-head single public segment required")
    if use_qk_l2norm_in_kernel:k=native.l2norm_fwd(k)
    gc=native.chunk_local_cumsum(g,chunk_size=64,cu_seqlens=cu_seqlens,block_indices=None)
    A=native.chunk_scaled_dot_kkt_fwd(k=k,beta=beta,g_cumsum=gc,
                                    cu_seqlens=cu_seqlens,chunk_indices=None,output_dtype=torch.float32)
    A=native.solve_tril(A=A,cu_seqlens=cu_seqlens,chunk_indices_large_block=None,
                       chunk_indices_bt=None,output_dtype=k.dtype)
    w,u=native.recompute_w_u_fwd(k=k,v=v,beta=beta,A=A,g_cumsum=gc,
                                cu_seqlens=cu_seqlens,chunk_indices=None)
    # Native h primitive uses head-first data, key-major state and natural exp.
    _,_,final=torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h(
        k.to(torch.bfloat16).transpose(1,2).contiguous(),
        w.to(torch.bfloat16).transpose(1,2).contiguous(),
        u.to(torch.bfloat16).transpose(1,2).contiguous(),
        g=gc.transpose(1,2).contiguous(),gk=None,initial_state=initial_state,
        output_final_state=True,chunk_size=64,save_new_value=True,
        cu_seqlens=tuple(cu_seqlens.tolist()),chunk_indices=None,
        use_exp2=False,transpose_state_layout=False)
    return None,final
