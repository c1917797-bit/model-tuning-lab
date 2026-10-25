"""Explicit R36 bootstrap; disabled mode imports no local treatment."""
import os
if os.environ.get("INDEPENDENT_GRAPH_HYPIC")=="1":
    try:
        from pathlib import Path
        import hashlib,json
        path=Path(os.environ["INDEPENDENT_GRAPH_MANIFEST"]).resolve()
        manifest=json.loads(path.read_bytes());own=Path(__file__).resolve()
        if own!=path.parent/"step_durability_r36/sitecustomize.py":
            raise ValueError("actual durability sitecustomize origin differs")
        if hashlib.sha256(own.read_bytes()).hexdigest()!=manifest["source_sha256"]["step_durability_r36/sitecustomize.py"]:
            raise ValueError("durability sitecustomize source drift")
        from patch import enable
        _remove_durability_bootstrap=enable()
    except BaseException:
        import traceback
        traceback.print_exc()
        os._exit(78)
