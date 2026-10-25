"""Exact source proof for a proposed selective graph entry.

Capture before our producer/model/layer hooks. Unknown wrappers are rejected.
This does not activate the candidate or prove real graph capture/replay.
"""
from dataclasses import dataclass
import hashlib
import inspect
from pathlib import Path
import sys
import types

PINS = {
    "vllm.compilation.decorators": ("decorators.py", "dd7167637a478aeaea3f2410a727ddefc702bda1d9bf632831c2a8b4811ebb1e"),
    "vllm.config.compilation": ("compilation.py", "301f785491044b4428aec617b8a98161ab7ffc424fc2bfb0f2ab26bed6ee6913"),
    "vllm.forward_context": ("forward_context.py", "1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5"),
    "vllm.v1.cudagraph_dispatcher": ("cudagraph_dispatcher.py", "2ac6454dd72c9f54d159b5a2da0fdd60a4f841970eb32dbf54129e3c6a8d0bfd"),
    "vllm_ascend.worker.model_runner_v1": ("model_runner_v1.py", "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"),
    "vllm_ascend.compilation.acl_graph": ("acl_graph.py", "27f3b838f223dec86113649625f65b158969a30ce0265271d6a3ce1403db2491"),
    "vllm_ascend.ops.gdn": ("gdn.py", "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"),
    "vllm_ascend.attention.attention_v1": ("attention_v1.py", "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"),
}


def _codes(code):
    yield code
    for child in code.co_consts:
        if isinstance(child, types.CodeType):
            yield from _codes(child)


def source_module(name):
    module = sys.modules.get(name)
    if type(module) is not types.ModuleType or module.__name__ != name:
        raise ValueError("pinned imported module identity missing: " + name)
    basename, digest = PINS[name]
    path = Path(module.__file__).resolve()
    if path.name != basename or not path.is_file():
        raise ValueError("pinned native module source path drift")
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != digest:
        raise ValueError("pinned native module source bytes drift")
    return module, source


def verify_official_tree():
    """Read pinned files without importing runner/ACL modules during startup."""
    sources = {}
    for name, (basename, digest) in PINS.items():
        package_name, relative = name.split(".", 1)
        package = sys.modules.get(package_name)
        if type(package) is not types.ModuleType or not getattr(package, "__file__", None):
            raise ValueError("official package origin missing")
        path = Path(package.__file__).resolve().parent.joinpath(
            *relative.split(".")).with_suffix(".py")
        if path.name != basename or not path.is_file():
            raise ValueError("official tree source path drift")
        imported = sys.modules.get(name)
        if imported is not None and (type(imported) is not types.ModuleType
                or Path(imported.__file__).resolve() != path.resolve()):
            raise ValueError("official imported source origin drift")
        source = path.read_bytes()
        if hashlib.sha256(source).hexdigest() != digest:
            raise ValueError("official tree source bytes drift")
        sources[name] = source
    return sources


def verify_raw_function(module, source, function, *, name, first_line=None, qualname=None):
    if (type(function) is not types.FunctionType
            or function.__globals__ is not vars(module)
            or function.__module__ != module.__name__
            or hasattr(function, "__wrapped__")):
        raise ValueError("raw source-owned native function required")
    path = Path(module.__file__).resolve()
    if Path(function.__code__.co_filename).resolve() != path:
        raise ValueError("native code source origin drift")
    compiled = compile(source, function.__code__.co_filename, "exec",
                       dont_inherit=True, optimize=sys.flags.optimize)
    candidates = [c for c in _codes(compiled)
                  if c.co_name == name and (first_line is None or c.co_firstlineno == first_line)
                  and (qualname is None or c.co_qualname == qualname)]
    if len(candidates) != 1 or function.__code__ != candidates[0]:
        raise ValueError("native source-owned code drift or ambiguous owner")
    return function


@dataclass(frozen=True)
class NativeBundle:
    model_class: type
    model_receipt: object
    call_owner: type
    call: types.FunctionType
    dynamic: types.FunctionType
    chunk: object
    gdn_class: type
    gdn: types.FunctionType
    c2_class: type
    c2: types.FunctionType
    modules: tuple
    defaults: tuple

    def assert_saved_native(self):
        for name, module in self.modules:
            if sys.modules.get(name) is not module:
                raise ValueError("native imported module replaced")
        if (self.call.__closure__ is None
                or self.call.__closure__[0].cell_contents is not self.dynamic):
            raise ValueError("native compiler helper closure changed")
        functions = (self.call, self.dynamic, self.gdn, self.c2, self.model_receipt.forward)
        for function, (code, globals_dict, defaults, kwdefaults) in zip(functions, self.defaults):
            if (function.__code__ is not code or function.__globals__ is not globals_dict
                    or function.__defaults__ is not defaults
                    or function.__kwdefaults__ is not kwdefaults
                    or hasattr(function, "__wrapped__")):
                raise ValueError("saved native callable changed")


def capture_native_bundle():
    """Enabled-only runtime entry; imports pinned official sources, never unwraps.

    No old HYPIC code is imported. This must run before independent activation.
    """
    import importlib
    required = ("vllm.compilation.decorators", "vllm.config.compilation",
                "vllm.forward_context", "vllm_ascend.ops.gdn",
                "vllm_ascend.attention.attention_v1")
    for name in required:
        importlib.import_module(name)
    from independent_c2_native_forward import verify_c2_native_forward
    model_module = importlib.import_module("vllm.model_executor.models.qwen3_5")
    model_class = model_module.Qwen3_5Model
    model_receipt = verify_c2_native_forward(model_class, model_class.forward)
    sources = verify_official_tree()
    modules = {name: (sys.modules[name], sources[name]) for name in PINS
               if name in sys.modules}
    call_owner = next(c for c in model_class.__mro__ if "__call__" in vars(c))
    if call_owner not in (model_class, model_receipt.owner_class):
        raise ValueError("native compiler decorator call owner drift")
    call = vars(call_owner)["__call__"]
    module, source = modules["vllm.compilation.decorators"]
    verify_raw_function(module, source, call, name="__call__", first_line=502)
    if call.__code__.co_freevars != ("_mark_dynamic_inputs",) or call.__closure__ is None:
        raise ValueError("native compiler decorator closure drift")
    dynamic = call.__closure__[0].cell_contents
    verify_raw_function(module, source, dynamic, name="_mark_dynamic_inputs")
    target_module = importlib.import_module("vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn")
    gdn_class = target_module.QwenGatedDeltaNetAttention
    gdn_module, source = modules["vllm_ascend.ops.gdn"]
    gdn = gdn_class._forward_core
    if gdn is not gdn_module.AscendGatedDeltaNetAttention._forward_core:
        raise ValueError("actual registered Ascend GDN target drift")
    verify_raw_function(gdn_module, source, gdn, name="_forward_core", first_line=147,
                        qualname="AscendGatedDeltaNetAttention._forward_core")
    c2_module, source = modules["vllm_ascend.attention.attention_v1"]
    c2_class = c2_module.AscendAttentionBackendImpl
    c2 = vars(c2_class)["forward"]
    verify_raw_function(c2_module, source, c2, name="forward",
                        qualname="AscendAttentionBackendImpl.forward")
    functions = (call, dynamic, gdn, c2, model_receipt.forward)
    return NativeBundle(model_class, model_receipt, call_owner, call, dynamic,
                        gdn_module.chunk_gated_delta_rule, gdn_class, gdn,
                        c2_class, c2, tuple((name, pair[0]) for name, pair in modules.items()),
                        tuple((f.__code__, f.__globals__, f.__defaults__, f.__kwdefaults__)
                              for f in functions))
