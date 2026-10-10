"""Concrete mixed configuration adapter interface with exact source binding.
CPU proves only SchedulerConfig necessary invariants; N1 constructs full config.
The immutable deployment manifest binds the adapter and official source closure.
"""
POLICY=dict(max_num_seqs=16,max_num_batched_tokens=40960,max_model_len=33792,
 tensor_parallel_size=4,enforce_eager=True,enable_chunked_prefill=True,
 enable_prefix_caching=False,async_scheduling=False,mamba_cache_mode="none",
 worker_cls="kivi_mixed_bootstrap.MixedWorker",kv_cache_memory_bytes=6*1024**3)
def actual(api,args,stage,torch,m,loader):
 loader.need(stage in("cpu","n1"),"source/parser versus hardware config scope")
 for key,value in POLICY.items():loader.need(getattr(args,key)==value,"mixed parsed policy "+key)
 row=m["runtime_roles"]["native_config_adapter"]
 loader.need(row in m["files"]+m["dependencies"],"external exact config source in mounted closure")
 helper=loader.module("_mixed_external_native_config",row)
 # CPU never calls ModelConfig/registry on Devices[]. The concrete adapter
 # distinguishes actual scheduler necessary invariants from N1 full config.
 result=helper.check_mixed_config(api=api,args=args,stage=stage,torch=torch,
  source_manifest=m,expected_policy=dict(POLICY))
 loader.need(type(result)is dict and result["schema"]=="kivi.actual-mixed-native-config/v2"
  and result["source_ref"]==row and result["stage"]==stage and result["policy"]==POLICY
 and result["actual_objects_built"]is True
  and result["full_engine_config_built"]is(stage=="n1")
  and result["weights_loaded"]is False and result["engine_started"]is False
  and result["model_ready"]is False,"actual source-bound configuration, not parser-only PASS")
 return helper.validate_record(result,m,stage)
