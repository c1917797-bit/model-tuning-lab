#!/usr/bin/env python3
"""Compare paired baseline/candidate quality captures and build a review file."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import json
import os
import statistics
from pathlib import Path
from typing import Any


def normalize(value: str) -> str:
    return " ".join(value.split())


def load(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("schema") != "qwen35-quality-output-capture/v1":
        raise ValueError(f"unexpected capture schema in {path}")
    return result


def secure_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--review-md", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = load(args.baseline)
    candidate = load(args.candidate)
    for key in ("dataset_sha256", "model", "seed", "temperature"):
        if baseline.get(key) != candidate.get(key):
            raise ValueError(f"capture contract mismatch for {key}")
    baseline_rows = {
        int(row["dataset_index"]): row for row in baseline["captures"]
    }
    candidate_rows = {
        int(row["dataset_index"]): row for row in candidate["captures"]
    }
    if baseline_rows.keys() != candidate_rows.keys():
        raise ValueError("baseline and candidate selected different rows")

    comparisons = []
    review = [
        "# Qwen3.5 baseline/candidate quality review",
        "",
        f"- Dataset SHA256: `{baseline['dataset_sha256']}`",
        f"- Baseline: `{baseline['label']}`",
        f"- Candidate: `{candidate['label']}`",
        f"- Samples: {len(baseline_rows)}",
        "",
        "Review each response pair for retained facts, intent, constraints, "
        "completeness, and readability. Exact matches need no semantic ruling.",
        "",
    ]
    for ordinal, index in enumerate(sorted(baseline_rows), start=1):
        left = baseline_rows[index]
        right = candidate_rows[index]
        if left["question_sha256"] != right["question_sha256"]:
            raise ValueError(f"question mismatch at dataset index {index}")
        left_text = str(left["response"])
        right_text = str(right["response"])
        exact = left_text == right_text
        normalized_exact = normalize(left_text) == normalize(right_text)
        similarity = difflib.SequenceMatcher(
            None, normalize(left_text), normalize(right_text), autojunk=False
        ).ratio()
        comparisons.append(
            {
                "ordinal": ordinal,
                "dataset_index": index,
                "question_sha256": left["question_sha256"],
                "baseline_response_sha256": left["response_sha256"],
                "candidate_response_sha256": right["response_sha256"],
                "baseline_completion_tokens": left["completion_tokens"],
                "candidate_completion_tokens": right["completion_tokens"],
                "exact_match": exact,
                "normalized_whitespace_exact_match": normalized_exact,
                "normalized_character_similarity": similarity,
            }
        )
        review.extend(
            [
                f"## Sample {ordinal} — dataset index {index}",
                "",
                f"- Exact match: **{'yes' if exact else 'no'}**",
                f"- Normalized character similarity: {similarity:.6f}",
                "",
                "### Prompt",
                "",
                f"<pre>{html.escape(str(left['question']))}</pre>",
                "",
                "### Baseline",
                "",
                f"<pre>{html.escape(left_text)}</pre>",
                "",
                "### Candidate",
                "",
                f"<pre>{html.escape(right_text)}</pre>",
                "",
                "### Human ruling",
                "",
                "- [ ] Equivalent / no material loss",
                "- [ ] Material regression",
                "- Notes:",
                "",
            ]
        )
    similarities = [
        float(row["normalized_character_similarity"]) for row in comparisons
    ]
    report = {
        "schema": "qwen35-quality-paired-comparison/v1",
        "baseline": str(args.baseline),
        "candidate": str(args.candidate),
        "dataset_sha256": baseline["dataset_sha256"],
        "model": baseline["model"],
        "samples": len(comparisons),
        "exact_matches": sum(row["exact_match"] for row in comparisons),
        "normalized_whitespace_exact_matches": sum(
            row["normalized_whitespace_exact_match"] for row in comparisons
        ),
        "similarity": {
            "min": min(similarities),
            "mean": statistics.fmean(similarities),
            "median": statistics.median(similarities),
            "max": max(similarities),
        },
        "automatic_lossless_gate": all(
            row["exact_match"] for row in comparisons
        ),
        "manual_review_required": not all(
            row["exact_match"] for row in comparisons
        ),
        "comparisons": comparisons,
    }
    secure_write(
        args.report_json,
        json.dumps(report, indent=2, sort_keys=True) + "\n",
    )
    secure_write(args.review_md, "\n".join(review) + "\n")
    print(
        json.dumps(
            {
                "samples": report["samples"],
                "exact_matches": report["exact_matches"],
                "automatic_lossless_gate": report[
                    "automatic_lossless_gate"
                ],
                "report_json_sha256": hashlib.sha256(
                    args.report_json.read_bytes()
                ).hexdigest(),
                "review_md_sha256": hashlib.sha256(
                    args.review_md.read_bytes()
                ).hexdigest(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
