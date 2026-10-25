"""Default-disabled R33 prefix-only output-work experiment and startup bridge."""
import ast,hashlib,importlib,inspect,json,os,sys
from functools import wraps
from pathlib import Path

def _output_only_ast(function):
    tree=ast.parse(inspect.getsource(function));removed=[];rewritten=[]
    class Transform(ast.NodeTransformer):
        def visit_Expr(self,node):
            v=node.value
            if(isinstance(v,ast.Call)and isinstance(v.func,ast.Attribute)
                    and isinstance(v.func.value,ast.Name)and v.func.value.id=="outputs"and v.func.attr=="append"):
                removed.append(ast.dump(node));return None
            return self.generic_visit(node)
        def visit_Assign(self,node):
            if(len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id=="result"):
                if(not isinstance(node.value,ast.Tuple)or len(node.value.elts)!=2
                        or ast.unparse(node.value.elts[0])!="torch.stack(outputs)[None].to(v.dtype)"
                        or ast.unparse(node.value.elts[1])!="state[None]"):
                    raise ValueError("exact output/state return required")
                node.value.elts[0]=ast.Constant(None);rewritten.append(True)
            return self.generic_visit(node)
    tree=Transform().visit(tree);tree.body[0].name="terminal_boundary"
    if len(removed)!=1 or len(rewritten)!=1:raise ValueError("one discarded output site required")
    return ast.dump(tree,include_attributes=False)

def install_prefix_terminal(*,enabled=False,terminal_only=False,emit=None,source_bindings=None):
    if type(enabled)is not bool or type(terminal_only)is not bool:raise ValueError("explicit prefix booleans required")
    if not enabled:
        if terminal_only:raise ValueError("treatment requires common diagnostic")
        return lambda:None
    if not callable(emit)or type(source_bindings)is not dict:raise ValueError("source-bound sink required")
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    own=sys.modules[__name__];verify_support(own,source_bindings.get(__name__))
    from . import terminal_math as math_module
    boundary=importlib.import_module("independent_recurrent_boundary")
    prefix=importlib.import_module("independent_c1_short_prefix")
    suffix=importlib.import_module("independent_c1_short_suffix")
    for module in(boundary,prefix,suffix,math_module):
        src=verify_support(module,source_bindings.get(module.__name__))
        if module is boundary:verify_raw_function(module,src,module.recurrent_boundary,name="recurrent_boundary")
        if module is prefix:verify_raw_function(module,src,module.align_short_prefix_terminals,name="align_short_prefix_terminals")
        if module is math_module:verify_raw_function(module,src,module.terminal_boundary,name="terminal_boundary")
    original=boundary.recurrent_boundary;terminal=math_module.terminal_boundary
    if prefix.recurrent_boundary is not original or suffix.recurrent_boundary is not original:
        raise RuntimeError("prefix/suffix alias already owned")
    caller=ast.parse(inspect.getsource(prefix.align_short_prefix_terminals))
    calls=[n for n in ast.walk(caller)if isinstance(n,ast.Assign)and isinstance(n.value,ast.Call)
           and isinstance(n.value.func,ast.Name)and n.value.func.id=="recurrent_boundary"]
    if(len(calls)!=1 or ast.unparse(calls[0].targets[0])!="(_, state)"
       or any(isinstance(n,ast.Name)and isinstance(n.ctx,ast.Load)and n.id=="_"for n in ast.walk(caller))):
        raise ValueError("prefix must discard every recurrent output")
    if _output_only_ast(original)!=ast.dump(ast.parse(inspect.getsource(terminal)),include_attributes=False):
        raise ValueError("terminal implementation changes more than unused outputs")
    validated=set()
    @wraps(original)
    def wrapped(*args,**kwargs):
        assert_owned()
        if len(args)!=6 or set(kwargs)-{"input_observer"}:raise ValueError("exact prefix ABI required")
        from independent_compact_model_hook import CURRENT_COMPACT_MODEL
        selection=CURRENT_COMPACT_MODEL.get()
        if selection is None or not selection.plans:raise ValueError("selected HYPIC wave required")
        identities={(p.rank,p.step)for p in selection.plans}
        if len(identities)!=1:raise ValueError("selected wave identity drift")
        rank,step=next(iter(identities))
        shape=tuple((tuple(t.shape),str(t.dtype),str(t.device))for t in args)
        signature=hashlib.sha256(json.dumps(shape,separators=(",",":")).encode()).hexdigest()
        already=shape in validated
        if not already and len(validated)>=256:raise ValueError("bounded shape set exhausted")
        result=(terminal if terminal_only else original)(*args,**kwargs)
        common={"rank":rank,"step":step,"phase":"prefix","length":args[0].shape[1],
            "request_ids":[p.request_id for p in selection.plans],
            "shape_sha256":signature,"terminal_only":terminal_only}
        emit(dict(common,event="r33_prefix_terminal_observed",first_shape_already_validated=already,
            output_matmul_dispatch_sites_skipped=args[0].shape[1]if terminal_only else 0,
            association="selected wave; not an individual-layer/request exposure claim"))
        if not already:
            import torch
            shadow_kwargs=dict(kwargs,input_observer=None)
            reference=(original if terminal_only else terminal)(*args,**shadow_kwargs)
            passed=torch.equal(result[1],reference[1])
            emit(dict(common,event="r33_prefix_terminal_first_shape_verified",device=str(args[0].device),shapes=shape,
                passed=passed,full_terminal_state=True,
                state_arithmetic_and_query_normalization_unchanged=True))
            if not passed:raise ValueError("actual private terminal state differs")
            validated.add(shape)
        return result
    def assert_owned():
        if prefix.recurrent_boundary is not wrapped or suffix.recurrent_boundary is not original:
            raise RuntimeError("prefix-only alias ownership changed")
    prefix.recurrent_boundary=wrapped
    def stop():
        assert_owned();prefix.recurrent_boundary=original;validated.clear()
    stop.assert_ownership=assert_owned
    try:
        emit({"event":"r33_prefix_terminal_installed","terminal_only":terminal_only,
            "prefix_only":True,"suffix_unchanged":True,"state_math_changed":False,
            "math_sha256":source_bindings[math_module.__name__],
            "scope":"installation only; actual per-rank request evidence required"})
    except BaseException:
        stop();raise
    return stop

