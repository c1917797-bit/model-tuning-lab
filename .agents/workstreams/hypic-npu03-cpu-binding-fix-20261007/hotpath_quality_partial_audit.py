#!/usr/bin/env python3
"""Read-only audit of already persisted hot-path quality rows; never a final verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from hotpath_quality_audit import BASE, CAND, frozen_cases, payload_hash, require


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("no-cache", "hypic-only"), required=True)
    args = parser.parse_args()
    root = BASE if args.arm == "no-cache" else CAND
    contract = json.loads((root / "contract.json").read_text())
    require(contract["arm"] == args.arm and contract["mode"] == "full",
            "partial audit arm/contract mismatch")
    cases, evaluator = frozen_cases()
    paths = sorted((root / "samples").glob("*.json"))
    seen_ids: set[str] = set()
    correct = 0
    rows = 0
    indexes = set()
    for path in paths:
        row = json.loads(path.read_text())
        index = row["index"]
        require(0 <= index < len(cases) and index not in indexes
                and path.stem == f"{index:03d}", f"duplicate/bad sample index: {index}")
        indexes.add(index)
        item = cases[index]
        for field in ("sample_id", "reference", "prompt_sha256", "prompt_tokens",
                      "difficulty", "length"):
            require(row[field] == item[field], f"sample {index}: {field} drift")
        require(row["arm"] == args.arm and row["mode"] == "full"
                and row["segment_ends"] == [item["boundary"], item["prompt_tokens"]],
                f"sample {index}: arm/segment drift")
        require(len(row["warm"]) == 2 and len(row["scores"]) == 3,
                f"sample {index}: warm/score count drift")
        for warm in row["warm"]:
            require(warm["request_sha256"] == payload_hash(item, 1)
                    and warm["usage"]["prompt_tokens"] == item["prompt_tokens"]
                    and 0 <= warm["usage"]["completion_tokens"] <= 1,
                    f"sample {index}: warm payload/usage drift")
            require(isinstance(warm["request_id"], str)
                    and warm["request_id"] not in seen_ids,
                    f"sample {index}: duplicate/bad warm ID")
            seen_ids.add(warm["request_id"])
        for repeat, score in enumerate(row["scores"], 1):
            require(score["repetition"] == repeat
                    and score["request_sha256"] == payload_hash(item, 2048)
                    and score["usage"]["prompt_tokens"] == item["prompt_tokens"]
                    and 0 <= score["usage"]["completion_tokens"] <= 2048,
                    f"sample {index}: scored payload/usage drift")
            require(isinstance(score["request_id"], str)
                    and score["request_id"] not in seen_ids,
                    f"sample {index}: duplicate/bad score ID")
            seen_ids.add(score["request_id"])
            text = score["response_text"]
            require(isinstance(text, str)
                    and score["response_sha256"] == hashlib.sha256(text.encode()).hexdigest(),
                    f"sample {index}: response hash drift")
            prediction, scored_correct = evaluator.score_case(
                "longbenchv2", text, item["reference"])
            require(score["prediction"] == prediction
                    and score["correct"] is bool(scored_correct),
                    f"sample {index}: scorer drift")
            rows += 1
            correct += bool(scored_correct)
    print(json.dumps({
        "schema": "hypic-hotpath-partial-row-audit/v1",
        "arm": args.arm, "partial_not_quality_verdict": True,
        "persisted_samples": len(paths), "expected_samples": len(cases),
        "audited_scored_rows": rows, "audited_correct": correct,
        "distinct_request_ids": len(seen_ids),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
