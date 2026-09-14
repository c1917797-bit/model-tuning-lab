"""Environment contract for the opt-in SlimInfer Ascend runtime canary."""

from __future__ import annotations

from dataclasses import dataclass
import os


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}
_SUPPORTED_MODES = {"identity-canary", "metadata-canary", "selection-shadow"}


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ValueError(f"{name} must be a boolean value, got {raw!r}")


@dataclass(frozen=True)
class SlimInferConfig:
    enable: bool
    mode: str
    evidence_file: str | None
    require_runtime_hooks: bool


def get_config() -> SlimInferConfig:
    mode = os.environ.get("MST_SLIMINFER_MODE", "identity-canary").strip()
    if mode not in _SUPPORTED_MODES:
        raise ValueError(
            f"MST_SLIMINFER_MODE must be one of {sorted(_SUPPORTED_MODES)}, got {mode!r}"
        )
    evidence_file = os.environ.get("MST_SLIMINFER_EVIDENCE_FILE")
    return SlimInferConfig(
        enable=_bool_env("MST_SLIMINFER_ENABLE"),
        mode=mode,
        evidence_file=evidence_file or None,
        require_runtime_hooks=_bool_env(
            "MST_SLIMINFER_REQUIRE_RUNTIME_HOOKS", default=True
        ),
    )
