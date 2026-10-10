"""Exact image660 QKV OOT qualification; default OFF, no Torch/native imports.
Observes already-loaded objects only. No weight loading or projection is executed.
"""
import hashlib,importlib,inspect,json,os,sys
from pathlib import Path
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
PUBLIC="vllm.model_executor.layers.linear"
ASCEND="vllm_ascend.ops.linear"
CUSTOM="vllm.model_executor.custom_op"
PARAMETER="vllm.model_executor.parameter"
OP="vllm_ascend.ops.linear_op"
UTILITY="vllm_ascend.utils"
def require(v,m):
    if not v:raise ValueError(m)
def origin(name):
    pin=next(p for p in PINS if p["module"]==name);m=sys.modules.get(name)
    require(m is not None and m.__name__==name and m.__spec__.name==name,
        "already-loaded exact QKV module: "+name)
    path=Path(m.__file__)
    require(str(path)==pin["runtime_path"]and Path(m.__spec__.origin).resolve()==path.resolve()and
        hashlib.sha256(path.read_bytes()).hexdigest()==pin["snapshot"]["sha256"],
        "whole exact actual QKV module source: "+name)
    return m,dict(module=name,path=str(path),sha256=pin["snapshot"]["sha256"])
def function(fn,name,module,path):
    require(inspect.isfunction(fn)and fn.__name__==name and fn.__module__==module and
        Path(inspect.getsourcefile(fn)).resolve()==Path(path).resolve()and
        Path(fn.__code__.co_filename).resolve()==Path(path).resolve(),
        "exact source-defined QKV function: "+name)
    return dict(module=module,name=name,path=str(path))
def qualified():
    modules={};origins={}
    for pin in PINS:modules[pin["module"]],origins[pin["module"]]=origin(pin["module"])
    m=modules[PUBLIC];a=modules[ASCEND];c=modules[CUSTOM];p=modules[PARAMETER];o=modules[OP];u=modules[UTILITY]
    cls=a.AscendQKVParallelLinear
    require(inspect.isclass(cls)and cls.__module__==ASCEND and cls.__name__=="AscendQKVParallelLinear"and
        cls.__bases__==(m.QKVParallelLinear,)and inspect.getmodule(cls)is a and
        Path(inspect.getsourcefile(cls)).resolve()==Path(a.__file__).resolve(),
        "only exact native Ascend QKV direct subclass, not arbitrary subclass")
    require(a.QKVParallelLinear is m.QKVParallelLinear and a.ColumnParallelLinear is m.ColumnParallelLinear and
        c.op_registry_oot.get("QKVParallelLinear")is cls and
        u.REGISTERED_ASCEND_OPS.get("QKVParallelLinear")is cls and u._ASCEND_CUSTOMOP_IS_REIGISTERED is True,
        "actual original OOT registry plus native registration")
    require(a.AscendUnquantizedLinearMethod.__bases__==(m.UnquantizedLinearMethod,)and
        a.AscendUnquantizedLinearMethod.__name__ not in m.WEIGHT_LOADER_V2_SUPPORTED and
        a.WEIGHT_LOADER_V2_SUPPORTED is m.WEIGHT_LOADER_V2_SUPPORTED,
        "actual Ascend unquantized constructor chooses legacy QKV loader, not public v2 assumption")
    methods={}
    for label,fn,name,module in (
        ("forward",cls.__dict__["forward"],"forward",ASCEND),
        ("constructor",cls.__dict__["__init__"],"__init__",ASCEND),
        ("column_constructor",a.AscendColumnParallelLinear.__dict__["__init__"],"__init__",ASCEND),
        ("legacy_loader",cls.weight_loader,"weight_loader",PUBLIC),
        ("offset",cls._get_shard_offset_mapping,"_get_shard_offset_mapping",PUBLIC),
        ("size",cls._get_shard_size_mapping,"_get_shard_size_mapping",PUBLIC),
        ("create_weights",a.AscendUnquantizedLinearMethod.create_weights,"create_weights",PUBLIC),
        ("get_parallel_op",a.get_parallel_op,"get_parallel_op",OP)):
        methods[label]=function(fn,name,module,origins[module]["path"])
    require(cls.weight_loader is m.QKVParallelLinear.weight_loader and
        a.AscendUnquantizedLinearMethod.create_weights is m.UnquantizedLinearMethod.create_weights and
        a.get_parallel_op is o.get_parallel_op and m.ModelWeightParameter is p.ModelWeightParameter,
        "exact original inherited loader/create-weights/TP selector/parameter")
    return cls,dict(schema="skvq.actual-native-QKV-class/v1",runtime_origins=origins,
        class_module=ASCEND,class_name="AscendQKVParallelLinear",direct_base_module=PUBLIC,
        direct_base_name="QKVParallelLinear",original_OOT_registration=True,
        quant_method="AscendUnquantizedLinearMethod",constructor_loader_branch="legacy",
        parameter_class="ModelWeightParameter",methods=methods,weights_loading_executed_by_qualification=False,
        projection_called=False,live_TP_parameter_geometry_verified=False)
