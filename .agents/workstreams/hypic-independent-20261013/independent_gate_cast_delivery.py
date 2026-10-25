"""Default-off source-owned gate-cast placement experiment, removable at startup."""
from functools import wraps
import hashlib
import importlib
from pathlib import Path
import sys

def install_gate_cast_placement(*,enabled=False,hoisted=False,emit=None,source_bindings=None):
    if type(enabled)is not bool or type(hoisted)is not bool:
        raise ValueError("explicit gate-cast diagnostic booleans required")
    if not enabled:
        if hoisted:raise ValueError("hoisted gates require enabled diagnostic")
        return lambda:None
    if not callable(emit)or type(source_bindings)is not dict:
        raise ValueError("source-bound gate-cast evidence sink required")
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    own=sys.modules[__name__]
    verify_support(own,source_bindings.get(__name__))
    boundary=importlib.import_module("independent_recurrent_boundary")
    original=boundary.recurrent_boundary
    source=verify_support(boundary,source_bindings.get(boundary.__name__))
    verify_raw_function(boundary,source,original,name="recurrent_boundary")
    modules=[importlib.import_module(name)for name in
        ("independent_c1_short_prefix","independent_c1_short_suffix")]
    for module in modules:
        verify_support(module,source_bindings.get(module.__name__))
        if module.recurrent_boundary is not original:
            raise RuntimeError("gate-cast caller alias already changed")
    wrappers=[];validated=set()
    for module,phase in zip(modules,("prefix","suffix")):
        def make_wrapper(phase):
            @wraps(original)
            def wrapped(*args,**kwargs):
                if "hoist_gate_casts"in kwargs or "gate_cast_observer"in kwargs:
                    raise ValueError("gate-cast caller cannot override frozen placement")
                from independent_compact_model_hook import CURRENT_COMPACT_MODEL
                selection=CURRENT_COMPACT_MODEL.get()
                if selection is None or not selection.plans:
                    raise ValueError("gate-cast diagnostic requires selected HYPIC wave")
                identities={(p.rank,p.step)for p in selection.plans}
                if len(identities)!=1:raise ValueError("gate-cast wave identity drift")
                rank,step=next(iter(identities))
                shape=(phase,tuple((tuple(t.shape),str(t.dtype),str(t.device)) for t in args[:6]))
                already_validated=shape in validated
                if not already_validated and len(validated)>=256:
                    raise ValueError("bounded first-shape gate-cast validation exhausted")
                def observe(metrics):
                    emit(dict(metrics,event="c1_gate_cast_placement_observed",
                        rank=rank,step=step,phase=phase,
                        request_ids=[p.request_id for p in selection.plans],
                        first_shape_already_validated=already_validated,
                        association="selected wave; not an individual layer receipt"))
                result=original(*args,**kwargs,hoist_gate_casts=hoisted,
                                gate_cast_observer=observe)
                if not already_validated:
                    import torch
                    reference=original(*args,**kwargs,hoist_gate_casts=False)
                    passed=all(torch.equal(x,y)for x,y in zip(result,reference))
                    emit({"event":"c1_gate_cast_first_shape_checked","rank":rank,"step":step,
                        "phase":phase,"request_ids":[p.request_id for p in selection.plans],
                        "hoisted":hoisted,"device":str(args[0].device),"passed":passed,
                        "length":args[0].shape[1],"full_private_output_and_state":True,
                        "scope":"same actual inputs vs retained per-token cast recurrence; not whole-model quality"})
                    if not passed:raise ValueError("gate-cast exact private shape comparison failed")
                    validated.add(shape)
                return result
            wrapped._independent_gate_cast_owned=True
            return wrapped
        wrappers.append(make_wrapper(phase))
    for module,wrapper in zip(modules,wrappers):module.recurrent_boundary=wrapper
    def assert_owned():
        if (boundary.recurrent_boundary is not original
                or any(module.recurrent_boundary is not wrapper
                       for module,wrapper in zip(modules,wrappers))):
            raise ValueError("gate-cast caller alias ownership changed")
    def stop():
        assert_owned()
        for module in modules:module.recurrent_boundary=original
        validated.clear()
    stop.assert_ownership=assert_owned
    try:
        emit({"event":"c1_gate_cast_placement_installed","hoisted":hoisted,
            "boundary_sha256":hashlib.sha256(source).hexdigest(),
            "same_recurrence_order":True,"completion_and_finite_guards_changed":False,
            "scope":"installation only; integrated device request proof pending"})
    except BaseException:
        stop();raise
    return stop
