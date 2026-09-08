#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


capture = load_module(
    "capture_qwen35_quality_outputs",
    ROOT / "scripts/capture_qwen35_quality_outputs.py",
)

rows = [
    {"question": "x"},
    {"question": "three"},
    {"question": "tw"},
]
assert capture.stratified_indices(rows, 3) == [0, 2, 1]
assert capture.stratified_indices(rows, 99) == [0, 2, 1]
try:
    capture.stratified_indices(rows, 0)
except ValueError as error:
    assert "positive" in str(error)
else:
    raise AssertionError("zero-sized quality capture was accepted")


def capture_payload(label: str, responses: list[str]) -> dict:
    captures = []
    for index, response in enumerate(responses):
        question = f"question-{index}"
        captures.append(
            {
                "ordinal": index + 1,
                "dataset_index": index,
                "question": question,
                "question_sha256": capture.sha256_text(question),
                "response": response,
                "response_sha256": capture.sha256_text(response),
                "prompt_tokens": 4,
                "completion_tokens": 2,
                "finish_reason": "stop",
            }
        )
    return {
        "schema": "qwen35-quality-output-capture/v1",
        "label": label,
        "model": "Qwen3-5/Qwen3.5-27B",
        "dataset_sha256": "a" * 64,
        "seed": 1024,
        "temperature": 0,
        "captures": captures,
    }


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    baseline = root / "baseline.json"
    candidate = root / "candidate.json"
    report = root / "comparison.json"
    review = root / "review.md"
    baseline.write_text(
        json.dumps(capture_payload("control", ["same", "left"])),
        encoding="utf-8",
    )
    candidate.write_text(
        json.dumps(capture_payload("candidate", ["same", "right"])),
        encoding="utf-8",
    )
    command = [
        sys.executable,
        str(ROOT / "scripts/compare_qwen35_quality_outputs.py"),
        "--baseline",
        str(baseline),
        "--candidate",
        str(candidate),
        "--report-json",
        str(report),
        "--review-md",
        str(review),
    ]
    subprocess.run(command, check=True)
    result = json.loads(report.read_text(encoding="utf-8"))
    assert result["samples"] == 2
    assert result["exact_matches"] == 1
    assert result["manual_review_required"] is True
    assert (report.stat().st_mode & 0o777) == 0o600
    assert (review.stat().st_mode & 0o777) == 0o600
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0
    assert "refusing to replace" in repeated.stderr

print("PASS: quality capture/compare offline contract")
