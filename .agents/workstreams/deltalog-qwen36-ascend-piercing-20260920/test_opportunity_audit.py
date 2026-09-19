from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("opportunity_audit.py")
SPEC = importlib.util.spec_from_file_location("deltalog_opportunity_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_reduction_from_speedup() -> None:
    assert abs(MODULE.reduction_from_speedup(2.0) - 0.5) < 1e-12


def test_required_fraction() -> None:
    required = MODULE.required_fraction(1.10, MODULE.reduction_from_speedup(1.86))
    assert 0.19 < required < 0.20


def test_amdahl_bound() -> None:
    assert MODULE.amdahl_speedup(0.05, 0.5) < 1.03


def test_operator_identity() -> None:
    operator = {"name": "aclnnRecurrentGatedDeltaRule_RecurrentGatedDeltaRule", "type": "RecurrentGatedDeltaRule"}
    assert MODULE.is_recurrent(operator)

