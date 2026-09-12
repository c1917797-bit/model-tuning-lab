#!/usr/bin/env python3
"""Direct-assertion tests for the T19 GDN terminal budget analyzer."""

import importlib.util
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/analyze_qwen35_gdn_terminal_budget.py"
)
SPEC = importlib.util.spec_from_file_location("gdn_terminal_budget", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def row(start, duration, name, shape="", stream="7"):
    return {
        "start": float(start),
        "end": float(start + duration),
        "duration": float(duration),
        "name": name,
        "shape": shape,
        "stream": stream,
    }


def run_checks():
    rows = [
        row(0, 205, MODULE.AICPU),
        row(140, 5, MODULE.NORM),
        row(146, 55, MODULE.CORE, MODULE.DECODE_SHAPE),
        row(300, 200, MODULE.AICPU),
        row(440, 52, MODULE.CORE, MODULE.DECODE_SHAPE),
    ]
    result = MODULE.analyze_rows(rows)
    assert result["target_k1536_calls"] == 2
    assert result["paired_gdn_calls"] == 1
    assert result["missing_preceding_gdn_norm"] == 1
    metric = result["metrics"]["norm_start_to_envelope_end_us"]
    assert metric["median_us"] == 65.0
    assert result["metrics"]["full_envelope_us"]["median_us"] == 205.0

    no_aicpu = [
        row(140, 5, MODULE.NORM),
        row(146, 55, MODULE.CORE, MODULE.DECODE_SHAPE),
    ]
    result = MODULE.analyze_rows(no_aicpu)
    assert result["paired_gdn_calls"] == 0
    assert result["missing_aicpu_envelope"] == 1


if __name__ == "__main__":
    run_checks()
    print("PASS: T19 GDN terminal budget analyzer")
