"""Exact function-alias binding proof; no model/runtime imports."""
import inspect
from pathlib import Path
from .contract import LAYERS, file_digest, require
from .session import layer_index

BINDING_SOURCES = {
    "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py": "21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3",
    "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py": "885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0",
    "/vllm-workspace/vllm/vllm/forward_context.py": "1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5",
}


def verify_native_alias(donor, target):
    require(donor is not target and target._forward_core is donor._forward_core and
            target.forward is donor.forward, "actual Qwen receiver is not the frozen native Ascend alias")
    require(inspect.isfunction(donor._forward_core) and inspect.isfunction(donor.forward),
            "native alias must be ordinary exact function objects")
    return donor._forward_core


def bind_aliased_core(donor, target, wrapper):
    original = verify_native_alias(donor, target)
    require(inspect.isfunction(wrapper) and not hasattr(donor, "_damp_original_core") and
            not hasattr(target, "_damp_original_core"), "duplicate/invalid collector core installation")
    # Python function-object copying is not inheritance: update both actual bindings.
    donor._damp_original_core = target._damp_original_core = original
    donor._forward_core = target._forward_core = wrapper
    return original


def function_identity(function):
    function = getattr(function, "__func__", function)
    require(inspect.isfunction(function), "uninspectable live function owner")
    path = str(Path(inspect.getsourcefile(function)).resolve())
    return dict(module=function.__module__, qualname=function.__qualname__, path=path,
                sha256=file_digest(path), firstlineno=function.__code__.co_firstlineno)


def live_bindings(no_compile_layers, donor, target, wrapper):
    require(isinstance(no_compile_layers, dict), "actual dispatcher layer table required")
    found = []
    for prefix, instance in no_compile_layers.items():
        if not isinstance(instance, (donor, target)):
            continue
        require(type(instance) is target and instance.prefix == prefix,
                "unverified actual GDN class/subclass or dispatcher prefix mismatch")
        require(getattr(instance._forward_core, "__func__", None) is wrapper and
                getattr(instance.forward, "__func__", None) is donor.forward,
                "actual instance bypasses collector/native outer forward")
        class_path = str(Path(inspect.getfile(type(instance))).resolve())
        found.append(dict(layer=layer_index(prefix), prefix=prefix,
                          instance_class=type(instance).__module__ + "." + type(instance).__qualname__,
                          class_path=class_path, class_sha256=file_digest(class_path),
                          core_owner=function_identity(instance._forward_core),
                          original_core_owner=function_identity(instance._damp_original_core),
                          outer_forward_owner=function_identity(instance.forward)))
    require(len(found) == len(LAYERS) and {r["layer"] for r in found} == set(LAYERS),
            "actual dispatcher does not contain exactly all 48 verified GDN instances")
    return sorted(found, key=lambda r: r["layer"])
