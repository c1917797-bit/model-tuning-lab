"""Actual-device runtime class preflight; no model construction or inference."""
import torch,torch_npu,json
def main():
    torch.npu.set_device(0)
    from independent_runtime_adapter import activate_context
    stop=activate_context(enabled=True)
    from vllm_ascend.worker.model_runner_v1 import NPUModelRunner
    assert getattr(NPUModelRunner._prepare_inputs,'_independent_context_owned',False)
    assert getattr(NPUModelRunner.execute_model,'_independent_context_owned',False)
    stop()
    assert not getattr(NPUModelRunner._prepare_inputs,'_independent_context_owned',False)
    assert not getattr(NPUModelRunner.execute_model,'_independent_context_owned',False)
    torch.npu.synchronize()
    print(json.dumps({'scope':'NPU-backed class source/install/uninstall preflight only',
                      'source_verified':True,'installed':True,'uninstalled':True,
                      'weights_loaded':False,'inference_requests':0}),flush=True)
if __name__=='__main__':main()
