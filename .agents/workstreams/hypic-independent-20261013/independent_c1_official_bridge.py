"""Independent C1 dual-invocation bridge to the official chunk GDN primitive.
No existing HYPIC implementation is imported. Runner injection enables CPU tests.
Runtime context and actual NPU numerics still require device validation.
"""
import torch
from independent_c1_reference import SegmentAffine
def official_segment_affine(runner, keys, values, log_decay, beta, *, cu_seqlens=None, prebuilt_meta=None):
    if keys.ndim!=4 or values.ndim!=4 or keys.shape[0]!=1:
        raise ValueError("expected flattened [1,T,H,D]")
    b,t,hk,dk=keys.shape; hv=values.shape[2];dv=values.shape[3]
    if values.shape[:2]!=(b,t) or hk<=0 or hv%hk or t<=0:
        raise ValueError("token/group shape mismatch")
    if keys.dtype!=torch.bfloat16 or values.dtype!=keys.dtype or keys.device!=values.device:
        raise ValueError("official primitive requires matching BF16 data")
    if log_decay.shape!=(b,t,hv) or beta.shape!=log_decay.shape:
        raise ValueError("gates must use value heads")
    if any(x.device!=keys.device for x in (log_decay,beta)):
        raise ValueError("gate device mismatch")
    if cu_seqlens is None:
        cu_seqlens=torch.tensor([0,t],device=keys.device,dtype=torch.int64)
    if cu_seqlens.numel()!=2:
        raise ValueError("one public segment only")
    kw=dict(output_final_state=True,cu_seqlens=cu_seqlens,prebuilt_meta=prebuilt_meta,
            head_first=False,use_qk_l2norm_in_kernel=True)
    zero=torch.zeros((1,hv,dk,dv),device=keys.device,dtype=torch.float32)
    _,state=runner(keys,keys,values,log_decay,beta,initial_state=zero,**kw)
    identity=torch.eye(dk,device=keys.device,dtype=torch.float32).expand(1,hv,dk,dk).contiguous()
    zero_values=torch.zeros((1,t,hv,dk),device=keys.device,dtype=keys.dtype)
    _,transition=runner(keys,keys,zero_values,log_decay,beta,initial_state=identity,**kw)
    if state is None or transition is None or state.shape!=zero.shape or transition.shape!=identity.shape:
        raise ValueError("official final-state ABI mismatch")
    return SegmentAffine(transition[0],state[0])
