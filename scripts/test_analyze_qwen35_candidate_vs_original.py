#!/usr/bin/env python3
"""Contract tests for the repeated P95/P99 candidate decision."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_qwen35_candidate_vs_original.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("_qwen35_decision", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(concurrency: int, repeat_index: int, p95: float, p99: float) -> dict:
    metric = {"p50": p95 * 0.8, "p95": p95, "p99": p99}
    return {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "model": "Qwen3-5/Qwen3.5-27B",
        "dataset_sha256": (
            "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e"
        ),
        "requests": 32,
        "completed": 32,
        "errors": 0,
        "concurrency": concurrency,
        "repeat_index": repeat_index,
        "max_tokens": "per-request model context remainder",
        "seed": 1024,
        "natural_eos": True,
        "finish_reasons": {"stop": 32},
        "response_sha256": [f"response-{index}" for index in range(32)],
        "ttft_ms": metric,
        "tpot_ms": metric,
        "e2e_ms": metric,
    }


def _write(path: Path, row: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(row, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode()).hexdigest()


def _run(module, argv: list[str]) -> tuple[int, dict]:
    previous = sys.argv
    stdout = io.StringIO()
    try:
        sys.argv = [str(SCRIPT), *argv]
        with contextlib.redirect_stdout(stdout):
            status = module.main()
    finally:
        sys.argv = previous
    return status, json.loads(stdout.getvalue())


def main() -> None:
    module = _load_module()
    with tempfile.TemporaryDirectory(prefix="qwen35-decision-") as root_text:
        root = Path(root_text)
        original_dir = root / "original"
        candidate_dir = root / "candidate"
        original_dir.mkdir()
        candidate_dir.mkdir()
        original_hashes = {}
        for concurrency in module.CONCURRENCIES:
            original_hashes[concurrency] = _write(
                original_dir / f"c{concurrency}-r1.json",
                _row(concurrency, 1, 100.0, 100.0),
            )
            for repeat_index, (p95, p99) in enumerate(
                ((60.0, 90.0), (65.0, 95.0), (70.0, 110.0)), start=1
            ):
                _write(
                    candidate_dir
                    / f"c{concurrency}"
                    / f"repeat-{repeat_index}.json",
                    _row(concurrency, repeat_index, p95, p99),
                )
        module.ORIGINAL_SHA256 = original_hashes

        output = root / "decision.json"
        status, report = _run(
            module,
            [
                "--original-dir",
                str(original_dir),
                "--candidate-dir",
                str(candidate_dir),
                "--candidate-id",
                "synthetic-pass",
                "--candidate-device-set",
                "0-3",
                "--output",
                str(output),
            ],
        )
        assert status == 0
        assert report["decision"] == "final-target-met"
        assert report["final_target_met"]
        assert report["repetitions"] == 3
        assert report["aggregation"] == "median of per-run P95/P99 values"
        for cell in report["cells"].values():
            assert cell["candidate_median_ttft_p50_ms"] == 52.0
            assert cell["candidate_median_tpot_p50_ms"] == 52.0
            assert cell["candidate_median_ttft_p95_ms"] == 65.0
            assert cell["candidate_median_tpot_p95_ms"] == 65.0
            assert cell["candidate_median_ttft_p99_ms"] == 95.0
            assert cell["p99_guard_met"]

        (candidate_dir / "c16" / "repeat-3.json").unlink()
        status, report = _run(
            module,
            [
                "--original-dir",
                str(original_dir),
                "--candidate-dir",
                str(candidate_dir),
                "--candidate-id",
                "synthetic-incomplete",
                "--candidate-device-set",
                "0-3",
                "--allow-incomplete",
                "--output",
                str(output),
            ],
        )
        assert status == 4
        assert report["decision"] == "reject-runtime-failure"
        assert not report["runtime_gate_met"]
        assert len(report["cells"]["16"]["missing_artifacts"]) == 1
    print("PASS: repeated P95/P99 decision contract")


if __name__ == "__main__":
    main()
