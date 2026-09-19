"""Runtime fingerprinting and thin adapter installation."""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import inspect
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType

from .config import MxrConfig


@dataclass(frozen=True)
class RuntimeFingerprint:
    version: str
    adapter: str
    gdn_path: str
    gdn_sha256: str
    native_fused_symbol: bool


def adapter_for_version(version: str) -> str:
    match = re.search(r"(?:^|[^0-9])0\.(\d+)(?:\.|$)", version)
    if match is None:
        raise RuntimeError(f"unsupported vLLM-Ascend version format: {version!r}")
    minor = int(match.group(1))
    if minor == 23:
        return "v023"
    if minor == 27:
        return "v027"
    raise RuntimeError(f"unsupported vLLM-Ascend version: {version!r}")


def _version() -> str:
    for distribution in ("vllm-ascend", "vllm_ascend"):
        try:
            return importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            continue
    module = importlib.import_module("vllm_ascend")
    value = getattr(module, "__version__", None)
    if not isinstance(value, str):
        raise RuntimeError("cannot determine vLLM-Ascend version")
    return value


def fingerprint() -> tuple[RuntimeFingerprint, ModuleType]:
    version = _version()
    adapter = adapter_for_version(version)
    gdn = importlib.import_module("vllm_ascend.ops.gdn")
    source_path = inspect.getsourcefile(gdn)
    if source_path is None:
        raise RuntimeError("cannot resolve vllm_ascend.ops.gdn source path")
    path = Path(source_path).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    source = path.read_text("utf-8")
    native_fused = "npu_chunk_gated_delta_rule" in source
    return (
        RuntimeFingerprint(
            version=version,
            adapter=adapter,
            gdn_path=str(path),
            gdn_sha256=digest,
            native_fused_symbol=native_fused,
        ),
        gdn,
    )


def _candidate(module_name: str):
    module = importlib.import_module(module_name)
    candidate = getattr(module, "chunk_gated_delta_rule", None)
    if not callable(candidate):
        raise RuntimeError(f"{module_name} has no callable chunk_gated_delta_rule")
    return candidate


def install(config: MxrConfig) -> RuntimeFingerprint:
    if not config.enabled:
        raise RuntimeError("install called while MXR is disabled")
    if config.evidence_path is None or config.backend_module is None:
        raise RuntimeError("enabled MXR configuration is incomplete")

    runtime, gdn = fingerprint()
    if runtime.gdn_sha256 != config.expected_gdn_sha256:
        raise RuntimeError(
            "vllm_ascend.ops.gdn source identity mismatch: "
            f"expected {config.expected_gdn_sha256}, got {runtime.gdn_sha256}"
        )

    action: str
    if runtime.adapter == "v027" and runtime.native_fused_symbol and not config.allow_v027_override:
        action = "delegate_native_fused"
    else:
        candidate = _candidate(config.backend_module)
        if not hasattr(gdn, "chunk_gated_delta_rule"):
            raise RuntimeError("vllm_ascend.ops.gdn has no chunk_gated_delta_rule binding")
        gdn.chunk_gated_delta_rule = candidate
        if runtime.adapter == "v027" and runtime.native_fused_symbol:
            attention = getattr(gdn, "AscendGatedDeltaNetAttention", None)
            if attention is None or not hasattr(attention, "_fused_chunk_available"):
                raise RuntimeError("v0.27 native fused probe contract changed")
            attention._fused_chunk_available = False
        action = "candidate_installed"

    config.evidence_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": "mst.mxr.runtime/v1", **asdict(runtime), "action": action}
    config.evidence_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return runtime