def forward(p):
    cls,_=qualified();fn=p.forward
    require(type(p)is cls and inspect.ismethod(fn)and fn.__self__ is p and fn.__func__ is cls.forward and
        "forward"not in p.__dict__,"original Ascend projection instance forward before own tap")
    return fn
def observation(outer):
    """Evidence only: missing/unreadable fields are recorded, never accepted."""
    p=outer.qkv_proj
    def typed(value):
        if value is None or type(value)in(bool,int,float,str):return dict(type=type(value).__module__+"."+type(value).__qualname__,value=value)
        if type(value)in(list,tuple)and all(type(v)is int for v in value):return dict(type=type(value).__module__+"."+type(value).__qualname__,value=list(value))
        return dict(type=type(value).__module__+"."+type(value).__qualname__,raw_repr=repr(value))
    def field(obj,name):
        try:return typed(getattr(obj,name))
        except (AttributeError,RuntimeError)as e:return dict(unreadable=type(e).__name__,message=str(e))
    fields=("disable_tp","gather_output","tp_rank","tp_size","head_size","v_head_size","total_num_heads",
        "num_heads","total_num_kv_heads","num_kv_heads","num_kv_head_replicas","output_sizes",
        "output_partition_sizes","quant_config","hidden_size","return_bias","skip_bias_add","prefix")
    result=dict(actual_class=type(p).__module__+"."+type(p).__qualname__,
        actual_class_MRO=[c.__module__+"."+c.__qualname__ for c in type(p).__mro__],
        fields={n:field(p,n)for n in fields},custom_op=field(p,"custom_op"),
        quant_method_type=type(p.quant_method).__module__+"."+type(p.quant_method).__qualname__,parameters={})
    for name in("weight","bias"):
        value=getattr(p,name)
        if value is None:result["parameters"][name]=None;continue
        loader=value.weight_loader
        result["parameters"][name]=dict(actual_class=type(value).__module__+"."+type(value).__qualname__,
            shape=list(value.shape),dtype=str(value.dtype),device=str(value.device),
            loader_module=getattr(getattr(loader,"__func__",loader),"__module__",None),
            loader_qualname=getattr(getattr(loader,"__func__",loader),"__qualname__",None),
            loader_bound_self_is_projection=getattr(loader,"__self__",None)is p,
            output_dim=field(value,"output_dim"),tp_rank=field(value,"tp_rank"),tp_size=field(value,"tp_size"))
    return result
def preweights(source,destination,publish):
    """Real N1 only after all4tiny/fullEngine. No groups, weights, or synthetic model."""
    require(os.environ.get("QWEN36_SKVQ_TP4_CAPTURE_ENABLE")=="1","explicit capture opt-in")
    u=importlib.import_module(UTILITY);_,uo=origin(UTILITY)
    function(u.register_ascend_customop,"register_ascend_customop",UTILITY,uo["path"])
    u.register_ascend_customop() # Original idempotent registry, not fabricated alias assignment.
    for name in(PUBLIC,ASCEND,CUSTOM,PARAMETER,OP):importlib.import_module(name)
    a=sys.modules[ASCEND];c=sys.modules[CUSTOM]
    raw=publish(destination,dict(source_ref=source,pid=os.getpid(),
        class_module=a.AscendQKVParallelLinear.__module__,class_name=a.AscendQKVParallelLinear.__name__,
        actual_bases=[v.__module__+"."+v.__qualname__ for v in a.AscendQKVParallelLinear.__bases__],
        original_OOT_alias_is_native=c.op_registry_oot.get("QKVParallelLinear")is a.AscendQKVParallelLinear,
        actual_V2_supported_method_names=list(sys.modules[PUBLIC].WEIGHT_LOADER_V2_SUPPORTED),
        actual_parameter_class=sys.modules[PARAMETER].ModelWeightParameter.__module__+"."+sys.modules[PARAMETER].ModelWeightParameter.__name__,
        weights_loaded=False,projection_called=False))
    cls,value=qualified()
    return dict(schema="skvq.preweights-native-QKV-qualification/v1",source_ref=source,
        raw_ref=raw,qualification=value,actual_original_registry_called=True,
        weights_loaded=False,live_TP_parameter_geometry_verified=False)
if __name__=="__main__":
    print(json.dumps(dict(default_enabled=False,Torch_imported="torch"in sys.modules,model_launched=False)))
