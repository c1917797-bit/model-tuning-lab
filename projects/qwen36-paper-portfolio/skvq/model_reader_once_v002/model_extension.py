"""Safe named worker extension; only factory owned instance hooks, no function pickle."""
import importlib,inspect,multiprocessing as mp,os,sys
from pathlib import Path
import bridge_contract as B
QUALNAME="model_extension.SKVQCompiledReaderExtension"
METHODS=("skvq_reader_install","skvq_reader_status","skvq_reader_finish","skvq_reader_restore")
WORKER_SHA="c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3"
def secure():
    B.need(os.environ.get("VLLM_ALLOW_INSECURE_SERIALIZATION","0")=="0"and
      os.environ.get("VLLM_WORKER_MULTIPROC_METHOD")=="spawn","safe primitive RPC and explicit native spawn")
def origins(C,m,names):
    pins=m["rpc_runtime_sources"];out={}
    for name in names:
        row=next(r for r in pins if r["module"]==name);C.read(row["snapshot"])
        module=importlib.import_module(name);actual=C.ref(module.__file__)
        B.need(module.__spec__.name==name and actual==dict(path=row["runtime_path"],bytes=row["snapshot"]["bytes"],
          sha256=row["snapshot"]["sha256"]),"original deployed RPC source, not snapshot impersonation")
        out[name]=actual
    return out
def native_class(C,cls,source,*,installed):
    secure();origin=C.ref(inspect.getsourcefile(cls))
    B.need(cls.__name__=="NPUWorker"and cls.__module__ in("vllm_ascend.worker.worker","vllm_ascend.worker.npu_worker")and
      inspect.getsourcefile(cls)==sys.modules[cls.__module__].__file__ and origin["sha256"]==WORKER_SHA and
      origin["path"]=="/vllm-workspace/vllm-ascend/"+cls.__module__.replace(".","/")+".py","exact original native worker class")
    for name in METHODS:
        B.need(getattr(cls,name,None)is getattr(SKVQCompiledReaderExtension,name)if installed else not hasattr(cls,name),
          "actual original factory extension method resolution/no conflict")
    B.need((SKVQCompiledReaderExtension in cls.__bases__)is installed,"actual direct extension base installed")
    return dict(schema="skvq.model-reader.extension/v1",source_ref=source,reader_source_ref=B.READER,
      extension_ref=C.ref(__file__),qualified_name=QUALNAME,methods=list(METHODS),worker_origin=origin,
      installed=installed,safe_serialization=True,numerical_authority=False)
def before_weights(configuration,source):
    C,r,m=B.source(source["sha256"]);secure()
    B.need(r==source and configuration.parallel_config.worker_extension_cls==QUALNAME,"same model bridge extension config")
    record=origins(C,m,("vllm.v1.worker.worker_base","vllm.config.parallel"))
    from vllm.utils.import_utils import resolve_obj_by_qualname
    cls=resolve_obj_by_qualname(configuration.parallel_config.worker_cls)
    B.need(resolve_obj_by_qualname(QUALNAME)is SKVQCompiledReaderExtension,"real original factory resolver")
    value=native_class(C,cls,source,installed=False);value["origins"]=record;return value
def installed(worker,expected):
    C,r,m=B.source(expected)
    B.need(worker.vllm_config.parallel_config.worker_extension_cls==QUALNAME and
      mp.get_start_method(allow_none=True)=="spawn","actual spawn worker configured extension")
    return C,r,m,native_class(C,type(worker),r,installed=True)
