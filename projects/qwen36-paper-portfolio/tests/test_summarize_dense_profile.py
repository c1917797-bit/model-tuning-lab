import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "summarize_dense_profile.py"
SPEC = importlib.util.spec_from_file_location("summarize_dense_profile", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_union_preserves_overlap():
    assert MODULE.union_ns([(0, 10), (5, 12), (20, 30)]) == 22


def test_small_scope_cannot_reach_ten_percent():
    assert MODULE.required_local_speedup(0.05) is None


def test_measured_sized_scope_has_finite_gate():
    speedup = MODULE.required_local_speedup(0.14)
    assert speedup is not None
    assert 2.8 < speedup < 2.9
