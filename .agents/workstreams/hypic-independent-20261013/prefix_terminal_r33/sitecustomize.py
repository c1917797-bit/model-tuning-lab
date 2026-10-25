"""Explicit common R33 bootstrap; disabled graph imports no local treatment."""
import os
if os.environ.get("INDEPENDENT_GRAPH_HYPIC")=="1":
    restore=None
    try:
        from pathlib import Path
        import hashlib,json
        path=Path(os.environ["INDEPENDENT_GRAPH_MANIFEST"]).resolve()
        manifest=json.loads(path.read_text())
        own=Path(__file__).resolve()
        if own!=path.parent/"prefix_terminal_r33/sitecustomize.py":
            raise ValueError("actual R33 bootstrap origin mismatch")
        if hashlib.sha256(own.read_bytes()).hexdigest()!=manifest["source_sha256"]["prefix_terminal_r33/sitecustomize.py"]:
            raise ValueError("R33 bootstrap source drift")
        from prefix_terminal_r33.patch import install_activation_bridge
        restore=install_activation_bridge(path)
        from graph_candidate.worker_loader import enable
        enable()
    except BaseException:
        import traceback
        traceback.print_exc()
        if restore is not None:
            try:restore()
            except BaseException:traceback.print_exc()
        os._exit(78)
