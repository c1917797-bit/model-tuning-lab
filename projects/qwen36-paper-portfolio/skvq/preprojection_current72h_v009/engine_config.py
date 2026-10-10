"""Actual scalar SchedulerConfig CPU, then ModelConfig/full config after all4 N1; no weights."""
import argparse,inspect,json,os,sys,time
from pathlib import Path
import current_contract as C
from model_kwargs import kwargs
ARG_SHA="3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d"
MODEL="/cache/efim/Qwen3.6-27B"
def validate_model_scheduler(m,s):
    C.require(m.model==MODEL and m.max_model_len==4097 and m.enforce_eager is True and
        str(m.dtype)=="torch.bfloat16","actual complete model/eager/dtype config")
    C.require(m.architecture=="Qwen3_5ForConditionalGeneration" and m.runner_type=="generate" and
        m.is_encoder_decoder is False and m.is_chunked_prefill_supported is True,
        "actual supported checkpoint class; no platform/architecture stub")
    C.require(s.max_num_seqs==1 and s.max_num_batched_tokens==4096 and s.enable_chunked_prefill is True and
        s.async_scheduling is False,"supported scheduler, one4096 request fits one whole iteration")
    C.require(s.max_num_partial_prefills==s.max_long_partial_prefills==1 and
        s.long_prefill_token_threshold==0 and s.max_num_scheduled_tokens in (None,4096),
        "no configured smaller prefill subchunk; runtime full4096 still required")
    t=m.hf_text_config
    C.require((t.num_hidden_layers,t.num_attention_heads,t.num_key_value_heads,t.head_dim)==(64,24,4,256),"actual all64 Qwen geometry")
    return {"max_model_len":m.max_model_len,"max_num_seqs":s.max_num_seqs,
        "max_num_batched_tokens":s.max_num_batched_tokens,"enable_chunked_prefill":s.enable_chunked_prefill,
        "async_scheduling":s.async_scheduling,"enforce_eager":m.enforce_eager,
        "is_encoder_decoder":m.is_encoder_decoder,
        "num_hidden_layers":t.num_hidden_layers,"FA_local_Q_KV_D":[6,1,256],
        "actual_full4096_metadata_and_tokens_still_required_at_every_FA":True}
def validate(c):
    p,s,m=c.parallel_config,c.scheduler_config,c.model_config
    C.require((p.tensor_parallel_size,p.pipeline_parallel_size,p.data_parallel_size,
        p.prefill_context_parallel_size,p.decode_context_parallel_size)==(4,1,1,1,1),"actual TP4/PP1/DP1/PCP1/DCP1")
    C.require(p.worker_extension_cls=="rpc_extension.SKVQCaptureExtension","explicit native named RPC extension")
    C.require(c.speculative_config is None and c.kv_transfer_config is None and c.lora_config is None,"no speculative/transfer/LoRA")
    C.require(c.compilation_config.mode.name=="NONE","actual eager compilation NONE")
    C.require(c.cache_config.enable_prefix_caching is False and c.cache_config.cache_dtype=="auto","dense no prefix")
    effective=validate_model_scheduler(m,s)
    effective.update(enable_prefix_caching=c.cache_config.enable_prefix_caching,
        compilation_mode=c.compilation_config.mode.name,
        TP_PP_DP_PCP_DCP=[p.tensor_parallel_size,p.pipeline_parallel_size,p.data_parallel_size,
            p.prefill_context_parallel_size,p.decode_context_parallel_size])
    return effective
def scheduler_config(engine,model,scheduler_cls):
    """Exact EngineArgs L2033 kwargs; real installed validators, no synthetic platform."""
    engine._check_feature_supported()
    engine._set_default_chunked_prefill_and_prefix_caching_args(model)
    return scheduler_cls(
        runner_type=model.runner_type,
        max_num_batched_tokens=engine.max_num_batched_tokens,
        max_num_seqs=engine.max_num_seqs,
        max_model_len=model.max_model_len,
        enable_chunked_prefill=engine.enable_chunked_prefill,
        disable_chunked_mm_input=engine.disable_chunked_mm_input,
        is_multimodal_model=model.is_multimodal_model,
        is_encoder_decoder=model.is_encoder_decoder,
        policy=engine.scheduling_policy,
        scheduler_cls=engine.scheduler_cls,
        max_num_partial_prefills=engine.max_num_partial_prefills,
        max_long_partial_prefills=engine.max_long_partial_prefills,
        long_prefill_token_threshold=engine.long_prefill_token_threshold,
        scheduler_reserve_full_isl=engine.scheduler_reserve_full_isl,
        disable_hybrid_kv_cache_manager=engine.disable_hybrid_kv_cache_manager,
        async_scheduling=engine.async_scheduling,
        stream_interval=engine.stream_interval)
