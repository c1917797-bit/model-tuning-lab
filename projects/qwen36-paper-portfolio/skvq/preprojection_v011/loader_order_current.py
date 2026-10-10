"""DEFAULT OFF; actual already-loaded source-bound legacy QKV loader observation.
No Torch/model/group imports or calls. No weights changed or fake native PASS.
"""
import hashlib,inspect,os,sys
from pathlib import Path
from qkv_projection_current import qualified,ASCEND,PARAMETER
LINEAR_MODULE="vllm.model_executor.layers.linear"
LINEAR_SHA="a5e099997f868a5ce670aa2afe94da90222fceace36aef4e1275f3830ee257ab"
WORKER_SHA="c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3"
BASE="/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001"
def require(v,m):
    if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def actual(outer,rank):
    require(os.environ.get("QWEN36_SKVQ_TP4_CAPTURE_ENABLE")=="1","explicit MAIN-owned capture opt-in")
    require(type(rank) is int and 0<=rank<4,"actual provider public TP rank")
    m=sys.modules.get(LINEAR_MODULE);require(m is not None,"already-loaded real linear module")
    path=Path(m.__file__)
    require(path.is_absolute() and m.__spec__.name==LINEAR_MODULE and
      Path(m.__spec__.origin).resolve()==path.resolve() and sha(path)==LINEAR_SHA,"real deployed linear loader source pin")
    cls,qualification=qualified()
    p=outer.qkv_proj
    require(type(p) is cls and p.disable_tp is False and
      p.gather_output is False and p.tp_rank==rank and p.tp_size==4,"exact actual TP-sharded QKV projection object")
    require(outer.attn_output_gate is True and outer.num_heads==6 and outer.num_kv_heads==1 and
      outer.head_dim==256 and outer.total_num_heads==24 and outer.total_num_kv_heads==4,"real TP4 FA Q/KV/gate")
    require(p.head_size==p.v_head_size==256 and p.total_num_heads==48 and p.num_heads==12 and
      p.total_num_kv_heads==4 and p.num_kv_heads==1 and p.num_kv_head_replicas==1,"real q-gate projection doubling / no KV replication")
    require(type(p.quant_method)is sys.modules[ASCEND].AscendUnquantizedLinearMethod and
      p.custom_op is None and p.return_bias is True and p.skip_bias_add is False,
      "actual source-qualified ordinary native unquantized projection path")
    require(p.output_sizes==[12288,1024,1024] and p.output_partition_sizes==[3072,256,256] and
      p.quant_config is None and p.hidden_size==outer.hidden_size,"real A16 local qgate/K/V output slices")
    fn=m.QKVParallelLinear.weight_loader
    require(inspect.isfunction(fn) and fn.__module__==LINEAR_MODULE and
      Path(inspect.getsourcefile(fn)).resolve()==path.resolve() and
      Path(fn.__code__.co_filename).resolve()==path.resolve(),"unmodified original legacy loader function")
    params={}
    for name in ("weight","bias"):
        value=getattr(p,name)
        if value is None:
            require(name=="bias","actual weight exists");params[name]=None;continue
        require(type(value)is sys.modules[PARAMETER].ModelWeightParameter if name=="weight" else False,
          "exact original unquantized ModelWeightParameter; current qkv_bias false")
        loader=value.weight_loader
        require(inspect.ismethod(loader) and loader.__self__ is p and loader.__func__ is fn,
          "actual loaded parameter bound to source-pinned legacy QKV loader; no v2 assumption")
        require(value.output_dim==0 and value.tp_rank==rank and value.tp_size==4 and
          not getattr(value,"is_sharded_weight",False) and
          not getattr(value,"use_bitsandbytes_4bit",False) and
          not getattr(value,"is_gguf_weight",False) and
          not getattr(value,"is_gguf_weight_type",False) and
          getattr(value,"packed_dim",None) is None,"normal unpacked unquantized TP parameter only")
        expected=[3584,p.hidden_size] if name=="weight" else [3584]
        require(list(value.shape)==expected and str(value.dtype) in ("torch.float16","torch.bfloat16") and
          value.device.type=="npu","actual original A16 loaded parameter shape/device")
        params[name]={"shape":list(value.shape),"dtype":str(value.dtype),"device":str(value.device),
          "data_ptr":value.data_ptr(),"storage_ptr":value.untyped_storage().data_ptr(),
          "storage_offset":value.storage_offset(),"tp_rank":value.tp_rank,"tp_size":value.tp_size,
          "output_dim":value.output_dim,"bound_legacy_loader":True}
    require(p._get_shard_offset_mapping("k")==3072 and p._get_shard_offset_mapping("v")==3328 and
      p._get_shard_size_mapping("k")==p._get_shard_size_mapping("v")==256,"actual source-method local packing offsets")
    return {"native_projection_qualification":qualification,"schema":"SKVQ_ACTUAL_QKV_LEGACY_ORDER_V1","rank":rank,"linear_source":{"path":str(path),"sha256":LINEAR_SHA},
      "q_gate":True,"global_fa_q_heads":24,"local_fa_q_heads":6,
      "global_q_projection_heads":48,"local_q_projection_heads":12,
      "global_kv_heads":4,"local_kv_heads":1,"kv_head_replicas":1,"head_dim":256,
      "legacy_kv_shard_rank":rank,"local_projection_offsets":{"k":3072,"v":3328},
      "global_kv_head":rank,"global_kv_channel_indices":list(range(rank*256,(rank+1)*256)),
      "actual_parameter_loader":"QKVParallelLinear.weight_loader","parameters":params,
      "actual_weight_publisher_identity_pending":True,"not_npu_numeric_pass":True}
if __name__=="__main__":
    import json
    print(json.dumps({"default_enabled":False,"Torch_imported":"torch" in sys.modules,"model_launched":False,
      "global_order_runtime_verified":False,"native_ready":False}))
