"""Bounded original-call CPU/wall attribution using Python3.12 local function events.
No function replacement, tensor reads, added synchronization, or per-token I/O.
Local events are ONLY PY_START/PY_RETURN for exact original code objects.
PY_UNWIND is a global exceptional event (Python does not allow it locally), filtered
to those code objects. No line/instruction/loop/C-call events are requested.
"""
import hashlib,inspect,sys,threading,time,types
from pathlib import Path
SCHEMA="kivi.original-local-call-cost/v1"
TOOL=4
TOOL_NAME="kivi-source-qualified-cost-v1"
TARGETS={
 "metadata":("row_plan","create","refresh","assert_live","assert_tensors"),
 "lifecycle":("owned","_guard_quant","_seal","begin","finish","prefill_after_dense","release"),
 "writer":("seal_k_into","seal_v_into"),"producer":("append_read","plan_requests"),
 "kernel":("forward",),"installer":("timing_layout","timing_cached_ingress"),
 "callback":("scalar_tensor",),"formal":("gather_native",)}
def need(v,m):
 if not v:raise ValueError(m)
def reference(path):
 p=Path(path).resolve();need(p.is_file()and not p.is_symlink(),"ordinary actual source")
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def codes(code):
 yield code
 for v in code.co_consts:
  if isinstance(v,types.CodeType):yield from codes(v)
def digest(co):
 def constant(v):
  if isinstance(v,types.CodeType):return sig(v)
  if type(v)is tuple:return('tuple',tuple(constant(x)for x in v))
  if type(v)is frozenset:return('frozenset',tuple(sorted((constant(x)for x in v),key=repr)))
  return(type(v).__name__,repr(v))
 def sig(c):
  constants=tuple(constant(v)for v in c.co_consts)
  return(c.co_argcount,c.co_posonlyargcount,c.co_kwonlyargcount,c.co_nlocals,c.co_stacksize,c.co_flags,
   c.co_code,c.co_names,c.co_varnames,c.co_freevars,c.co_cellvars,constants,c.co_name,c.co_qualname,
   c.co_firstlineno,c.co_linetable,c.co_exceptiontable)
 return hashlib.sha256(repr(sig(co)).encode()).hexdigest()
def key(co):return(co.co_filename,co.co_name,co.co_firstlineno)
def checked_codes(ref):
 need(type(ref)is dict and set(ref)=={"path","bytes","sha256"}and reference(ref["path"])==ref,"exact whole target source")
 return tuple(codes(compile(Path(ref["path"]).read_bytes(),ref["path"],"exec",dont_inherit=True)))
def module_codes(module,ref):
 need(type(module)is types.ModuleType and str(Path(module.__file__).resolve())==ref["path"],"actual loaded target module origin")
 seen=set();out=[]
 def visit(v):
  if id(v)in seen:return
  seen.add(id(v))
  if isinstance(v,(classmethod,staticmethod)):visit(v.__func__)
  elif isinstance(v,property):
   for f in(v.fget,v.fset,v.fdel):
    if f is not None:visit(f)
  elif isinstance(v,types.FunctionType):
   if v.__code__.co_filename==ref["path"]:out.extend(codes(v.__code__))
  elif isinstance(v,type)and v.__module__==module.__name__:
   for f in vars(v).values():visit(f)
 for v in vars(module).values():visit(v)
 return tuple(set(out))
