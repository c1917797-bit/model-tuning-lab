from __future__ import annotations
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name('opportunity_audit.py')
SPEC = importlib.util.spec_from_file_location('kvbuffer_opportunity_audit', MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

def test_amdahl_speedup() -> None:
    assert MODULE.amdahl_speedup(0.1, 1.0) == 1.0 / 0.9
    assert MODULE.amdahl_speedup(0.0, 1.0) == 1.0

def test_required_reduction() -> None:
    required = MODULE.required_reduction(0.1, 1.1)
    assert 0.90 < required < 0.92

def test_operator_matching() -> None:
    op = {'name': 'aclnnRecurrentGatedDeltaRule_RecurrentGatedDeltaRule', 'type': 'RecurrentGatedDeltaRule'}
    assert MODULE.matches(op, ('RecurrentGatedDeltaRule',))
    assert not MODULE.matches(op, ('CausalConv1d',))
