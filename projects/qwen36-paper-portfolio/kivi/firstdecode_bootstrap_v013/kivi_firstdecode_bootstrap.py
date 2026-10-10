"""Explicit EAGER first-decode worker export. DEFAULT-OFF; no launcher.
The existing MAIN-owned host supplies exact actual recipe and source manifest.
"""
import importlib,importlib.util,json,os,sys
from pathlib import Path
FLAG="QWEN36_KIVI_FIRSTDECODE_DIAGNOSTIC"
CUSTOM="kivi_firstdecode_bootstrap.FirstDecodeWorker"
WORKER_SHA="c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3"
PLATFORM_SHA="30c75952f784c4d047d7202dd7f68c8fc7c22bb975853a5048fb51ffcbe1f2a8"
WORKERBASE_SHA="a04f83667cf3a3cadbc438eed59c708af5be3409d3f98e54612bd78e2f97e631"
ARGS_SHA="3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d"
def need(v,m):
    if not v:raise ValueError(m)
def loader():
    path=Path(__file__).resolve().parent/"loader.py";name="_kivi_firstdecode_source_loader"
    if name in sys.modules:
        need(Path(sys.modules[name].__file__).resolve()==path,"no foreign source loader")
        return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value
    try:spec.loader.exec_module(value)
    except BaseException:del sys.modules[name];raise
    return value
