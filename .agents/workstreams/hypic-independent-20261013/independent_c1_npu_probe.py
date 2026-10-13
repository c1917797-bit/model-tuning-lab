"""Bounded C1 numerical test in unchanged official runtime; not a service benchmark.
Requires explicit device0 mapping and isolated controller admission. No model weights
are loaded; dimensions are the selected27B TP4 local GDN dimensions.
"""
import json
import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op
from vllm.config import VllmConfig, ModelConfig, ParallelConfig, set_current_vllm_config
from vllm.distributed import init_distributed_environment, initialize_model_parallel, destroy_model_parallel, destroy_distributed_environment
from vllm.forward_context import set_forward_context
from vllm_ascend.ops.triton.fla.chunk import chunk_gated_delta_rule
import vllm_ascend.ops.triton.fla.chunk as chunk_module
from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
from independent_c1_official_bridge import official_segment_affine
from independent_c1_state_only import official_state_only
from independent_c1_reference import serial_dense_oracle, apply_segment
def main():
    torch.npu.set_device(0)
    if not enable_custom_op():
        raise RuntimeError('official Ascend custom operators unavailable')
    init_device_properties_triton()
    config=VllmConfig(model_config=ModelConfig(model="/model",trust_remote_code=True),
                      parallel_config=ParallelConfig(tensor_parallel_size=1,prefill_context_parallel_size=1))
    with set_current_vllm_config(config):
        init_distributed_environment(world_size=1,rank=0,local_rank=0,backend="hccl",distributed_init_method="tcp://127.0.0.1:26491")
        initialize_model_parallel(backend="hccl")
        try:
            torch.manual_seed(411)
            k=torch.randn(1,65,4,128,dtype=torch.bfloat16)
            v=torch.randn(1,65,12,128,dtype=torch.bfloat16)
            g=-torch.rand(1,65,12,dtype=torch.float32)*.02
            beta=torch.rand(1,65,12,dtype=torch.float32)*.3
            incoming=torch.randn(12,128,128,dtype=torch.float32)*.01
            # FP64 CPU oracle uses the exact BF16 source inputs; native key
            # normalization error is measured, not silently deemed equality.
            kn=torch.nn.functional.normalize(k[0].double(),dim=-1)
            expected=serial_dense_oracle(kn,v[0].double(),beta[0].double(),g[0].double().exp(),incoming.double())
            with set_forward_context(None,config,num_tokens=65):
                originals={}
                def instrument(name,fn):
                    def wrapped(*args,**kwargs):
                        print(json.dumps({'stage':'primitive-start','name':name}),flush=True)
                        output=fn(*args,**kwargs)
                        torch.npu.synchronize()
                        print(json.dumps({'stage':'primitive-complete','name':name}),flush=True)
                        return output
                    return wrapped
                for name in ['l2norm_fwd','chunk_local_cumsum','chunk_scaled_dot_kkt_fwd','solve_tril','recompute_w_u_fwd']:
                    originals[name]=getattr(chunk_module,name)
                    setattr(chunk_module,name,instrument(name,originals[name]))
                op_originals={}
                for name in ['chunk_gated_delta_rule_fwd_h','chunk_fwd_o']:
                    op_originals[name]=getattr(torch.ops._C_ascend,name)
                    setattr(torch.ops._C_ascend,name,instrument(name,op_originals[name]))
                invocation=[0]
                def synchronized_runner(*args,**kwargs):
                    invocation[0]+=1
                    print(json.dumps({'stage':'official-call-start','invocation':invocation[0]}),flush=True)
                    output=official_state_only(*args,**kwargs)
                    torch.npu.synchronize()
                    print(json.dumps({'stage':'official-call-complete','invocation':invocation[0]}),flush=True)
                    return output
                material=official_segment_affine(synchronized_runner,k.npu(),v.npu(),g.npu(),beta.npu())
                actual=apply_segment(material,incoming.npu())
                torch.npu.synchronize()
                diff=actual.cpu().double()-expected
                print(json.dumps({"scope":"C1-selected27B-TP4-local-shape-only","shape":[65,4,12,128,128],
                                  "finite":bool(torch.isfinite(diff).all()),
                                  "max_abs":float(diff.abs().max()),"rms":float(diff.square().mean().sqrt()),
                                  "reference_rms":float(expected.square().mean().sqrt()),
                                  "not_service_or_full_algorithm":True}),flush=True)
        finally:
            if 'originals' in locals():
                for name,fn in originals.items():setattr(chunk_module,name,fn)
            if 'op_originals' in locals():
                for name,fn in op_originals.items():setattr(torch.ops._C_ascend,name,fn)
            destroy_model_parallel();destroy_distributed_environment()
if __name__=="__main__":main()
