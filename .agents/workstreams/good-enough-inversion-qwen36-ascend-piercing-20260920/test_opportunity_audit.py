from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("opportunity_audit.py")
SPEC = importlib.util.spec_from_file_location("good_enough_opportunity_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_amdahl_bound() -> None:
    assert MODULE.amdahl_speedup(0.03, 5.2) < 1.03


def test_perfect_deletion_bound() -> None:
    assert MODULE.amdahl_speedup(0.03, float("inf")) == 1.0 / 0.97


def test_required_fraction() -> None:
    required = MODULE.required_fraction(1.10, 5.2)
    assert 0.11 < required < 0.12

