"""Source-bound mixed EAGER capture server, actual factory guard. Default OFF."""
import argparse,importlib,importlib.util,json,os,runpy,sys
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def native_argv(port,cache_bytes):
    need(type(port)is int and 1024<=port<=65535 and type(cache_bytes)is int
         and cache_bytes==6*1024**3,"explicit bounded common configuration")
    return ["--model","/models/Qwen3.6-27B","--served-model-name","qwen36",
        "--host","127.0.0.1","--port",str(port),"--tensor-parallel-size","4",
        "--max-model-len","33792","--max-num-seqs","16","--max-num-batched-tokens","40960",
        "--kv-cache-memory-bytes",str(cache_bytes),"--no-enable-prefix-caching",
        "--mamba-cache-mode","none","--enable-chunked-prefill","--no-async-scheduling",
        "--enforce-eager","--worker-cls","kivi_mixed_bootstrap.MixedWorker"]
def parse_native(api,port,cache_bytes):
    parser=api.make_arg_parser(api.FlexibleArgumentParser(description=__doc__))
    args=parser.parse_args(native_argv(port,cache_bytes))
    api.validate_parsed_serve_args(args)
    need(args.async_scheduling is False and args.enable_chunked_prefill is True
         and args.enable_prefix_caching is False and args.mamba_cache_mode=="none"
         and args.enforce_eager is True and args.max_num_seqs==16
         and args.max_num_batched_tokens==40960,"actual deployed parser/config; no guessed bool values")
    return args
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    p.add_argument("--source-manifest-sha256");p.add_argument("--recipe-ref-json",type=Path)
    p.add_argument("--port",type=int,default=8250);p.add_argument("--cache-bytes",type=int,required=False)
    a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps(dict(default_enabled=False,model_ready=False,performance_ready=False)));return 0
    need(type(a.port)is int and 1024<=a.port<=65535 and a.recipe_ref_json is not None,
         "bounded explicit actual diagnostic port/recipe")
    here=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location("_kivi_mixed_source_loader",here/"loader.py")
    need(spec.name not in sys.modules,"no ambient server loader")
    l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
    m,source_ref,mods,adapter,new,own=l.load(a.source_manifest_sha256,memory_limit=64*1024**3)
    recipe_ref=json.loads(a.recipe_ref_json.read_bytes());recipe=l.obj(recipe_ref)
    need(recipe["source_ref"]==source_ref and recipe["cache_bytes"]==a.cache_bytes
         and type(a.cache_bytes)is int and a.cache_bytes==6*1024**3,
         "same preregistered actual common-cache value; no intuitive fitting")
    os.environ["QWEN36_KIVI_FIRSTDECODE_SOURCE_SHA256"]=a.source_manifest_sha256
    os.environ["QWEN36_KIVI_FIRSTDECODE_INPUT_REF"]=json.dumps(recipe_ref,separators=(",",":"))
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
    check=l.module("_mixed_config_bridge",l.own(m,"config_bridge.py"))
    l.publish(Path(recipe["diagnostic_root"])/"ACTUAL-ENGINE-CONFIG.json",check.actual(api,args,"n1",__import__("torch"),m,l))
    helper=l.module("_mixed_external_native_config",m["runtime_roles"]["native_config_adapter"])
    restore_config=helper.install_engine_config_gate(api=api,source_manifest=m,
        publish=lambda value:l.publish(Path(recipe["diagnostic_root"])/"ACTUAL-PRODUCTION-ENGINE-CONFIG.json",
            dict(value,source=source_ref,recipe_ref=recipe_ref,actual_pid=os.getpid())))
    try:api.uvloop.run(api.run_server(args))
    finally:
        try:restore_config()
        finally:restore()
    return 0
if __name__=="__main__":raise SystemExit(main())
