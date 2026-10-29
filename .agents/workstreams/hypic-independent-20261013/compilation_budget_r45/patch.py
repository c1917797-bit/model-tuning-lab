"""Default-off, owned Triton compilation observation; no kernel/cache/math change."""
import functools,hashlib,inspect,json,os,threading,time,types
from pathlib import Path
PROFILE="source-pinned-triton-compile-v1"
PINS={"triton.runtime.jit":"8f170a849331e9ce75b0d2d05e0bcd6ad2f9de838bfb277e823617982d672aad",
      "triton.compiler.compiler":"4e432986cb567b94d282f9a2c2f9911a6c3718337289fa936f240282a6a5d54b"}
KKT_SHA="bcd1e9d8d4ec4f44ba24955ac9b85c6ce26e019802e12c49337f11a31bf64a98"
class ObservationFailure(RuntimeError):pass
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def interval_union_ns(rows):
 out=0;end=None
 for a,b in sorted(rows):
  if type(a)is not int or type(b)is not int or a<0 or b<a:raise ValueError("exact ordered integer clock")
  if end is None or a>end:out+=b-a;end=b
  elif b>end:out+=b-end;end=b
 return out
def scalar_fields(values):
 if type(values)is not dict or len(values)>128:raise ValueError("bounded scalar metadata")
 out={}
 for key,v in values.items():
  if type(key)is not str or len(key)>128:raise ValueError("bounded metadata keys")
  if v is None or type(v)in(bool,int):out[key]=v
  elif type(v)is str and len(v)<=512:out[key]=v
  elif type(v)is float:
   import math
   if not math.isfinite(v):raise ValueError("finite scalar metadata")
   out[key]={"float_hex":v.hex()}
  else:out[key]={"unserialized_type":type(v).__module__+"."+type(v).__qualname__}
 return out
class CompilationObserver:
 def __init__(self,emit,*,rank=lambda:None,clock=time.perf_counter_ns,max_calls=4096):
  if not callable(emit)or not callable(rank)or not callable(clock)or type(max_calls)is not int or not 1<=max_calls<=4096:raise ValueError("bounded explicit observer")
  self.emit=emit;self.rank=rank;self.clock=clock;self.max_calls=max_calls
  self.lock=threading.RLock();self.stacks={};self.calls=0;self.completed=0;self.failed=False;self.emitting=False;self.closed=False
  self.slots=[];self.jit_aliases={};self.original_compile=None;self.compile_wrapper=None;self.skipped_initialized=0;self.native_receipts=[];self.readonly_objects=[]
 def now(self):
  try:v=self.clock()
  except BaseException as error:
   self.failed=True;raise ObservationFailure("observer clock failed")from error
  if type(v)is not int or v<0:
   self.failed=True;raise ObservationFailure("exact nonnegative integer clock required")
  return v
 def assert_ownership(self):
  for owner,name,expected in self.readonly_objects:
   if inspect.getattr_static(owner,name)is not expected:raise ObservationFailure("upstream class identity drift")
  for owner,name,original,wrapped in self.slots:
   if inspect.getattr_static(owner,name)is not wrapped:raise ObservationFailure("observer slot ownership drift")
  for obj,original in self.jit_aliases.values():
   if vars(obj).get("compile")is not self.compile_wrapper:raise ObservationFailure("captured JIT compiler alias drift")
  for fn,receipt in self.native_receipts:
   if(fn.__code__ is not receipt[0]or fn.__globals__ is not receipt[1]or fn.__defaults__ is not receipt[2]or fn.__kwdefaults__ is not receipt[3]):raise ObservationFailure("saved original compiler callable drift")
 def write(self,row):
  with self.lock:
   if self.emitting:raise ObservationFailure("recursive evidence writer")
   self.emitting=True
   try:self.emit(row)
   finally:self.emitting=False
 def call(self,kind,meta,original,args,kwargs):
  entered=self.now();tid=threading.get_ident()
  with self.lock:
   self.assert_ownership()
   if self.closed or self.failed or self.emitting:raise ObservationFailure("observer closed/failed/recursive")
   if self.calls>=self.max_calls: self.failed=True;raise ObservationFailure("compile observation call bound")
   rank=self.rank()
   if rank is not None and(type(rank)is not int or rank not in range(4)):raise ObservationFailure("rank0-3 or explicitly unassigned")
   stack=self.stacks.setdefault(tid,[])
   if len(stack)>=8: self.failed=True;raise ObservationFailure("observer nesting bound")
   if any(f["kind"]==kind for f in stack):self.failed=True;raise ObservationFailure("same-kind recursive compiler observation")
   self.calls+=1;frame={"id":self.calls,"kind":kind};parent=stack[-1]["id"]if stack else None;stack.append(frame)
   common={"call_id":frame["id"],"parent_call_id":parent,"kind":kind,"rank":rank,"thread_id":str(tid),"pid":os.getpid(),"metadata":meta}
   try:self.write(dict(common,event="r45_compilation_begin",wrapper_entry_ns=str(entered)))
   except BaseException:
    self.failed=True;stack.pop();raise
   try:started=self.now()
   except BaseException:
    self.failed=True;stack.pop();raise
  error=None;result=None
  try:result=original(*args,**kwargs)
  except BaseException as e:error=e
  try:
   ended=self.now()
   with self.lock:
    self.assert_ownership()
    if ended<started or not stack or stack[-1]is not frame:raise ObservationFailure("compiler interval/stack drift")
    stack.pop();self.completed+=1
    if error is not None:self.failed=True
    self.write(dict(common,event="r45_compilation_end",original_started_ns=str(started),original_ended_ns=str(ended),
        original_duration_ns=str(ended-started),failed=error is not None,error_type=type(error).__name__ if error is not None else None,
        wrapper_entry_ns=str(entered),begin_probe_ns=str(started-entered),return_type=type(result).__module__+"."+type(result).__qualname__ if error is None else None))
  except BaseException as observation:
   self.failed=True
   if stack and stack[-1]is frame:stack.pop()
   if error is not None:
    if hasattr(error,"add_note"):error.add_note("Compilation observer also failed: "+type(observation).__name__)
   else:raise ObservationFailure("diagnostic observation failed after original call")from observation
  if error is not None:raise error.with_traceback(error.__traceback__)
  return result
 def bind_jit(self,obj):
  value=vars(obj).get("compile")
  with self.lock:
   if id(obj)in self.jit_aliases:
    if value is not self.compile_wrapper:raise ObservationFailure("owned JIT alias changed")
   elif value is self.original_compile or value is self.compile_wrapper:
    self.jit_aliases[id(obj)]=(obj,self.original_compile);obj.compile=self.compile_wrapper
   else:raise ObservationFailure("unknown existing JIT compiler alias")
 def health(self):
  with self.lock:
   self.assert_ownership()
   return {"event":"r45_compilation_health","profile":PROFILE,"calls":self.calls,"completed":self.completed,
       "active":sum(len(s)for s in self.stacks.values()),"failed":self.failed,"skipped_initialized_loads":self.skipped_initialized,
       "scope":"Observed upstream calls; no compiler duration or cache hit alone is a service-speed claim."}
 def wrap_emit(self,original):
  @functools.wraps(original)
  def emit(event):
   result=original(event)
   if event.get("event")=="compact_model_rows_completed":self.write(dict(self.health(),rank=event["rank"],step=event["step"]))
   return result
  return emit
 def stop(self):
  with self.lock:
   if self.closed:return
   self.assert_ownership()
   if any(self.stacks.values()):raise ObservationFailure("uninstall while compile active")
   for obj,original in self.jit_aliases.values():obj.compile=original
   for owner,name,original,wrapped in reversed(self.slots):setattr(owner,name,original)
   self.closed=True
   if self.failed or self.completed!=self.calls:raise ObservationFailure("failed or incomplete diagnostic; original slots restored")
