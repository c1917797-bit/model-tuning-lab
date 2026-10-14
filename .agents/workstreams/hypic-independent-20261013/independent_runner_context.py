"""Reversible runner request-context attachment; technique selection pending."""
from contextvars import ContextVar
from functools import wraps
CURRENT_REQUEST_SLICES=ContextVar("independent_hypic_request_slices",default=None)
CURRENT_PROMPT_TOKENS=ContextVar("independent_hypic_prompt_tokens",default=None)
CURRENT_RUNTIME_SNAPSHOT=ContextVar("independent_hypic_runtime_snapshot",default=None)
def install_runner_context(runner_class,freeze_from_runner,*,enabled=False,verify_source=None,after_prepare=None):
    if not enabled:return lambda:None
    if verify_source is None:raise ValueError("source verification required")
    verify_source(runner_class)
    prepare=runner_class._prepare_inputs
    execute=runner_class.execute_model
    if getattr(prepare,'_independent_context_owned',False) or getattr(execute,'_independent_context_owned',False):
        raise RuntimeError("independent runner context already installed")
    @wraps(prepare)
    def wrapped_prepare(self,*args,**kwargs):
        output=prepare(self,*args,**kwargs)
        CURRENT_REQUEST_SLICES.set(freeze_from_runner(self,args,kwargs))
        if after_prepare is not None:
            after_prepare(self,CURRENT_REQUEST_SLICES.get())
        return output
    @wraps(execute)
    def wrapped_execute(self,*args,**kwargs):
        token=CURRENT_REQUEST_SLICES.set(None)
        prompt_token=CURRENT_PROMPT_TOKENS.set(None)
        runtime_token=CURRENT_RUNTIME_SNAPSHOT.set(None)
        try:return execute(self,*args,**kwargs)
        finally:
            CURRENT_REQUEST_SLICES.reset(token)
            CURRENT_PROMPT_TOKENS.reset(prompt_token)
            CURRENT_RUNTIME_SNAPSHOT.reset(runtime_token)
    wrapped_prepare._independent_context_owned=True
    wrapped_execute._independent_context_owned=True
    runner_class._prepare_inputs=wrapped_prepare;runner_class.execute_model=wrapped_execute
    def uninstall():
        if runner_class._prepare_inputs is not wrapped_prepare or runner_class.execute_model is not wrapped_execute:
            raise RuntimeError("hook ownership changed; do not overwrite another hook")
        runner_class._prepare_inputs=prepare;runner_class.execute_model=execute
    return uninstall
