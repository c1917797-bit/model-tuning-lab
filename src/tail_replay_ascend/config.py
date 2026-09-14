"""Fail-closed environment contract for Tail-Replay Ascend canaries."""

from __future__ import annotations

from dataclasses import dataclass
import os


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}
_SUPPORTED_MODES = {"recurrence-oracle", "group-oracle"}


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


def _positive_int_env(name: str, default: int) -> int:
    value = int(os.environ.get(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def _replay_ratios() -> tuple[float, ...]:
    raw = os.environ.get("MST_TAIL_REPLAY_RATIOS", "0.05,0.10")
    ratios = tuple(sorted({float(item.strip()) for item in raw.split(",") if item.strip()}))
    if not ratios or any(ratio <= 0.0 or ratio > 1.0 for ratio in ratios):
        raise ValueError(
            "MST_TAIL_REPLAY_RATIOS must contain one or more values in (0, 1]"
        )
    return ratios


@dataclass(frozen=True)
class TailReplayConfig:
    enable: bool
    mode: str
    replay_ratios: tuple[float, ...]
    evidence_file: str | None
    require_runtime_hooks: bool
    min_prefill_tokens: int
    max_prefill_tokens: int
    exact_split_relative_l2_max: float


def get_config() -> TailReplayConfig:
    mode = os.environ.get("MST_TAIL_REPLAY_MODE", "recurrence-oracle").strip()
    if mode not in _SUPPORTED_MODES:
        raise ValueError(
            f"MST_TAIL_REPLAY_MODE must be one of {sorted(_SUPPORTED_MODES)}, got {mode!r}"
        )
    minimum = _positive_int_env("MST_TAIL_REPLAY_MIN_PREFILL_TOKENS", 128)
    maximum = _positive_int_env("MST_TAIL_REPLAY_MAX_PREFILL_TOKENS", 4096)
    if maximum < minimum:
        raise ValueError("MST_TAIL_REPLAY_MAX_PREFILL_TOKENS must be >= the minimum")
    exact_limit = float(
        os.environ.get("MST_TAIL_REPLAY_EXACT_SPLIT_REL_L2_MAX", "0.01")
    )
    if exact_limit < 0.0:
        raise ValueError("MST_TAIL_REPLAY_EXACT_SPLIT_REL_L2_MAX must be non-negative")
    evidence_file = os.environ.get("MST_TAIL_REPLAY_EVIDENCE_FILE")
    return TailReplayConfig(
        enable=_bool_env("MST_TAIL_REPLAY_ENABLE"),
        mode=mode,
        replay_ratios=_replay_ratios(),
        evidence_file=evidence_file or None,
        require_runtime_hooks=_bool_env(
            "MST_TAIL_REPLAY_REQUIRE_RUNTIME_HOOKS", default=True
        ),
        min_prefill_tokens=minimum,
        max_prefill_tokens=maximum,
        exact_split_relative_l2_max=exact_limit,
    )
