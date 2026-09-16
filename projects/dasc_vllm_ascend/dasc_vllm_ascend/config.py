"""Fail-closed runtime configuration for the DASC plugin."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
DEFAULT_MAMBA_PATCH_SHA256 = "a8862c3509f698c05cdeba5aa408a28e506349eff97801b28161569b8e3c9778"
DEFAULT_MODEL_RUNNER_SHA256 = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
DEFAULT_VLLM_MAMBA_UTILS_SHA256 = "1d854c36fe1b32cfacd071393c05fc155f37190fe19afc5e6c02d5d0a2d561f3"


class DascConfigurationError(ValueError):
    pass


def _enabled(name: str, default: str = "0") -> bool:
    value = os.getenv(name, default)
    if value not in {"0", "1"}:
        raise DascConfigurationError(f"{name} must be 0 or 1, got {value!r}")
    return value == "1"


@dataclass(frozen=True)
class DascConfig:
    enabled: bool
    mode: str
    w_max: float
    epsilon: float
    representative_a: float
    evidence_path: Path | None
    expected_gdn_sha256: str
    expected_mamba_patch_sha256: str
    expected_model_runner_sha256: str
    expected_vllm_mamba_utils_sha256: str

    @classmethod
    def from_env(cls) -> "DascConfig":
        enabled = _enabled("MST_DASC_ENABLE")
        mode = os.getenv("MST_DASC_MODE", "nr-numerical")
        if mode not in {
            "nr-numerical",
            "physical-cache-eager",
            "physical-cache-native-all-heads",
            "compat-head256",
        }:
            raise DascConfigurationError(
                "MST_DASC_MODE must be nr-numerical, physical-cache-eager, "
                "physical-cache-native-all-heads, or compat-head256"
            )
        try:
            w_max = float(os.getenv("MST_DASC_W_MAX", "64"))
            epsilon = float(os.getenv("MST_DASC_EPSILON", "0.001"))
            representative_a = float(os.getenv("MST_DASC_REPRESENTATIVE_A", "-0.3"))
        except ValueError as error:
            raise DascConfigurationError("DASC numeric values must be numbers") from error
        if not math.isfinite(w_max) or w_max <= 0:
            raise DascConfigurationError("MST_DASC_W_MAX must be finite and positive")
        if not math.isfinite(epsilon) or not 0 < epsilon < 1:
            raise DascConfigurationError("MST_DASC_EPSILON must be finite and in (0, 1)")
        if not math.isfinite(representative_a):
            raise DascConfigurationError("MST_DASC_REPRESENTATIVE_A must be finite")

        raw_evidence = os.getenv("MST_DASC_EVIDENCE_PATH")
        evidence_path = Path(raw_evidence) if raw_evidence else None
        if enabled and (evidence_path is None or not evidence_path.is_absolute()):
            raise DascConfigurationError(
                "Enabled DASC requires an absolute MST_DASC_EVIDENCE_PATH"
            )

        expected_hashes = {
            "gdn": os.getenv("MST_DASC_EXPECTED_GDN_SHA256", DEFAULT_GDN_SHA256),
            "mamba_patch": os.getenv(
                "MST_DASC_EXPECTED_MAMBA_PATCH_SHA256", DEFAULT_MAMBA_PATCH_SHA256
            ),
            "model_runner": os.getenv(
                "MST_DASC_EXPECTED_MODEL_RUNNER_SHA256", DEFAULT_MODEL_RUNNER_SHA256
            ),
            "vllm_mamba_utils": os.getenv(
                "MST_DASC_EXPECTED_VLLM_MAMBA_UTILS_SHA256",
                DEFAULT_VLLM_MAMBA_UTILS_SHA256,
            ),
        }
        expected_hashes = {name: value.lower() for name, value in expected_hashes.items()}
        for name, value in expected_hashes.items():
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise DascConfigurationError(
                    f"MST_DASC expected {name} hash must be a lowercase SHA256"
                )
        return cls(
            enabled=enabled,
            mode=mode,
            w_max=w_max,
            epsilon=epsilon,
            representative_a=representative_a,
            evidence_path=evidence_path,
            expected_gdn_sha256=expected_hashes["gdn"],
            expected_mamba_patch_sha256=expected_hashes["mamba_patch"],
            expected_model_runner_sha256=expected_hashes["model_runner"],
            expected_vllm_mamba_utils_sha256=expected_hashes["vllm_mamba_utils"],
        )
