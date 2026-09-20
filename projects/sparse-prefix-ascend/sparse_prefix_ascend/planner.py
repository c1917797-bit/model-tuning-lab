"""Independent implementation of the checkpoint-placement DP in arXiv:2605.05219."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class PlacementPlan:
    positions: tuple[int, ...]
    checkpoint_budget: int
    block_size: int
    max_length: int

    def validate(self) -> None:
        if self.checkpoint_budget < 0:
            raise ValueError("checkpoint_budget must be non-negative")
        if self.block_size <= 0:
            raise ValueError("block_size must be positive")
        if self.max_length <= 0:
            raise ValueError("max_length must be positive")
        if len(self.positions) > self.checkpoint_budget:
            raise ValueError("positions exceed checkpoint budget")
        if tuple(sorted(set(self.positions))) != self.positions:
            raise ValueError("positions must be unique and strictly increasing")
        for position in self.positions:
            if position <= 0 or position > self.max_length:
                raise ValueError("checkpoint position is out of range")
            if position % self.block_size:
                raise ValueError("checkpoint position is not block aligned")


def overlap_histogram(
    overlap_depths: Iterable[int],
    *,
    max_length: int,
    block_size: int,
    decay: float = 1.0,
) -> tuple[float, ...]:
    """Build a block-binned histogram, optionally with exponential recency decay."""

    if max_length <= 0 or block_size <= 0:
        raise ValueError("max_length and block_size must be positive")
    if not isfinite(decay) or not 0.0 < decay <= 1.0:
        raise ValueError("decay must be in (0, 1]")
    values = tuple(int(value) for value in overlap_depths)
    bins = max_length // block_size
    weights = [0.0] * (bins + 1)
    scale = 1.0
    for value in reversed(values):
        clipped = min(max(value, 0), max_length)
        weights[clipped // block_size] += scale
        scale *= decay
    return tuple(weights)


def solve_distribution_aware(
    histogram: Iterable[float],
    *,
    checkpoint_budget: int,
    block_size: int,
) -> PlacementPlan:
    """Solve the paper's O(NM) checkpoint-placement recurrence on binned input."""

    weights = tuple(float(value) for value in histogram)
    if not weights:
        raise ValueError("histogram must contain bin zero")
    if any(not isfinite(value) or value < 0.0 for value in weights):
        raise ValueError("histogram weights must be finite and non-negative")
    if checkpoint_budget < 0 or block_size <= 0:
        raise ValueError("invalid budget or block size")

    n = len(weights) - 1
    budget = min(checkpoint_budget, n)
    max_length = max(1, n * block_size)
    total = sum(weights)
    if n == 0 or budget == 0 or total <= 0.0:
        plan = PlacementPlan((), checkpoint_budget, block_size, max_length)
        plan.validate()
        return plan

    probabilities = [value / total for value in weights]
    cumulative_p = [0.0] * (n + 2)
    cumulative_pt = [0.0] * (n + 2)
    for index, probability in enumerate(probabilities):
        cumulative_p[index + 1] = cumulative_p[index] + probability
        cumulative_pt[index + 1] = (
            cumulative_pt[index] + probability * index
        )

    dp_previous = [cumulative_pt[j + 1] for j in range(n + 1)]
    back_tables: list[list[int] | None] = [None]
    for _count in range(1, budget + 1):
        dp_current = [float("inf")] * (n + 1)
        back = [0] * (n + 1)
        dp_current[0] = 0.0
        for end in range(1, n + 1):
            best_cost = float("inf")
            best_start = 1
            for start in range(1, end + 1):
                cost = (
                    dp_previous[start - 1]
                    + cumulative_pt[end + 1]
                    - cumulative_pt[start]
                    - start
                    * (cumulative_p[end + 1] - cumulative_p[start])
                )
                if cost < best_cost:
                    best_cost = cost
                    best_start = start
            dp_current[end] = best_cost
            back[end] = best_start
        dp_previous = dp_current
        back_tables.append(back)

    positions: list[int] = []
    end = n
    for count in range(budget, 0, -1):
        if end <= 0:
            break
        table = back_tables[count]
        assert table is not None
        start = int(table[end])
        positions.append(start * block_size)
        end = start - 1
    plan = PlacementPlan(
        tuple(sorted(set(positions))),
        checkpoint_budget,
        block_size,
        n * block_size,
    )
    plan.validate()
    return plan


def balanced_plan(
    *,
    max_length: int,
    checkpoint_budget: int,
    block_size: int,
) -> PlacementPlan:
    """Strong fixed-count control with the same checkpoint byte budget."""

    if max_length <= 0 or checkpoint_budget < 0 or block_size <= 0:
        raise ValueError("invalid balanced-plan parameters")
    max_bin = max_length // block_size
    count = min(checkpoint_budget, max_bin)
    if count == 0:
        positions: tuple[int, ...] = ()
    else:
        bins = {
            max(1, min(max_bin, (index * max_bin) // (count + 1)))
            for index in range(1, count + 1)
        }
        positions = tuple(value * block_size for value in sorted(bins))
    plan = PlacementPlan(
        positions,
        checkpoint_budget,
        block_size,
        max_length,
    )
    plan.validate()
    return plan
