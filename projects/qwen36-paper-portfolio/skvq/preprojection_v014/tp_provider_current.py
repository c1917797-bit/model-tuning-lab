"""Exact image660 Ascend TP implementation adapter. Default OFF; no native import.
Only the archived GroupCoordinatorPatch is accepted. This never creates a group.
"""
import argparse,hashlib,importlib,inspect,json,os,sys,time
from pathlib import Path
PARALLEL_SOURCE="/cache/cch/qwen36-paper-preparation-20261007/recurrent/deltalog-v3/source_blobs/parallel_state.py"
PARALLEL_SHA="df02e5386bc83e6ac644ff46f0297fdd19003bd55584c629840348a5fda8473f"
PARALLEL_MODULE="vllm.distributed.parallel_state"
NATIVE_PINS=[
    {
        "module": "vllm_ascend.utils",
        "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/utils.py",
        "snapshot": {
            "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/utils.py",
            "bytes": 67646,
            "sha256": "575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02"
        }
    },
    {
        "module": "vllm_ascend.distributed.parallel_state",
        "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/distributed/parallel_state.py",
        "snapshot": {
            "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/distributed__parallel_state.py",
            "bytes": 15442,
            "sha256": "96ba7d62ffec181f8881c82a5499a53085f9ce4fdd7087ca7ed5d738e1acfc83"
        }
    },
    {
        "module": "vllm_ascend.patch.worker",
        "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/__init__.py",
        "snapshot": {
            "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/patch__worker__init__.py",
            "bytes": 3949,
            "sha256": "11002e315e93b2534d1fa4e859cf5bdcfbb22caaae370a26f29fbf586144cfb6"
        }
    },
    {
        "module": "vllm_ascend.patch.platform",
        "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/patch/platform/__init__.py",
        "snapshot": {
            "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/patch__platform__init__.py",
            "bytes": 2785,
            "sha256": "09a72414f791e8383692e87e50449feb66d63330ac428a14f9edd5afdcf9e627"
        }
    },
    {
        "module": "vllm_ascend.patch.worker.patch_distributed",
        "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_distributed.py",
        "snapshot": {
            "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/patch__worker__patch_distributed.py",
            "bytes": 9834,
            "sha256": "0fcc178ed9497705df47bdab59649ae59dc452f99121f95b43cd10cdc3efc411"
        }
    },
    {
        "module": "vllm_ascend.patch.platform.patch_distributed",
        "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/patch/platform/patch_distributed.py",
        "snapshot": {
            "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/patch__platform__patch_distributed.py",
            "bytes": 3341,
            "sha256": "a37863ccf18652313a7defacc066202b2df6bcf3b1a2009f75dde2efc80e7815"
        }
    },
    {
        "module": "vllm_ascend.patch.worker._hccl_pg_registry",
        "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/_hccl_pg_registry.py",
        "snapshot": {
            "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/patch__worker___hccl_pg_registry.py",
            "bytes": 9047,
            "sha256": "a30ece7f18625c51b87a05e0c24a8ca416ebe421aaeee80f35424232e3df35ce"
        }
    },
    {
        "module": "vllm_ascend.distributed.device_communicators.npu_communicator",
        "runtime_path": "/vllm-workspace/vllm-ascend/vllm_ascend/distributed/device_communicators/npu_communicator.py",
        "snapshot": {
            "path": "/cache/cch/qwen36-paper-preparation-20261007/MAIN-tp-runtime-source-660-20261010-001/distributed__device_communicators__npu_communicator.py",
            "bytes": 2810,
            "sha256": "7e84ea85f03729e62eb5a92760fe0b920654fda6059e370ae6fae80e70579a94"
        }
    }
]
PATCH_MODULE="vllm_ascend.patch.worker.patch_distributed"
GETTERS=("get_tp_group","get_world_group","get_tensor_model_parallel_rank",
    "get_tensor_model_parallel_world_size","get_pp_group","get_dp_group","get_pcp_group","get_dcp_group")
PATCH_METHODS=("__init__","_init_device_groups","_init_device_communicator","_release_hccl_resources",
    "destroy","destroy_hccl","restore_hccl","all_to_all")
def require(value,message):
    if not value:raise ValueError(message)
