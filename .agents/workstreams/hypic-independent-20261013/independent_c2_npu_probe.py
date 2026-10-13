"""C2 text-only RoPE diagnostic at selected27B TP4 local KV shape."""
import json
import torch
import torch_npu
from independent_c2_reference import rotate_partial_neox,relocate_keys
def main():
    torch.npu.set_device(0);torch.manual_seed(412)
    # Qwen3.5 head256/partial rotary64; one local KV head underTP4.
    base=torch.randn(65,1,256,dtype=torch.bfloat16)
    freq=1e7**(-torch.arange(0,64,2,dtype=torch.float64)/64)
    old=torch.arange(65,dtype=torch.int64)
    canonical=rotate_partial_neox(base,old,freq).contiguous()
    for shift in [1024,4096,7168]:
        public=canonical.npu();saved=public.clone()
        private=relocate_keys(public,old.npu(),(old+shift).npu(),freq.float().npu())
        torch.npu.synchronize()
        reference=relocate_keys(canonical.double(),old,old+shift,freq)
        absolute=rotate_partial_neox(base.double(),old+shift,freq)
        delta=private.cpu().double()-reference
        absolute_delta=private.cpu().double()-absolute
        assert torch.equal(public.cpu(),canonical),"public modified"
        assert public.data_ptr()!=private.data_ptr(),"private aliases public"
        assert torch.equal(private[...,64:].cpu(),canonical[...,64:]),"nonrotary tail changed"
        print(json.dumps({"scope":"C2-text-only-localKV; not MRoPE multimodal or service",
                          "shape":[65,1,256],"rotary_dim":64,"shift":shift,
                          "public_unchanged":True,"private_nonalias":True,"tail_unchanged":True,
                          "same_input_reference_max_abs":float(delta.abs().max()),
                          "same_input_reference_rms":float(delta.square().mean().sqrt()),
                          "absolute_new_anchor_rms":float(absolute_delta.square().mean().sqrt()),
                          "finite":bool(torch.isfinite(delta).all())}),flush=True)
if __name__=='__main__':main()
