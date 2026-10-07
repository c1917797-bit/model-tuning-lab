"""OFF-only native receiver verifier; never creates capture attributes."""
from __future__ import annotations
import inspect
from pathlib import Path
from v2_contract import BINDINGS_SHA, ROOT, file_sha, require

def helpers():
    path=ROOT/"projects/damp-ascend/collector/damp_capture/bindings.py"
    require(file_sha(path)==BINDINGS_SHA,"original helper bytes drift")
    from damp_capture import bindings
    from damp_capture.contract import LAYERS
    from damp_capture.session import layer_index
    require(Path(bindings.__file__).resolve()==path,"wrong binding helper import")
    return bindings,LAYERS,layer_index

def off_native_bindings(no_compile_layers,donor,target,native_core):
    bindings,LAYERS,layer_index=helpers()
    require(bindings.verify_native_alias(donor,target) is native_core,"native alias changed")
    require(not hasattr(donor,"_damp_original_core") and not hasattr(target,"_damp_original_core"),
            "OFF unexpectedly has capture attributes")
    require(isinstance(no_compile_layers,dict),"actual dispatcher table required")
    found=[]
    for prefix,instance in no_compile_layers.items():
        if not isinstance(instance,(donor,target)): continue
        require(type(instance) is target and instance.prefix==prefix,"actual class/prefix mismatch")
        require(getattr(instance._forward_core,"__func__",None) is native_core and
                getattr(instance.forward,"__func__",None) is donor.forward,
                "actual native instance binding mismatch")
        class_path=str(Path(inspect.getfile(type(instance))).resolve())
        found.append(dict(layer=layer_index(prefix),prefix=prefix,
            instance_class=type(instance).__module__+"."+type(instance).__qualname__,
            class_path=class_path,class_sha256=file_sha(class_path),
            core_owner=bindings.function_identity(instance._forward_core),
            original_core_owner=bindings.function_identity(native_core),
            outer_forward_owner=bindings.function_identity(instance.forward)))
    require(len(found)==len(LAYERS) and {r["layer"] for r in found}==set(LAYERS),
            "exact all48 native receiver bindings required")
    return sorted(found,key=lambda r:r["layer"])
