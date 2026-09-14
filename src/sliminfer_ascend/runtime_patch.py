"""Identity-preserving runtime patches for real-service canaries."""

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
_METADATA_CALL_LIMIT = 16
_SEQUENCE_ITEM_LIMIT = 16
_MAPPING_ITEM_LIMIT = 96


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


def _type_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _tensor_summary(value: Any) -> dict[str, Any] | None:
    shape = _shape(value)
    dtype = getattr(value, "dtype", None)
    device = getattr(value, "device", None)
    if shape is None or dtype is None or device is None:
        return None
    summary: dict[str, Any] = {
        "kind": "tensor",
        "type": _type_name(value),
        "shape": shape,
        "dtype": str(dtype),
        "device": str(device),
    }
    contiguous = getattr(value, "is_contiguous", None)
    if callable(contiguous):
        try:
            summary["is_contiguous"] = bool(contiguous())
        except Exception:
            pass
    return summary


def _safe_summary(
    value: Any,
    *,
    depth: int = 0,
    seen: set[int] | None = None,
) -> Any:
    """Describe runtime objects without reading NPU tensor values or synchronizing."""

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if len(value) <= 256 else value[:253] + "..."

    tensor = _tensor_summary(value)
    if tensor is not None:
        return tensor

    if depth >= 3:
        return {"kind": "object", "type": _type_name(value), "truncated": True}

    if seen is None:
        seen = set()
    object_id = id(value)
    if object_id in seen:
        return {"kind": "reference", "type": _type_name(value)}
    seen.add(object_id)

    if isinstance(value, dict):
        items = list(value.items())
        rendered = {
            str(key): _safe_summary(item, depth=depth + 1, seen=seen)
            for key, item in items[:_MAPPING_ITEM_LIMIT]
        }
        return {
            "kind": "mapping",
            "type": _type_name(value),
            "size": len(items),
            "items": rendered,
            "truncated": len(items) > _MAPPING_ITEM_LIMIT,
        }

    if isinstance(value, (list, tuple)):
        return {
            "kind": "sequence",
            "type": _type_name(value),
            "size": len(value),
            "items": [
                _safe_summary(item, depth=depth + 1, seen=seen)
                for item in value[:_SEQUENCE_ITEM_LIMIT]
            ],
            "truncated": len(value) > _SEQUENCE_ITEM_LIMIT,
        }

    attributes = getattr(value, "__dict__", None)
    if isinstance(attributes, dict):
        return {
            "kind": "object",
            "type": _type_name(value),
            "attributes": {
                str(key): _safe_summary(item, depth=depth + 1, seen=seen)
                for key, item in list(attributes.items())[:_MAPPING_ITEM_LIMIT]
            },
            "truncated": len(attributes) > _MAPPING_ITEM_LIMIT,
        }

    return {"kind": "opaque", "type": _type_name(value), "repr": repr(value)[:256]}


def _group_layer_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"kind": "unexpected", "summary": _safe_summary(value)}
    groups: dict[int, dict[str, Any]] = {}
    for layer_name, metadata in value.items():
        key = id(metadata)
        group = groups.setdefault(
            key,
            {
                "type": _type_name(metadata),
                "layer_names": [],
                "metadata": _safe_summary(metadata),
            },
        )
        group["layer_names"].append(str(layer_name))
    return {
        "kind": "layer_mapping",
        "layer_count": len(value),
        "group_count": len(groups),
        "groups": list(groups.values()),
    }


def _capture_forward_context() -> dict[str, Any]:
    try:
        from vllm.forward_context import get_forward_context

        context = get_forward_context()
    except Exception as exc:
        return {
            "available": False,
            "error_type": _type_name(exc),
            "error": str(exc)[:512],
        }

    attributes = getattr(context, "__dict__", {})
    result: dict[str, Any] = {
        "available": True,
        "type": _type_name(context),
        "attribute_names": sorted(str(key) for key in attributes),
    }
    for name, value in attributes.items():
        if name in {"attn_metadata", "slot_mapping"}:
            result[name] = _group_layer_mapping(value)
        else:
            result[name] = _safe_summary(value)
    return result


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
    event_lock = threading.Lock()
    emitted_calls = 0

    @wraps(original_forward)
    def forward_with_identity_canary(self, *args, **kwargs):
        nonlocal emitted_calls
        event_limit = (
            _METADATA_CALL_LIMIT if config.mode == "metadata-canary" else 1
        )
        if emitted_calls < event_limit:
            with event_lock:
                if emitted_calls < event_limit:
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
                        call_index=emitted_calls,
                        input_ids_shape=_shape(input_ids),
                        positions_shape=_shape(positions),
                        inputs_embeds_shape=_shape(inputs_embeds),
                        forward_context=(
                            _capture_forward_context()
                            if config.mode == "metadata-canary"
                            else None
                        ),
                    )
                    emitted_calls += 1
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
