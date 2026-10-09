#!/usr/bin/env python3
"""Read-only paired finish-reason diagnosis for immutable r13 quality roots."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from binding_off_service import ROOT, sha256


AUDIT_SHA256 = "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b"


def analyze(root: Path = ROOT) -> dict:
    audit_path = root / "hotpath-quality-cache10r13-dual-audit.json"
    if sha256(audit_path) != AUDIT_SHA256:
        raise ValueError("frozen r13 dual-audit hash drift")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit["evidence_valid"] is not True:
        raise ValueError("r13 quality evidence invalid")
    baseline = Path(audit["baseline"]["root"])
    candidate = Path(audit["candidate"]["root"])
    for arm, path in ((audit["baseline"], baseline), (audit["candidate"], candidate)):
        if sha256(path / "arm-result.json") != arm["arm_result_sha256"]:
            raise ValueError(f"arm-result hash drift: {path}")
    cold = {(row["index"], row["repetition"])
            for row in audit["strict_c1_c2_hot_coverage"]["cold_issues"]}
    if len(cold) != 13:
        raise ValueError("frozen cold-request cardinality drift")
    counts: Counter[str] = Counter()
    regressed_samples: Counter[int] = Counter()
    for index in range(127):
        base = json.loads((baseline / "samples" / f"{index:03}.json").read_text())
        hypic = json.loads((candidate / "samples" / f"{index:03}.json").read_text())
        if (base["index"] != hypic["index"] or base["index"] != index
                or base["sample_id"] != hypic["sample_id"]
                or base["prompt_sha256"] != hypic["prompt_sha256"]
                or len(base["scores"]) != 3 or len(hypic["scores"]) != 3
                or {row["repetition"] for row in base["scores"]} != {1, 2, 3}
                or {row["repetition"] for row in hypic["scores"]} != {1, 2, 3}):
            raise ValueError(f"sample identity drift: {index}")
        for prior, treated in zip(base["scores"], hypic["scores"]):
            repetition = prior["repetition"]
            if repetition != treated["repetition"]:
                raise ValueError(f"repetition drift: {index}")
            cohort = "cold" if (index, repetition) in cold else "hot"
            counts["paired_requests"] += 1
            counts[f"{cohort}_requests"] += 1
            if prior["correct"] and not treated["correct"]:
                counts["regressed"] += 1
                counts[f"{cohort}_regressed"] += 1
                regressed_samples[index] += 1
                if prior["finish_reason"] != "length" and treated["finish_reason"] == "length":
                    counts["regressed_new_length"] += 1
                    counts[f"{cohort}_regressed_new_length"] += 1
            elif treated["correct"] and not prior["correct"]:
                counts["improved"] += 1
                counts[f"{cohort}_improved"] += 1
            elif prior["correct"]:
                counts["both_correct"] += 1
            else:
                counts["both_wrong"] += 1
            if prior["finish_reason"] == "length":
                counts["baseline_length"] += 1
            if treated["finish_reason"] == "length":
                counts["candidate_length"] += 1
            if prior["response_sha256"] == treated["response_sha256"]:
                counts["identical_response_hash"] += 1
    if (counts["paired_requests"] != 381 or counts["hot_requests"] != 368
            or counts["cold_requests"] != 13 or counts["regressed"] != 30
            or counts["improved"] != 19 or counts["baseline_length"] != 48
            or counts["candidate_length"] != 60):
        raise ValueError("paired raw counts disagree with frozen dual audit")
    return {
        "schema": "hypic-r13-paired-length-diagnosis/v1",
        "quality_audit_sha256": AUDIT_SHA256,
        "scope": "descriptive paired raw rows; no causal attribution or quality reclassification",
        "counts": dict(sorted(counts.items())),
        "regressed_sample_count": len(regressed_samples),
        "regressed_samples_with_two_or_more_losses":
            sum(value >= 2 for value in regressed_samples.values()),
        "regressed_samples_with_three_losses":
            sum(value == 3 for value in regressed_samples.values()),
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), sort_keys=True))
