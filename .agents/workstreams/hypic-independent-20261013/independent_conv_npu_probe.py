"""Native convolution boundary diagnostic at selected27B TP4 local width."""
import json,torch,torch_npu
from vllm_ascend.utils import enable_custom_op
from independent_conv_boundary import stitch_conv_boundary
from independent_c2_reference import causal_conv_reference
def main():
    torch.npu.set_device(0);assert enable_custom_op();torch.manual_seed(414)
    x=(torch.randn(64,2560)*.1).to(torch.bfloat16)
    w=(torch.randn(2560,4)*.1).to(torch.bfloat16)
    tail=(torch.randn(3,2560)*.1).to(torch.bfloat16)
    def native(initial,warm):
        data=x.npu();weights=w.T.contiguous().npu();state=initial[None].contiguous().npu()
        output=torch.empty_like(data)
        torch.ops._C_ascend.npu_causal_conv1d_custom(output,data,weights,
            conv_state=state,bias_opt=None,query_start_loc_opt=torch.tensor([0,64],device='npu',dtype=torch.int32),
            cache_indices_opt=torch.tensor([0],device='npu',dtype=torch.int32),
            initial_state_mode_opt=torch.tensor([warm],device='npu',dtype=torch.bool),
            num_accepted_tokens_opt=None,activation_mode=1,pad_slot_id=-1,run_mode=0)
        torch.npu.synchronize();return output,state
    public,_=native(torch.zeros_like(tail),False)
    live,live_state=native(tail,True)
    saved=public.clone()
    private,final,warmup=stitch_conv_boundary(x.npu(),public,w.npu(),tail.npu(),activation='silu')
    torch.npu.synchronize()
    expected,_=causal_conv_reference(x.double(),w.double(),tail.double(),activation='silu')
    d=private.cpu().double()-live.cpu().double();ref=live.cpu().double()-expected
    assert torch.equal(public,saved),"public cache modified"
    print(json.dumps({'scope':'conv-width4-channels2560 local; not model integration','warmup':warmup,
        'finite':bool(torch.isfinite(d).all()),'stitched_native_rms':float(d.square().mean().sqrt()),
        'stitched_native_max':float(d.abs().max()),'native_reference_rms':float(ref.square().mean().sqrt()),
        'public_unchanged':True,'state_tail_shape':list(live_state.shape)}),flush=True)
if __name__=='__main__':main()