def install_activation_bridge(manifest_path):
    # Called by the source-bound new bootstrap before the unchanged worker loader.
    from graph_candidate import worker_loader,activation
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    _,manifest,config=worker_loader._manifest(manifest_path)
    diagnostic=config.get("r33_prefix_terminal_diagnostic",False)
    terminal_only=config.get("r33_prefix_terminal_only",False)
    if type(diagnostic)is not bool or type(terminal_only)is not bool:
        raise ValueError("explicit common observer and treatment booleans required")
    if not diagnostic:
        if terminal_only:raise ValueError("treatment requires diagnostic")
        return lambda:None
    value=os.environ.get("INDEPENDENT_PREFIX_TERMINAL_ONLY","0")
    if value not in("0","1")or(value=="1")is not terminal_only:
        raise ValueError("bound config and one environment switch disagree")
    bindings={n[:-3].replace("/","."):digest for n,digest in manifest["source_sha256"].items()if n.endswith(".py")}
    for module in(sys.modules[__name__],activation):
        src=verify_support(module,bindings.get(module.__name__))
        if module is activation:verify_raw_function(module,src,module.activate_graph_candidate,name="activate_graph_candidate")
    original=activation.activate_graph_candidate;used=False;closed=False
    def restore():
        nonlocal closed
        if closed:return
        if activation.activate_graph_candidate is not wrapped:raise RuntimeError("activation bridge ownership changed")
        activation.activate_graph_candidate=original;closed=True
    @wraps(original)
    def wrapped(cfg,*,enabled=False,emit=None,source_bindings=None,request_progress_limit=128):
        nonlocal used
        if used or activation.activate_graph_candidate is not wrapped:raise RuntimeError("one activation per worker")
        if cfg.get("r33_prefix_terminal_diagnostic")is not True or cfg.get("r33_prefix_terminal_only")is not terminal_only:
            raise ValueError("bound activation config differs")
        used=True
        clean={k:v for k,v in cfg.items()if k not in("r33_prefix_terminal_diagnostic","r33_prefix_terminal_only")}
        stop_base=original(clean,enabled=enabled,emit=emit,source_bindings=source_bindings,
                           request_progress_limit=request_progress_limit)
        try:
            stop_prefix=install_prefix_terminal(enabled=enabled,terminal_only=terminal_only,
                emit=emit,source_bindings=bindings)
        except BaseException:
            stop_base();restore();raise
        def stop():
            try:stop_prefix()
            finally:
                try:stop_base()
                finally:restore()
        return stop
    activation.activate_graph_candidate=wrapped
    return restore
