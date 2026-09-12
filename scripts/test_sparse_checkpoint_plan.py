"""Dependency-free exhaustive aligned-planner checks (not model proof)."""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from model_tuning_lab.sparse_checkpoint_plan import (
    plan_checkpoints, restorable_position, split_at_checkpoint, publication_mask)


def cost(histogram, positions):
    return sum(weight * (t - restorable_position(positions, t, t))
               for t, weight in enumerate(histogram))


cases = 0
for block in (1, 2, 3, 1536):
    for n in range(1, 7):
        for seed in range(5):
            hist = [0] * (n * block + 1)
            for t in range(len(hist)):
                hist[t] = (t * 7 + seed * 3) % 5
            for budget in range(n + 1):
                positions = plan_checkpoints(hist, block, budget)
                oracle = min(cost(hist, subset)
                             for size in range(budget + 1)
                             for subset in itertools.combinations(range(block, n * block + 1, block), size))
                assert cost(hist, positions) == oracle, (block, n, seed, budget)
                assert len(positions) <= budget
                assert all(p > 0 and p % block == 0 for p in positions)
                cases += 1
assert plan_checkpoints([], 1536, 2) == []
assert plan_checkpoints([0, 0], 1, 1) == []
assert restorable_position([1536, 3072], 4000, 2048) == 1536
assert restorable_position([1536], 1535, 4000) == 0
for bad in ([float("nan")], [-1], [float("inf")]):
    try:
        plan_checkpoints(bad, 1, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid histogram accepted")
assert split_at_checkpoint([1536, 3072], 0, 4608, 5000) == 1536
assert split_at_checkpoint([1536, 3072], 1536, 3072, 5000) == 1536
assert split_at_checkpoint([1536], 0, 0, 5000) == 0
assert split_at_checkpoint([1536], 5000, 1, 5000) == 1
assert split_at_checkpoint([1536], 0, 512, 5000) == 512
assert publication_mask([1536, 4608], 0, 4, 1536) == [True, False, True, False]
assert publication_mask([1536, 4608], 1, 3, 1536) == [False, True]
print(f"PASS {cases} exhaustive aligned plans and scheduler/publication boundaries; NOT runtime/model/performance proof")
