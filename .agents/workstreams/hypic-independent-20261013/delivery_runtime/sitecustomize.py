"""Fail-closed import-hook adapter, not worker hot-path proof."""
import importlib.util,json,os,sys
from pathlib import Path
if os.environ.get("INDEPENDENT_COMPACT_HYPIC")=="1":
    try:
        path=Path(__file__).resolve().parent/"patch.py"
        spec=importlib.util.spec_from_file_location("_independent_hypic_delivery_patch",path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.activate()
    except BaseException as exc:
        try:print(json.dumps({"event":"HYPIC_DELIVERY_LOAD_FAILED","pid":os.getpid(),"error_type":type(exc).__name__}),file=sys.stderr,flush=True)
        finally:os._exit(78)
    print(json.dumps({"event":"HYPIC_DELIVERY_IMPORT_HOOK_READY","pid":os.getpid(),"scope":"loader only; actual rank/layer hot receipts required"}),file=sys.stderr,flush=True)
