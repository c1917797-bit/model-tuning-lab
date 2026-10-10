"""Local source-body projections, NEVER real framework/NPU evidence.
Actual pinned dataclasses/factories/native methods/allocator/lifecycle bodies run.
Only framework imports, tensors and device fences are inert metadata test doubles.
"""
import ast, collections, copy, dataclasses, enum, hashlib, json, math, os, sys, threading, types
from pathlib import Path

ROOT=Path("C:/Users/Huawei/AppData/Local/Temp")
SHARED=Path("C:/Users/Huawei/AppData/Local/Packages/sandbox.{48fdcea7-5947-498c-a068-4bc4cdaddb04}/AC/Temp/kivi-c132-reviewed-source/model-deps")
PATHS={
 "interface":(ROOT/"c158-kivi014-provider-source/kv_cache_interface.py","8d6be98bbf75b3d55007b64ccf5afef047ca01790a432522f70a196412c103d9"),
 "utils":(ROOT/"c158-kivi014-provider-source/kv_cache_utils.py","b89f9afa7f95fcc30412ae2031d5370a23e95f35d068fa14e5824dce1c900ee5"),
 "native":(ROOT/"c156-kivi-native-reviewed-20261010/npu_worker.py","c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3"),
 "runner":(SHARED/"runner-94d75.py","94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"),
 "lifecycle":(SHARED/"device_lifecycle.py","20e49b37b1fc62201dd749813e5aba56dd9211bbaf140c672dca5162e190a533"),
 "writer":(SHARED/"device_writer.py","051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b"),
 "pool":(ROOT/"c158-native-worker-cache-source/v1__core__block_pool.py","84755b84c36ed6460ceefe2690c9484a9c31488c5da6daa6c918f497d8837dee"),
 "manager":(ROOT/"c158-native-worker-cache-source/v1__core__single_type_kv_cache_manager.py","dc425e1e87b6157f3e5c46be2bfee54076ccb020b86c5a8aaa3d9901c75e46ef"),
}
# The local archive is explicit fixture mode, never a remote framework substitute.
HERE=Path(__file__).resolve().parent
if os.environ.get("KIVI_PROVIDER_LOCAL_ARCHIVE")!="1":
    manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
    refs=manifest["dependencies"]
    PATHS={role:(Path(next(r["path"] for r in refs if r["sha256"]==sha)),sha)
           for role,(path,sha) in PATHS.items()}
    LAYOUT_PATH=Path(manifest["provider_original_failed_layout"]["path"])
    LAYOUT_CONSUMER_PATH=Path(manifest["runtime_roles"]["kivi_layout_consumer"]["path"])
else:
    LAYOUT_PATH=ROOT/"c158-kivi014-actual/r0-p387-s56400319-LAYOUT.json"
    LAYOUT_CONSUMER_PATH=SHARED/"kivi_layout_consumer.py"
def projection(role, names, env, methods=None):
    path,sha=PATHS[role];wire=path.read_bytes()
    assert hashlib.sha256(wire).hexdigest()==sha,(path,"pin")
    tree=ast.parse(wire.decode("utf-8"),str(path))
    nodes=[]
    for node in tree.body:
        if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names:
            if methods and node.name in methods:
                node=copy.deepcopy(node)
                node.body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name in methods[node.name]]
            nodes.append(node)
    assert {n.name for n in nodes}==set(names)
    module=types.ModuleType("_provider_fixture_"+role);module.__file__=str(path)
    module.__dict__.update(env);sys.modules[module.__name__]=module
    future=ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0)
    code=ast.fix_missing_locations(ast.Module(body=[future]+nodes,type_ignores=[]))
    exec(compile(code,str(path),"exec"),module.__dict__)
    return module

class Tensor:
    next_base=100000000000
    def __init__(self,shape,dtype,device,events):
        self.shape=tuple(shape if isinstance(shape,(list,tuple)) else (shape,))
        self.dtype=dtype;self.device=device;self.events=events
        self.base=Tensor.next_base;Tensor.next_base+=self.numel()*self.element_size()+4096
    def numel(self):return math.prod(self.shape)
    def element_size(self):return {"torch.int8":1,"torch.int32":4,"torch.float32":4,"torch.int64":8,
                                   "torch.bfloat16":2,"torch.float16":2}[self.dtype]
    def zero_(self):self.events.append("zero");return self
    def copy_(self,other):self.events.append("copy");return self
    def __getitem__(self,item):return self
    def __mul__(self,value):return self
    def fill_(self,value):return self
