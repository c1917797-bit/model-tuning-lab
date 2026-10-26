"""Automatic explicit R38 loader; default disabled imports no inference code."""
import os
_graph=os.environ.get("INDEPENDENT_GRAPH_HYPIC","0")
_cost=os.environ.get("INDEPENDENT_COMPONENT_COST_BUDGET","0")
if _graph not in("0","1")or _cost not in("0","1")or(_cost=="1"and _graph!="1"):
    raise SystemExit("R38_INVALID_EXPLICIT_ACTIVATION")
if _graph=="1":
    try:
        from component_budget_r38.patch import enable
        _remove_component_bootstrap=enable()
    except BaseException as error:
        import sys
        print("R38_BOOTSTRAP_FAILED: "+type(error).__name__+": "+str(error),file=sys.stderr,flush=True)
        raise SystemExit(170)from error