def construct(full=False):
    C.require(type(full)is bool,"explicit partial/full config mode")
    source=C.source()
    # Autoload is OFF in the actual owner. Explicit extension import precedes torch.npu access.
    import torch,torch_npu
    C.require(hasattr(torch,"npu") and torch.npu is torch_npu.npu,"actual installed torch_npu registration")
    C.require(not torch.cuda.is_initialized(),"never initializes CUDA")
    if not full:C.require(not torch.npu.is_initialized(),"Devices[] before actual partial config")
    from vllm.engine.arg_utils import EngineArgs
    C.require(C.reference(inspect.getfile(EngineArgs))["sha256"]==ARG_SHA,"actual same660 EngineArgs original module")
    if full:
        configuration=EngineArgs(**kwargs()).create_engine_config()
        effective=validate(configuration)
        import rpc_extension
        extension=rpc_extension.before_weights(configuration,source)
    else:
        from vllm.config.scheduler import SchedulerConfig
        engine=EngineArgs(**kwargs())
        engine._check_feature_supported()
        # ModelConfig registry inspection really touches HAL on image660.
        # This is an independent real SchedulerConfig of explicitly declared argv scalars,
        # NOT a synthetic ModelConfig or a claim of checkpoint/architecture validation.
        # Original default_factory supplies InitVar is_encoder_decoder=False only for
        # this declared decoder branch; N1 must independently prove real ModelConfig False.
        scheduler=SchedulerConfig.default_factory(runner_type="generate",max_model_len=engine.max_model_len,
            max_num_batched_tokens=engine.max_num_batched_tokens,max_num_seqs=engine.max_num_seqs,
            enable_chunked_prefill=engine.enable_chunked_prefill,async_scheduling=engine.async_scheduling,
            max_num_partial_prefills=engine.max_num_partial_prefills,
            max_long_partial_prefills=engine.max_long_partial_prefills,
            long_prefill_token_threshold=engine.long_prefill_token_threshold)
        C.require(engine.enable_prefix_caching is False,"explicit common prefix OFF")
        C.require(engine.max_model_len==4097 and engine.enforce_eager is True and
            scheduler.max_num_batched_tokens==4096 and scheduler.max_num_seqs==1 and
            scheduler.enable_chunked_prefill is True and scheduler.async_scheduling is False,
            "real necessary declared scalar scheduler invariants only; no model construction")
        effective={"max_model_len":engine.max_model_len,"enforce_eager":engine.enforce_eager,
            "max_num_batched_tokens":scheduler.max_num_batched_tokens,"max_num_seqs":scheduler.max_num_seqs,
            "enable_chunked_prefill":scheduler.enable_chunked_prefill,"async_scheduling":scheduler.async_scheduling,
            "is_encoder_decoder":False}
    manifest=json.loads(Path(source["path"]).read_bytes());origins={}
    for pin in manifest["runtime_configuration_sources"]:
        module=sys.modules.get(pin["module"])
        C.require(module is not None and module.__name__==pin["module"],"actual config module loaded")
        actual=C.reference(module.__file__)
        C.require(actual["sha256"]==pin["snapshot"]["sha256"],"actual original config module byte identity")
        origins[pin["module"]]=actual
    initialized=bool(torch.npu.is_initialized())
    if not full:C.require(not initialized,"actual partial config did not initialize NPU")
    return {"status":"ACTUAL_FULL_ENGINE_CONFIG_CHECKED" if full else "ACTUAL_DECLARED_SCHEDULER_CONFIG_CHECKED",
        "source_ref":source,"kwargs":kwargs(),"effective":effective,"runtime_origins":origins,
        "native_worker_extension_qualification":extension if full else None,
        "torch_origin":C.reference(torch.__file__),"torch_npu_origin":C.reference(torch_npu.__file__),
        "NPU_initialized":initialized,"full_engine_config_verified":full,
        "model_config_constructed":full,"actual_scheduler_config_constructed":True,
        "CPU_scope":"explicit EngineArgs values plus real SchedulerConfig; checkpoint class validation only at N1",
        "full_engine_config_required_at_N1":not full,
        "pid":os.getpid(),"observed_epoch":time.time(),"model_loaded":False,"native_ready":False}
def match_partial(prior,full,source):
    C.require(prior["status"]=="ACTUAL_DECLARED_SCHEDULER_CONFIG_CHECKED" and
        prior["source_ref"]==full["source_ref"]==source and prior["NPU_initialized"]is False and
        prior["full_engine_config_verified"]is False and prior["full_engine_config_required_at_N1"]is True and
        prior["model_config_constructed"]is False and full["model_config_constructed"]is True and
        full["status"]=="ACTUAL_FULL_ENGINE_CONFIG_CHECKED" and full["full_engine_config_verified"]is True,
        "honest Devices[] partial then genuine N1 full config")
    C.require(prior["kwargs"]==full["kwargs"] and prior["runtime_origins"]==full["runtime_origins"] and
        prior["torch_origin"]==full["torch_origin"] and prior["torch_npu_origin"]==full["torch_npu_origin"] and
        all(full["effective"].get(k)==v for k,v in prior["effective"].items()),
        "same source/common actual configuration CPU to N1 before weights")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--output");a=ap.parse_args()
    if not a.execute:print(json.dumps({"default_enabled":False,"model_loaded":False}));return
    C.configure(a.source_manifest_sha256)
    C.require(not list(Path("/dev").glob("davinci*"))and not any(Path("/dev",n).exists()for n in("devmm_svm","hisi_hdc")),
        "actual Devices[] partial CPU config prerequisite")
    base=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
    sys.path.insert(0,str(base))
    from io_contract import publish_json
    print(json.dumps(publish_json(a.output,construct()),sort_keys=True))
if __name__=="__main__":main()
