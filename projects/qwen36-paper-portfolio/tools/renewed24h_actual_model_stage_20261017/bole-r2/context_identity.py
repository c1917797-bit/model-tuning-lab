"""One exact stdlib contextmanager wrapping this source-owned enter function.

No arbitrary unwrap and no source gate bypass: both actual code objects,
globals, identity, closure and source refs must match the pinned modules.
"""
import contextlib,inspect,sys,types,json
from pathlib import Path

def need(v,s):
 if not v:raise ValueError(s)

def code_constant(module_code,name):
 rows=[x for x in module_code.co_consts if isinstance(x,types.CodeType)and x.co_name==name]
 need(len(rows)==1,'unique exact source code object '+name)
 return rows[0]

def enter_source(C,fn,own_ref,stdlib_ref):
 import context_adapter
 observed=dict(expected=own_ref,expected_stdlib=stdlib_ref,module=getattr(fn,'__module__',None),qualname=getattr(fn,'__qualname__',None),actual=None)
 try:
  filename=inspect.getsourcefile(fn);observed['actual']=None if filename is None else C.ref(filename)
  own=C.checked(own_ref);stdlib=C.checked(stdlib_ref)
  need(sys.flags.optimize==0,'exact reviewed unoptimized Python source compilation')
  need(C.ref(context_adapter.__file__)==own_ref and C.ref(contextlib.__file__)==stdlib_ref,'exact own context and actual stdlib files')
  need(observed['actual']==stdlib_ref,'outer helper actually originates in the exact standard library source')
  need(fn is context_adapter.enter and fn is context_adapter._SOURCE_ENTER_WRAPPER and type(fn)is types.FunctionType,'only actual registered context_adapter.enter, not an arbitrary decorated function')
  need(fn.__module__=='context_adapter'and fn.__qualname__=='enter'and set(fn.__dict__)=={'__wrapped__'},'only exact reviewed enter attributes')
  own_code=compile(own.read_bytes(),str(own),'exec',dont_inherit=True,optimize=0)
  std_code=compile(stdlib.read_bytes(),str(stdlib),'exec',dont_inherit=True,optimize=0)
  factory=code_constant(std_code,'contextmanager')
  helper=code_constant(factory,'helper')
  need(contextlib.contextmanager.__code__==factory and contextlib.contextmanager.__globals__ is contextlib.__dict__,'actual unmodified stdlib contextmanager factory')
  need(fn.__code__ is context_adapter._SOURCE_ENTER_WRAPPER_CODE and
       fn.__code__ is code_constant(contextlib.contextmanager.__code__,'helper')and
       fn.__code__==helper and fn.__globals__ is contextlib.__dict__ and fn.__defaults__ is None and fn.__kwdefaults__ is None,'exact stdlib helper code/globals/defaults')
  inner=fn.__wrapped__
  need(C.ref(inspect.getsourcefile(inner))==own_ref,'wrapped body actually originates in exact own source')
  need(inner is context_adapter._SOURCE_ENTER_GENERATOR and type(inner)is types.FunctionType and not hasattr(inner,'__wrapped__')and
       inner.__code__ is context_adapter._SOURCE_ENTER_GENERATOR_CODE and
       inner.__code__==code_constant(own_code,'enter')and inner.__globals__ is context_adapter.__dict__ and
       inner.__module__=='context_adapter'and inner.__qualname__=='enter'and
       inner.__defaults__ is None and inner.__kwdefaults__ is None,'one exact actual enter body/globals, no arbitrary unwrap')
  need(fn.__code__.co_freevars==('func',)and fn.__closure__ is not None and len(fn.__closure__)==1 and fn.__closure__[0].cell_contents is inner,
       'exact stdlib closure captures this same source-owned body')
  need(contextlib._GeneratorContextManager.__module__=='contextlib'and C.ref(inspect.getsourcefile(contextlib._GeneratorContextManager))==stdlib_ref,'actual stdlib generator manager source')
  manager_code=code_constant(std_code,'_GeneratorContextManager')
  for name in('__enter__','__exit__'):
   method=contextlib._GeneratorContextManager.__dict__[name]
   need(method.__code__==code_constant(manager_code,name)and method.__globals__ is contextlib.__dict__,'actual stdlib generator manager method '+name)
  init=contextlib._GeneratorContextManager.__init__
  need(init.__code__==code_constant(code_constant(std_code,'_GeneratorContextManagerBase'),'__init__')and init.__globals__ is contextlib.__dict__,'actual stdlib generator manager constructor')
 except BaseException as error:
  raise ValueError('exact contextmanager enter identity '+json.dumps(observed,sort_keys=True)+' reason='+repr(error))from error
 return dict(own_source=own_ref,stdlib_source=stdlib_ref,wrapper='contextlib.contextmanager.helper',depth=1)
