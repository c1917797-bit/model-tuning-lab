"""Source-pinned entrypoint for the bounded diagnostic observer."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

_HANDLE = None


def activate():
    global _HANDLE
    if os.environ.get("HYPIC_STATE_OBSERVER_ENABLE") != "1":
        return None
    root = Path(__file__).resolve().parent
    raw = (root/"MANIFEST.json").read_bytes()
    manifest = json.loads(raw)
    for path_key, hash_key in (("patch_file", "patch_sha256"), ("loader_file", "loader_sha256"),
                               ("launcher_file", "launcher_sha256")):
        item = manifest["treatment"]
        if hashlib.sha256((root/item[path_key]).read_bytes()).hexdigest() != item[hash_key]:
            raise ValueError("package byte identity mismatch")
    for name, digest in manifest["support_sha256"].items():
        if Path(name).name != name or not name.endswith(".py"):
            raise ValueError("invalid support path")
        path = root.parent/name
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("support byte identity mismatch")
        imported = sys.modules.get(path.stem)
        if imported is not None and Path(imported.__file__).resolve() != path:
            raise ValueError("foreign support module already imported")
    config_path = Path(os.environ["HYPIC_STATE_CAPTURE_CONFIG"])
    if not config_path.is_absolute():
        raise ValueError("absolute frozen config path required")
    config = json.loads(config_path.read_bytes())
    if set(config) != {"raw_root", "request_id", "kv_layer", "gdn_layer"}:
        raise ValueError("unexpected capture config fields")
    config["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    sys.path.insert(0, str(root.parent))
    _HANDLE = importlib.import_module("numerical_state_loader_v2").activate(config)
    return _HANDLE


def deactivate():
    global _HANDLE
    if _HANDLE is not None:
        _HANDLE.uninstall()
        _HANDLE = None
