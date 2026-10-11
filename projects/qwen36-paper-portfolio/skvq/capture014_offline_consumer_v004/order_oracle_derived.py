"""Independent stdlib TP4 head-channel oracle; never imports the provider/Torch."""
def require(v,m):
    if not v:raise ValueError(m)
SHA="a5e099997f868a5ce670aa2afe94da90222fceace36aef4e1275f3830ee257ab"
def consume_record(v,rank):
    require(v["schema"]=="SKVQ_ACTUAL_QKV_LEGACY_ORDER_V1" and type(rank) is int and 0<=rank<4 and v["rank"]==rank,"actual source/rank scope")
    require(v["linear_source"]["sha256"]==SHA and v["q_gate"] is True and
      (v["global_fa_q_heads"],v["local_fa_q_heads"],v["global_q_projection_heads"],v["local_q_projection_heads"])==(24,6,48,12),"Q gate not conflated with FA heads")
    require((v["global_kv_heads"],v["local_kv_heads"],v["kv_head_replicas"],v["head_dim"])==(4,1,1,256),"no replicated/cross-shard KV interpretation")
    require(v["legacy_kv_shard_rank"]==rank and v["global_kv_head"]==rank and
      v["global_kv_channel_indices"]==[head*256+d for head in [rank] for d in range(256)] and
      v["local_projection_offsets"]=={"k":3072,"v":3328},"independent head-major channel map")
    consume_qualification(v["native_projection_qualification"])
    require(v["actual_parameter_loader"]=="QKVParallelLinear.weight_loader","legacy real bound loader only")
    for side,r in v["parameters"].items():
        if r is None:
            require(side=="bias","real weight required");continue
        require(r["bound_legacy_loader"] is True and r["tp_rank"]==rank and r["tp_size"]==4 and
          r["output_dim"]==0 and r["shape"][0]==3584 and r["dtype"] in ("torch.float16","torch.bfloat16") and
          r["data_ptr"]>0 and r["storage_ptr"]>0,"actual recorded A16 loaded parameter binding")
    return list(v["global_kv_channel_indices"])
def consume_four(records):
    require(type(records) is dict and set(records)==set(range(4)),"all4 actual rank records")
    joined=[i for r in range(4) for i in consume_record(records[r],r)]
    require(joined==list(range(1024)),"full unique1024 source-global KV hidden channels")
    return joined

# Independent exact source/runtime identity, no provider/Torch import or shared math.
PINS=[
  {
    "module": "vllm.model_executor.layers.linear",
    "runtime_path": "/vllm-workspace/vllm/vllm/model_executor/layers/linear.py",
    "snapshot": {
      "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/source-public-linear-660-20261008-1106-001/linear.py",
      "sha256": "a5e099997f868a5ce670aa2afe94da90222fceace36aef4e1275f3830ee257ab",
      "bytes": 63273
    }
  },
  {
    "module": "vllm_ascend.ops.linear",
    "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py",
    "snapshot": {
      "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-actual-linear-projection-source-660-20261010-001/ascend_linear.py",
      "bytes": 21354,
      "sha256": "3f14a92019a6612158ba41a26c358c8f164cbda66b743c518a5e4019694b5dc3"
    }
  },
  {
    "module": "vllm.model_executor.custom_op",
    "runtime_path": "/vllm-workspace/vllm/vllm/model_executor/custom_op.py",
    "snapshot": {
      "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-actual-linear-projection-source-660-20261010-001/custom_op.py",
      "bytes": 13924,
      "sha256": "4b4ba01623005d6a93698eaec007a934dd512bf9ec7241090927de819621de2e"
    }
  },
  {
    "module": "vllm.model_executor.parameter",
    "runtime_path": "/vllm-workspace/vllm/vllm/model_executor/parameter.py",
    "snapshot": {
      "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-actual-linear-projection-source-660-20261010-001/parameter.py",
      "bytes": 21976,
      "sha256": "ff6054fbd19ec932c548d562c6f4cc4506383b71cbe411fcfd554c8b1d87b510"
    }
  },
  {
    "module": "vllm_ascend.ops.linear_op",
    "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py",
    "snapshot": {
      "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-actual-linear-projection-source-660-20261010-001/linear_op.py",
      "bytes": 30813,
      "sha256": "0333d3229dbfed3010413510b76395a9ad89138dfd1d578caab057573b6cd0fb"
    }
  },
  {
    "module": "vllm_ascend.utils",
    "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/utils.py",
    "snapshot": {
      "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/utils.py",
      "bytes": 67646,
      "sha256": "575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02"
    }
  }
]
METHODS={
  "forward": {
    "name": "forward",
    "module": "vllm_ascend.ops.linear",
    "path": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py"
  },
  "constructor": {
    "name": "__init__",
    "module": "vllm_ascend.ops.linear",
    "path": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py"
  },
  "column_constructor": {
    "name": "__init__",
    "module": "vllm_ascend.ops.linear",
    "path": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py"
  },
  "legacy_loader": {
    "name": "weight_loader",
    "module": "vllm.model_executor.layers.linear",
    "path": "/vllm-workspace/vllm/vllm/model_executor/layers/linear.py"
  },
  "offset": {
    "name": "_get_shard_offset_mapping",
    "module": "vllm.model_executor.layers.linear",
    "path": "/vllm-workspace/vllm/vllm/model_executor/layers/linear.py"
  },
  "size": {
    "name": "_get_shard_size_mapping",
    "module": "vllm.model_executor.layers.linear",
    "path": "/vllm-workspace/vllm/vllm/model_executor/layers/linear.py"
  },
  "create_weights": {
    "name": "create_weights",
    "module": "vllm.model_executor.layers.linear",
    "path": "/vllm-workspace/vllm/vllm/model_executor/layers/linear.py"
  },
  "get_parallel_op": {
    "name": "get_parallel_op",
    "module": "vllm_ascend.ops.linear_op",
    "path": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py"
  }
}
def consume_qualification(value):
    import hashlib
    from pathlib import Path
    require(value["schema"]=="skvq.actual-native-QKV-class/v1","new explicit native class source")
    require(set(value["runtime_origins"])=={p["module"]for p in PINS},"exact six QKV native origins")
    for p in PINS:
        ref=p["snapshot"];raw=Path(ref["path"]).read_bytes()
        require(len(raw)==ref["bytes"]and hashlib.sha256(raw).hexdigest()==ref["sha256"],"whole source snapshot")
        require(value["runtime_origins"][p["module"]]==dict(module=p["module"],path=p["runtime_path"],sha256=ref["sha256"]),
            "original deployed runtime source equals entire snapshot")
    require(value["class_module"]=="vllm_ascend.ops.linear"and value["class_name"]=="AscendQKVParallelLinear"and
        value["direct_base_module"]=="vllm.model_executor.layers.linear"and value["direct_base_name"]=="QKVParallelLinear"and
        value["original_OOT_registration"]is True and value["quant_method"]=="AscendUnquantizedLinearMethod"and
        value["constructor_loader_branch"]=="legacy"and value["parameter_class"]=="ModelWeightParameter"and
        value["methods"]==METHODS and value["weights_loading_executed_by_qualification"]is False and
        value["projection_called"]is False and value["live_TP_parameter_geometry_verified"]is False,
        "exact native class/forward/legacy constructor binding, no borrowed live parameter authority")
    return value