def _source_metadata(src,expected_type=None):
 if (expected_type is not None and type(src)is not expected_type)or type(src).__name__!="ASTSource"or type(vars(src).get("signature"))is not dict:
  return {"source_kind":type(src).__module__+"."+type(src).__qualname__,"unassociated":True}
 fn=vars(src).get("fn");raw=vars(fn).get("fn")if hasattr(fn,"__dict__")else None
 name=vars(src).get("name")
 out={"kernel_name":name if type(name)is str else None,"signature":scalar_fields(vars(src)["signature"]),"constants":scalar_fields(vars(src).get("constants")or{})}
 if name=="chunk_scaled_dot_kkt_fwd_kernel":
  if type(raw)is not types.FunctionType:raise ObservationFailure("source-owned raw KKT function")
  p=Path(raw.__code__.co_filename).resolve()
  source=p.read_bytes()
  if p.name!="chunk_scaled_dot_kkt.py"or hashlib.sha256(source).hexdigest()!=KKT_SHA:raise ObservationFailure("official KKT source drift")
  import sys
  from graph_candidate.source_contract import verify_raw_function
  module=sys.modules.get(raw.__module__)
  if module is None or Path(module.__file__).resolve()!=p:raise ObservationFailure("actual KKT source module missing")
  verify_raw_function(module,source,raw,name="chunk_scaled_dot_kkt_fwd_kernel")
  out["kernel_source_sha256"]=KKT_SHA
 return out
