import ast,pathlib,hashlib,abc,types,contextlib,json
p=pathlib.Path("/vllm-workspace/vllm/vllm/profiler/wrapper.py");raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=="31f8a33afd23e67a2ade5a95d0d837a03b0a9164d5b18acf561d948c9ae6c06c"
cls=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef)and n.name=="WorkerProfiler")
class Logger:
 def __init__(self):self.warnings=[]
 def warning(self,*a):self.warnings.append(a)
 def __getattr__(self,n):return lambda *a,**k:None
log=Logger();ns={"ABC":abc.ABC,"abstractmethod":abc.abstractmethod,"ProfilerConfig":object,"logger":log,"nullcontext":contextlib.nullcontext}
exec(compile(ast.Module(body=[cls],type_ignores=[]),str(p),"exec"),ns);W=ns["WorkerProfiler"]
class D(W):
 def __init__(self,delay=0,cap=7,fail_start=False,fail_stop=False):
  super().__init__(types.SimpleNamespace(delay_iterations=delay,max_iterations=cap));self.starts=0;self.stops=0;self.fail_start=fail_start;self.fail_stop=fail_stop
 def _start(self):
  self.starts+=1
  if self.fail_start:raise RuntimeError("HOST_start_failure")
 def _stop(self):
  self.stops+=1
  if self.fail_stop:raise RuntimeError("HOST_stop_failure")
done=[];d=D();d.start()
for _ in range(7):d.step()
assert d.starts==1 and d.stops==0 and d._running
d.step();assert d.stops==1 and not d._running and d._active
done.append("max7 stops on8th worker step, active until explicit stop")
d.stop();assert not d._active and d._active_iteration_count==0 and d._profiling_for_iters==0
d.start()
for _ in range(8):d.step()
assert d.starts==2 and d.stops==2
d.stop();done.append("explicit stop resets counters before restart")
d=D(delay=2,cap=2);d.start();d.step();assert d.starts==0
d.step();assert d.starts==1 and d.stops==0
d.step();assert d.stops==0
d.step();assert d.stops==1
d.stop();done.append("delayed start and >cap observed on original class")
before=len(log.warnings);d=D(fail_start=True);d.start();assert d._active and not d._running and len(log.warnings)==before+1
d.stop();done.append("start error caught, no recording proof from successful call return")
before=len(log.warnings);d=D(fail_stop=True);d.start();d.stop();assert not d._running and not d._active and len(log.warnings)==before+1
done.append("stop error caught, running state false cannot prove exported trace")
print(json.dumps({"passed":len(done),"controls":done,"original_source_path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"scope":"AST-selected original official WorkerProfiler class with fake _start/_stop only; no torch import/NPU trace/inference proof."}))