def file_sha(path):
    p=Path(path);require(p.is_file()and not p.is_symlink(),"actual regular source")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def module_origin(module,name,expected_sha=None):
    require(module is not None and module.__name__==name,"already imported original runtime module: "+name)
    spec=module.__spec__;path=Path(module.__file__)
    require(spec is not None and spec.name==name and spec.origin is not None and
        path.is_absolute()and Path(spec.origin).resolve()==path.resolve(),"actual module loader origin")
    digest=file_sha(path)
    if expected_sha is not None:require(digest==expected_sha,"actual deployed module byte pin: "+name)
    return {"module":name,"path":str(path),"sha256":digest}
def function_origin(module,name,path):
    fn=getattr(module,name)
    require(inspect.isfunction(fn)and fn.__name__==name and fn.__module__==module.__name__ and
        Path(inspect.getsourcefile(fn)).resolve()==Path(path).resolve()and
        Path(fn.__code__.co_filename).resolve()==Path(path).resolve(),"original imported callable origin: "+name)
    return fn
def process_start():
    raw=Path("/proc/self/stat").read_text();return int(raw[raw.rfind(")")+2:].split()[19])
def runtime_origins():
    result={}
    for pin in NATIVE_PINS:
        row=module_origin(sys.modules.get(pin["module"]),pin["module"],pin["snapshot"]["sha256"])
        require(row["path"]==pin["runtime_path"],"exact deployed Ascend module path")
        result[pin["module"]]=row
    return result
def qualified_class(ps):
    public=module_origin(ps,PARALLEL_MODULE,PARALLEL_SHA)
    origins=runtime_origins();patch=sys.modules[PATCH_MODULE]
    original=patch.GroupCoordinator;cls=patch.GroupCoordinatorPatch
    require(inspect.isclass(original)and original.__name__=="GroupCoordinator"and
        original.__module__==PARALLEL_MODULE and inspect.getmodule(original)is ps and
        Path(inspect.getsourcefile(original)).resolve()==Path(public["path"]).resolve(),
        "exact original public class retained as direct base")
    require(inspect.isclass(cls)and cls.__name__=="GroupCoordinatorPatch"and
        cls.__module__==PATCH_MODULE and inspect.getmodule(cls)is patch and
        cls.__bases__==(original,)and ps.GroupCoordinator is cls and
        Path(inspect.getsourcefile(cls)).resolve()==Path(origins[PATCH_MODULE]["path"]).resolve(),
        "only exact deployed Ascend GroupCoordinatorPatch alias")
    require(patch._register_group is ps._register_group and patch._get_unique_name is ps._get_unique_name,
        "original registration/name functions retained")
    for name in ("_register_group","_get_unique_name"):function_origin(ps,name,public["path"])
    methods={}
    for name in PATCH_METHODS:
        fn=cls.__dict__.get(name)
        require(inspect.isfunction(fn)and fn.__name__==name and fn.__module__==PATCH_MODULE and
            Path(inspect.getsourcefile(fn)).resolve()==Path(origins[PATCH_MODULE]["path"]).resolve()and
            Path(fn.__code__.co_filename).resolve()==Path(origins[PATCH_MODULE]["path"]).resolve(),
            "actual source-defined patch method: "+name)
        methods[name]={"module":fn.__module__,"name":fn.__name__,"path":fn.__code__.co_filename}
    for name in GETTERS:function_origin(ps,name,public["path"])
    require(ps._TP_STATE_PATCHED is False,"no alternate patched TP-state semantics")
    value={"schema":"skvq.actual-native-tp-class/v1","public_source":public,
        "runtime_origins":origins,"class_module":PATCH_MODULE,"class_name":"GroupCoordinatorPatch",
        "direct_base_module":PARALLEL_MODULE,"direct_base_name":"GroupCoordinator",
        "public_alias_is_exact_patch":True,"original_registration_retained":True,
        "original_getters":list(GETTERS),"methods":methods,"TP_STATE_PATCHED":False,
        "group_construction_or_collective_called":False,"live_TP_groups_verified":False}
    return cls,value