def install_bindings(observer,jit,exported,compiler,root,*,async_mode,verify=True):
 """Bind the reviewed exact slots. Unit tests use verify=False with owned fakes."""
 J=jit.JITFunction;C=compiler.CompiledKernel
 binder=inspect.getattr_static(J,"create_binder");miss=inspect.getattr_static(J,"_do_compile");load=inspect.getattr_static(C,"_init_handles");original=compiler.compile
 if exported.compile is not original or root.compile is not original:raise ObservationFailure("upstream compiler alias identity")
 if verify:
  import sys
  from graph_candidate.source_contract import verify_raw_function
  for module,functions in((jit,((miss,"_do_compile","JITFunction._do_compile"),(binder,"create_binder","JITFunction.create_binder"))),(compiler,((original,"compile",None),(load,"_init_handles","CompiledKernel._init_handles"),(compiler.ASTSource.__init__,"__init__","ASTSource.__init__")))):
   path=Path(module.__file__).resolve();source=path.read_bytes()
   if hashlib.sha256(source).hexdigest()!=PINS[module.__name__]:raise ObservationFailure("official Triton source bytes drift")
   if sys.modules.get(module.__name__)is not module:raise ObservationFailure("actual imported compiler module identity")
   for fn,name,qual in functions:verify_raw_function(module,source,fn,name=name,qualname=qual)
 observer.readonly_objects=[(jit,"JITFunction",J),(compiler,"CompiledKernel",C)]
 if hasattr(compiler,"ASTSource"):observer.readonly_objects.append((compiler,"ASTSource",compiler.ASTSource))
 observer.original_compile=original
 def compile_wrapper(*args,**kwargs):
  src=args[0]if args else kwargs.get("src");meta=_source_metadata(src,getattr(compiler,"ASTSource",None))
  return observer.call("compiler_api",meta,original,args,kwargs)
 observer.compile_wrapper=compile_wrapper
 def binder_wrapper(self,*args,**kwargs):
  result=binder(self,*args,**kwargs);observer.bind_jit(self);return result
 def miss_wrapper(self,*args,**kwargs):
  observer.bind_jit(self)
  key=args[0]if args else kwargs.get("key");constants=args[5]if len(args)>5 else kwargs.get("constants")
  signature=args[1]if len(args)>1 else kwargs.get("signature")
  if type(key)is not str or len(key)>1048576:raise ObservationFailure("bounded original JIT key")
  meta={"kernel_name":vars(self).get("__name__"),"jit_key_sha256":digest(key),"signature":scalar_fields(signature),"constants":scalar_fields(constants),
        "async_compile_active":async_mode()is not None}
  return observer.call("jit_cache_miss",meta,miss,(self,*args),kwargs)
 def load_wrapper(self,*args,**kwargs):
  if vars(self).get("module")is not None:
   observer.skipped_initialized+=1;return load(self,*args,**kwargs)
  meta=_source_metadata(vars(self).get("src"),getattr(compiler,"ASTSource",None));meta["compiled_kernel_hash"]=vars(self).get("hash")
  return observer.call("binary_load",meta,load,(self,*args),kwargs)
 desired=((J,"create_binder",binder,binder_wrapper),(J,"_do_compile",miss,miss_wrapper),(C,"_init_handles",load,load_wrapper),
          (compiler,"compile",original,compile_wrapper),(exported,"compile",original,compile_wrapper),(root,"compile",original,compile_wrapper))
 try:
  for owner,name,native,wrapped in desired:
   if inspect.getattr_static(owner,name)is not native:raise ObservationFailure("slot changed before activation")
   setattr(owner,name,wrapped);observer.slots.append((owner,name,native,wrapped))
  observer.native_receipts=[(f,(f.__code__,f.__globals__,f.__defaults__,f.__kwdefaults__))for f in(binder,miss,load,original)]
  if hasattr(compiler,"ASTSource"):
   f=compiler.ASTSource.__init__;observer.native_receipts.append((f,(f.__code__,f.__globals__,f.__defaults__,f.__kwdefaults__)))
  observer.assert_ownership()
 except BaseException:
  for owner,name,native,wrapped in reversed(observer.slots):
   if inspect.getattr_static(owner,name)is wrapped:setattr(owner,name,native)
  observer.slots=[];raise
 return observer
def activate(*,enabled=False,emit=None,rank=lambda:None,max_calls=4096):
 """Disabled entry imports no Triton or device packages."""
 if not enabled:return None
 if enabled is not True:raise ValueError("explicit enabled boolean")
 import importlib
 import triton
 jit=importlib.import_module("triton.runtime.jit");exported=importlib.import_module("triton.compiler");compiler=importlib.import_module("triton.compiler.compiler")
 from triton.runtime import _async_compile
 observer=CompilationObserver(emit,rank=rank,max_calls=max_calls)
 install_bindings(observer,jit,exported,compiler,triton,async_mode=_async_compile.active_mode.get)
 try:observer.write({"event":"r45_compilation_observer_installed","profile":PROFILE,"default_disabled":True,"upstream_sources":PINS,"max_calls":max_calls,
    "scope":"Owned observational slots only; no kernel/math/cache-policy change and no service benefit proven."})
 except BaseException:
  observer.failed=True
  try:observer.stop()
  except BaseException:pass
  raise
 return observer