class Session:
 def __init__(self,refs,modules,*,rank,arm,source_ref,recipe_ref,synchronize=None):
  need(sys.version_info[:2]==(3,12)and hasattr(sys,"monitoring"),"same660 Python3.12 actual local monitoring API")
  need(type(rank)is int and rank in range(4)and arm in("dense","candidate"),"actual rank/arm")
  need(set(refs)==set(modules)==set(TARGETS),"complete source and actual module closure")
  self.rank=rank;self.arm=arm;self.source_ref=source_ref;self.recipe_ref=recipe_ref;self.refs=dict(refs)
  self.labels={};self.code_refs=[]
  for role,ref in refs.items():
   wanted={key(co):digest(co)for co in checked_codes(ref)if co.co_name in TARGETS[role]}
   actual=module_codes(modules[role],ref)
   found=set()
   for co in actual:
    if key(co)not in wanted:continue
    need(digest(co)==wanted[key(co)],"actual target code differs from exact source")
    need(co not in self.labels,"unambiguous original target")
    self.labels[co]=role+"."+co.co_name;found.add(co.co_name);self.code_refs.append(dict(role=role,name=co.co_qualname,line=co.co_firstlineno,code_sha256=digest(co)))
   need(found==set(TARGETS[role]),"whole actual target closure, no supplied missing module")
  self.synchronize=None;self.sync_source=None
  if synchronize is not None:
   fn=getattr(synchronize,"__func__",synchronize)
   need(type(fn)is types.FunctionType,"actual Python existing synchronize; no guessed builtin wrapper")
   ref=reference(inspect.getfile(fn));original=checked_codes(ref)
   need(any(key(co)==key(fn.__code__)and digest(co)==digest(fn.__code__)for co in original),"actual existing synchronize code/source")
   self.synchronize=fn.__code__;self.sync_source=ref;self.labels[fn.__code__]="existing_sync"
  self.stats={};self.active={};self.phase=None;self.closed=False;self.intact=True;self.thread=None
  self.windows=[];self.events=0;self.unrelated_unwinds=0;self.callback_wall_ns=0
 def _start(self,code,offset):
  begin=time.perf_counter_ns();self.events+=1
  try:
   frame=sys._getframe(1);need(frame.f_code is code,"actual monitoring frame")
   need(self.phase is not None and threading.get_ident()==self.thread,"same original native thread/window")
   label=self.labels[code]
   if code is self.synchronize:
    caller=frame.f_back
    label+="@%s:%s:%s"%(caller.f_code.co_filename,caller.f_code.co_name,caller.f_lineno)
   row=self.stats.setdefault((self.phase,label),dict(calls=0,returns=0,exceptions=0,wall_ns=0,thread_cpu_ns=0,max_wall_ns=0,owned_prefix_entries=0))
   row["calls"]+=1
   if label=="metadata.row_plan":
    r=frame.f_locals["view"].r;row["owned_prefix_entries"]+=len(r.kp)+len(r.vp)
   need(id(frame)not in self.active,"one original frame entry")
   self.active[id(frame)]=(self.phase,label,time.perf_counter_ns(),time.thread_time_ns())
  finally:self.callback_wall_ns+=time.perf_counter_ns()-begin
 def _end(self,frame,code,exception):
  start=self.active.pop(id(frame),None);need(start is not None and frame.f_code is code,"matching original return/unwind")
  phase,label,w,c=start;wall=time.perf_counter_ns()-w;cpu=time.thread_time_ns()-c
  row=self.stats[(phase,label)];row["returns"]+=1;row["exceptions"]+=int(exception)
  row["wall_ns"]+=wall;row["thread_cpu_ns"]+=cpu;row["max_wall_ns"]=max(row["max_wall_ns"],wall)
 def _return(self,code,offset,value):
  begin=time.perf_counter_ns();self.events+=1
  try:self._end(sys._getframe(1),code,False)
  finally:self.callback_wall_ns+=time.perf_counter_ns()-begin
 def _unwind(self,code,offset,error):
  begin=time.perf_counter_ns();self.events+=1
  try:
   if code in self.labels:self._end(sys._getframe(1),code,True)
   else:self.unrelated_unwinds+=1
  finally:self.callback_wall_ns+=time.perf_counter_ns()-begin
 def run(self,phase,function,*args,**kwargs):
  need(not self.closed and self.intact and self.phase is None and not self.active,"one complete original call")
  need(type(phase)is str and phase and len(phase)<=120,"bounded phase")
  mon=sys.monitoring;ev=mon.events
  need(mon.get_tool(TOOL)is None and sys.getprofile()is None and threading.getprofile()is None,"do not replace ambient monitoring/profiling")
  thread=threading.get_ident();need(self.thread is None or self.thread==thread,"same actual execution thread")
  self.thread=thread;self.phase=phase;failed=True;wall=time.perf_counter_ns();cpu=time.thread_time_ns();events=self.events
  mon.use_tool_id(TOOL,TOOL_NAME)
  try:
   for event,callback in((ev.PY_START,self._start),(ev.PY_RETURN,self._return),(ev.PY_UNWIND,self._unwind)):
    need(mon.register_callback(TOOL,event,callback)is None,"fresh callbacks only")
   mon.set_events(TOOL,ev.PY_UNWIND)
   for co in self.labels:mon.set_local_events(TOOL,co,ev.PY_START|ev.PY_RETURN)
   answer=function(*args,**kwargs);failed=False;return answer
  finally:
   same=mon.get_tool(TOOL)==TOOL_NAME
   if same:
    mon.set_events(TOOL,0)
    for co in self.labels:mon.set_local_events(TOOL,co,0)
    for event in(ev.PY_START,ev.PY_RETURN,ev.PY_UNWIND):mon.register_callback(TOOL,event,None)
    mon.free_tool_id(TOOL)
   self.windows.append(dict(phase=phase,wall_ns=time.perf_counter_ns()-wall,thread_cpu_ns=time.thread_time_ns()-cpu,
    monitor_events=self.events-events,failed=failed))
   self.phase=None;self.intact=self.intact and same and not self.active
   if not failed:need(self.intact,"probe ownership or original return lost")
 def finish(self):
  need(self.intact and not self.closed and self.phase is None and not self.active,"complete one original profile")
  self.closed=True
  return dict(schema=SCHEMA,rank=self.rank,arm=self.arm,source_ref=self.source_ref,recipe_ref=self.recipe_ref,
   source_roles=self.refs,actual_code_bindings=sorted(self.code_refs,key=lambda r:(r['role'],r['name'],r['line'])),synchronize_observed_source=self.sync_source,
   windows=self.windows,stats=[dict(phase=p,label=l,**v)for(p,l),v in sorted(self.stats.items())],
   monitor_events=self.events,unrelated_unwinds=self.unrelated_unwinds,callback_wall_ns=self.callback_wall_ns,
   local_events=["PY_START","PY_RETURN"],global_events=["PY_UNWIND"],
   timings_are_inclusive=True,inclusive_categories_must_not_be_summed=True,wall_includes_probe_overhead=True,
   callback_overhead_is_observed_not_subtracted=True,thread_cpu_excludes_other_threads=True,
   device_kernel_time_measured=False,new_synchronizations=0,tensor_snapshots=0,per_token_file_publications=0,
   numerical_verified=False,performance_accepted=False,run_authority=False)
