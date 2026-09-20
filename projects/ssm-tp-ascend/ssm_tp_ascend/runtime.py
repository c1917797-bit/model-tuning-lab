"""Read-only production-path probe for Qwen GDN tensor parallelism.

The probe is intentionally not an optimization.  It records which existing
vLLM-Ascend row-parallel implementation is selected and the tensors that cross
the GDN output-projection boundary.  The evidence decides whether the paper
leaves a real implementation opportunity before any candidate is authored.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

_INSTALLED = False
_CALL_COUNTS: dict[tuple[int, str], int] = {}


def _enabled() -> bool:
    return os.environ.get("VLLM_ASCEND_SSM_TP_PROBE_ENABLE", "0") == "1"


def _evidence_path() -> str:
    return os.environ.get("VLLM_ASCEND_SSM_TP_EVIDENCE_FILE", "")


def _sha256(path: str | None) -> str | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.is_file():
        return None
    digest = hashlib.sha256()
    with candidate.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _emit(event: str, **fields: Any) -> None:
    path = _evidence_path()
    if not path:
        raise RuntimeError(
            "VLLM_ASCEND_SSM_TP_EVIDENCE_FILE is required when the probe is enabled"
        )
    payload = {
        "schema": 1,
        "event": event,
        "component": "ssm_tp_ascend",
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "time_ns": time.time_ns(),
        **fields,
    }
    encoded = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, encoded)
    finally:
        os.close(descriptor)


def _is_gdn_out_proj(prefix: str) -> bool:
    return ".linear_attn.out_proj" in prefix


def _sample_call(count: int) -> bool:
    # Capture prefill/decode shape transitions without logging every layer call.
    return count <= 4 or count & (count - 1) == 0


def _tensor_fields(tensor: Any, label: str) -> dict[str, Any]:
    if tensor is None:
        return {
            f"{label}_dtype": None,
            f"{label}_shape": None,
            f"{label}_device": None,
        }
    return {
        f"{label}_dtype": str(getattr(tensor, "dtype", None)),
        f"{label}_shape": list(getattr(tensor, "shape", ())),
        f"{label}_device": str(getattr(tensor, "device", None)),
    }


def _patch_selection(linear_op: Any, linear_module: Any) -> None:
    original = linear_op.get_parallel_op
    if getattr(original, "_ssm_tp_probe_wrapped", False):
        return

    def get_parallel_op(disable_tp, prefix, layer, direct):
        result = original(disable_tp, prefix, layer, direct)
        if direct == "row" and _is_gdn_out_proj(prefix):
            custom_op, tp_rank, tp_size = result
            _emit(
                "gdn_row_parallel_selected",
                prefix=prefix,
                disable_tp=bool(disable_tp),
                custom_op=type(custom_op).__name__ if custom_op is not None else None,
                tp_rank=int(tp_rank),
                tp_size=int(tp_size),
                enable_matmul_allreduce=os.environ.get(
                    "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE"
                ),
            )
        return result

    get_parallel_op._ssm_tp_probe_wrapped = True
    get_parallel_op._ssm_tp_probe_original = original
    linear_op.get_parallel_op = get_parallel_op
    # vllm_ascend.ops.linear imports the function by name, so patch that bound
    # reference as well.  Missing this would produce a false "plugin loaded"
    # event without observing model construction.
    linear_module.get_parallel_op = get_parallel_op


def _patch_runtime(linear_op: Any) -> None:
    original = linear_op.CustomRowParallelOp.apply
    if getattr(original, "_ssm_tp_probe_wrapped", False):
        return

    def apply(self, input_):
        result = original(self, input_)
        prefix = str(getattr(self, "prefix", ""))
        if not _is_gdn_out_proj(prefix):
            return result

        key = (os.getpid(), type(self).__name__)
        count = _CALL_COUNTS.get(key, 0) + 1
        _CALL_COUNTS[key] = count
        if _sample_call(count):
            output = result[0] if isinstance(result, tuple) else result
            layer = getattr(self, "layer", None)
            weight = getattr(layer, "weight", None)
            fields = {}
            fields.update(_tensor_fields(input_, "input"))
            fields.update(_tensor_fields(output, "output"))
            fields.update(_tensor_fields(weight, "weight"))
            _emit(
                "gdn_row_parallel_runtime",
                prefix=prefix,
                custom_op=type(self).__name__,
                call_count=count,
                tp_rank=int(getattr(self, "tp_rank", -1)),
                tp_size=int(getattr(self, "tp_size", -1)),
                reduce_results=bool(getattr(self, "reduce_results", False)),
                input_is_parallel=bool(getattr(self, "input_is_parallel", False)),
                **fields,
            )
        return result

    apply._ssm_tp_probe_wrapped = True
    apply._ssm_tp_probe_original = original
    linear_op.CustomRowParallelOp.apply = apply


def register() -> None:
    global _INSTALLED
    if not _enabled() or _INSTALLED:
        return
    if not _evidence_path():
        raise RuntimeError(
            "VLLM_ASCEND_SSM_TP_EVIDENCE_FILE is required when the probe is enabled"
        )

    from vllm_ascend.ops import linear as linear_module
    from vllm_ascend.ops import linear_op

    _patch_selection(linear_op, linear_module)
    _patch_runtime(linear_op)
    _emit(
        "ssm_tp_probe_installed",
        linear_module_file=str(getattr(linear_module, "__file__", "")),
        linear_module_sha256=_sha256(getattr(linear_module, "__file__", None)),
        linear_op_file=str(getattr(linear_op, "__file__", "")),
        linear_op_sha256=_sha256(getattr(linear_op, "__file__", None)),
        plugin_file=__file__,
        plugin_sha256=_sha256(__file__),
    )
    _INSTALLED = True
