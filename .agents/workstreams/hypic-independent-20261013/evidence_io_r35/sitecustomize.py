"""Explicit R35 bootstrap; disabled mode imports no local diagnostic."""
import os
if os.environ.get("INDEPENDENT_GRAPH_HYPIC")=="1":
    try:
        from pathlib import Path
        import hashlib,json
        path=Path(os.environ["INDEPENDENT_GRAPH_MANIFEST"]).resolve()
        manifest=json.loads(path.read_bytes());own=Path(__file__).resolve()
        if own!=path.parent/"evidence_io_r35/sitecustomize.py":
            raise ValueError("actual IO sitecustomize origin differs")
        if hashlib.sha256(own.read_bytes()).hexdigest()!=manifest["source_sha256"]["evidence_io_r35/sitecustomize.py"]:
            raise ValueError("IO sitecustomize source drift")
        from patch import enable
        _remove_io_bootstrap=enable()
    except BaseException:
        import traceback
        traceback.print_exc()
        os._exit(78)
