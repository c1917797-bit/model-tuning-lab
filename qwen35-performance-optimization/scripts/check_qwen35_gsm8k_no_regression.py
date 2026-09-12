#!/usr/bin/env python3
"""Fail closed on three paired full-GSM8K accuracy repetitions."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path


EXPECTED_ROWS = 1319
EXPECTED_DATA_SHA256 = (
    "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14"
)
EXPECTED_SCORER = "supplied_ais_bench_gsm8k_numeric_postprocess"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_summary(path: Path) -> tuple[dict, dict[int, dict]]:
    summary = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema": "hypic-quality-eval/v1",
        "dataset": "gsm8k",
        "data_sha256": EXPECTED_DATA_SHA256,
        "requests": EXPECTED_ROWS,
        "successful": EXPECTED_ROWS,
        "failed": 0,
        "temperature": 0,
        "seed": 0,
        "enable_thinking": False,
        "ignore_eos": False,
        "max_out_len": 1024,
        "scorer": EXPECTED_SCORER,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {summary.get(key)!r}"
            )
    correct = summary.get("correct")
    accuracy = summary.get("accuracy_pct")
    if not isinstance(correct, int) or not isinstance(accuracy, (int, float)):
        raise ValueError(f"{path}: missing correct/accuracy_pct")
    expected_accuracy = correct * 100.0 / EXPECTED_ROWS
    if abs(float(accuracy) - expected_accuracy) > 1e-9:
        raise ValueError(f"{path}: accuracy_pct does not match correct count")
    details_path = Path(summary.get("details_path", ""))
    if not details_path.is_file():
        raise ValueError(f"{path}: details_path does not exist")
    if summary.get("details_sha256") != sha256(details_path):
        raise ValueError(f"{path}: details SHA256 mismatch")
    rows = {}
    with details_path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            index = row.get("index")
            if not isinstance(index, int) or index in rows:
                raise ValueError(f"{details_path}: invalid or duplicate index")
            if row.get("ok") is not True or row.get("error") is not None:
                raise ValueError(f"{details_path}: unsuccessful row {index}")
            if not isinstance(row.get("correct"), bool):
                raise ValueError(f"{details_path}: missing correctness at row {index}")
            digest = row.get("response_sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError(f"{details_path}: invalid response hash at row {index}")
            rows[index] = row
    if set(rows) != set(range(EXPECTED_ROWS)):
        raise ValueError(f"{details_path}: expected indices 0..1318")
    if sum(row["correct"] for row in rows.values()) != correct:
        raise ValueError(f"{path}: detail correctness count mismatch")
    return summary, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", type=Path, nargs=3, required=True)
    parser.add_argument("--candidate", type=Path, nargs=3, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    controls = [load_summary(path) for path in args.control]
    candidates = [load_summary(path) for path in args.candidate]
    repetitions = []
    all_passed = True
    for repeat, ((control, control_rows), (candidate, candidate_rows)) in enumerate(
        zip(controls, candidates), start=1
    ):
        identity_keys = (
            "data_sha256",
            "requests",
            "temperature",
            "seed",
            "enable_thinking",
            "ignore_eos",
            "max_out_len",
            "scorer",
        )
        if any(control.get(key) != candidate.get(key) for key in identity_keys):
            raise ValueError(f"repeat {repeat}: control/candidate identity mismatch")
        control_only = []
        candidate_only = []
        for index in range(EXPECTED_ROWS):
            left = control_rows[index]["correct"]
            right = candidate_rows[index]["correct"]
            if left and not right:
                control_only.append(index)
            elif right and not left:
                candidate_only.append(index)
        passed = candidate["correct"] >= control["correct"]
        all_passed &= passed
        repetitions.append(
            {
                "repeat": repeat,
                "control_correct": control["correct"],
                "candidate_correct": candidate["correct"],
                "control_accuracy_pct": control["accuracy_pct"],
                "candidate_accuracy_pct": candidate["accuracy_pct"],
                "accuracy_delta_points": (
                    float(candidate["accuracy_pct"]) - float(control["accuracy_pct"])
                ),
                "control_only_correct_count": len(control_only),
                "candidate_only_correct_count": len(candidate_only),
                "control_only_indices_sha256": hashlib.sha256(
                    json.dumps(control_only, separators=(",", ":")).encode()
                ).hexdigest(),
                "candidate_only_indices_sha256": hashlib.sha256(
                    json.dumps(candidate_only, separators=(",", ":")).encode()
                ).hexdigest(),
                "passed": passed,
                "control_summary_sha256": sha256(args.control[repeat - 1]),
                "candidate_summary_sha256": sha256(args.candidate[repeat - 1]),
            }
        )
    control_median = statistics.median(
        float(item[0]["accuracy_pct"]) for item in controls
    )
    candidate_median = statistics.median(
        float(item[0]["accuracy_pct"]) for item in candidates
    )
    median_passed = candidate_median >= control_median
    passed = all_passed and median_passed
    report = {
        "schema": "qwen35-gsm8k-no-regression/v1",
        "candidate_id": args.candidate_id,
        "dataset_sha256": EXPECTED_DATA_SHA256,
        "samples_per_repeat": EXPECTED_ROWS,
        "repetitions": repetitions,
        "control_median_accuracy_pct": control_median,
        "candidate_median_accuracy_pct": candidate_median,
        "median_delta_points": candidate_median - control_median,
        "every_repeat_non_decreasing": all_passed,
        "median_non_decreasing": median_passed,
        "passed": passed,
        "decision": "pass" if passed else "reject-accuracy-regression",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
