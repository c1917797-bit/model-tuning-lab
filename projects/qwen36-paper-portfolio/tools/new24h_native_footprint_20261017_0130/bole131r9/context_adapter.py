"""Re-enter the ACTUAL Ascend context constructor, not a hand-filled HAL stub."""
from contextlib import contextmanager
from model_entry import need,code_source
_RUNTIME=None


def configure(worker,C,source_ref):
 global _RUNTIME
 need(_RUNTIME is None,'one real worker owns this diagnostic context adapter')
 import vllm_ascend.ascend_forward_context as native
 from vllm.forward_context import get_forward_context,is_forward_context_available
 from vllm.config import CUDAGraphMode
 m=C.obj(source_ref)
 need(C.ref(native.__file__)==m['runtime_sources']['ascend_forward_context'],
      'exact actual native16616B Ascend context source')
 code_source(C,get_forward_context,m['runtime_sources']['forward_context'])
 code_source(C,is_forward_context_available,m['runtime_sources']['forward_context'])
 need(worker.model_runner.vllm_config.parallel_config.data_parallel_size==1,
      'no extra DP coordination or inferred microbatch context')
 _RUNTIME=(worker,C,source_ref,native,get_forward_context,is_forward_context_available,CUDAGraphMode)


@contextmanager
def enter(original_context,*,num_tokens,source_ref):
 need(_RUNTIME is not None,'actual worker context configured after native load')
 worker,C,sr,native,get_context,available,modes=_RUNTIME
 need(source_ref==sr and type(num_tokens)is int and num_tokens in(1,3),
      'only source-owned one-token AR or three-node tree context')
 need(original_context.dp_metadata is None and original_context.ubatch_slices is None and
      original_context.cudagraph_runtime_mode==modes.NONE,
      'actual original context was same eager/DP1 scope')
 before=get_context()if available()else None
 with native.set_ascend_forward_context(original_context.attn_metadata,
      worker.model_runner.vllm_config,num_tokens=num_tokens,
      num_actual_tokens=num_tokens,aclgraph_runtime_mode=modes.NONE,
      model_instance=worker._bole_model_objects['outer'],is_draft_model=False,
      skip_compiled=True):
  actual=get_context()
  need(actual is not original_context and actual is not before and
       actual.no_compile_layers==original_context.no_compile_layers,
       'native constructor produced fresh context with same actual layer registry')
  need(native._EXTRA_CTX.num_tokens==num_tokens and
       native._EXTRA_CTX.is_draft_model is False and
       native._EXTRA_CTX.flash_comm_v1_enabled is False and
       native._EXTRA_CTX.flashcomm_v2_enabled is False,
       'actual native proxy observes correct target token count and no padding/SP mode')
  yield
 need((get_context()if available()else None)is before,'original draft/runner context restored by native context manager')

# Identity anchors captured at this reviewed module's actual import. No rewrap.
_SOURCE_ENTER_WRAPPER=enter
_SOURCE_ENTER_GENERATOR=enter.__wrapped__
_SOURCE_ENTER_WRAPPER_CODE=enter.__code__
_SOURCE_ENTER_GENERATOR_CODE=enter.__wrapped__.__code__
