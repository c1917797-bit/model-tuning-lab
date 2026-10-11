"""Honest actual parser+SchedulerConfig CPU; actual ModelConfig/fullEngine only after all4 N1."""
import inspect,os,sys
import bridge_contract as B
from model_options import kwargs
ARG_SHA="3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d"
def construct(source,*,full=False):
    C,r,m=B.source(source["sha256"])
    import torch,torch_npu
    B.need(torch.npu is torch_npu.npu and not torch.cuda.is_initialized(),"actual torch_npu autoload-OFF import/no CUDA")
    if not full:B.need(not torch.npu.is_initialized(),"Devices[] no HAL config")
    from vllm.engine.arg_utils import EngineArgs
    B.need(C.ref(inspect.getfile(EngineArgs))["sha256"]==ARG_SHA,"source-qualified actual EngineArgs")
    engine=EngineArgs(**kwargs())
    if full:
        configuration=engine.create_engine_config();p=configuration.parallel_config
        model=configuration.model_config;s=configuration.scheduler_config
        B.need((p.tensor_parallel_size,p.pipeline_parallel_size,p.data_parallel_size,p.prefill_context_parallel_size,
          p.decode_context_parallel_size)==(4,1,1,1,1)and p.worker_extension_cls==kwargs()["worker_extension_cls"],
          "actual native TP4/eager extension")
        B.need(model.model==kwargs()["model"]and model.max_model_len==33792 and model.enforce_eager is True and
          str(model.dtype)=="torch.bfloat16"and model.is_encoder_decoder is False and
          model.architecture=="Qwen3_5ForConditionalGeneration"and model.is_chunked_prefill_supported is True,
          "actual checkpoint architecture/HAL-dependent model configuration")
        t=model.hf_text_config
        B.need((t.num_hidden_layers,t.num_attention_heads,t.num_key_value_heads,t.head_dim)==(64,24,4,256),
          "all64/GDN48/FA16 actual Qwen geometry")
        B.need(configuration.compilation_config.mode.name=="NONE"and
          configuration.cache_config.kv_cache_memory_bytes==6442450944 and
          configuration.cache_config.cache_dtype=="auto"and configuration.cache_config.enable_prefix_caching is False and
          configuration.speculative_config is configuration.lora_config is configuration.kv_transfer_config is None,
          "new common dense/candidate6GiB retained, no auxiliary algorithm or savings claim")
        import model_extension as E
        extension=E.before_weights(configuration,r)
    else:
        from vllm.config.scheduler import SchedulerConfig
        engine._check_feature_supported()
        s=SchedulerConfig.default_factory(runner_type="generate",max_model_len=engine.max_model_len,
          max_num_batched_tokens=engine.max_num_batched_tokens,max_num_seqs=engine.max_num_seqs,
          enable_chunked_prefill=engine.enable_chunked_prefill,async_scheduling=engine.async_scheduling,
          max_num_partial_prefills=engine.max_num_partial_prefills,max_long_partial_prefills=engine.max_long_partial_prefills,
          long_prefill_token_threshold=engine.long_prefill_token_threshold)
        extension=None
    B.need(s.max_num_seqs==1 and s.max_num_batched_tokens==33792 and s.enable_chunked_prefill is True and
      s.async_scheduling is False and s.max_num_partial_prefills==s.max_long_partial_prefills==1 and
      s.long_prefill_token_threshold==0,"full32768 single prefill capacity and unchanged no active split policy")
    effective=dict(max_num_seqs=s.max_num_seqs,max_num_batched_tokens=s.max_num_batched_tokens,
      enable_chunked_prefill=s.enable_chunked_prefill,async_scheduling=s.async_scheduling,
      declared_model_len=33792,declared_encoder_decoder=False)
    origins={}
    for pin in m["runtime_configuration_sources"]:
        module=sys.modules.get(pin["module"])
        B.need(module is not None and module.__name__==pin["module"],"actual config modules loaded")
        origin=C.ref(module.__file__)
        B.need(origin==dict(path=pin["runtime_path"],bytes=pin["snapshot"]["bytes"],sha256=pin["snapshot"]["sha256"]),
          "whole installed actual configuration source/path/size")
        origins[pin["module"]]=origin
    if not full:B.need(not torch.npu.is_initialized(),"actual necessary CPU scheduler checks didn't initialize NPU")
    return dict(schema="skvq.model-reader.actual-engine-config/v1",source_ref=r,kwargs=kwargs(),effective=effective,
      actual_runtime_origins=origins,torch_ref=C.ref(torch.__file__),torch_npu_ref=C.ref(torch_npu.__file__),
      full_engine_config_verified=full,model_config_constructed=full,NPU_initialized=bool(torch.npu.is_initialized()),
      actual_extension_qualification=extension,CPU_scope="declared argv scalars + actual default_factory; no synthetic ModelConfig",
      **B.false_scopes())
def match(prior,current):
    B.need(prior["full_engine_config_verified"]is False and prior["model_config_constructed"]is False and
      prior["NPU_initialized"]is False and current["full_engine_config_verified"]is True and
      current["model_config_constructed"]is True and prior["source_ref"]==current["source_ref"]and
      prior["kwargs"]==current["kwargs"]and prior["effective"]==current["effective"]and
      prior["actual_runtime_origins"]==current["actual_runtime_origins"]and
      prior["torch_ref"]==current["torch_ref"]and prior["torch_npu_ref"]==current["torch_npu_ref"],
      "real same config/source CPU partial->afterall4 N1 full, no CPU model claim")
