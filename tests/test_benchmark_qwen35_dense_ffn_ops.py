#!/usr/bin/env python3

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/benchmark_qwen35_dense_ffn_ops.py"
SPEC = importlib.util.spec_from_file_location("ffn_bench", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def cells(speedups, *, allclose=True):
    result = []
    for m in (1, 5, 8, 16):
        result.append(
            {
                "m": m,
                "variant": "nd",
                "status": "ok",
                "correctness": {"allclose": True},
                "speedup_vs_nd": 1.0,
            }
        )
        result.append(
            {
                "m": m,
                "variant": "gate_up_nz",
                "status": "ok",
                "correctness": {"allclose": allclose},
                "speedup_vs_nd": speedups[m],
            }
        )
    return result


promote = MODULE.evaluate_decision(
    cells({1: 1.05, 5: 1.06, 8: 1.07, 16: 1.08})
)
assert promote["decision"] == "promote-layout-to-e2e"
assert promote["winner"] == "gate_up_nz"

regression = MODULE.evaluate_decision(
    cells({1: 1.20, 5: 1.20, 8: 1.20, 16: 0.97})
)
assert regression["decision"] == "reject-built-in-layout-lane"

incorrect = MODULE.evaluate_decision(
    cells({1: 1.20, 5: 1.20, 8: 1.20, 16: 1.20}, allclose=False)
)
assert incorrect["decision"] == "reject-built-in-layout-lane"

print("PASS: dense FFN microbenchmark decision")
