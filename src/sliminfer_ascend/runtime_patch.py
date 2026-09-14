"""Identity-preserving runtime patch for the first real-service canary."""

from __future__ import annotations

from functools import wraps
from hashlib import sha256
import inspect
from pathlib import Path
import sys
import threading
from types import ModuleType
from typing import Any

from .config import SlimInferConfig
from .diagnostics import emit_event
from .import_hook import PostImportFinder


_TARGET_MODULE = "vllm.model_executor.models.qwen3_5"
_TARGET_CLASS = "Qwen3_5Model"


def _source_identity(obj: Any) -> tuple[str | None, str | None]:
    path = inspect.getsourcefile(obj)
    if path is None:
        return None, None
    try:
        digest = sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        digest = None
    return path, digest


def _shape(value: Any) -> list[int] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    return [int(dim) for dim in shape]


def _distributed_rank() -> int | None:
    try:
        import torch.distributed as dist

        if dist.is_available() and dist.is_initialized():
            return int(dist.get_rank())
    except Exception:
        return None
    return None


def _patch_model_class(cls: type, config: SlimInferConfig) -> bool:
    if cls.__dict__.get("_mst_sliminfer_identity_patch_installed", False):
        return False
    original_forward = cls.forward
    source_path, source_digest = _source_identity(original_forward)
    first_call_lock = threading.Lock()
    first_call_emitted = False

    @wraps(original_forward)
    def forward_with_identity_canary(self, *args, **kwargs):
        nonlocal first_call_emitted
        if not first_call_emitted:
            with first_call_lock:
                if not first_call_emitted:
                    input_ids = kwargs.get("input_ids")
                    positions = kwargs.get("positions")
                    inputs_embeds = kwargs.get("inputs_embeds")
                    if input_ids is None and args:
                        input_ids = args[0]
                    if positions is None and len(args) > 1:
                        positions = args[1]
                    emit_event(
                        "model_forward_enter",
                        component="model",
                        mode=config.mode,
                        target_module=cls.__module__,
                        target_class=cls.__name__,
                        original_forward_module=original_forward.__module__,
                        original_forward_qualname=original_forward.__qualname__,
                        source_path=source_path,
                        source_sha256=source_digest,
                        distributed_rank=_distributed_rank(),
                        input_ids_shape=_shape(input_ids),
                        positions_shape=_shape(positions),
                        inputs_embeds_shape=_shape(inputs_embeds),
                    )
                    first_call_emitted = True
        return original_forward(self, *args, **kwargs)

    cls.forward = forward_with_identity_canary
    cls._mst_sliminfer_identity_patch_installed = True
    emit_event(
        "model_patch_installed",
        component="model",
        mode=config.mode,
        target_module=cls.__module__,
        target_class=cls.__name__,
        original_forward_module=original_forward.__module__,
        original_forward_qualname=original_forward.__qualname__,
        source_path=source_path,
        source_sha256=source_digest,
    )
    return True


def _apply_model_patch(module: ModuleType, config: SlimInferConfig) -> None:
    cls = getattr(module, _TARGET_CLASS, None)
    if cls is None:
        if config.require_runtime_hooks:
            raise RuntimeError(
                f"SlimInfer canary target {_TARGET_MODULE}.{_TARGET_CLASS} was not found"
            )
        return
    _patch_model_class(cls, config)


def install_model_patch(config: SlimInferConfig) -> None:
    """Patch now or immediately after the pinned Qwen3.5 model module imports."""

    module = sys.modules.get(_TARGET_MODULE)
    if module is not None:
        _apply_model_patch(module, config)
        return

    def callback(imported_module: ModuleType) -> None:
        _apply_model_patch(imported_module, config)

    PostImportFinder(_TARGET_MODULE, callback).install()
    emit_event(
        "model_patch_deferred",
        component="model",
        mode=config.mode,
        target_module=_TARGET_MODULE,
        target_class=_TARGET_CLASS,
    )
