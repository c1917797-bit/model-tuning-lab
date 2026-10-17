"""One exact PyTorch inference_mode wrapper, not generic __wrapped__ walking."""
import hashlib,inspect,sys,types
from pathlib import Path

RUNNER_SHA='94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968'
def need(v,s):
    if not v:raise ValueError(s)
def code(parent,name):
    values=[x for x in parent.co_consts if isinstance(x,types.CodeType) and x.co_name==name]
    need(len(values)==1,'unique exact code constant '+name);return values[0]
def module_source(module,pin):
    p=Path(module.__file__);raw=p.read_bytes()
    need(str(p)==pin['path'] and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'exact actual-image PyTorch source '+str(p))
    need(sys.flags.optimize==0,'reviewed unoptimized source comparison')
    return compile(raw,str(p),'exec',dont_inherit=True,optimize=0)
def inference_wrapper(torch,fn,inner,pins):
    import torch.utils._contextlib as ctx
    import torch.autograd.grad_mode as grad
    cc=module_source(ctx,pins['contextlib']);gc=module_source(grad,pins['grad_mode'])
    factory=code(cc,'context_decorator');wrapper=code(factory,'decorate_context')
    need(ctx.context_decorator.__code__==factory and ctx.context_decorator.__globals__ is ctx.__dict__,'actual unmodified PyTorch context factory')
    need(type(fn) is types.FunctionType and fn.__code__ is code(ctx.context_decorator.__code__,'decorate_context')
         and fn.__code__==wrapper and fn.__globals__ is ctx.__dict__ and fn.__defaults__ is None and fn.__kwdefaults__ is None,'one exact actual PyTorch decorator body/globals/defaults')
    need(fn.__code__.co_freevars==('ctx_factory','func') and fn.__closure__ is not None and len(fn.__closure__)==2
         and fn.__closure__[1].cell_contents is inner and fn.__wrapped__ is inner,'exact same captured native function, no generic unwrap')
    bound=fn.__closure__[0].cell_contents
    need(type(bound) is types.MethodType and type(bound.__self__) is torch.inference_mode
         and torch.inference_mode is grad.inference_mode and bound.__self__.mode is True
         and bound.__func__ is grad.inference_mode.__dict__['clone'],'actual inference_mode(True).clone bound factory')
    cls=code(gc,'inference_mode')
    for name in('__init__','__new__','__enter__','__exit__','clone'):
        method=grad.inference_mode.__dict__[name]
        if isinstance(method,staticmethod):method=method.__func__
        need(method.__code__==code(cls,name) and method.__globals__ is grad.__dict__,'actual source inference-mode method '+name)
    return fn
def execute_entry(torch,R,fn,pins):
    """Validate native class body while CALLING the original decorated outer."""
    need(R.__dict__.get('execute_model') is fn and type(fn) is types.FunctionType,'direct actual declaring execute method')
    runner=sys.modules[R.__module__];path=Path(inspect.getsourcefile(R));raw=path.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==RUNNER_SHA and Path(runner.__file__)==path,'actual pinned runner module/class source')
    inner=getattr(fn,'__wrapped__',None)
    need(type(inner) is types.FunctionType and not hasattr(inner,'__wrapped__') and inner.__globals__ is runner.__dict__
         and inner.__module__==R.__module__ and inner.__qualname__=='NPUModelRunner.execute_model'
         and inspect.getsourcefile(inner)==str(path) and inner.__defaults__==(None,) and inner.__kwdefaults__ is None,'one original native execute body/defaults/globals')
    root=compile(raw,str(path),'exec',dont_inherit=True,optimize=0);expected=code(code(root,'NPUModelRunner'),'execute_model')
    need(inner.__code__==expected,'exact full-source native execute code object')
    inference_wrapper(torch,fn,inner,pins)
    return fn  # Never substitute an unwrapped body and remove inference mode.
