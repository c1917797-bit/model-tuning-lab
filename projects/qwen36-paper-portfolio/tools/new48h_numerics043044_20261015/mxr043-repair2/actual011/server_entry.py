"""Source-bound server launcher for one real EAGER32768+2 diagnostic. Default OFF."""
import argparse,hashlib,importlib,importlib.util,json,os,runpy,sys
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def native_argv(port,cache_bytes):
    need(type(port)is int and 1024<=port<=65535 and type(cache_bytes)is int
         and 0<cache_bytes<=10*1024**3,"explicit bounded common configuration")
    return ["--model","/models/Qwen3.6-27B","--served-model-name","qwen36",
        "--dtype","bfloat16","--seed","0","--data-parallel-size","1","--disable-log-stats",
        "--host","127.0.0.1","--port",str(port),"--tensor-parallel-size","4",
        "--max-model-len","33792","--max-num-seqs","1","--max-num-batched-tokens","32768",
        "--kv-cache-memory-bytes",str(cache_bytes),"--no-enable-prefix-caching",
        "--mamba-cache-mode","none","--enable-chunked-prefill","--no-async-scheduling",
        "--enforce-eager","--worker-cls","kivi_firstdecode_bootstrap.FirstDecodeWorker"]
def parse_native(api,port,cache_bytes):
    parser=api.make_arg_parser(api.FlexibleArgumentParser(description=__doc__))
    args=parser.parse_args(native_argv(port,cache_bytes))
    api.validate_parsed_serve_args(args)
    need(args.dtype=="bfloat16" and args.seed==0 and args.data_parallel_size==1,
         "actual common BF16/seed0/DP1 parser options")
    need(args.async_scheduling is False and args.enable_chunked_prefill is True
         and args.enable_prefix_caching is False and args.mamba_cache_mode=="none"
         and args.enforce_eager is True and args.max_num_seqs==1
         and args.max_num_batched_tokens==32768,"actual deployed parser/config; no guessed bool values")
    return args

def require_engine_config(config,proof,cache_bytes):
    policy=proof.require_firstdecode_policy(config.model_config,config.scheduler_config,cache_bytes)
    need(str(config.model_config.dtype)=="torch.bfloat16" and config.model_config.seed==0,
         "actual common BF16 and seed0 after native config normalization")
    need(config.parallel_config.tensor_parallel_size==4
         and config.parallel_config.pipeline_parallel_size==config.parallel_config.data_parallel_size==1
         and config.parallel_config.prefill_context_parallel_size==config.parallel_config.decode_context_parallel_size==1
         and config.parallel_config.worker_cls=="kivi_firstdecode_bootstrap.FirstDecodeWorker"
         and config.parallel_config.enable_dbo is False,"unchanged native TP4/PP1/DP1/CP1/own worker/no DBO")
    need(config.cache_config.enable_prefix_caching is False and config.cache_config.mamba_cache_mode=="none"
         and config.cache_config.kv_cache_memory_bytes==cache_bytes,"same actual common prefix OFF/Mamba none/cache bytes")
    need(config.speculative_config is None and config.kv_transfer_config is None
         and config.ec_transfer_config is None,"no speculation/external cache/encoder transfer")
    need(config.compilation_config.cudagraph_mode.name=="NONE"
         and config.compilation_config.mode.name=="NONE","actual eager/no graph or compilation")
    return policy

def actual_config_precheck(api,args,stage,torch,proof,cache_bytes):
    need(stage in("cpu","n1"),"only actual CPU8 or N1 config checks")
    installed=proof.actual_sources()
    if stage=="cpu":need(torch.npu.is_initialized()is False,"Devices[] before actual config")
    if stage=="cpu":
        # Even actual ModelConfig invokes installed Qwen registry/HAL inspection.
        # Only actual parser -> original SchedulerConfig scalar constraints here.
        from vllm.config.scheduler import SchedulerConfig
        scheduler=proof.cpu_scheduler_config(args,SchedulerConfig)
        policy=proof.require_cpu_policy(args,scheduler,cache_bytes)
        need(torch.npu.is_initialized()is False,"CPU scalar config did not initialize NPU")
        full=False
    else:
        engine=api.AsyncEngineArgs.from_cli_args(args)
        from vllm.usage.usage_lib import UsageContext
        config=engine.create_engine_config(usage_context=UsageContext.OPENAI_API_SERVER)
        policy=require_engine_config(config,proof,cache_bytes);full=True
    return dict(schema="kivi.actual-firstdecode-effective-config/v1",stage=stage,
        actual_installed_sources=installed,actual_policy=policy,
        actual_model_config_constructed=full,actual_scheduler_config_constructed=True,
        model_dependent_scheduler_fields_verified=full,
        cpu_scheduler_assumptions=dict(proof.CPU_SCHEDULER_ASSUMPTIONS)if stage=="cpu"else None,
        full_engine_config_verified=full,engine_or_weights_created=False,
        model_ready=False,performance_ready=False,run_authority=False)

