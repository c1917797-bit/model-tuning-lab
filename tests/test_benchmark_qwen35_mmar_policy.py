import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_qwen35_mmar_policy.py"
)
SPEC = importlib.util.spec_from_file_location("benchmark_qwen35_mmar_policy", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _cell(m: int, k: int, speedup: float, correct: bool = True) -> dict:
    return {
        "m": m,
        "k": k,
        "separate_speedup_vs_fused": speedup,
        "correctness": {"allclose": correct},
    }


def test_recommend_bypass_max_m_requires_contiguous_cross_shape_wins():
    cells = [
        _cell(1, 1536, 1.10),
        _cell(1, 4352, 1.08),
        _cell(2, 1536, 1.05),
        _cell(2, 4352, 1.03),
        _cell(4, 1536, 1.01),
        _cell(4, 4352, 1.06),
    ]
    assert MODULE.recommend_bypass_max_m(cells) == 2


def test_recommend_bypass_max_m_rejects_incorrect_first_cell():
    cells = [_cell(1, 1536, 1.10, correct=False), _cell(1, 4352, 1.10)]
    assert MODULE.recommend_bypass_max_m(cells) is None