class SKVQCompiledReaderExtension:
    def skvq_reader_install(self,reader_whole_ref_json,prompt_ref_json,root,bridge_source_sha256):
        C,r,m,qualification=installed(self,bridge_source_sha256)
        B.need(not hasattr(self,"_skvq_actual_reader_factory"),"one exact owned model factory; no duplicate")
        whole=C.obj(C.ref(reader_whole_ref_json));prompt=C.obj(C.ref(prompt_ref_json));B.prompt(C,prompt)
        from model_factory import Factory
        directory=Path(root)/("rank"+str(self.rank))
        self._skvq_actual_reader_factory=Factory(self,whole,prompt,directory,r)
        f=self._skvq_actual_reader_factory
        row=C.atomic(directory/"BRIDGE_INSTALL.json",dict(source_ref=r,reader_source_ref=B.READER,rank=self.rank,
          qualification=qualification,reader_whole_ref=whole,prompt_ref=prompt,reader_install_ref=f.install_ref,
          factory_delta_ref=C.ref(directory/"EXPLICIT_FACTORY_DELTA.json"),
          worker_process=__import__("numeric").identity(),actual_instance_hooks=32,geometry_ref=f.geometry_ref,
          native_prefill_and_cache_write_retained=True,GDN48_function_identity_only=True,**B.false_scopes()))
        return dict(rank=self.rank,install_ref=row,source_ref=r)
    def skvq_reader_status(self):
        f=getattr(self,"_skvq_actual_reader_factory",None);B.need(f is not None,"actual installed factory")
        return dict(rank=self.rank,reader_source_ref=B.READER,actual_native_prefill_calls=f.session.original_calls,
          actual_compiled_decode_calls=f.session.candidate_calls,native_finished_ref=f.finish.ref,
          poisoned=f.session.poisoned,closed=f.session.closed,**B.false_scopes())
    def skvq_reader_finish(self):
        f=getattr(self,"_skvq_actual_reader_factory",None);B.need(f is not None,"actual installed factory")
        row=f.complete()
        return dict(rank=self.rank,reader_source_ref=B.READER,final_ref=row,**B.false_scopes())
    def skvq_reader_restore(self):
        f=getattr(self,"_skvq_actual_reader_factory",None)
        if f is None:return dict(rank=self.rank,restored=True,never_installed=True,**B.false_scopes())
        if not f.session.closed or not f.finish.closed:f.restore()
        return dict(rank=self.rank,restored=f.session.closed and f.finish.closed,never_installed=False,**B.false_scopes())
def calls(source):
    root=Path(source["path"]).parent
    return [(METHODS[0],60,(str(root/"PROBE_READER_REF.json"),str(root/"PROBE_PROMPT_REF.json"),str(root/"PROBE_OUT"),source["sha256"]),{}),
      (METHODS[1],30,(),{}),(METHODS[2],60,(),{}),(METHODS[3],30,(),{})]
def preflight(source):
    C,r,m=B.source(source["sha256"]);secure()
    import torch,torch_npu
    B.need(torch.npu is torch_npu.npu and not torch.npu.is_initialized(),"real Devices[] safe codec no NPU initialization")
    observed=origins(C,m,("vllm.v1.serial_utils","vllm.v1.worker.worker_base","vllm.v1.engine.core_client",
      "vllm.config.parallel","vllm.entrypoints.llm"))
    serial=sys.modules["vllm.v1.serial_utils"];wb=sys.modules["vllm.v1.worker.worker_base"]
    B.need(serial.envs.VLLM_ALLOW_INSECURE_SERIALIZATION is False,"original safe codec flag")
    encoder=serial.MsgpackEncoder();decoder=serial.MsgpackDecoder();wrapper=object.__new__(wb.WorkerWrapperBase)
    def create(name):
        def probe(self,*args,**kw):
            inspect.signature(getattr(SKVQCompiledReaderExtension,name)).bind(self,*args,**kw)
            return dict(method=name,args=list(args),kwargs=kw,probe_only=True)
        return probe
    wrapper.worker=type("SKVQReaderPrimitiveTransportProbe",(),{n:create(n)for n in METHODS})();records=[]
    for i,(name,timeout,args,kw)in enumerate(calls(source)):
        decoded=decoder.decode(encoder.encode((0,i,"collective_rpc",(name,timeout,args,kw))))
        B.need(decoded[:3]==[0,i,"collective_rpc"]and decoded[3][0]==name,"actual string core utility envelope")
        value=serial.run_method(wrapper,name,decoded[3][2],decoded[3][3])
        B.need(value==dict(method=name,args=list(args),kwargs=kw,probe_only=True)and
          decoder.decode(encoder.encode(value))==value,"actual original wrapper/encoder exact primitive roundtrip")
        records.append(dict(method=name,args=list(args),timeout=timeout,kwargs=kw))
    try:encoder.encode((0,1,"collective_rpc",(lambda:None,30,(),{})))
    except TypeError:rejected=True
    else:rejected=False
    B.need(rejected and not torch.npu.is_initialized(),"function refusal remains; no initialized HAL")
    return dict(schema="skvq.model-reader.named-rpc-cpu/v1",source_ref=r,methods=records,origins=observed,
      actual_function_serialization_rejected=True,NPU_initialized=False,surrogate_receiver_only=True,**B.false_scopes())