def consume_class(value):
    require(type(value)is dict and value["schema"]=="skvq.actual-native-tp-class/v1","actual native class schema")
    require(file_sha(PARALLEL_SOURCE)==PARALLEL_SHA,"whole original public source archive")
    public=value["public_source"]
    require(set(public)=={"module","path","sha256"}and public["module"]==PARALLEL_MODULE and
        public["path"]=="/vllm-workspace/vllm/vllm/distributed/parallel_state.py"and
        public["sha256"]==PARALLEL_SHA,"actual public runtime source identity")
    require(set(value["runtime_origins"])=={p["module"]for p in NATIVE_PINS},"exact native runtime source set")
    for pin in NATIVE_PINS:
        require(file_sha(pin["snapshot"]["path"])==pin["snapshot"]["sha256"]and
            Path(pin["snapshot"]["path"]).stat().st_size==pin["snapshot"]["bytes"],"whole native archive")
        require(value["runtime_origins"][pin["module"]]=={"module":pin["module"],"path":pin["runtime_path"],
            "sha256":pin["snapshot"]["sha256"]},"actual native runtime source equals exact archive")
    require(value["class_module"]==PATCH_MODULE and value["class_name"]=="GroupCoordinatorPatch"and
        value["direct_base_module"]==PARALLEL_MODULE and value["direct_base_name"]=="GroupCoordinator"and
        value["public_alias_is_exact_patch"]is True and value["original_registration_retained"]is True and
        value["original_getters"]==list(GETTERS)and value["TP_STATE_PATCHED"]is False and
        value["group_construction_or_collective_called"]is False and value["live_TP_groups_verified"]is False,
        "exact class qualification is not live group or model authority")
    require(set(value["methods"])==set(PATCH_METHODS),"exact source-defined class methods")
    path=next(p["runtime_path"]for p in NATIVE_PINS if p["module"]==PATCH_MODULE)
    for name in PATCH_METHODS:
        require(value["methods"][name]=={"module":PATCH_MODULE,"name":name,"path":path},"exact patch method source")
    return value
def preweights(source,destination,publish):
    """After actual all4 tiny/fullConfig only. Invoke original adapt_patch(False), no worker/groups."""
    require(os.environ.get("QWEN36_SKVQ_TP4_CAPTURE_ENABLE")=="1","explicit opt-in")
    import torch,torch_npu
    require(torch.npu is torch_npu.npu and not torch.distributed.is_initialized(),
        "no initialized distributed state in preweights qualification process")
    utility=importlib.import_module("vllm_ascend.utils")
    pin=next(p for p in NATIVE_PINS if p["module"]==utility.__name__)
    module_origin(utility,utility.__name__,pin["snapshot"]["sha256"])
    function_origin(utility,"adapt_patch",pin["runtime_path"])
    before=process_start();utility.adapt_patch(is_global_patch=False)
    ps=sys.modules.get(PARALLEL_MODULE);patch=sys.modules.get(PATCH_MODULE)
    raw={"source_ref":source,"pid":os.getpid(),"pid_start_ticks":before,
        "class_module":getattr(getattr(ps,"GroupCoordinator",None),"__module__",None),
        "class_name":getattr(getattr(ps,"GroupCoordinator",None),"__name__",None),
        "patch_loaded":patch is not None,"distributed_initialized":torch.distributed.is_initialized()}
    raw_ref=publish(destination,raw) # Persist actual state before the strict class gate.
    cls,qualified=qualified_class(ps)
    # Execute this exact native representation method without __init__/PG creation.
    # Source body short-circuits communicator construction when this flag is False.
    torch.npu.set_device(0)
    shell=object.__new__(cls);shell.use_device_communicator=False
    cls._init_device_communicator(shell)
    current=torch.npu.current_device()
    representation={"source_ref":source,"pid":os.getpid(),"pid_start_ticks":before,
        "method_source":qualified["methods"]["_init_device_communicator"],
        "actual_device_repr":repr(shell.device),"actual_device_type":type(shell.device).__module__+"."+type(shell.device).__qualname__,
        "actual_device_value":shell.device if type(shell.device)is int else None,
        "actual_current_device_repr":repr(current),
        "actual_current_device_type":type(current).__module__+"."+type(current).__qualname__,
        "actual_current_device_value":current if type(current)is int else None,
        "use_device_communicator":False,"GroupCoordinator_init_called":False,
        "distributed_initialized":torch.distributed.is_initialized(),"live_TP_groups_verified":False}
    representation_ref=publish(Path(destination).with_name("N1-NATIVE-DEVICE-REPRESENTATION-RAW.json"),representation)
    require(type(shell.device)is int and type(current)is int and shell.device==current==0,
        "real original native method returns true int logical device0")
    require(not torch.distributed.is_initialized()and process_start()==before,
        "preweights did not initialize process groups and retains same process")
    return {"schema":"skvq.preweights-native-tp-qualification/v1","source_ref":source,
        "raw_ref":raw_ref,"representation_ref":representation_ref,"pid":os.getpid(),"pid_start_ticks":before,"qualification":qualified,
        "actual_original_adapt_patch_false_called":True,"distributed_initialized_before":False,
        "distributed_initialized_after":False,"weights_loaded":False,"live_TP_groups_verified":False}