def consume_preweights(value,source,read):
    require(value["schema"]=="skvq.preweights-native-QKV-qualification/v1"and value["source_ref"]==source and
        value["actual_original_registry_called"]is True and value["weights_loaded"]is False and
        value["live_TP_parameter_geometry_verified"]is False,"actual no-weight native qualification only")
    consume_qualification(value["qualification"]);raw=read(value["raw_ref"])
    require(raw["source_ref"]==source and type(raw["pid"])is int and raw["pid"]>1 and
        raw["class_module"]=="vllm_ascend.ops.linear"and raw["class_name"]=="AscendQKVParallelLinear"and
        raw["actual_bases"]==["vllm.model_executor.layers.linear.QKVParallelLinear"]and
        raw["original_OOT_alias_is_native"]is True and
        "AscendUnquantizedLinearMethod"not in raw["actual_V2_supported_method_names"]and
        raw["actual_parameter_class"]=="vllm.model_executor.parameter.ModelWeightParameter"and
        raw["weights_loaded"]is False and raw["projection_called"]is False,
        "persisted actual original representation before strict native QKV class gate")
    return value
def consume_install_raw(value,rank,identity,records,source,*,loader_identity):
    from capture_identity import exact,pair
    from tp_provider_current import consume_identity
    require(exact(value["identity"],loader_identity),"raw and loader reuse same first original observation")
    pair(value["identity"],identity,rank,consume_identity)
    require(value["schema"]=="skvq.QKV-install-before-qualification/v1"and value["source_ref"]==source and
        value["rank"]==rank and set(value["observed"])==set(records),
        "complete original all16 same-worker raw before first projection qualification")
    for logical,record in records.items():
        observed=value["observed"][logical];consume_record(record,rank)
        require(observed["actual_class"]=="vllm_ascend.ops.linear.AscendQKVParallelLinear"and
            observed["actual_class_MRO"][1]=="vllm.model_executor.layers.linear.QKVParallelLinear"and
            observed["quant_method_type"]=="vllm_ascend.ops.linear.AscendUnquantizedLinearMethod"and
            observed["custom_op"]==dict(type="builtins.NoneType",value=None),
            "original native class/ordinary local projection path, not unknown subclass")
        fields=observed["fields"]
        for name,want in (("disable_tp",False),("gather_output",False),("tp_rank",rank),("tp_size",4),
            ("head_size",256),("v_head_size",256),("total_num_heads",48),("num_heads",12),
            ("total_num_kv_heads",4),("num_kv_heads",1),("num_kv_head_replicas",1),
            ("output_sizes",[12288,1024,1024]),("output_partition_sizes",[3072,256,256]),
            ("quant_config",None),("return_bias",True),("skip_bias_add",False)):
            require(fields[name]==dict(type="builtins."+type(want).__name__,value=want),"original typed field: "+name)
        weight=observed["parameters"]["weight"]
        require(observed["parameters"]["bias"]is None and
            weight["actual_class"]=="vllm.model_executor.parameter.ModelWeightParameter"and
            weight["shape"]==record["parameters"]["weight"]["shape"]and
            weight["dtype"]==record["parameters"]["weight"]["dtype"]and
            weight["device"]==record["parameters"]["weight"]["device"]and
            weight["loader_module"]=="vllm.model_executor.layers.linear"and
            weight["loader_qualname"]=="QKVParallelLinear.weight_loader"and
            weight["loader_bound_self_is_projection"]is True,
            "raw original unquantized parameter matches qualified record")
    return value

