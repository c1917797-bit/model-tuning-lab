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
def validate_runner(runner,Mode,ascend_config):
 cc=runner.vllm_config.compilation_config;pc=runner.vllm_config.parallel_config
 require(runner.model_config.enforce_eager is False and cc.cudagraph_mode==Mode.FULL_DECODE_ONLY and
  cc.cudagraph_mode.decode_mode()==Mode.FULL and cc.cudagraph_mode.mixed_mode()==Mode.NONE and
  tuple(cc.cudagraph_capture_sizes)==BATCHES and cc.cudagraph_num_of_warmups==2 and
  tuple(ascend_config.pa_shape_list)==BATCHES and pc.tensor_parallel_size==4 and pc.data_parallel_size==1 and
  runner.max_num_reqs==16 and runner.speculative_config is None and runner.lora_config is None and
  not runner.use_cp and not runner.use_async_scheduling and not runner.enable_enpu and
  not runner.use_sparse and not runner.use_compress,"actual common TP4/nondraft/stock FULL native PA/all16/no async admission")
 return True

FA=tuple(range(3,64,4))
SCREEN_LENGTH=32768+1024
SCREEN_PAGES=(SCREEN_LENGTH+127)//128
