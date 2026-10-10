"""Mixed B16/40960 config adapter. CPU is NOT a ModelConfig or HAL proof.
v008's source reader is reused exactly; its CPU create_model_config is never used.
MAIN's actual probe showed model registry -> Triton Ascend get_arch needs HAL.
"""
import hashlib,importlib,importlib.util,inspect,sys
from pathlib import Path
PROOF_SHA="431f29ca7c6b62e880e782a2afb8d36f2e1dfd10179fe9c0ca525f655815f2ae"
POLICY=dict(max_num_seqs=16,max_num_batched_tokens=40960,max_model_len=33792,
 tensor_parallel_size=4,enforce_eager=True,enable_chunked_prefill=True,
 enable_prefix_caching=False,async_scheduling=False,mamba_cache_mode="none",
 worker_cls="kivi_mixed_bootstrap.MixedWorker",kv_cache_memory_bytes=6*1024**3)
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p).resolve();b=p.read_bytes()
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def proof(m):
 r=m["runtime_roles"]["native_config_proof"]
 need(r["sha256"]==PROOF_SHA and ref(r["path"])==r and r in m["files"]+m["dependencies"],"exact v008 source reader, not its failed CPU run")
 n="_mixed_actual_config_v008_reader"
 if n in sys.modules:
  q=sys.modules[n];need(ref(q.__file__)==r,"no foreign proof namespace");return q
 s=importlib.util.spec_from_file_location(n,r["path"]);q=importlib.util.module_from_spec(s)
 sys.modules[n]=q
 try:s.loader.exec_module(q)
 except BaseException:sys.modules.pop(n,None);raise
 return q
def parsed(args,expected):
 need(expected==POLICY,"unique mixed policy, not B1")
 for key,value in POLICY.items():
  need(type(getattr(args,key))is type(value) and getattr(args,key)==value,"actual parsed mixed policy "+key)
def scheduler_policy(s):
 need(type(s.max_num_batched_tokens)is int and s.max_num_batched_tokens==40960
  and type(s.max_num_seqs)is int and s.max_num_seqs==16 and s.enable_chunked_prefill is True
  and s.async_scheduling is False,"B16/40960 chunked/noasync")
 need(s.long_prefill_token_threshold==0 and s.max_num_partial_prefills==s.max_long_partial_prefills==1
  and s.max_num_scheduled_tokens in(None,40960) and s.scheduler_reserve_full_isl is True,
  "same full-input reserve and no alternate subchunk schedule")
 return dict(max_num_batched_tokens=s.max_num_batched_tokens,max_num_seqs=s.max_num_seqs,
  enable_chunked_prefill=s.enable_chunked_prefill,async_scheduling=s.async_scheduling,
  max_num_partial_prefills=s.max_num_partial_prefills,max_long_partial_prefills=s.max_long_partial_prefills,
  long_prefill_token_threshold=s.long_prefill_token_threshold,
  max_num_scheduled_tokens=s.max_num_scheduled_tokens,scheduler_reserve_full_isl=s.scheduler_reserve_full_isl)
def scheduler_necessary(args,scheduler_cls):
 # Actual SchedulerConfig with CLI scalars only. The encoder/runner values are
 # explicit policy assumptions, NOT a fake or partially constructed ModelConfig.
 # They are re-proved against the real normalized model at N1 and production.
 s=scheduler_cls(runner_type="generate",is_encoder_decoder=False,
  max_model_len=args.max_model_len,max_num_batched_tokens=args.max_num_batched_tokens,
  max_num_seqs=args.max_num_seqs,enable_chunked_prefill=args.enable_chunked_prefill,
  async_scheduling=args.async_scheduling,max_num_partial_prefills=args.max_num_partial_prefills,
  max_long_partial_prefills=args.max_long_partial_prefills,
  long_prefill_token_threshold=args.long_prefill_token_threshold,
  scheduler_reserve_full_isl=args.scheduler_reserve_full_isl)
 return scheduler_policy(s)
