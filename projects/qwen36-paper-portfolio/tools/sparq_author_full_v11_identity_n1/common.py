"""Same stock PA/FULL config for both arms; no algorithm-specific eager tax."""
BATCHES=tuple(range(1,17))
COMPILATION=dict(cudagraph_mode="FULL_DECODE_ONLY",cudagraph_capture_sizes=list(BATCHES),cudagraph_num_of_warmups=2)
ADDITIONAL=dict(pa_shape_list=list(BATCHES))
COMMON=dict(tensor_parallel_size=4,data_parallel_size=1,dtype="bfloat16",max_model_len=40960,
 max_num_batched_tokens=40960,max_num_seqs=16,enforce_eager=False,enable_prefix_caching=False,
 mamba_cache_mode="none",enable_chunked_prefill=False,async_scheduling=False,seed=0,kv_cache_memory_bytes=10*1024**3,
 compilation_config=COMPILATION,additional_config=ADDITIONAL)
AUX_CEILING=2*1024**3
def require(ok,why):
 if not ok:raise ValueError(why)
def validate(actual,arm):
 require(arm in ("dense","candidate") and actual==COMMON,"both arms exact same stock FULL_DECODE_ONLY/PA config, not candidate eager")
 return dict(source_policy_checked=True,model_executed=False,model_ready=False)
# Same installed image660 AscendPlatform.check_and_update_config, L533:
# requests stay at2 on BOTH arms; stock platform overwrites effective count to1.
ASCEND_PLATFORM_SOURCE="/cache/cch/qwen36-paper-preparation-20261007/sparse/sp4-kivi-public-worker-plugin-source-v1-001/ascend_platform.py"
ASCEND_PLATFORM_RUNTIME="/vllm-workspace/vllm-ascend/vllm_ascend/platform.py"
ASCEND_PLATFORM_SHA="30c75952f784c4d047d7202dd7f68c8fc7c22bb975853a5048fb51ffcbe1f2a8"
ASCEND_EFFECTIVE_WARMUPS=1
def _field(owner,name):
 try:return getattr(owner,name)
 except AttributeError as error:raise ValueError("actual common missing field "+name) from error
def _equal(name,actual,expected):
 require(actual==expected,"actual common "+name+": got "+repr(actual)+" expected "+repr(expected))
def _sequence(name,actual):
 try:return tuple(actual)
 except TypeError as error:raise ValueError("actual common "+name+": invalid sequence "+repr(actual)) from error
def validate_runner(runner,Mode,ascend_config):
 # Only warmup request/effective interpretation changes. All prior predicates
 # remain independent hard requirements; missing runtime facts never pass.
 cfg=_field(runner,"vllm_config");cc=_field(cfg,"compilation_config");pc=_field(cfg,"parallel_config")
 eager=_field(_field(runner,"model_config"),"enforce_eager")
 require(eager is False,"actual common enforce_eager: got "+repr(eager)+" expected identity False")
 mode=_field(cc,"cudagraph_mode")
 _equal("cudagraph_mode",mode,Mode.FULL_DECODE_ONLY)
 _equal("cudagraph_mode.decode_mode",_field(mode,"decode_mode")(),Mode.FULL)
 _equal("cudagraph_mode.mixed_mode",_field(mode,"mixed_mode")(),Mode.NONE)
 _equal("cudagraph_capture_sizes",_sequence("cudagraph_capture_sizes",_field(cc,"cudagraph_capture_sizes")),BATCHES)
 warmups=_field(cc,"cudagraph_num_of_warmups")
 require(type(warmups) is int and warmups==ASCEND_EFFECTIVE_WARMUPS,
  "actual common cudagraph_num_of_warmups: got "+repr(warmups)+" expected official effective integer1; requested2 unchanged")
 _equal("pa_shape_list",_sequence("pa_shape_list",_field(ascend_config,"pa_shape_list")),BATCHES)
 _equal("tensor_parallel_size",_field(pc,"tensor_parallel_size"),4)
 _equal("data_parallel_size",_field(pc,"data_parallel_size"),1)
 _equal("max_num_reqs",_field(runner,"max_num_reqs"),16)
 for name in ("speculative_config","lora_config"):
  actual=_field(runner,name)
  require(actual is None,"actual common "+name+": got "+repr(actual)+" expected identity None")
 for name in ("use_cp","use_async_scheduling","enable_enpu","use_sparse","use_compress"):
  actual=_field(runner,name)
  require(not actual,"actual common "+name+": got "+repr(actual)+" expected disabled")
 return True

FA=tuple(range(3,64,4))
SCREEN_LENGTH=32768+1024
SCREEN_PAGES=(SCREEN_LENGTH+127)//128
