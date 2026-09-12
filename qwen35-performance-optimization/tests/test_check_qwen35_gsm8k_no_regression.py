#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "check_qwen35_gsm8k_no_regression.py"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_run(root: Path, name: str, correct: int) -> Path:
    details = root / f"{name}.jsonl"
    with details.open("w", encoding="utf-8") as stream:
        for index in range(1319):
            stream.write(
                json.dumps(
                    {
                        "index": index,
                        "ok": True,
                        "error": None,
                        "correct": index < correct,
                        "response_sha256": hashlib.sha256(
                            f"{name}-{index}".encode()
                        ).hexdigest(),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    summary = root / f"{name}.summary.json"
    summary.write_text(
        json.dumps(
            {
                "schema": "hypic-quality-eval/v1",
                "dataset": "gsm8k",
                "data_sha256": (
                    "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14"
                ),
                "requests": 1319,
                "successful": 1319,
                "failed": 0,
                "temperature": 0,
                "seed": 0,
                "enable_thinking": False,
                "ignore_eos": False,
                "max_out_len": 1024,
                "scorer": "supplied_ais_bench_gsm8k_numeric_postprocess",
                "correct": correct,
                "accuracy_pct": correct * 100.0 / 1319,
                "details_path": str(details),
                "details_sha256": digest(details),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def run(module, root: Path, controls: list[Path], candidates: list[Path]):
    previous = sys.argv
    output = io.StringIO()
    sys.argv = [
        str(SCRIPT),
        "--control",
        *(str(path) for path in controls),
        "--candidate",
        *(str(path) for path in candidates),
        "--candidate-id",
        "fixture",
        "--output",
        str(root / "decision.json"),
    ]
    try:
        with contextlib.redirect_stdout(output):
            status = module.main()
    finally:
        sys.argv = previous
    return status, json.loads(output.getvalue())


def main() -> None:
    spec = importlib.util.spec_from_file_location("gsm8k_gate", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="qwen35-gsm8k-gate-") as text:
        root = Path(text)
        controls = [write_run(root, f"control-{i}", 1200) for i in range(3)]
        equal = [write_run(root, f"equal-{i}", 1200) for i in range(3)]
        status, report = run(module, root, controls, equal)
        assert status == 0 and report["passed"]
        regressed = [write_run(root, f"regressed-{i}", 1199) for i in range(3)]
        status, report = run(module, root, controls, regressed)
        assert status == 3 and not report["passed"]
        assert report["decision"] == "reject-accuracy-regression"
    print("PASS: full GSM8K no-regression gate")


if __name__ == "__main__":
    main()