def install_engine_config_gate(api,proof,cache_bytes,publish):
    # This guard is in the actual API server's existing config creation call:
    # original create_engine_config -> validate final normalized config ->
    # return that SAME object; only then can API instantiate the engine.
    original=api.AsyncEngineArgs.create_engine_config
    proof.actual_sources()
    import inspect
    need(hashlib.sha256(Path(inspect.getfile(original)).read_bytes()).hexdigest()
         ==proof.PINS["vllm.engine.arg_utils"],"original installed config factory; no stacked wrapper")
    def checked(self,*args,**kwargs):
        config=original(self,*args,**kwargs)
        policy=require_engine_config(config,proof,cache_bytes)
        publish(dict(schema="kivi.actual-firstdecode-effective-config/v1",stage="server",
            actual_installed_sources=proof.actual_sources(),actual_policy=policy,
            full_engine_config_verified=True,engine_or_weights_created=False,
            model_ready=False,performance_ready=False,run_authority=False))
        return config
    api.AsyncEngineArgs.create_engine_config=checked
    def restore():
        need(api.AsyncEngineArgs.create_engine_config is checked,"actual config wrapper not replaced")
        api.AsyncEngineArgs.create_engine_config=original
    return restore

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    p.add_argument("--source-manifest-sha256");p.add_argument("--recipe-ref-json",type=Path)
    p.add_argument("--port",type=int,default=8250);p.add_argument("--cache-bytes",type=int,required=False)
    a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps(dict(default_enabled=False,model_ready=False,performance_ready=False)));return 0
    need(type(a.port)is int and 1024<=a.port<=65535 and a.recipe_ref_json is not None,
         "bounded explicit actual diagnostic port/recipe")
    here=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location("_kivi_firstdecode_source_loader",here/"loader.py")
    need(spec.name not in sys.modules,"no ambient server loader")
    l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
    m,source_ref,mods,adapter,new,own=l.load(a.source_manifest_sha256,memory_limit=64*1024**3)
    recipe_ref=json.loads(a.recipe_ref_json.read_bytes());recipe=l.obj(recipe_ref)
    need(recipe["source_ref"]==source_ref and recipe["cache_bytes"]==a.cache_bytes
         and type(a.cache_bytes)is int and 0<a.cache_bytes<=10*1024**3,
         "same preregistered actual common-cache value; no intuitive fitting")
    os.environ["QWEN36_KIVI_FIRSTDECODE_SOURCE_SHA256"]=a.source_manifest_sha256
    os.environ["QWEN36_KIVI_FIRSTDECODE_INPUT_REF"]=json.dumps(recipe_ref,separators=(",",":"))
    own["screen_gate"].worker_check(recipe,l.obj,source_ref)
    need(recipe["algorithm_arm"]==os.environ.get("QWEN36_KIVI_SCREEN_ARM"),"same source-declared actual arm")
    # Explicit non-IAB Python search path for native child resolver; all source-bound.
    os.environ["PYTHONPATH"]=str(here)+(os.pathsep+os.environ["PYTHONPATH"]if os.environ.get("PYTHONPATH")else"")
    if str(here)not in sys.path:sys.path.insert(0,str(here))
    from vllm.v1.engine.input_processor import InputProcessor
    from vllm.v1.engine.async_llm import AsyncLLM
    l.publish(Path(recipe["diagnostic_root"])/("CANN-SERVER-p%d.json"%os.getpid()),
              dict(source_ref=source_ref,recipe_ref=recipe_ref,actual_pid=os.getpid(),
                   binding=own["cann_python_binding"],cached_after_frontend_imports=own["cann_python"].cached(),
                   model_ready=False,performance_ready=False))
    restore=own["ownership"].install_frontend(InputProcessor,AsyncLLM,new["assignment_capture"],
                                              new["bindings"],new["assignment_oracle"],recipe,l.obj,l.publish)
    api=importlib.import_module("vllm.entrypoints.openai.api_server")
    actual=Path(api.__file__).resolve()
    need(l.ref(actual)["sha256"]==m["installed_api_server_sha256"],"actual deployed api_server source")
    api.cli_env_setup()
    args=parse_native(api,a.port,a.cache_bytes)
    proof=l.module("_kivi_firstdecode_config_proof",l.own(m,"config_cpu.py"))
    config_path=Path(recipe["diagnostic_root"])/("SERVER-CONFIG-p%d.json"%os.getpid())
    restore_config=install_engine_config_gate(api,proof,a.cache_bytes,
        lambda value:l.publish(config_path,dict(value,source=source_ref,recipe_ref=recipe_ref,
                                                actual_pid=os.getpid())))
    try:api.uvloop.run(api.run_server(args))
    finally:
        try:restore_config()
        finally:restore()
    return 0
if __name__=="__main__":raise SystemExit(main())
