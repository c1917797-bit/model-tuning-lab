"""Only actual patch_qwen3_5's source-proven copied forward, no unwrap."""
import inspect,json,sys,types

NAMES=dict(gdn='vllm_ascend.ops.gdn',target='vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn',
 patch='vllm_ascend.patch.worker.patch_qwen3_5',base='vllm.model_executor.layers.mamba.gdn.base')

def native_code(C,reference):
 raw=C.checked(reference).read_bytes()
 top=compile(raw,reference['path'],'exec',dont_inherit=True,optimize=0)
 cls=next(c for c in top.co_consts if inspect.iscode(c)and c.co_name=='AscendGatedDeltaNetAttention')
 return next(c for c in cls.co_consts if inspect.iscode(c)and c.co_name=='forward')

def validate(C,method,refs,emit):
 modules={k:sys.modules.get(n)for k,n in NAMES.items()}
 checks={};details={};actual_sources={};f=getattr(method,'__func__',None);receiver=getattr(method,'__self__',None)
 def check(name,work):
  try:checks[name]=bool(work())
  except BaseException as error:checks[name]=False;details[name]=repr(error)[:512]
 def source(obj):
  path=inspect.getsourcefile(obj)
  return None if path is None else C.ref(path)
 for k,m in modules.items():
  check(k+'_canonical_module_source',lambda k=k,m=m:m is not None and m.__name__==NAMES[k] and C.ref(m.__file__)==refs[k])
  try:actual_sources[k]=C.ref(m.__file__)
  except BaseException as error:actual_sources[k]=dict(error=repr(error)[:512])
 g=modules['gdn'];p=modules['patch'];q=modules['target'];base=modules['base']
 G=getattr(g,'AscendGatedDeltaNetAttention',None);T=getattr(q,'QwenGatedDeltaNetAttention',None);B=getattr(base,'GatedDeltaNetAttention',None)
 check('bound_method',lambda:type(method)is types.MethodType and type(f)is types.FunctionType)
 check('source_function',lambda:source(f)==refs['gdn'])
 check('canonical_function_module',lambda:inspect.getmodule(f)is g and f.__module__==NAMES['gdn'])
 check('globals',lambda:f.__globals__ is g.__dict__)
 check('underlying_body',lambda:f.__code__==native_code(C,refs['gdn']) and f.__closure__ is None and f.__defaults__ is None)
 check('qualname',lambda:f.__qualname__=='AscendGatedDeltaNetAttention.forward')
 check('no_wrapper',lambda:not hasattr(f,'__wrapped__'))
 check('origin_class',lambda:source(G)==refs['gdn'] and G.__module__==NAMES['gdn'] and G.forward is f)
 check('target_class',lambda:source(T)==refs['target'] and T.__module__==NAMES['target'] and q.QwenGatedDeltaNetAttention is T)
 check('base_class',lambda:source(B)==refs['base'] and B.__module__==NAMES['base'])
 check('known_copy_assignment',lambda:p._GDN_PATCH_TARGET is p._GDNBaseCls is T and p.AscendGatedDeltaNetAttention is G and T.__dict__['forward']is G.__dict__['forward']is f)
 check('receiver_exact_target',lambda:type(receiver)is T and 'forward'not in receiver.__dict__ and method.__self__ is receiver)
 check('common_direct_base_MRO',lambda:G.__bases__==(B,)and T.__bases__==(B,)and T.__mro__[1]is G.__mro__[1]is B)
 # Keep only bounded primitive diagnostics, persisted before aggregate rejection.
 record=dict(schema='bole.actual-known-copy-GDN-identity/v1',checks=checks,errors=details,
  actual_class=None if receiver is None else type(receiver).__module__+'.'+type(receiver).__qualname__,
  MRO=[]if receiver is None else[c.__module__+'.'+c.__qualname__ for c in type(receiver).__mro__],
  function_module=getattr(f,'__module__',None),qualname=getattr(f,'__qualname__',None),wrapped=hasattr(f,'__wrapped__'),
  source_refs=refs,actual_module_sources=actual_sources,
  actual_function_source=None if type(f)is not types.FunctionType else dict(filename=f.__code__.co_filename,firstlineno=f.__code__.co_firstlineno,code_name=f.__code__.co_name),
  passed=all(checks.values()),qualification=False)
 if len(json.dumps(record,sort_keys=True).encode())>16384:raise ValueError('bounded GDN identity receipt')
 emit(record)
 if not record['passed']:raise ValueError('exact active known-copy GDN identity '+','.join(k for k,v in checks.items()if not v))
 return f.__code__
