"""Explicit R45 startup; disabled observation imports no inference code."""
import os
_graph = os.environ.get("INDEPENDENT_GRAPH_HYPIC", "0")
_compile = os.environ.get("INDEPENDENT_COMPILATION_BUDGET", "0")
if _graph not in ("0", "1") or _compile not in ("0", "1") or (_compile == "1" and _graph != "1"):
    raise SystemExit("R45_INVALID_EXPLICIT_ACTIVATION")
if _graph == "1":
    try:
        import sys
        from pathlib import Path
        from compilation_budget_r45 import worker_loader as _loader
        from graph_candidate.prefill_bridge import verify_support
        from graph_candidate.source_contract import verify_raw_function
        _path, _manifest, _config = _loader._manifest(os.environ["INDEPENDENT_GRAPH_MANIFEST"])
        if Path(__file__).resolve() != _path.parent / "compilation_budget_r45/sitecustomize.py":
            raise ValueError("actual R45 bootstrap origin differs")
        _source = verify_support(_loader, _manifest["source_sha256"]["compilation_budget_r45/worker_loader.py"])
        for _name, _value in vars(_loader).items():
            if type(_value).__name__ == "function" and _value.__module__ == _loader.__name__:
                verify_raw_function(_loader, _source, _value, name=_name)
        _loader._compilation_budget_enabled(_manifest)
        _remove_compilation_bootstrap = _loader.enable()
    except BaseException as error:
        import sys
        print("R45_BOOTSTRAP_FAILED: " + type(error).__name__ + ": " + str(error), file=sys.stderr, flush=True)
        raise SystemExit(171) from error