def describe(t):
    stride=[];step=1
    for n in reversed(t.shape):stride.insert(0,step);step*=n
    return dict(shape=list(t.shape),stride=stride,dtype=t.dtype,device=t.device,
                element_size=t.element_size(),logical_bytes=t.numel()*t.element_size(),
                storage_base=t.base,storage_bytes=t.numel()*t.element_size(),
                storage_offset_elements=0,data_ptr=t.base,contiguous=True,observed_format_code=2)
def torch_fixture(events):
    t=types.SimpleNamespace()
    for name in ("int8","int32","float32","int64","bfloat16","float16"):setattr(t,name,"torch."+name)
    t.dtype=object;t.Tensor=Tensor;t.device=lambda value:value
    t.empty=lambda shape,*,dtype,device:Tensor(shape,dtype,device,events)
    t.zeros=lambda shape,*,dtype,device:t.empty(shape,dtype=dtype,device=device).zero_()
    t.arange=lambda count,*,dtype,device:t.empty((count,),dtype=dtype,device=device)
    t.inference_mode=lambda:lambda fn:fn
    t.npu=types.SimpleNamespace(synchronize=lambda:events.append("sync"))
    return t

def actual_modules(events):
    t=torch_fixture(events)
    common=dict(copy=copy,Counter=collections.Counter,defaultdict=collections.defaultdict,
        dataclass=dataclasses.dataclass,fields=dataclasses.fields,replace=dataclasses.replace,
        Enum=enum.Enum,IntEnum=enum.IntEnum,prod=math.prod,torch=t,
        cdiv=lambda a,b:(a+b-1)//b,round_up=lambda a,b:(a+b-1)//b*b,
        get_dtype_size=lambda d:{"torch.bfloat16":2,"torch.float16":2,"torch.float32":4}[d],
        MambaAttentionBackendEnum=types.SimpleNamespace(MAMBA2="MAMBA2"),
        logger=types.SimpleNamespace(warning=lambda *x:None,info=lambda *x:None,debug=lambda *x:None))
    interface=projection("interface",[
        "KVQuantMode","KVCacheSpec","AttentionSpec","FullAttentionSpec","MLAAttentionSpec",
        "HiddenStateCacheSpec","SlidingWindowSpec","SlidingWindowMLASpec","MambaSpec",
        "UniformTypeKVCacheSpecs","KVCacheTensor","KVCacheGroupSpec","KVCacheConfig"],common)
    interface.KVCacheSpecRegistry=types.SimpleNamespace(get_uniform_type_base_spec=lambda s:type(s))
    env=dict(common,**{n:getattr(interface,n) for n in dir(interface) if not n.startswith("_") and n not in common})
    utils=projection("utils",[
        "get_kv_cache_groups","is_kv_cache_type_attention_free","is_kv_cache_spec_uniform",
        "group_and_unify_kv_cache_specs","unify_kv_cache_spec_page_size",
        "_get_kv_cache_groups_uniform_page_size","create_kv_cache_group_specs",
        "get_kv_cache_config_from_groups","get_num_blocks","may_override_num_blocks","get_uniform_page_size",
        "get_max_concurrency_for_kv_cache_config","max_memory_usage_bytes",
        "KVCacheBlock","FreeKVCacheBlockQueue"],env)
    writer=projection("writer",["make_shifts","allocate_writer_arena","seal_k_into","seal_v_into"],{})
    lifecycle=projection("lifecycle",["require","Request","CompactArena","ReadView"],
        dict(threading=threading,dataclass=dataclasses.dataclass,**{n:getattr(writer,n) for n in
             ("allocate_writer_arena","seal_k_into","seal_v_into")}))
    native=projection("native",["NPUWorker"],dict(env,GiB_bytes=1024**3,WorkerBase=object,
        ensure_kv_transfer_initialized=lambda *args:events.append("native_transfer_check")),
        methods={"NPUWorker":{"determine_available_memory","initialize_from_config","get_kv_cache_spec"}})
    # Inert layer API results come from the preserved actual014 layout dimensions.
    # Crucially the container, FA-before-Mamba traversal and padding are ORIGINAL
    # runner code, not a hand-built replacement dictionary.
    class AttentionLayerBase: pass
    class Attention(AttentionLayerBase):
        kv_sharing_target_layer_name=None
        def __init__(self,spec):self.spec=spec
        def get_kv_cache_spec(self,config):return self.spec
    class MambaBase(AttentionLayerBase):
        def __init__(self,spec):self.spec=spec
        def get_kv_cache_spec(self,config):return self.spec
    runner_env=dict(env,GPUModelRunner=object,
        is_hidden_state_cache_spec=lambda spec:False,has_ec_transfer=lambda:False,
        get_layers_from_vllm_config=lambda config,base:config.fixture_attention_layers,
        AttentionLayerBase=AttentionLayerBase,Attention=Attention,MambaBase=MambaBase,
        MLAAttention=type("UnusedMLAAttention",(AttentionLayerBase,),{}),
        CacheOnlyAttentionLayer=type("UnusedCacheOnly",(AttentionLayerBase,),{}))
    runner=projection("runner",["NPUModelRunner"],runner_env,methods={"NPUModelRunner":{
        "_allocate_kv_cache_tensors","_get_layer_kv_cache_specs","get_kv_cache_spec"}})
    runner.NPUModelRunner.fixture_Attention=Attention
    runner.NPUModelRunner.fixture_MambaBase=MambaBase
    return t,interface,utils,lifecycle,native.NPUWorker,runner.NPUModelRunner

