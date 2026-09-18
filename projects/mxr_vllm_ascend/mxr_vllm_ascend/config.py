"""Fail-closed environment contract for the MXR plugin."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean flag, got {raw!r}")


@dataclass(frozen=True)
class MxrConfig:
    enabled: bool
    backend_module: str | None = None
    evidence_path: Path | None = None
    expected_gdn_sha256: str | None = None
    allow_v027_override: bool = False

    @classmethod
    def from_env(cls) -> "MxrConfig":
        enabled = _flag("MST_MXR_ENABLE")
        if not enabled:
            return cls(enabled=False)

        backend = os.environ.get("MST_MXR_BACKEND_MODULE", "").strip()
        if not backend:
            raise RuntimeError("MST_MXR_BACKEND_MODULE is required when MXR is enabled")

        evidence_raw = os.environ.get("MST_MXR_EVIDENCE_PATH", "").strip()
        evidence = Path(evidence_raw)
        if not evidence_raw or not evidence.is_absolute():
            raise RuntimeError("MST_MXR_EVIDENCE_PATH must be an absolute path")

        expected = os.environ.get("MST_MXR_EXPECTED_GDN_SHA256", "").strip().lower()
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise RuntimeError("MST_MXR_EXPECTED_GDN_SHA256 must be one lowercase SHA256")

        return cls(
            enabled=True,
            backend_module=backend,
            evidence_path=evidence,
            expected_gdn_sha256=expected,
            allow_v027_override=_flag("MST_MXR_ALLOW_V027_OVERRIDE"),
        )
