#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "evaluate_qwen35_failfast_pair.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("qwen35_failfast_pair", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(ttft: float, tpot: float, *, concurrency: int = 1) -> dict:
    return {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "model": "Qwen3.5-27B",
        "dataset_sha256": "dataset",
        "requests": 4,
        "completed": 4,
        "errors": 0,
        "concurrency": concurrency,
        "repeat_index": 1,
        "max_tokens": "per-request model context remainder",
        "seed": 1024,
        "natural_eos": True,
        "finish_reasons": {"stop": 4},
        "response_sha256": ["a", "b", "c", "d"],
        "ttft_ms": {"p95": ttft},
        "tpot_ms": {"p95": tpot},
        "e2e_ms": {"p95": ttft + tpot},
    }


def run(module, control: Path, candidate: Path, output: Path) -> tuple[int, dict]:
    previous = sys.argv
    stdout = io.StringIO()
    try:
        sys.argv = [
            str(SCRIPT),
            "--control",
            str(control),
            "--candidate",
            str(candidate),
            "--candidate-id",
            "synthetic",
            "--output",
            str(output),
        ]
        with contextlib.redirect_stdout(stdout):
            status = module.main()
    finally:
        sys.argv = previous
    return status, json.loads(stdout.getvalue())


def main() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="qwen35-failfast-pair-") as text:
        root = Path(text)
        control = root / "control.json"
        candidate = root / "candidate.json"
        output = root / "decision.json"

        control.write_text(json.dumps(row(100.0, 100.0)) + "\n")
        candidate.write_text(json.dumps(row(80.0, 90.0)) + "\n")
        status, report = run(module, control, candidate, output)
        assert status == 0
        assert report["performance_target_met"]
        assert report["decision"] == "advance-to-quality-canary"
        assert report["metrics"]["ttft_ms"]["reduction_fraction"] == 0.2
        assert report["metrics"]["tpot_ms"]["reduction_fraction"] == 0.1
        assert report["response_hash_all_equal"]

        candidate.write_text(json.dumps(row(81.0, 91.0)) + "\n")
        status, report = run(module, control, candidate, output)
        assert status == 2
        assert not report["performance_target_met"]
        assert report["decision"] == "iterate"

        bad_identity = row(60.0, 80.0, concurrency=16)
        candidate.write_text(json.dumps(bad_identity) + "\n")
        try:
            run(module, control, candidate, output)
        except ValueError as exc:
            assert "identity mismatch" in str(exc)
        else:
            raise AssertionError("identity mismatch was not rejected")

    print("PASS: qwen35 fail-fast pair decision contract")


if __name__ == "__main__":
    main()
