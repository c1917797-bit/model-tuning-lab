#!/usr/bin/env python3
"""Compare two normalized Ascend hotspot reports for diagnostic attribution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

INPUT_SCHEMA = "qwen35-ascend-profile-hotspots/v1"
OUTPUT_SCHEMA = "qwen35-ascend-profile-comparison/v1"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_report(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"{path}: expected schema {INPUT_SCHEMA}")
    semantics = payload.get("measurement_semantics", {})
    if semantics.get("not_wall_time") is not True:
        raise ValueError(f"{path}: missing not_wall_time safety marker")
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError(f"{path}: profile contains no source files")
    summary = payload.get("summary")
    if not isinstance(summary, dict) or not summary.get("kernel_calls"):
        raise ValueError(f"{path}: profile contains no kernel calls")
    return payload


def index(rows: list[dict]) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        name = row.get("name")
        if not isinstance(name, str) or name in indexed:
            raise ValueError("profile rows require unique string names")
        indexed[name] = row
    return indexed


def compare_rows(baseline_rows: list[dict], candidate_rows: list[dict]) -> list[dict]:
    baseline = index(baseline_rows)
    candidate = index(candidate_rows)
    output = []
    for name in sorted(set(baseline) | set(candidate)):
        before = baseline.get(name, {})
        after = candidate.get(name, {})
        before_us = float(before.get("duration_us", 0.0))
        after_us = float(after.get("duration_us", 0.0))
        before_calls = int(before.get("calls", 0))
        after_calls = int(after.get("calls", 0))
        output.append(
            {
                "name": name,
                "baseline_duration_us": before_us,
                "candidate_duration_us": after_us,
                "duration_delta_us": round(after_us - before_us, 3),
                "duration_ratio": round(after_us / before_us, 6)
                if before_us
                else None,
                "baseline_calls": before_calls,
                "candidate_calls": after_calls,
                "call_delta": after_calls - before_calls,
                "baseline_us_per_call": round(before_us / before_calls, 6)
                if before_calls
                else None,
                "candidate_us_per_call": round(after_us / after_calls, 6)
                if after_calls
                else None,
            }
        )
    output.sort(key=lambda row: (-abs(row["duration_delta_us"]), row["name"]))
    return output


def compare(baseline_path: Path, candidate_path: Path, top: int) -> dict:
    baseline = load_report(baseline_path)
    candidate = load_report(candidate_path)
    baseline_hashes = {item["sha256"] for item in baseline["files"]}
    candidate_hashes = {item["sha256"] for item in candidate["files"]}
    if baseline_hashes == candidate_hashes:
        raise ValueError("baseline and candidate resolve to identical profile inputs")
    baseline_summary = baseline["summary"]
    candidate_summary = candidate["summary"]
    baseline_total = float(baseline_summary["total_kernel_duration_us"])
    candidate_total = float(candidate_summary["total_kernel_duration_us"])
    return {
        "schema": OUTPUT_SCHEMA,
        "diagnostic_only": True,
        "acceptance_evidence": False,
        "warning": (
            "Kernel duration sums can overlap across streams. Ratios diagnose "
            "where work changed; they do not prove TTFT, TPOT, or E2E speedup."
        ),
        "baseline": {
            "path": str(baseline_path),
            "sha256": file_sha256(baseline_path),
            "source_file_count": len(baseline["files"]),
            "kernel_calls": int(baseline_summary["kernel_calls"]),
            "total_kernel_duration_us": baseline_total,
        },
        "candidate": {
            "path": str(candidate_path),
            "sha256": file_sha256(candidate_path),
            "source_file_count": len(candidate["files"]),
            "kernel_calls": int(candidate_summary["kernel_calls"]),
            "total_kernel_duration_us": candidate_total,
        },
        "diagnostic_total_duration_ratio": round(candidate_total / baseline_total, 6)
        if baseline_total
        else None,
        "categories": compare_rows(
            baseline_summary["categories"], candidate_summary["categories"]
        ),
        "top_kernel_deltas": compare_rows(
            baseline_summary["top_kernels"], candidate_summary["top_kernels"]
        )[:top],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be positive")
    payload = compare(args.baseline, args.candidate, args.top)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
