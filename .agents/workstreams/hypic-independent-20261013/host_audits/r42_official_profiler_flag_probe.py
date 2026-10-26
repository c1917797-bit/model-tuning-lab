import pathlib,ast,types,typing,contextlib,json,hashlib
p=pathlib.Path("/vllm-workspace/vllm-ascend/vllm_ascend/profiler/torch_npu_profiler.py");raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=="0c9ffcaf695a9b1fcb44a51bdd92e69f763a7c5be64a8efbd498d6536b9e09e5"
node=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef)and n.name=="TorchNPUProfilerWrapper")
class Backend:
 ExportType=types.SimpleNamespace(Text="Text")
 ProfilerLevel=types.SimpleNamespace(Level1="Level1")
 AiCMetrics=types.SimpleNamespace(PipeUtilization="PipeUtilization")
 ProfilerActivity=types.SimpleNamespace(CPU="CPU",NPU="NPU")
 _ExperimentalConfig=staticmethod(lambda **k:k)
 profile=staticmethod(lambda **k:k)
 tensorboard_trace_handler=staticmethod(lambda *a,**k:("handler",a,k))
state={"daemon":False}
ns={"WorkerProfiler":object,"ProfilerConfig":object,"Any":typing.Any,"torch_npu":types.SimpleNamespace(profiler=Backend),"envs_ascend":types.SimpleNamespace(MSMONITOR_USE_DAEMON=False),"get_ascend_config":lambda:types.SimpleNamespace(msmonitor_use_daemon=state["daemon"]),"suppress":contextlib.suppress}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),"exec"),ns);C=ns["TorchNPUProfilerWrapper"]
def cfg(flag=True,kind="torch",path="/scratch/profiles"):return types.SimpleNamespace(profiler=kind,torch_profiler_dir=path,torch_profiler_with_memory=False,torch_profiler_with_stack=flag)
a=C._create_profiler(cfg(True),"rank0");b=C._create_profiler(cfg(False),"rank0")
diff=[k for k in a if a[k]!=b[k]];assert diff==["with_modules"]and a["with_modules"]is True and b["with_modules"]is False
assert b["activities"]==["CPU","NPU"]and b["experimental_config"]["profiler_level"]=="Level1"and b["experimental_config"]["aic_metrics"]=="PipeUtilization"
done=["exact original backend changes only with_modules and preserves CPU/NPU Level1/PipeUtilization"]
for label,config in[("unsupported profiler rejected",cfg(False,kind="cuda")),("missing output directory rejected",cfg(False,path=""))]:
 try:C._create_profiler(config,"rank0")
 except RuntimeError:done.append(label)
 else:raise AssertionError(label)
state["daemon"]=True
try:C._create_profiler(cfg(False),"rank0")
except RuntimeError:done.append("conflicting daemon rejected")
else:raise AssertionError("daemon")
print(json.dumps({"passed":len(done),"controls":done,"original_source_sha256":hashlib.sha256(raw).hexdigest(),"sole_backend_argument_delta":diff,"candidate_with_modules":False,"activities":b["activities"],"scope":"Original class AST with fake backend configuration mapping only; no NPU profiling, segfault cure or performance claim."}))
