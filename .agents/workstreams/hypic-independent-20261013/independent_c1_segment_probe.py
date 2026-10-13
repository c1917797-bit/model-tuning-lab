"""Selected-shape segmented C1 diagnostic; neither a serving hook nor benchmark."""
import json,torch,torch_npu
from vllm_ascend.utils import enable_custom_op
from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
from vllm.config import VllmConfig,ModelConfig,ParallelConfig,set_current_vllm_config
from vllm.distributed import init_distributed_environment,initialize_model_parallel,destroy_model_parallel,destroy_distributed_environment
from independent_c1_state_only import official_state_only
from independent_c1_official_bridge import official_segment_affine
from independent_c1_reference import apply_segment,compose_segments
def main():
    torch.npu.set_device(0);assert enable_custom_op();init_device_properties_triton()
    cfg=VllmConfig(model_config=ModelConfig(model='/model',trust_remote_code=True),parallel_config=ParallelConfig())
    with set_current_vllm_config(cfg):
        init_distributed_environment(world_size=1,rank=0,local_rank=0,backend='hccl',distributed_init_method='tcp://127.0.0.1:26491')
        initialize_model_parallel(backend='hccl')
        try:
            for length in [64,65,128]:
                torch.manual_seed(500+length)
                k=torch.randn(1,length,4,128,dtype=torch.bfloat16).npu()
                v=torch.randn(1,length,12,128,dtype=torch.bfloat16).npu()
                g=(-torch.rand(1,length,12)*.02).npu();beta=(torch.rand(1,length,12)*.3).npu()
                initial=(torch.randn(12,128,128)*.01).npu()
                split=length//2
                first=official_segment_affine(official_state_only,k[:,:split],v[:,:split],g[:,:split],beta[:,:split])
                second=official_segment_affine(official_state_only,k[:,split:],v[:,split:],g[:,split:],beta[:,split:])
                combined=apply_segment(compose_segments(first,second),initial)
                sequential=apply_segment(second,apply_segment(first,initial))
                expanded=k.repeat_interleave(3,dim=2).contiguous()
                _,direct=official_state_only(expanded,expanded,v,g,beta,initial_state=initial[None],
                    output_final_state=True,cu_seqlens=torch.tensor([0,length],device='npu',dtype=torch.int64))
                torch.npu.synchronize()
                d=combined.cpu().double()-direct[0].cpu().double()
                order=combined.cpu().double()-sequential.cpu().double()
                wrong=apply_segment(compose_segments(second,first),initial).cpu().double()-direct[0].cpu().double()
                print(json.dumps({'scope':'C1-two-segment-actual-local-shape','length':length,'split':split,
                    'finite':bool(torch.isfinite(d).all()),'composition_vs_whole_rms':float(d.square().mean().sqrt()),
                    'composition_vs_whole_max':float(d.abs().max()),'associative_apply_rms':float(order.square().mean().sqrt()),
                    'reverse_order_negative_control_rms':float(wrong.square().mean().sqrt())}),flush=True)
        finally:destroy_model_parallel();destroy_distributed_environment()
if __name__=='__main__':main()
