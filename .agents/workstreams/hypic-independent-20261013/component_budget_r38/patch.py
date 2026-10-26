"""Own removable R38 observation; unchanged original component functions execute."""
import os,sys
from pathlib import Path
def enable():
    if os.environ.get("INDEPENDENT_GRAPH_HYPIC","0")!="1":
        if os.environ.get("INDEPENDENT_COMPONENT_COST_BUDGET","0")!="0":
            raise ValueError("component observation requires explicit graph activation")
        return lambda:None
    from graph_candidate import worker_loader as w
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    path=Path(os.environ["INDEPENDENT_GRAPH_MANIFEST"]).resolve()
    _,manifest,config=w._manifest(path)
    own=Path(__file__).resolve()
    if own!=path.parent/"component_budget_r38/patch.py":raise ValueError("actual component bootstrap origin differs")
    src=verify_support(sys.modules[__name__],manifest["source_sha256"]["component_budget_r38/patch.py"])
    verify_raw_function(sys.modules[__name__],src,enable,name="enable")
    src=verify_support(w,manifest["source_sha256"]["graph_candidate/worker_loader.py"])
    for name in("enable","_component_budget_enabled","_step_durability_enabled","_io_budget_enabled","_close_component"):
        verify_raw_function(w,src,getattr(w,name),name=name)
    w._component_budget_enabled(manifest)
    if not w._step_durability_enabled(manifest)or w._io_budget_enabled(manifest):
        raise ValueError("R38 retains step durability and excludes IO timing observer")
    if any(k in config for k in("r33_prefix_terminal_diagnostic","r33_prefix_terminal_only")):
        raise ValueError("R33 observer must remain absent")
    if os.environ.get("INDEPENDENT_PREFIX_TERMINAL_ONLY","0")!="0":
        raise ValueError("rejected prefix-output treatment remains disabled")
    remove=w.enable();closed=False
    def stop():
        nonlocal closed
        if closed:return
        remove();closed=True
    return stop
