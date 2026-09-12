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
    / "analyze_qwen35_current_targets.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("qwen35_current_targets", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(
    concurrency: int,
    repetition: int,
    ttft_p95: float,
    tpot_p95: float,
    p99_scale: float = 1.05,
) -> dict:
    return {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "model": "Qwen3-5/Qwen3.5-27B",
        "dataset_sha256": "dataset",
        "requests": 32,
        "completed": 32,
        "errors": 0,
        "concurrency": concurrency,
        "repeat_index": repetition,
        "max_tokens": "per-request model context remainder",
        "seed": 1024,
        "natural_eos": True,
        "cache_salt_prefix": "synthetic-run",
        "prefix_cache_isolation": True,
        "finish_reasons": {"stop": 32},
        "response_sha256": [f"response-{index}" for index in range(32)],
        "ttft_ms": {
            "p50": ttft_p95 * 0.8,
            "p95": ttft_p95,
            "p99": ttft_p95 * p99_scale,
        },
        "tpot_ms": {
            "p50": tpot_p95 * 0.8,
            "p95": tpot_p95,
            "p99": tpot_p95 * p99_scale,
        },
    }


def write_matrix(root: Path, *, candidate: bool, fail_c16: bool = False) -> None:
    for concurrency in (1, 5, 8, 16):
        for repetition in (1, 2, 3):
            if candidate:
                ttft = (55.0, 60.0, 65.0)[repetition - 1]
                tpot = (75.0, 80.0, 85.0)[repetition - 1]
                if fail_c16:
                    tpot = (90.5, 91.0, 91.5)[repetition - 1]
            else:
                ttft = 100.0
                tpot = 100.0
            path = root / f"c{concurrency}" / f"repeat-{repetition}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    row(concurrency, repetition, ttft, tpot),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )


def run(module, baseline: Path, candidate: Path, output: Path) -> tuple[int, dict]:
    previous = sys.argv
    stdout = io.StringIO()
    try:
        sys.argv = [
            str(SCRIPT),
            "--baseline-dir",
            str(baseline),
            "--candidate-dir",
            str(candidate),
            "--candidate-id",
            "synthetic-t12",
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
    with tempfile.TemporaryDirectory(prefix="qwen35-current-targets-") as text:
        root = Path(text)
        baseline = root / "baseline"
        candidate = root / "candidate"
        output = root / "decision.json"
        write_matrix(baseline, candidate=False)
        write_matrix(candidate, candidate=True)
        status, report = run(module, baseline, candidate, output)
        assert status == 0
        assert report["performance_target_met"]
        assert report["decision"] == "performance-target-met-await-quality"
        assert report["thresholds"][
            "ttft_p95_candidate_over_baseline_max"
        ] == 0.80
        assert report["thresholds"][
            "tpot_p95_candidate_over_baseline_max"
        ] == 0.90
        for cell in report["cells"].values():
            assert cell["ttft_p95_ratio"] == 0.60
            assert cell["tpot_p95_ratio"] == 0.80
            assert cell["performance_target_met"]

        write_matrix(candidate, candidate=True, fail_c16=True)
        status, report = run(module, baseline, candidate, output)
        assert status == 2
        assert not report["performance_target_met"]
        assert not report["cells"]["16"]["performance_target_met"]
    print("PASS: current 20/10 P95 acceptance contract")


if __name__ == "__main__":
    main()
