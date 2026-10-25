"""Authorize only source-owned native FULL-decode compilation warmups.

This helper runs at the outer Python entry, never inside a traced model/layer.
Actual PIC/prefill NONE calls retain the official skip_compiled route. Startup
and FULL decode share one native execution branch; no compile mode is rewritten.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
import types

_PINS = {
    "vllm_ascend.worker.model_runner_v1": (
        "model_runner_v1.py",
        "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
        "NPUModelRunner._dummy_run"),
    "vllm.v1.worker.gpu_model_runner": (
        "gpu_model_runner.py",
        "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666",
        "GPUModelRunner._warmup_and_capture"),
}


def _codes(code):
    yield code
    for child in code.co_consts:
        if isinstance(child, types.CodeType):
            yield from _codes(child)


def _source_code(name):
    module = sys.modules.get(name)
    if type(module) is not types.ModuleType or module.__name__ != name:
        raise ValueError("actual imported native warmup module required")
    basename, digest, qualname = _PINS[name]
    path = Path(module.__file__).resolve()
    source = path.read_bytes()
    if path.name != basename or hashlib.sha256(source).hexdigest() != digest:
        raise ValueError("official native warmup source drift")
    root = compile(source, str(path), "exec", dont_inherit=True,
                   optimize=sys.flags.optimize)
    candidates = [code for code in _codes(root) if code.co_qualname == qualname]
    if len(candidates) != 1:
        raise ValueError("exact native warmup code required")
    return module, candidates[0]


@dataclass(frozen=True)
class NativeWarmupProof:
    """Pin actual imported owners; test fixtures are explicitly CPU-only.

    No arbitrary unwrap or replacement of official dummy/warmup methods occurs.
    Serving code must use from_runtime(). The proof is checked before tracing.
    """
    dummy_code: types.CodeType
    dummy_globals: dict
    warmup_code: types.CodeType
    warmup_globals: dict
    runner_class: type
    graph_mode: type
    max_frames: int = 64

    @classmethod
    def from_runtime(cls):
        worker, dummy = _source_code("vllm_ascend.worker.model_runner_v1")
        gpu, warmup = _source_code("vllm.v1.worker.gpu_model_runner")
        runner = getattr(worker, "NPUModelRunner", None)
        if not isinstance(runner, type) or runner.__module__ != worker.__name__:
            raise ValueError("exact native dummy runner owner required")
        compilation = sys.modules.get("vllm.config.compilation")
        mode = getattr(compilation, "CUDAGraphMode", None)
        if not isinstance(mode, type):
            raise ValueError("actual native graph mode required")
        return cls(dummy, vars(worker), warmup, vars(gpu), runner, mode)

    def allows(self, model, context):
        if (context.cudagraph_runtime_mode is not self.graph_mode.NONE
                or context.ubatch_slices is not None
                or context.skip_compiled is not False):
            return False
        frame = sys._getframe(1)
        runner = None
        num_tokens = None
        try:
            for _ in range(self.max_frames):
                if frame is None:
                    return False
                local = frame.f_locals
                if frame.f_code == self.dummy_code and frame.f_globals is self.dummy_globals:
                    candidate = local.get("self")
                    if (runner is not None or type(candidate) is not self.runner_class
                            or getattr(candidate, "compilation_config", None)
                                is not getattr(model, "compilation_config", None)
                            or getattr(model, "compilation_config", None) is None
                            or type(local.get("num_tokens")) is not int
                            or local["num_tokens"] <= 0
                            or local.get("uniform_decode") is not True
                            or local.get("force_attention") is not True
                            or local.get("is_profile") is not False
                            or local.get("is_graph_capturing") is not False
                            or local.get("with_prefill") is not False
                            or local.get("create_mixed_batch") is not False
                            or local.get("allow_microbatching") is not False
                            or local.get("num_active_loras") != 0
                            or local.get("cudagraph_runtime_mode") is not self.graph_mode.NONE):
                        return False
                    descriptor = context.batch_descriptor
                    if (local.get("max_query_len") != 1
                            or type(local.get("num_reqs")) is not int
                            or local["num_reqs"] != local["num_tokens"]
                            or type(local.get("num_tokens_padded")) is not int
                            or local["num_tokens_padded"] < local["num_tokens"]
                            or getattr(descriptor, "num_tokens", None) != local["num_tokens_padded"]
                            or local.get("batch_desc") is not descriptor):
                        return False
                    runner, num_tokens = candidate, local["num_tokens"]
                elif frame.f_code == self.warmup_code and frame.f_globals is self.warmup_globals:
                    desc = local.get("desc")
                    return (
                        runner is not None and local.get("self") is runner
                        and local.get("cudagraph_runtime_mode") is self.graph_mode.FULL
                        and local.get("allow_microbatching") is False
                        and type(local.get("num_warmups")) is int
                        and local["num_warmups"] > 0
                        and getattr(desc, "uniform", None) is True
                        and getattr(desc, "has_lora", None) is False
                        and type(getattr(desc, "num_reqs", None)) is int
                        and desc.num_reqs == num_tokens
                        and type(getattr(desc, "num_tokens", None)) is int
                        and desc.num_tokens == num_tokens
                        and getattr(desc, "num_active_loras", None) == 0)
                frame = frame.f_back
            return False
        finally:
            del frame