def __getattr__(name):
    if name!="FirstDecodeWorker":raise AttributeError(name)
    need(os.environ.get(FLAG)=="1","explicit firstdecode opt-in; OFF imports no Torch")
    l=loader();sha=os.environ["QWEN36_KIVI_FIRSTDECODE_SOURCE_SHA256"]
    m,source_ref,mods,adapter,new,own=l.load(sha,memory_limit=64*1024**3)
    recipe_ref=json.loads(os.environ["QWEN36_KIVI_FIRSTDECODE_INPUT_REF"])
    recipe=l.obj(recipe_ref)
    need(recipe["source_ref"]==source_ref and recipe["schema"]=="kivi.firstdecode-bootstrap-recipe/v1"
         and recipe["native_worker_qualified_name"]=="vllm_ascend.worker.worker.NPUWorker"
         and recipe["worker_qualified_name"]==CUSTOM and recipe["run_authority"]is False,
         "exact owned EAGER source/worker recipe, not stale bootstrap")
    capture=mods["layout"][1];identity=capture.identity()
    need(recipe["container_id"]in identity["cgroup"],"same actual current owned CID")
    pre=l.module("_kivi_firstdecode_prerequisite",l.own(m,"prerequisite.py"))
    pre.owned(recipe,l.obj,source_ref,identity)
    # load() checked actual64GiB namespace leaf BEFORE donor/runtime imports.
    memory=own["memory"]
    def memory_record(stage):
        value=memory.memory(expected_limit=64*1024**3)
        memory.consume_memory(value,expected_limit=64*1024**3,
                              container_id=recipe["container_id"],namespace_pid=identity["pid"])
        l.publish(Path(recipe["diagnostic_root"])/(stage+"-p%d.json"%identity["pid"]),
                  dict(schema="kivi.actual-firstdecode-memory/v1",stage=stage,source_ref=source_ref,
                       recipe_ref=recipe_ref,memory=value,model_ready=False))
    memory_record("BEFORE-NATIVE-WORKER")
    torch=importlib.import_module("torch");npu=importlib.import_module("torch_npu")
    tp=importlib.import_module("vllm.distributed.parallel_state")
    kv=importlib.import_module("vllm.v1.kv_cache_interface")
    context=importlib.import_module("vllm.forward_context")
    native=importlib.import_module("vllm_ascend.worker.worker").NPUWorker
    acl_cached=own["cann_python"].cached(required=True,memcpy_required=True)
    l.publish(Path(recipe["diagnostic_root"])/("CANN-WORKER-p%d.json"%identity["pid"]),
              dict(source_ref=source_ref,recipe_ref=recipe_ref,identity=identity,
                   binding=own["cann_python_binding"],cached_after_native_import=acl_cached,
                   model_ready=False,performance_ready=False))
    platform=importlib.import_module("vllm_ascend.platform")
    wb=importlib.import_module("vllm.v1.worker.worker_base")
    args=importlib.import_module("vllm.engine.arg_utils")
    for value,digest in((native,WORKER_SHA),(native.initialize_from_config,WORKER_SHA),
                        (native.load_model,WORKER_SHA),(platform.NPUPlatform.check_and_update_config,PLATFORM_SHA),
                        (wb.WorkerWrapperBase,WORKERBASE_SHA),(args.EngineArgs.create_engine_config,ARGS_SHA)):
        capture.source_file(value,digest)
    adapter.OPS_PACKET=torch.ops.npu.get_npu_format
    binding=recipe["native_format_binding"]
    observed=adapter.observe(lambda:mods["format_policy"].bind_getter(npu,binding,adapter,adapter.OPS_PACKET)[2])
    l.publish(Path(recipe["diagnostic_root"])/("BOOTSTRAP-p%d.json"%identity["pid"]),
              dict(schema="kivi.actual-firstdecode-bootstrap/v1",source=source_ref,recipe_ref=recipe_ref,
                   identity=identity,getter_observation=observed,before_native_constructor=True,model_ready=False))
    need(observed["ok"]is True,"actual getter/enum/source qualification; raw failure retained")
    boundary_ref=l.own(m,"runtime_boundary.py")
    boundary=l.module("_kivi_actual_runtime_boundary",boundary_ref)
    original_init=native.__init__;original_load=native.load_model;original_shutdown=native.shutdown
    class FirstDecodeWorker(native):
        def __init__(self,vllm_config,local_rank,rank,distributed_init_method,is_driver_worker=False,**kwargs):
            pc=vllm_config.parallel_config;mc=vllm_config.model_config
            need(type(rank)is int and rank in range(4) and type(local_rank)is int and rank==local_rank
                 and pc.worker_cls==CUSTOM and not pc.worker_extension_cls
                 and pc.tensor_parallel_size==4 and pc.data_parallel_size==pc.pipeline_parallel_size==1
                 and mc.enforce_eager is True,"real explicit EAGER TP4 worker selected by native platform")
            original_init(self,vllm_config,local_rank,rank,distributed_init_method,
                          is_driver_worker=is_driver_worker,**kwargs)
        def load_model(self,*args,**kwargs):
            memory_record("BEFORE-WEIGHTS")
            return original_load(self,*args,**kwargs)
        def initialize_from_config(self,config):
            rank=tp.get_tensor_model_parallel_rank()
            return boundary.initialize(lambda:self._kivi_initialize_from_config(config),rank=rank,
                recipe=recipe,recipe_ref=recipe_ref,source_ref=source_ref,helper_ref=boundary_ref,
                identity=identity,publish=l.publish)
        def _kivi_initialize_from_config(self,config):
            rank=tp.get_tensor_model_parallel_rank()
            need(type(rank)is int and rank in range(4) and tp.get_tensor_model_parallel_world_size()==4,
                 "actual initialized TP4 before native cache allocation")
            own["ownership"].rank_request(capture,recipe,rank,source_ref,l.publish)
            rank_ref,rank_owner=own["ownership"].await_ref(recipe["rank_bindings_path"],l.obj)
            front_ref,front=own["ownership"].await_ref(recipe["frontend_binding_path"],l.obj)
            plan_ref=recipe["declared_ingress_plan_ref"];plan=l.obj(plan_ref)
            bindings=new["bindings"].Bindings(plan,plan_ref,front_ref,rank_ref,
                                              recipe["diagnostic_root"],new["assignment_oracle"])
            layout=own["runtime_owner"].layout_input(recipe,identity,rank,sha)
            layout_ref=l.publish(Path(recipe["diagnostic_root"])/("LAYOUT-INPUT-r%d.json"%rank),layout)
            props,driver_proof=boundary.core_properties(torch,mods["triton"],rank,l.ref)
            l.publish(Path(recipe["diagnostic_root"])/("DRIVER-PROPERTIES-r%d.json"%rank),
                dict(driver_proof,source_ref=source_ref,recipe_ref=recipe_ref,identity=identity))
            def qualify():
                need(capture.identity()==identity,"same actual worker at algorithm boundary")
                pre.owned(recipe,l.obj,source_ref,identity)
            def resolved(runner,event,event_ref,publish,final_ref,raw):
                zero=new["spans"].snapshot_zeroer(torch,runner,event,mods["callback"],capture.identity,rank)
                return own["runtime_owner"].post_input(recipe,bindings,event,event_ref,final_ref,zero,
                                                       mods["fields"],new["spans"],publish)
            def final(ref):
                l.publish(Path(recipe["diagnostic_root"])/("RANK-%d-FINAL-INDEX.json"%rank),ref)
            refs=dict(m["runtime_roles"])
            selected=own["worker"].make_worker(native,mods,adapter,own["prebind"],torch,npu,tp,kv,context,
                layout_owner=layout,layout_owner_ref=layout_ref,layout_mf=sha,post_owner=None,post_owner_ref=None,
                installer=new["installer"],spans=new["spans"],book=new["book"],formal=mods["formal"],
                producer=new["producer"],kernel=new["kernel"],metadata=mods["metadata"],
                journal_module=new["journal"],source_refs=refs,device_properties=props,qualify=qualify,
                ingress_bindings=bindings,capture_raw=True,raw_root=recipe["raw_root"],
                provenance=new["provenance"],first_decode_capture_only=True,
                raw_journal_module=own["raw_journal"],resolve_post_owner=resolved,
                finish_module=own["finish_after_native"],publish_final=final)
            need(selected is not native,"actual packed worker factory enabled, no silent OFF fallback")
            self._kivi_firstdecode_selected=selected
            return selected.initialize_from_config(self,config)
        def shutdown(self):
            # Never synthesize final/finished IDs. A missing native final remains a failure.
            return original_shutdown(self)
    FirstDecodeWorker.__module__=__name__;globals()["FirstDecodeWorker"]=FirstDecodeWorker
    return FirstDecodeWorker
