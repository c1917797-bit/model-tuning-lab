#!/usr/bin/env python3
"""Fail closed on the final all-357-row paired Qwen3.5 quality gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_ROWS = 357


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def load_capture(path: Path) -> dict:
    payload = load_json(path)
    expected = {
        "schema": "qwen35-quality-output-capture/v1",
        "dataset_rows": EXPECTED_ROWS,
        "sample_count": EXPECTED_ROWS,
        "temperature": 0,
        "seed": 1024,
        "natural_eos_required": True,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {payload.get(key)!r}"
            )
    captures = payload.get("captures")
    if not isinstance(captures, list) or len(captures) != EXPECTED_ROWS:
        raise ValueError(f"{path}: captures must contain all 357 rows")
    by_index = {}
    for row in captures:
        index = row.get("dataset_index")
        if not isinstance(index, int) or index in by_index:
            raise ValueError(f"{path}: invalid or duplicate dataset index")
        question = row.get("question")
        response = row.get("response")
        if not isinstance(question, str) or not isinstance(response, str):
            raise ValueError(f"{path}: raw paired text is missing")
        if row.get("question_sha256") != sha256_text(question):
            raise ValueError(f"{path}: question SHA256 mismatch at row {index}")
        if row.get("response_sha256") != sha256_text(response):
            raise ValueError(f"{path}: response SHA256 mismatch at row {index}")
        if row.get("finish_reason") != "stop":
            raise ValueError(f"{path}: row {index} did not terminate naturally")
        by_index[index] = row
    if set(by_index) != set(range(EXPECTED_ROWS)):
        raise ValueError(f"{path}: capture does not cover dataset indices 0..356")
    return {"payload": payload, "rows": by_index}


def validate_manual_decision(
    path: Path,
    *,
    candidate_id: str,
    dataset_sha256: str,
    exact_matches: int,
    artifacts: dict[str, str],
    differences: dict[int, tuple[dict, dict]],
) -> dict:
    payload = load_json(path)
    expected = {
        "schema": "qwen35-quality-human-decision/v3",
        "candidate_id": candidate_id,
        "dataset_sha256": dataset_sha256,
        "samples": EXPECTED_ROWS,
        "exact_matches": exact_matches,
        "reviewed_differences": EXPECTED_ROWS - exact_matches,
        "material_regressions": 0,
        "decision": "pass",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(
                f"{path}: {key} must be {value!r}, got {payload.get(key)!r}"
            )
    if not payload.get("reviewer") or not payload.get("reviewed_at_utc"):
        raise ValueError(f"{path}: reviewer and reviewed_at_utc are required")
    reviews = payload.get("reviews")
    if not isinstance(reviews, list) or len(reviews) != len(differences):
        raise ValueError(
            f"{path}: reviews must contain every differing pair exactly once"
        )
    reviewed = {}
    verdict_counts = {"equivalent": 0, "candidate_better": 0}
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError(f"{path}: every review must be an object")
        index = review.get("dataset_index")
        if index not in differences or index in reviewed:
            raise ValueError(f"{path}: invalid or duplicate review index {index!r}")
        baseline_row, candidate_row = differences[index]
        expected_hashes = {
            "baseline_response_sha256": baseline_row["response_sha256"],
            "candidate_response_sha256": candidate_row["response_sha256"],
        }
        for key, value in expected_hashes.items():
            if review.get(key) != value:
                raise ValueError(f"{path}: {key} mismatch at row {index}")
        verdict = review.get("verdict")
        if verdict not in verdict_counts:
            raise ValueError(
                f"{path}: row {index} verdict must be equivalent or candidate_better"
            )
        rationale = review.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError(f"{path}: row {index} requires a rationale")
        verdict_counts[verdict] += 1
        reviewed[index] = review
    if set(reviewed) != set(differences):
        raise ValueError(f"{path}: one or more differing rows were not reviewed")
    expected_counts = {
        "equivalent_differences": verdict_counts["equivalent"],
        "candidate_better_differences": verdict_counts["candidate_better"],
    }
    for key, value in expected_counts.items():
        if payload.get(key) != value:
            raise ValueError(f"{path}: {key} must be {value}")
    for name, digest in artifacts.items():
        record = payload.get(name)
        if not isinstance(record, dict) or record.get("sha256") != digest:
            raise ValueError(f"{path}: {name} artifact SHA256 mismatch")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--manual-decision", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = load_capture(args.baseline)
    candidate = load_capture(args.candidate)
    for key in ("dataset_sha256", "model", "seed", "temperature"):
        if baseline["payload"].get(key) != candidate["payload"].get(key):
            raise ValueError(f"paired capture mismatch for {key}")
    exact_matches = 0
    differences = {}
    for index in range(EXPECTED_ROWS):
        left = baseline["rows"][index]
        right = candidate["rows"][index]
        if left["question_sha256"] != right["question_sha256"]:
            raise ValueError(f"paired prompt mismatch at row {index}")
        if left["response_sha256"] == right["response_sha256"]:
            exact_matches += 1
        else:
            differences[index] = (left, right)

    comparison = load_json(args.comparison)
    expected_comparison = {
        "schema": "qwen35-quality-paired-comparison/v1",
        "dataset_sha256": baseline["payload"]["dataset_sha256"],
        "samples": EXPECTED_ROWS,
        "exact_matches": exact_matches,
    }
    for key, value in expected_comparison.items():
        if comparison.get(key) != value:
            raise ValueError(
                f"{args.comparison}: {key} must be {value!r}, "
                f"got {comparison.get(key)!r}"
            )

    artifacts = {
        "baseline_capture": sha256_file(args.baseline),
        "candidate_capture": sha256_file(args.candidate),
        "comparison": sha256_file(args.comparison),
    }
    manual = None
    if exact_matches == EXPECTED_ROWS:
        passed = True
        method = "all-357-byte-identical"
    elif args.manual_decision is None:
        passed = False
        method = "manual-review-required"
    else:
        manual = validate_manual_decision(
            args.manual_decision,
            candidate_id=args.candidate_id,
            dataset_sha256=baseline["payload"]["dataset_sha256"],
            exact_matches=exact_matches,
            artifacts=artifacts,
            differences=differences,
        )
        artifacts["manual_decision"] = sha256_file(args.manual_decision)
        passed = True
        method = "all-differences-row-reviewed-no-material-regression"

    report = {
        "schema": "qwen35-full-quality-decision/v1",
        "candidate_id": args.candidate_id,
        "dataset_sha256": baseline["payload"]["dataset_sha256"],
        "samples": EXPECTED_ROWS,
        "exact_matches": exact_matches,
        "differing_pairs": EXPECTED_ROWS - exact_matches,
        "passed": passed,
        "method": method,
        "material_regressions": (
            0 if passed else None
        ),
        "manual_reviewer": manual.get("reviewer") if manual else None,
        "artifact_sha256": artifacts,
        "claim_boundary": (
            "paired no-regression on the frozen 357-row workload; empty "
            "reference answers do not prove universal model accuracy"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