def config(max_seqs=1):
    N=types.SimpleNamespace
    return N(cache_config=N(kv_cache_memory_bytes=6*1024**3,num_gpu_blocks_override=None,
             mamba_cache_mode="none",enable_prefix_caching=False),
             model_config=N(max_model_len=33792,enforce_eager=True,enable_sleep_mode=False,dtype="torch.bfloat16"),
             parallel_config=N(tensor_parallel_size=4,pipeline_parallel_size=1,
                               decode_context_parallel_size=1,prefill_context_parallel_size=1),
             scheduler_config=N(disable_hybrid_kv_cache_manager=False,max_num_seqs=max_seqs),
             speculative_config=None,kv_transfer_config=None)

def specs_from_actual(interface):
    import json
    p=LAYOUT_PATH;wire=p.read_bytes()
    assert hashlib.sha256(wire).hexdigest()=="6c74e99297f6e1edd7745d45aa2a9c492253983c994714f2793c1a38605e2035"
    event=json.loads(wire);specs={}
    # Actual source dataclasses from exact native event dimensions; NOT new runtime evidence.
    for name,row in event["layers"].items():
        if row["kind"]=="FA":
            spec=interface.FullAttentionSpec(block_size=row["block_size"],num_kv_heads=row["num_kv_heads"],
                head_size=row["head_size"],dtype=row["views"][0]["dtype"],page_size_padded=row["page_size_bytes"])
        else:
            spec=interface.MambaSpec(block_size=row["block_size"],shapes=tuple(tuple(s) for s in row["shapes"]),
                 dtypes=tuple(row["dtypes"]),page_size_padded=row["page_size_bytes"],mamba_cache_mode="none")
        specs[name]=spec
    # Native runner scans model order, not JSON lexical serialization order.
    return dict(sorted(specs.items(),key=lambda x:int(x[0].split(".layers.")[1].split(".")[0])))

def new_runner(cls,cfg,specs,events):
    r=cls();r.vllm_config=cfg;r.model_config=cfg.model_config;r.device="npu:0";r.use_compress=False
    r.runner_only_attn_layers=set()
    r.shared_kv_cache_layers={}
    # Registry input remains model layer order; actual runner reorders the output.
    cfg.fixture_attention_layers={
        name:(cls.fixture_Attention(spec) if type(spec).__name__=="FullAttentionSpec"
              else cls.fixture_MambaBase(spec))
        for name,spec in sorted(specs.items(),key=lambda item:int(item[0].split(".layers.")[1].split(".")[0]))}
    r.profile_run=lambda:events.append("native_profile")
    def initialize(kv):
        events.append("native_initialize");r.kv_cache_config=copy.deepcopy(kv)
        r.raw=r._allocate_kv_cache_tensors(r.kv_cache_config)
        events.append("native_reshape_bind_fixture")
    r.initialize_kv_cache=initialize
    return r

def actual_managers(interface,utils):
    from abc import ABC,abstractmethod
    env=dict(ABC=ABC,abstractmethod=abstractmethod,defaultdict=collections.defaultdict,
             cdiv=lambda a,b:(a+b-1)//b,KVCacheBlock=utils.KVCacheBlock,
             FreeKVCacheBlockQueue=utils.FreeKVCacheBlockQueue)
    env.update({n:getattr(interface,n) for n in ("FullAttentionSpec","MambaSpec","MLAAttentionSpec")})
    # This unused specialized type is only referenced in a type equality tuple.
    env["TQFullAttentionSpec"]=type("UnusedTQFullAttentionSpec",(),{})
    pool=projection("pool",["BlockHashToBlockMap","BlockPool"],env)
    env["BlockPool"]=pool.BlockPool
    managers=projection("manager",["SingleTypeKVCacheManager","FullAttentionManager","MambaManager"],env)
    return pool,managers