def consume_preweights(value,source,read):
    require(value["schema"]=="skvq.preweights-native-tp-qualification/v1"and value["source_ref"]==source and
        value["actual_original_adapt_patch_false_called"]is True and value["distributed_initialized_before"]is False and
        value["distributed_initialized_after"]is False and value["weights_loaded"]is False and
        value["live_TP_groups_verified"]is False,"actual preweights qualification only")
    raw=read(value["raw_ref"])
    require(raw["source_ref"]==source and raw["pid"]==value["pid"]and
        raw["pid_start_ticks"]==value["pid_start_ticks"]and raw["class_module"]==PATCH_MODULE and
        raw["class_name"]=="GroupCoordinatorPatch"and raw["patch_loaded"]is True and
        raw["distributed_initialized"]is False,"actual raw before class assertions")
    qualification=consume_class(value["qualification"])
    raw=read(value["representation_ref"])
    require(raw["source_ref"]==source and raw["pid"]==value["pid"]and
        raw["pid_start_ticks"]==value["pid_start_ticks"]and
        raw["method_source"]==qualification["methods"]["_init_device_communicator"]and
        raw["actual_device_type"]==raw["actual_current_device_type"]=="builtins.int"and
        type(raw["actual_device_value"])is int and type(raw["actual_current_device_value"])is int and
        raw["actual_device_value"]==raw["actual_current_device_value"]==0 and
        raw["actual_device_repr"]==raw["actual_current_device_repr"]=="0"and
        raw["use_device_communicator"]is False and raw["GroupCoordinator_init_called"]is False and
        raw["distributed_initialized"]is False and raw["live_TP_groups_verified"]is False,
        "actual native method representation without fake live group authority")
    return qualification
def logical_device(group,current,name):
    require(type(current)is int and 0<=current<4 and type(group.device)is int and
        type(group.local_rank)is int and group.device==group.local_rank==current,
        "source-defined true integer logical NPU device: "+name)
    return current
def group_snapshot(module,group,dist,name,world,current):
    require(type(group)is module.GroupCoordinator,"exact deployed GroupCoordinatorPatch: "+name)
    require(module._groups.get(group.unique_name)is not None and module._groups[group.unique_name]()is group,
        "actual registered live group: "+name)
    require(type(group.world_size)is int and group.world_size==world and type(group.ranks)is list and
        len(group.ranks)==world and len(set(group.ranks))==world and all(type(x)is int for x in group.ranks),
        "actual group members: "+name)
    require(type(group.rank)is int and type(group.rank_in_group)is int and 0<=group.rank_in_group<world and
        group.ranks[group.rank_in_group]==group.rank,"actual global-to-group rank: "+name)
    logical=logical_device(group,current,name);pg={}
    require(group.backend=="hccl","actual source-created HCCL group")
    for side,backend in (("cpu","gloo"),("device","hccl")):
        g=getattr(group,side+"_group");members=dist.get_process_group_ranks(g)
        rank=dist.get_rank(group=g);size=dist.get_world_size(group=g)
        require(members==group.ranks and type(rank)is int and rank==group.rank_in_group and
            type(size)is int and size==world and str(dist.get_backend(g))==backend,
            "real ProcessGroup/coordinator/backend equality: "+name+"/"+side)
        pg[side]={"members":list(members),"rank_in_group":rank,"world_size":size,"backend":backend,"object_id":id(g)}
    return {"unique_name":group.unique_name,"global_rank":group.rank,"rank_in_group":group.rank_in_group,
        "local_rank":group.local_rank,"members":list(group.ranks),"world_size":group.world_size,
        "device":str(group.device),"device_type":"npu","logical_device":logical,
        "device_representation":"source-defined-int-logical-index","object_id":id(group),"process_groups":pg}
