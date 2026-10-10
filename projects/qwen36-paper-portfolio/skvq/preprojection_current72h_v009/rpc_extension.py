"""Safe source-bound named RPC extension. No Torch/vLLM import at module import.
Original WorkerWrapperBase injects this class into the unchanged NPUWorker bases.
CPU transport probe is a surrogate, never actual Session/hook/model authority.
"""
import importlib,inspect,json,os,sys
from pathlib import Path
import current_contract as C
QUALNAME="rpc_extension.SKVQCaptureExtension"
METHODS=("skvq_capture_install","skvq_capture_arm","skvq_capture_finish","skvq_capture_restore")
WORKER_SHA="c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3"
def secure():
    C.require(os.environ.get("VLLM_ALLOW_INSECURE_SERIALIZATION","0")=="0",
        "default safe serialization required; no insecure pickle opt-in")
def origins(source,modules):
    rows=json.loads(Path(source["path"]).read_bytes())["rpc_runtime_sources"];result={}
    for name in modules:
        pin=next(x for x in rows if x["module"]==name);C.checked(pin["snapshot"])
        module=importlib.import_module(name);value=C.reference(module.__file__)
        C.require(module.__name__==name and module.__spec__ is not None and module.__spec__.name==name and
            Path(module.__spec__.origin).resolve()==Path(module.__file__).resolve() and
            value=={"path":pin["runtime_path"],"bytes":pin["snapshot"]["bytes"],
                "sha256":pin["snapshot"]["sha256"]},"actual original named RPC module origin")
        result[name]=value
    return result
def consume_origins(value,source,modules):
    rows=json.loads(Path(source["path"]).read_bytes())["rpc_runtime_sources"]
    C.require(type(value)is dict and set(value)==set(modules),"exact RPC origin module set")
    for name in modules:
        pin=next(x for x in rows if x["module"]==name);C.checked(pin["snapshot"])
        C.require(value[name]=={"path":pin["runtime_path"],"bytes":pin["snapshot"]["bytes"],
            "sha256":pin["snapshot"]["sha256"]},"original RPC runtime origin independently matches archive")
def native_class(cls,source,installed=False):
    secure();origin=C.reference(inspect.getsourcefile(cls))
    C.require(cls.__name__=="NPUWorker" and cls.__module__ in
        ("vllm_ascend.worker.worker","vllm_ascend.worker.npu_worker") and
        inspect.getsourcefile(cls)==sys.modules[cls.__module__].__file__ and
        origin["sha256"]==WORKER_SHA and
        origin["path"]=="/vllm-workspace/vllm-ascend/"+cls.__module__.replace(".","/")+".py","original exact NPUWorker receiver source retained")
    for name in METHODS:
        if installed:
            C.require(getattr(cls,name,None)is getattr(SKVQCaptureExtension,name),
                "actual native extension method resolution, no foreign shadow")
        else:
            C.require(not hasattr(cls,name),"native extension conflicts rejected before weights")
    C.require((SKVQCaptureExtension in cls.__bases__)is installed,
        "before factory unextended, after original factory exact direct extension base")
    return {"source_ref":source,"extension_ref":C.reference(__file__),"qualified_name":QUALNAME,
        "methods":list(METHODS),"worker_class":{"module":cls.__module__,"name":cls.__name__,"origin":origin},
        "extension_in_direct_bases":installed,"safe_serialization":True,
        "class_source_checked_only":True,"hook_installation_or_numerical_authority":False}
def before_weights(configuration,source):
    secure();modules=("vllm.v1.worker.worker_base","vllm.config.parallel")
    records=origins(source,modules)
    p=configuration.parallel_config
    C.require(p.worker_extension_cls==QUALNAME and type(p.worker_cls)is str,
        "same explicit source-qualified native worker extension in full config")
    from vllm.utils.import_utils import resolve_obj_by_qualname
    cls=resolve_obj_by_qualname(p.worker_cls);extension=resolve_obj_by_qualname(p.worker_extension_cls)
    C.require(extension is SKVQCaptureExtension and
        C.reference(inspect.getsourcefile(extension))==C.reference(__file__),
        "native factory resolver finds exact current extension, not cached foreign module")
    value=native_class(cls,source)
    value["runtime_origins"]=records
    return value
