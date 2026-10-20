"""Scoped read-only projection trace; caller supplies original bounded snapshot.

No function replacement, backend import, collective invocation or extra GEMM.
Construction requires actual bound objects and exact installed-source Ref3s.
"""
import inspect,types

def need(v,m):
 if not v:raise ValueError(m)

def source_code(C,method,refs):
 need(inspect.ismethod(method),'actual Python bound projection method')
 f=method.__func__;module=inspect.getmodule(f);path=inspect.getsourcefile(f)
 need(module is not None and f.__globals__ is module.__dict__ and not hasattr(f,'__wrapped__'),'unwrapped exact module globals')
 need(path in refs and C.ref(path)==refs[path],'exact installed method source, no historic alias')
 # Compile the COMPLETE module: sliced AST compilation changes Python3.12 code.
 codes=[]
 def visit(code,path=()):
  path=path+(()if code.co_name=='<module>'else(code.co_name,))
  if getattr(code,'co_qualname','.'.join(path))==f.__qualname__:codes.append(code)
  for x in code.co_consts:
   if isinstance(x,types.CodeType):visit(x,path)
 visit(compile(C.checked(refs[path]).read_bytes(),path,'exec',dont_inherit=True))
 need(len(codes)==1 and codes[0]==f.__code__,'complete-source exact native projection body')
 return f.__code__

class ProjectionTrace:
 def __init__(self,C,layer,refs,snapshot,scope):
  """scope returns (original call ordinal, GDN0 receiver) or None.

snapshot(call,stage,values) must use original root witness owning clones/caps.
This class does not grant permission to execute the model.
"""
  self.layer=layer;self.snapshot=snapshot;self.scope=scope
  self.frames={};self.methods={};self.calls=[];self.fault=None
  self.scalar=dict(layer_class=type(layer).__module__+'.'+type(layer).__qualname__,prefix=layer.prefix,
   tp_rank=layer.tp_rank,tp_size=layer.tp_size,input_is_parallel=layer.input_is_parallel,
   reduce_results=layer.reduce_results,return_bias=layer.return_bias,
   custom_class=None if layer.custom_op is None else type(layer.custom_op).__module__+'.'+type(layer.custom_op).__qualname__,
   quant_class=type(layer.quant_method).__module__+'.'+type(layer.quant_method).__qualname__)
  targets=[('projection.forward',layer.forward),('quant.apply',layer.quant_method.apply)]
  for base in type(layer).__mro__[1:]:
   f=base.__dict__.get('forward')
   if base.__name__=='RowParallelLinear'and inspect.isfunction(f)and f.__qualname__=='RowParallelLinear.forward'and f is not layer.forward.__func__:
    targets.append(('projection.generic_forward',types.MethodType(f,layer)))
  if layer.custom_op is not None:
   targets.extend([('custom.apply',layer.custom_op.apply),('custom.apply_impl',layer.custom_op.apply_impl)])
   if hasattr(layer.custom_op,'matmul_and_reduce'):targets.append(('custom.matmul_and_reduce',layer.custom_op.matmul_and_reduce))
  for role,method in targets:
   code=source_code(C,method,refs)
   need(code not in self.methods,'distinct exact native method codes')
   self.methods[code]=(role,method.__self__,method.__func__)
 def event(self,frame,event,arg):
  if event=='call':
   match=self.methods.get(frame.f_code);scope=self.scope()
   if match is None or scope is None:return False
   role,obj,f=match
   need(getattr(scope[1],'out_proj',None)is self.layer,'strong current GDN0 projection ownership')
   need(frame.f_locals.get('self')is obj and frame.f_globals is f.__globals__,'same active receiver/globals')
   need(type(scope[0])is int and scope[0]in(0,2),'original repeated-root call ordinal')
   self.frames[id(frame)]=(frame,role,scope[0],set())
   self.calls.append((scope[0],role,'call'))
   values={k:frame.f_locals[k]for k in ('input_','input_parallel','x','bias','bias_')if k in frame.f_locals}
   self.snapshot(scope[0],role+'.entry',values)
   return True
  row=self.frames.get(id(frame))
  if row is None:return False
  need(row[0]is frame,'same live traced frame')
  _,role,call,seen=row
  if event=='exception':
   self.fault=repr(arg[1]);return True
  if event=='line':
   # A line event occurs AFTER the previous statement, BEFORE this statement.
   # Capture each actual local only after it exists; never manufacture a value.
   for key in ('input_parallel','output_parallel','output'):
    if key in frame.f_locals and key not in seen:
     seen.add(key);self.snapshot(call,role+'.'+key,{key:frame.f_locals[key]})
  if event=='return':
   values={'returned':arg[0]if isinstance(arg,tuple)else arg}
   self.snapshot(call,role+'.return',values)
   self.calls.append((call,role,'return'));del self.frames[id(frame)]
  return True
 def finish(self):
  need(not self.frames and self.fault is None,'projection trace completed without exception')
  for call in(0,2):
   need(self.calls.count((call,'projection.forward','call'))==self.calls.count((call,'projection.forward','return'))==1,'one actual projection per original forward')
  return dict(schema='bole.root-projection-internal-trace/v1',active=self.scalar,calls=self.calls,
   diagnostic_only=True,qualified=False,local_result_may_be_absent_when_fused=True)
