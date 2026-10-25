"""R36 removable bootstrap for the source-bound selected-step evidence durability."""
import hashlib,os,sys
from pathlib import Path
def enable():
    from graph_candidate import worker_loader
    from graph_candidate.prefill_bridge import verify_support
    from graph_candidate.source_contract import verify_raw_function
    path=Path(os.environ["INDEPENDENT_GRAPH_MANIFEST"]).resolve()
    _,manifest,_=worker_loader._manifest(path)
    own=Path(__file__).resolve()
    if own!=path.parent/"step_durability_r36/patch.py":raise ValueError("actual durability bootstrap origin differs")
    source=verify_support(sys.modules[__name__],manifest["source_sha256"]["step_durability_r36/patch.py"])
    verify_raw_function(sys.modules[__name__],source,enable,name="enable")
    worker_loader._step_durability_enabled(manifest)
    if worker_loader._io_budget_enabled(manifest):
        raise ValueError("IO timing observer must remain disabled in every durability arm")
    if os.environ.get("INDEPENDENT_PREFIX_TERMINAL_ONLY","0")!="0":
        raise ValueError("rejected prefix-output treatment stays disabled")
    from prefix_terminal_r33.patch import install_activation_bridge
    restore=install_activation_bridge(path)
    try:remove=worker_loader.enable()
    except BaseException:
        restore();raise
    closed=False
    def stop():
        nonlocal closed
        if closed:return
        try:remove()
        finally:restore();closed=True
    return stop
