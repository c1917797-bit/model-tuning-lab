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
    / "check_qwen35_full_quality.py"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def write_capture(path: Path, label: str, changed: bool = False) -> None:
    rows = []
    for index in range(357):
        question = f"question-{index}"
        response = f"response-{index}"
        if changed and index == 0:
            response = "equivalent-response-zero"
        rows.append(
            {
                "dataset_index": index,
                "question": question,
                "question_sha256": text_digest(question),
                "response": response,
                "response_sha256": text_digest(response),
                "finish_reason": "stop",
            }
        )
    path.write_text(
        json.dumps(
            {
                "schema": "qwen35-quality-output-capture/v1",
                "label": label,
                "dataset_sha256": "dataset",
                "dataset_rows": 357,
                "sample_count": 357,
                "model": "Qwen3-5/Qwen3.5-27B",
                "seed": 1024,
                "temperature": 0,
                "natural_eos_required": True,
                "captures": rows,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def run(module, root: Path, manual: Path | None = None) -> tuple[int, dict]:
    previous = sys.argv
    stdout = io.StringIO()
    argv = [
        str(SCRIPT),
        "--baseline",
        str(root / "baseline.json"),
        "--candidate",
        str(root / "candidate.json"),
        "--comparison",
        str(root / "comparison.json"),
        "--candidate-id",
        "synthetic-t12",
        "--output",
        str(root / "decision.json"),
    ]
    if manual is not None:
        argv.extend(["--manual-decision", str(manual)])
    try:
        sys.argv = argv
        with contextlib.redirect_stdout(stdout):
            status = module.main()
    finally:
        sys.argv = previous
    return status, json.loads(stdout.getvalue())


def main() -> None:
    spec = importlib.util.spec_from_file_location("qwen35_full_quality", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="qwen35-full-quality-") as text:
        root = Path(text)
        write_capture(root / "baseline.json", "control")
        write_capture(root / "candidate.json", "candidate")
        (root / "comparison.json").write_text(
            json.dumps(
                {
                    "schema": "qwen35-quality-paired-comparison/v1",
                    "dataset_sha256": "dataset",
                    "samples": 357,
                    "exact_matches": 357,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        status, report = run(module, root)
        assert status == 0
        assert report["passed"]
        assert report["method"] == "all-357-byte-identical"

        write_capture(root / "candidate.json", "candidate", changed=True)
        (root / "comparison.json").write_text(
            json.dumps(
                {
                    "schema": "qwen35-quality-paired-comparison/v1",
                    "dataset_sha256": "dataset",
                    "samples": 357,
                    "exact_matches": 356,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        status, report = run(module, root)
        assert status == 3
        assert not report["passed"]
        manual = root / "manual.json"
        manual.write_text(
            json.dumps(
                {
                    "schema": "qwen35-quality-human-decision/v2",
                    "candidate_id": "synthetic-t12",
                    "dataset_sha256": "dataset",
                    "samples": 357,
                    "exact_matches": 356,
                    "reviewed_differences": 1,
                    "equivalent_samples": 357,
                    "material_regressions": 0,
                    "decision": "pass",
                    "reviewer": "fixture-reviewer",
                    "reviewed_at_utc": "2026-09-08T00:00:00Z",
                    "baseline_capture": {
                        "sha256": digest(root / "baseline.json")
                    },
                    "candidate_capture": {
                        "sha256": digest(root / "candidate.json")
                    },
                    "comparison": {
                        "sha256": digest(root / "comparison.json")
                    },
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        status, report = run(module, root, manual)
        assert status == 0
        assert report["passed"]
        assert report["manual_reviewer"] == "fixture-reviewer"
    print("PASS: all-357-row quality decision contract")


if __name__ == "__main__":
    main()
