"""Enable only the explicitly selected graph candidate in a fresh process."""
import os
if os.environ.get("INDEPENDENT_GRAPH_HYPIC") == "1":
    try:
        from graph_candidate.worker_loader import enable
        enable()
    except BaseException:
        import traceback
        traceback.print_exc()
        os._exit(78)