def installed_worker(worker,expected=None):
    source=C.source(expected);secure()
    C.require(worker.vllm_config.parallel_config.worker_extension_cls==QUALNAME,
        "actual worker carries current native extension config")
    return native_class(type(worker),source,True)
class SKVQCaptureExtension:
    def skvq_capture_install(self,input_path,root,current_manifest_sha256):
        qualification=installed_worker(self,current_manifest_sha256)
        from projection_tap_current import install_rpc
        result=install_rpc(self,input_path,root,current_manifest_sha256)
        result["named_rpc_extension"]=qualification
        return result
    def skvq_capture_arm(self,i):
        installed_worker(self)
        from runtime_capture_current import arm_rpc
        return arm_rpc(self,i)
    def skvq_capture_finish(self):
        installed_worker(self)
        from runtime_capture_current import finish_rpc
        return finish_rpc(self)
    def skvq_capture_restore(self):
        # Original source-qualified exact-owned restoration must remain callable
        # after failed install; never require a Session/source admission first.
        from runtime_capture_current import restore_rpc
        return restore_rpc(self)
def call_cases(source):
    root=Path(source["path"]).parent
    return [(METHODS[0],60,(str(root/"RPC-PROBE-INPUT.json"),str(root/"RPC-PROBE-OUT"),source["sha256"]),{}),
        (METHODS[1],30,(0,),{}),(METHODS[2],60,(),{}),(METHODS[3],30,(),{})]
def preflight(source):
    secure()
    import torch,torch_npu
    C.require(torch.npu is torch_npu.npu and not torch.npu.is_initialized(),
        "real Devices[] transport probe does not initialize NPU")
    modules=("vllm.v1.serial_utils","vllm.v1.worker.worker_base","vllm.v1.engine.core_client",
        "vllm.config.parallel","vllm.entrypoints.llm")
    observed=origins(source,modules)
    serial=sys.modules["vllm.v1.serial_utils"];wb=sys.modules["vllm.v1.worker.worker_base"]
    C.require(serial.envs.VLLM_ALLOW_INSECURE_SERIALIZATION is False,
        "actual native encoder safe setting")
    encoder=serial.MsgpackEncoder();decoder=serial.MsgpackDecoder()
    wrapper=object.__new__(wb.WorkerWrapperBase);cases=call_cases(source)
    # Real wrapper/getattr/run_method/encoder, but no real native worker or
    # original capture delegate executes in this Devices[] necessary test.
    def make(name):
        def probe(self,*args,**kw):
            inspect.signature(getattr(SKVQCaptureExtension,name)).bind(self,*args,**kw)
            return {"method":name,"args":list(args),"kwargs":kw,"probe_only":True}
        return probe
    carrier=type("NamedRpcTransportProbe",(),{n:make(n)for n in METHODS})
    wrapper.worker=carrier();records=[]
    for index,(name,timeout,args,kw)in enumerate(cases):
        message=(0,index,"collective_rpc",(name,timeout,args,kw))
        decoded=decoder.decode(encoder.encode(message))
        C.require(decoded[:3]==[0,index,"collective_rpc"] and decoded[3][0]==name,
            "actual core utility envelope preserves string method")
        _,_,actual_args,actual_kw=decoded[3]
        result=serial.run_method(wrapper,name,actual_args,actual_kw)
        C.require(result=={"method":name,"args":list(args),"kwargs":kw,"probe_only":True},
            "real WorkerWrapperBase method resolution and exact original delegate signatures")
        decoded_result=decoder.decode(encoder.encode(result))
        C.require(decoded_result==result,"actual safe reply encoding for primitive RPC result")
        records.append({"method":name,"timeout":timeout,"args":list(args),"kwargs":kw,
            "request_and_reply_roundtrip":True,"wrapper_method_resolution":True})
    try:encoder.encode((0,1,"collective_rpc",(lambda:None,30,(),{})))
    except TypeError:callable_rejected=True
    else:callable_rejected=False
    C.require(callable_rejected and not torch.npu.is_initialized(),
        "original function refusal retained; no NPU initialization")
    return {"schema":"skvq.capture.safe-named-rpc-preflight/v1","source_ref":source,
        "extension_ref":C.reference(__file__),"qualified_name":QUALNAME,"runtime_origins":observed,
        "methods":records,"actual_function_serialization_rejected":True,"safe_serialization":True,
        "NPU_initialized":False,"surrogate_receiver_only":True,"actual_worker_installed":False,
        "model_ready":False,"native_ready":False}
