"""Reference semantics for Dynamic MoE routing.

The functions here intentionally avoid framework-specific dispatch code. They encode the
paper's portable semantic contract: sort routing probabilities and retain the minimal prefix
whose cumulative mass reaches a threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ExpertSelection:
    expert_ids: tuple[int, ...]
    weights: tuple[float, ...]

    @property
    def count(self) -> int:
        return len(self.expert_ids)


def _validate_probabilities(probabilities: Sequence[float]) -> None:
    if not probabilities:
        raise ValueError("at least one expert probability is required")
    if any(value < 0.0 for value in probabilities):
        raise ValueError("expert probabilities must be non-negative")
    if sum(probabilities) <= 0.0:
        raise ValueError("expert probability mass must be positive")


def dynamic_top_p_select(
    probabilities: Sequence[float], threshold: float = 0.4
) -> ExpertSelection:
    """Select the minimal descending-probability prefix reaching ``threshold``.

    ``probabilities`` are expected to be router probabilities (normally softmax output).
    The selected weights are not renormalized, matching the upstream Dynamic_MoE inference
    code's weighted aggregation behavior.
    """

    _validate_probabilities(probabilities)
    if threshold <= 0.0:
        raise ValueError("threshold must be > 0")

    ranked = sorted(enumerate(probabilities), key=lambda item: item[1], reverse=True)
    selected: list[tuple[int, float]] = []
    cumulative = 0.0
    for expert_id, weight in ranked:
        selected.append((expert_id, float(weight)))
        cumulative += float(weight)
        if cumulative >= threshold:
            break

    return ExpertSelection(
        expert_ids=tuple(expert_id for expert_id, _ in selected),
        weights=tuple(weight for _, weight in selected),
    )


def fixed_top_k_select(probabilities: Sequence[float], k: int = 2) -> ExpertSelection:
    """Fixed Top-K baseline with the same non-renormalized router weights."""

    _validate_probabilities(probabilities)
    if k <= 0:
        raise ValueError("k must be > 0")
    if k > len(probabilities):
        raise ValueError("k cannot exceed the number of experts")

    ranked = sorted(enumerate(probabilities), key=lambda item: item[1], reverse=True)[:k]
    return ExpertSelection(
        expert_ids=tuple(expert_id for expert_id, _ in ranked),
        weights=tuple(float(weight) for _, weight in ranked),
    )


def mean_activated_experts(rows: Iterable[Sequence[float]], threshold: float = 0.4) -> float:
    counts = [dynamic_top_p_select(row, threshold).count for row in rows]
    if not counts:
        raise ValueError("at least one routing row is required")
    return sum(counts) / len(counts)
