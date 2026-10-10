"""Literal inherited capture configuration. Both N1 parser and LLM use this."""
def kwargs():
    return dict(model="/cache/efim/Qwen3.6-27B",tokenizer="/cache/efim/Qwen3.6-27B",trust_remote_code=False,
        tensor_parallel_size=4,pipeline_parallel_size=1,data_parallel_size=1,distributed_executor_backend="mp",worker_extension_cls="rpc_extension.SKVQCaptureExtension",
        dtype="bfloat16",quantization=None,seed=0,enforce_eager=True,compilation_config={"mode":0},
        max_model_len=4097,max_num_batched_tokens=4096,max_num_seqs=1,enable_chunked_prefill=True,
        enable_prefix_caching=False,async_scheduling=False,kv_cache_dtype="auto",gpu_memory_utilization=0.65,
        cpu_offload_gb=0,speculative_config=None,kv_transfer_config=None)