def consume_identity(value,rank):
    consume_class(value["native_group_class"])
    require(value["schema"]=="SKVQ_LIVE_TP_IDENTITY_V1"and type(rank)is int and 0<=rank<4 and
        value["public_TP_rank"]==rank and type(value["pid"])is int and value["pid"]>0 and
        type(value["pid_start_ticks"])is int and value["pid_start_ticks"]>0,"actual live worker identity")
    for name,world in (("tp",4),("world",4),("pp",1),("dp",1),("pcp",1),("dcp",1)):
        row=value["groups"][name];members=list(range(4))if world==4 else [rank]
        require(row["members"]==members and row["global_rank"]==rank and
            row["world_size"]==world and row["rank_in_group"]==(rank if world==4 else 0)and
            type(row["logical_device"])is int and row["logical_device"]==row["local_rank"]==rank and
            row["device"]==str(rank)and row["device_type"]=="npu"and
            row["device_representation"]=="source-defined-int-logical-index","actual exact rank/device/members")
        for side,backend in (("cpu","gloo"),("device","hccl")):
            pg=row["process_groups"][side]
            require(pg["members"]==members and pg["world_size"]==world and
                pg["rank_in_group"]==row["rank_in_group"]and pg["backend"]==backend,
                "independent actual process group/backend closure")
    return value
def observe():
    require(os.environ.get("QWEN36_SKVQ_TP4_CAPTURE_ENABLE")=="1","explicit opt-in; default OFF")
    start=process_start();ps=sys.modules.get(PARALLEL_MODULE);_,qualified=qualified_class(ps)
    origin=qualified["public_source"];torch=sys.modules.get("torch");dist=sys.modules.get("torch.distributed")
    require(torch is not None and dist is not None and torch.distributed is dist,
        "already loaded Torch distributed")
    require(dist.is_available()and dist.is_initialized(),"actual initialized groups; never initialize here")
    torch_origin=module_origin(torch,"torch");dist_origin=module_origin(dist,"torch.distributed")
    functions={n:function_origin(ps,n,origin["path"])for n in GETTERS}
    current=torch.npu.current_device()
    require(type(current)is int and 0<=current<4,"actual true integer current NPU device")
    tp=functions["get_tp_group"]();world=functions["get_world_group"]()
    require(ps._TP is tp and ps._WORLD is world,"actual active TP/WORLD")
    snapshots={"tp":group_snapshot(ps,tp,dist,"tp",4,current),
        "world":group_snapshot(ps,world,dist,"world",4,current)}
    require(tp.ranks==world.ranks==list(range(4))and tp.rank==world.rank==dist.get_rank()and
        dist.get_world_size()==4 and tp.local_rank==world.local_rank==current,
        "single-node global four-rank capture")
    require(functions["get_tensor_model_parallel_rank"]()==tp.rank_in_group and
        functions["get_tensor_model_parallel_world_size"]()==4,"original public TP API equals live group")
    for name in ("pp","dp","pcp","dcp"):
        group=functions["get_"+name+"_group"]()
        require(getattr(ps,"_"+name.upper())is group,"actual active singleton group")
        snapshots[name]=group_snapshot(ps,group,dist,name,1,current)
        require(group.rank==tp.rank and group.ranks==[tp.rank],"no pipeline/data/context sharding")
    require(file_sha(origin["path"])==PARALLEL_SHA and process_start()==start,"stable source/process")
    cmd=Path("/proc/self/cmdline").read_bytes();require(cmd.endswith(bytes([0]))and len(cmd)>1,"real NUL cmdline")
    return {"schema":"SKVQ_LIVE_TP_IDENTITY_V1","observed_utc_ns":time.time_ns(),"pid":os.getpid(),
        "pid_start_ticks":start,"proc_cmdline_sha256":hashlib.sha256(cmd).hexdigest(),
        "parallel_source":origin,"torch_source":torch_origin,"distributed_source":dist_origin,
        "native_group_class":qualified,"public_TP_rank":tp.rank_in_group,"groups":snapshots,
        "physical_card_lease_pending":True,"post_rope_origin_pending":True,"actual_calibration_pending":True,
        "native_ready":False,"model_ready":False}
class RankProvider:
    def __init__(self):self.initial=None;self.poisoned=False
    def __call__(self):
        require(not self.poisoned,"latched live identity failure")
        try:
            value=observe()
            signature={k:value[k]for k in ("pid","pid_start_ticks","parallel_source","native_group_class","public_TP_rank","groups")}
            if self.initial is None:self.initial=signature
            else:require(signature==self.initial,"immutable worker/process/source/group identity")
            return value
        except BaseException:self.poisoned=True;raise
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true");a=p.parse_args(argv)
    require(not a.execute,"native qualification only through admitted all4 N1 or real worker")
    print(json.dumps({"default_enabled":False,"native_imported":PATCH_MODULE in sys.modules,
        "collective_called":False,"model_launched":False,"native_ready":False,"model_ready":False}))
if __name__=="__main__":main()
