"""Actual official class-chain install/uninstall probe, no weights or requests."""
import json
import torch,torch_npu


def main():
    torch.npu.set_device(0)
    import vllm_ascend.ops
    from vllm_ascend.worker.model_runner_v1 import NPUModelRunner
    from vllm.model_executor.models.qwen3_5 import Qwen3_5Model
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    from vllm_ascend.attention.attention_v1 import AscendAttentionBackendImpl
    from independent_compact_activation import activate_compact_hypic
    before=(NPUModelRunner._prepare_inputs,NPUModelRunner.execute_model,
            Qwen3_5Model.forward,QwenGatedDeltaNetAttention._forward_core,
            AscendAttentionBackendImpl.forward)
    events=[]
    config=dict(model_identity='27B-class-preflight-only',code_identity='independent-class-chain',
                public_tokens=list(range(16)),capacity_bytes=268435456,
                kv_capacity_bytes=536870912,boundary_tokens=8)
    stop=activate_compact_hypic(config,enabled=True,emit=events.append)
    try:
        assert getattr(NPUModelRunner._prepare_inputs,'_independent_context_owned',False)
        assert getattr(Qwen3_5Model.forward,'_independent_compact_model_owned',False)
        assert getattr(QwenGatedDeltaNetAttention._forward_core,'_independent_compact_gdn_owned',False)
        assert getattr(AscendAttentionBackendImpl.forward,'_independent_compact_c2_owned',False)
    finally:stop()
    after=(NPUModelRunner._prepare_inputs,NPUModelRunner.execute_model,
           Qwen3_5Model.forward,QwenGatedDeltaNetAttention._forward_core,
           AscendAttentionBackendImpl.forward)
    assert all(a is b for a,b in zip(before,after))
    torch.npu.synchronize()
    print(json.dumps({'scope':'official NPU-backed full hook-chain preflight only',
        'installed':True,'uninstalled':True,'source_verified':True,
        'weights_loaded':False,'inference_requests':0,'events':events}),flush=True)


if __name__=='__main__':main()
