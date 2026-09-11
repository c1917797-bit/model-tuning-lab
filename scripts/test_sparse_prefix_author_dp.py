"""CPU-only reproduction of a pinned external author's checkpoint planner.

No model accuracy or accelerator performance claim is made by this test.
Author source remains outside this repository and is never modified.
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path


def cost(hist, positions):
    return sum(w * (t - max([0] + [p for p in positions if p <= t]))
               for t, w in enumerate(hist)) / sum(hist)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.source)
    spec = importlib.util.spec_from_file_location("author_strategies", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for n in range(1, 8):
        histograms = [[0] + [((seed * 13 + t * 7) % 11) + 1
                            for t in range(1, n + 1)] for seed in range(1, 21)]
        histograms += [[0] + [int(t == peak) for t in range(1, n + 1)]
                       for peak in range(1, n + 1)]
        for hidx, hist in enumerate(histograms):
            for budget in range(n + 1):
                solution = module.solve_dp(hist, budget)
                positions = [] if solution is None else module.backtrack(
                    solution[0], solution[2], solution[1])
                actual = cost(hist, positions)
                optimal = min(cost(hist, subset)
                              for size in range(budget + 1)
                              for subset in itertools.combinations(range(1, n + 1), size))
                ok = (len(positions) <= budget and
                      all(1 <= p <= n for p in positions) and
                      abs(actual - optimal) < 1e-12)
                rows.append(dict(n=n, histogram_id=hidx, histogram=hist,
                                 budget=budget, positions=positions,
                                 actual=actual, optimal=optimal, ok=ok))
    edge_checks = {
        "empty_histogram": module.solve_dp([], 2) is None,
        "zero_histogram": module.solve_dp([0, 0, 0], 2) is None,
        "zero_budget": module.solve_dp([0, 1, 1], 0) is None,
    }
    try:
        module.checkpoint_positions(128, tag="log")
    except TypeError:
        legacy_helper_missing_type = True
    else:
        legacy_helper_missing_type = False
    result = {
        "scope": "author CPU planner versus exhaustive small-case oracle only",
        "source_revision": args.revision,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "cases": len(rows), "failed_cases": sum(not r["ok"] for r in rows),
        "edge_checks": edge_checks,
        "legacy_helper_missing_type_reproduced": legacy_helper_missing_type,
        "model_accuracy_tested": False, "npu_performance_tested": False,
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    if result["failed_cases"] or not all(edge_checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
