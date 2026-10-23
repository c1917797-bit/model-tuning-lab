"""Narrow source-bound native model-forward receipt for opt-in C2 snapshots.

The pinned image must be fresh, read-only and contain only the frozen owned
hooks. This verifies one inherited Python entry, not arbitrary plugin safety.
"""
import ast
from dataclasses import dataclass
import hashlib
import inspect
from pathlib import Path
import sys
import types

_MODEL_MODULE = "vllm.model_executor.models.qwen3_5"
_OWNER_MODULE = "vllm.model_executor.models.qwen3_next"
_MODEL_SOURCE_SHA256 = "04f3de5372973770d71c5c05f2e8a5e221ec52b62cca7a1e302d9201b61b8adc"
_OWNER_SOURCE_SHA256 = "8d614ce262ab9340585f9a2ad4ab117228f076e3672fcb5f04930ff0a38223ae"


@dataclass(frozen=True)
class NativeForwardReceipt:
    model_class: type
    owner_class: type
    model_module: types.ModuleType
    owner_module: types.ModuleType
    forward: types.FunctionType
    code: types.CodeType
    globals_dict: dict
    defaults: object
    kwdefaults: object


def _module(name):
    module = sys.modules.get(name)
    if type(module) is not types.ModuleType or module.__name__ != name:
        raise ValueError("C2 native forward module identity missing")
    return module


def _source(module, basename, digest):
    origin = getattr(module, "__file__", None)
    if not origin:
        raise ValueError("C2 native forward source origin missing")
    path = Path(origin).resolve()
    if path.name != basename or not path.is_file():
        raise ValueError("C2 native forward source path drift")
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != digest:
        raise ValueError("C2 native forward source hash drift")
    return path, source


def _forward_code(source, filename):
    tree = ast.parse(source, filename=filename)
    owners = [n for n in tree.body
              if isinstance(n, ast.ClassDef) and n.name == "Qwen3NextModel"]
    if len(owners) != 1:
        raise ValueError("C2 native forward source owner ambiguous")
    methods = [n for n in owners[0].body
               if isinstance(n, ast.FunctionDef) and n.name == "forward"]
    if len(methods) != 1 or methods[0].decorator_list:
        raise ValueError("C2 native forward source method drift")
    compiled = compile(source, filename, "exec", dont_inherit=True,
                       optimize=sys.flags.optimize)
    classes = [c for c in compiled.co_consts
               if isinstance(c, types.CodeType) and c.co_name == owners[0].name]
    if len(classes) != 1:
        raise ValueError("C2 native forward compiled owner ambiguous")
    codes = [c for c in classes[0].co_consts
             if isinstance(c, types.CodeType) and c.co_name == methods[0].name]
    if len(codes) != 1 or codes[0].co_firstlineno != methods[0].lineno:
        raise ValueError("C2 native forward compiled method drift")
    return codes[0]


def verify_c2_native_forward(model_class, actual_forward):
    """Verify the actual inherited entry without unwrapping or executing source."""
    model_module, owner_module = _module(_MODEL_MODULE), _module(_OWNER_MODULE)
    owner = getattr(owner_module, "Qwen3NextModel", None)
    if (model_class is not getattr(model_module, "Qwen3_5Model", None)
            or not isinstance(model_class, type) or not isinstance(owner, type)
            or "forward" in vars(model_class)
            or owner not in model_class.__mro__):
        raise ValueError("C2 native inherited model class identity drift")
    resolved_owner = next((c for c in model_class.__mro__ if "forward" in vars(c)), None)
    if (resolved_owner is not owner or type(actual_forward) is not types.FunctionType
            or inspect.getattr_static(model_class, "forward") is not actual_forward
            or vars(owner).get("forward") is not actual_forward
            or hasattr(actual_forward, "__wrapped__")
            or actual_forward.__globals__ is not vars(owner_module)
            or actual_forward.__module__ != _OWNER_MODULE):
        raise ValueError("C2 native forward callable identity drift")
    _source(model_module, "qwen3_5.py", _MODEL_SOURCE_SHA256)
    path, source = _source(owner_module, "qwen3_next.py", _OWNER_SOURCE_SHA256)
    filename = actual_forward.__code__.co_filename
    if (Path(filename).resolve() != path
            or actual_forward.__code__ != _forward_code(source, filename)
            or actual_forward.__defaults__ != (None, None)
            or actual_forward.__kwdefaults__ is not None):
        raise ValueError("C2 native forward code/defaults drift")
    return NativeForwardReceipt(
        model_class, owner, model_module, owner_module, actual_forward,
        actual_forward.__code__, actual_forward.__globals__,
        actual_forward.__defaults__, actual_forward.__kwdefaults__)


def assert_c2_owned_forward(self, model_class, wrapper, native):
    """Check only the saved owned entry and its actual fully-eager model instance."""
    if type(native) is not NativeForwardReceipt:
        raise ValueError("C2 native forward receipt required")
    if (model_class is not native.model_class or type(self) is not model_class
            or sys.modules.get(_MODEL_MODULE) is not native.model_module
            or sys.modules.get(_OWNER_MODULE) is not native.owner_module
            or vars(native.model_module).get("Qwen3_5Model") is not model_class
            or vars(native.owner_module).get("Qwen3NextModel") is not native.owner_class
            or vars(native.owner_class).get("forward") is not native.forward
            or type(wrapper) is not types.FunctionType
            or inspect.getattr_static(model_class, "forward") is not wrapper
            or "forward" in vars(self)
            or getattr(wrapper, "_independent_compact_model_owned", False) is not True
            or getattr(wrapper, "__wrapped__", None) is not native.forward):
        raise ValueError("C2 owned forward chain changed")
    forward = native.forward
    if (forward.__code__ is not native.code
            or forward.__globals__ is not native.globals_dict
            or forward.__defaults__ is not native.defaults
            or forward.__kwdefaults__ is not native.kwdefaults
            or hasattr(forward, "__wrapped__")):
        raise ValueError("C2 saved native forward changed")
    config = getattr(self, "compilation_config", None)
    model_config = getattr(self, "vllm_config", None)
    compilation = sys.modules.get("vllm.config.compilation")
    mode_class = getattr(compilation, "CompilationMode", None)
    if (getattr(self, "do_not_compile", None) is not True
            or config is None or getattr(model_config, "compilation_config", None) is not config
            or not isinstance(mode_class, type)
            or type(getattr(config, "mode", None)) is not mode_class
            or config.mode is not getattr(mode_class, "NONE", None)):
        raise ValueError("C2 snapshot requires actual fully eager model")
