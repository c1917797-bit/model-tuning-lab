"""Delivery adapter only; independent algorithm remains in the parent package."""
import hashlib,importlib,json,os,sys
from pathlib import Path

def activate():
    if os.environ.get("INDEPENDENT_COMPACT_HYPIC")!="1":return
    package=Path(__file__).resolve().parent;base=package.parent
    manifest=json.loads((package/"MANIFEST.json").read_text())
    treatment=manifest["treatment"]
    for key,name in (("patch_sha256","patch.py"),("loader_sha256","sitecustomize.py"),("launcher_sha256","run_with_patch.sh")):
        p=package/name
        if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=treatment[key]:
            raise ValueError("delivery wrapper source drift: "+name)
    runtime_name=manifest.get("runtime_manifest_file")
    if runtime_name not in ("LIFECYCLE_COMPACT_MANIFEST_R16.json",
                            "LIFECYCLE_COMPACT_MANIFEST_R21.json"):
        raise ValueError("explicit versioned independent runtime manifest required")
    runtime_path=base/runtime_name
    if runtime_path.is_symlink() or hashlib.sha256(runtime_path.read_bytes()).hexdigest()!=manifest["runtime_manifest_sha256"]:
        raise ValueError("runtime manifest drift")
    if Path(os.environ.get("INDEPENDENT_COMPACT_MANIFEST","/missing")).resolve()!=runtime_path:
        raise ValueError("explicit exact runtime manifest environment required")
    runtime=json.loads(runtime_path.read_text())
    for name,digest in runtime["source_sha256"].items():
        original=base/name;p=original.resolve()
        if original.is_symlink() or not p.is_relative_to(base) or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError("runtime source drift: "+name)
    if str(base)not in sys.path:sys.path.insert(0,str(base))
    module=importlib.import_module("independent_compact_loader")
    if Path(module.__file__).resolve()!=base/"independent_compact_loader.py":
        raise ValueError("wrong independent loader import origin")
    module.enable()