def consume_preflight(value,source):
    C.require(value["schema"]=="skvq.capture.safe-named-rpc-preflight/v1" and value["source_ref"]==source and
        value["extension_ref"]==C.reference(__file__) and value["qualified_name"]==QUALNAME and
        value["safe_serialization"]is True and value["actual_function_serialization_rejected"]is True and
        value["NPU_initialized"]is False and value["surrogate_receiver_only"]is True and
        value["actual_worker_installed"]is False and value["model_ready"]is False and value["native_ready"]is False,
        "actual safe codec probe scope, not worker/hook/model proof")
    expected=[{"method":n,"timeout":t,"args":list(a),"kwargs":k,
        "request_and_reply_roundtrip":True,"wrapper_method_resolution":True}for n,t,a,k in call_cases(source)]
    C.require(value["methods"]==expected,"all four exact RPC preflight methods and argument signatures")
    consume_origins(value["runtime_origins"],source,("vllm.v1.serial_utils","vllm.v1.worker.worker_base",
        "vllm.v1.engine.core_client","vllm.config.parallel","vllm.entrypoints.llm"))
    return value
def consume_install(result,source):
    value=result["named_rpc_extension"];worker=value["worker_class"]
    C.require(value["source_ref"]==source and value["extension_ref"]==C.reference(__file__) and
        value["qualified_name"]==QUALNAME and value["methods"]==list(METHODS) and
        value["extension_in_direct_bases"]is True and value["safe_serialization"]is True and
        value["class_source_checked_only"]is True and value["hook_installation_or_numerical_authority"]is False and
        worker["name"]=="NPUWorker" and worker["module"]in
            ("vllm_ascend.worker.worker","vllm_ascend.worker.npu_worker") and
        worker["origin"]["sha256"]==WORKER_SHA and
        worker["origin"]["path"]=="/vllm-workspace/vllm-ascend/"+worker["module"].replace(".","/")+".py",
        "actual original NPUWorker source and native named extension, not substitute worker")
    return value
def consume_before_weights(value,source):
    C.require(value["source_ref"]==source and value["extension_ref"]==C.reference(__file__) and
        value["qualified_name"]==QUALNAME and value["methods"]==list(METHODS) and
        value["extension_in_direct_bases"]is False and value["safe_serialization"]is True and
        value["class_source_checked_only"]is True and value["hook_installation_or_numerical_authority"]is False and
        value["worker_class"]["name"]=="NPUWorker" and value["worker_class"]["module"]in
            ("vllm_ascend.worker.worker","vllm_ascend.worker.npu_worker") and
        value["worker_class"]["origin"]["sha256"]==WORKER_SHA and
        value["worker_class"]["origin"]["path"]=="/vllm-workspace/vllm-ascend/"+value["worker_class"]["module"].replace(".","/")+".py",
        "genuine N1 original class/resolver qualification before weights, no hook/model authority")
    consume_origins(value["runtime_origins"],source,("vllm.v1.worker.worker_base","vllm.config.parallel"))
    return value
