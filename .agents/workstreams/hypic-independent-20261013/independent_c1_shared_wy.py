"""Independent packed C1 shared-algebra adapter; no activation or cache writes.

The caller supplies source-verified unchanged official primitives and complete
nonempty-window metadata. Preserve native grouped Q/K and value heads.
This module is not a device admission or runtime loader.
"""
from dataclasses import dataclass
import torch

@dataclass
class SharedWY:
    q: object
    k: object
    w: object
    u: object
    g: object
    starts: tuple
    indices: tuple
    state_op: object
    output_op: object
    scale: float

    def state(self, initial, *, zero_value=False):
        # Transition pass has value width K, even when real V differs.
        values=self.u.new_zeros((*self.u.shape[:-1],initial.shape[-1])) if zero_value else self.u
        return self.state_op(
            self.k,self.w,values,
            g=self.g,gk=None,initial_state=initial,output_final_state=True,
            chunk_size=64,save_new_value=True,cu_seqlens=self.starts,
            chunk_indices=self.indices,use_exp2=False,transpose_state_layout=False)

    def affine_maps(self):
        # For H' = T H + S, use the SAME prepared W/g in both passes.
        n=len(self.starts)-1;heads=self.u.shape[1];key=self.k.shape[-1]
        value=self.u.shape[-1]
        zeros=torch.zeros((n,heads,key,value),device=self.k.device,dtype=torch.float32)
        _,_,s=self.state(zeros)
        eye=torch.eye(key,device=self.k.device,dtype=torch.float32)
        identity=eye.expand(n,heads,key,key).contiguous()
        _,_,t=self.state(identity,zero_value=True)
        return t,s

    def render(self, seeds):
        h,v_new,final=self.state(seeds)
        output=self.output_op(self.q,self.k,v_new,h,self.scale,g=self.g,
            g_gamma=None,cu_seqlens=self.starts,chunk_indices=self.indices,
            chunk_size=64,transpose_state_layout=False)
        return output.transpose(1,2).contiguous(),final


def prepare_shared_wy(q,k,v,g,beta,*,meta,native,state_op,output_op,scale=None):
    """Prepare all packed windows once; no whole-chunk wrapper recursion."""
    if q.ndim!=4 or q.shape!=k.shape or q.shape[0]!=1:
        raise ValueError("packed [1,token,head,key] Q/K required")
    if (v.ndim!=4 or v.shape[:2]!=k.shape[:2] or k.shape[2]<=0
            or v.shape[2]<=0 or v.shape[2]%k.shape[2]
            or g.shape!=v.shape[:3] or beta.shape!=g.shape):
        raise ValueError("integral native grouped key/value head geometry required")
    if q.dtype!=k.dtype or k.dtype!=v.dtype or k.dtype!=torch.bfloat16:
        raise ValueError("official BF16 packed ABI required")
    if any(x.device!=k.device for x in (q,v,g,beta)):
        raise ValueError("one packed device required")
    starts=tuple(meta.cu_seqlens_host)
    if not 2<=len(starts)<=65 or starts[0]!=0 or starts[-1]!=k.shape[1] or any(
        type(x) is not int or x<0 for x in starts) or any(a>=b for a,b in zip(starts,starts[1:])):
        raise ValueError("complete nonempty bounded window starts required")
    indices=meta.chunk_indices_chunk64_host
    if indices is None:raise ValueError("prebuilt host chunk indices required")
    indices=tuple(indices)
    q=native.l2norm_fwd(q);k=native.l2norm_fwd(k)
    cu=torch.tensor(starts,dtype=torch.int64,device=k.device)
    gc=native.chunk_local_cumsum(g,chunk_size=64,cu_seqlens=cu,
                                 block_indices=meta.block_indices_cumsum)
    a=native.chunk_scaled_dot_kkt_fwd(k=k,beta=beta,g_cumsum=gc,cu_seqlens=cu,
                chunk_indices=meta.chunk_indices_chunk64,output_dtype=torch.float32)
    a=native.solve_tril(A=a,cu_seqlens=cu,
                chunk_indices_large_block=meta.chunk_indices_large_block,
                chunk_indices_bt=meta.chunk_indices_chunk64,output_dtype=k.dtype)
    w,u=native.recompute_w_u_fwd(k=k,v=v,beta=beta,A=a,g_cumsum=gc,
                cu_seqlens=cu,chunk_indices=meta.chunk_indices_chunk64)
    convert=lambda x:x.to(torch.bfloat16).transpose(1,2).contiguous()
    return SharedWY(convert(q),convert(k),convert(w),convert(u),
                    gc.transpose(1,2).contiguous(),starts,indices,state_op,output_op,
                    k.shape[-1]**-0.5 if scale is None else float(scale))