def require_engine_config(config):
 m=config.model_config;s=config.scheduler_config;p=config.parallel_config;c=config.cache_config
 need(m.architecture=="Qwen3_5ForConditionalGeneration" and m.hf_config.model_type=="qwen3_5"
  and m.runner_type=="generate" and m.is_encoder_decoder is False and m.is_chunked_prefill_supported is True,
  "actual model registry resolves required generative chunked architecture")
 need(m.max_model_len==33792 and m.enforce_eager is True,"same eager full domain")
 observed=scheduler_policy(s)
 need(p.tensor_parallel_size==4 and p.pipeline_parallel_size==p.data_parallel_size==1
  and p.prefill_context_parallel_size==p.decode_context_parallel_size==1
  and p.worker_cls==POLICY["worker_cls"] and p.enable_dbo is False,"same actual TP4/CP1/worker/noDBO")
 need(c.enable_prefix_caching is False and c.mamba_cache_mode=="none"
  and c.kv_cache_memory_bytes==POLICY["kv_cache_memory_bytes"],"same common cache/prefix OFF")
 need(config.speculative_config is config.kv_transfer_config is config.ec_transfer_config is None,
  "no hidden speculation/cache/encoder transfer")
 need(config.compilation_config.cudagraph_mode.name==config.compilation_config.mode.name=="NONE",
  "actual eager no graph/compile")
 return dict(scheduler=observed,architecture=m.architecture,model_type=m.hf_config.model_type,
  model_verified=True,full_engine_config_verified=True)
def record(m,stage,installed,observed,full):
 return dict(schema="kivi.actual-mixed-native-config/v2",source_ref=m["runtime_roles"]["native_config_adapter"],
  stage=stage,policy=dict(POLICY),actual_installed_sources=installed,observed=observed,
  actual_objects_built=True,actual_scheduler_config_constructed=True,
  actual_model_config_constructed=full,model_verified=full,full_engine_config_built=full,
  CPU_model_registry_called=False if stage=="cpu" else None,weights_loaded=False,engine_started=False,
  model_ready=False,performance_ready=False,run_authority=False)
def validate_record(x,m,stage):
 need(x["schema"]=="kivi.actual-mixed-native-config/v2" and x["source_ref"]==m["runtime_roles"]["native_config_adapter"]
  and x["stage"]==stage and x["policy"]==POLICY and x["actual_objects_built"]is True
  and x["actual_scheduler_config_constructed"]is True,"actual mixed config record identity")
 full=stage in("n1","server")
 need(x["actual_model_config_constructed"]is x["model_verified"]is x["full_engine_config_built"]is full,
  "CPU necessary invariants never count as actual model/full config")
 for key in("weights_loaded","engine_started","model_ready","performance_ready","run_authority"):
  need(x[key]is False,"config scope "+key)
 if not full:need(x["CPU_model_registry_called"]is False,"CPU must never call model registry")
 from types import SimpleNamespace
 observed=x["observed"]
 scheduler_policy(SimpleNamespace(**observed["scheduler"]))
 need(observed["model_verified"]is full and observed["full_engine_config_verified"]is full,
  "observed model capability not borrowed from CPU")
 if full:need(observed["architecture"]=="Qwen3_5ForConditionalGeneration"
  and observed["model_type"]=="qwen3_5","actual normalized architecture")
 pins=proof(m).PINS
 need(set(x["actual_installed_sources"])==set(pins)
  and all(x["actual_installed_sources"][n]["sha256"]==h for n,h in pins.items()),"actual official config sources")
 return x
def check_mixed_config(*,api,args,stage,torch,source_manifest,expected_policy):
 m=source_manifest;need(stage in("cpu","n1"),"actual CPU or all4 N1 only");parsed(args,expected_policy)
 p=proof(m);installed=p.actual_sources()
 if stage=="cpu":
  need(torch.npu.is_initialized()is False,"Devices[] before scalar scheduler")
  scheduler=importlib.import_module("vllm.config.scheduler").SchedulerConfig
  observed=dict(scheduler=scheduler_necessary(args,scheduler),
   model_verified=False,assumptions=dict(runner_type="generate",is_encoder_decoder=False),
   full_engine_config_verified=False)
  need(torch.npu.is_initialized()is False,"CPU scheduler caused no NPU initialization")
 else:
  engine=api.AsyncEngineArgs.from_cli_args(args)
  usage=importlib.import_module("vllm.usage.usage_lib").UsageContext.OPENAI_API_SERVER
  observed=require_engine_config(engine.create_engine_config(usage_context=usage))
 return record(m,stage,installed,observed,stage=="n1")
def install_engine_config_gate(*,api,source_manifest,publish):
 m=source_manifest;p=proof(m);installed=p.actual_sources()
 original=api.AsyncEngineArgs.create_engine_config
 need(ref(inspect.getfile(original))["sha256"]==p.PINS["vllm.engine.arg_utils"],"actual native factory no stacked wrapper")
 def checked(self,*args,**kwargs):
  config=original(self,*args,**kwargs)
  observed=require_engine_config(config)
  publish(record(m,"server",p.actual_sources(),observed,True))
  return config
 api.AsyncEngineArgs.create_engine_config=checked
 def restore():
  need(api.AsyncEngineArgs.create_engine_config is checked,"owned production gate still installed")
  api.AsyncEngineArgs.create_engine_config=original
 return restore
