#!/usr/bin/env python3
"""Read-only variability diagnosis for the immutable r13 paired quality roots.

Text-prefix comparisons are descriptive. They cannot identify a CANN, HCCL,
cache, or numerical root cause and never change the frozen quality verdict.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import median

from binding_off_service import ROOT, sha256


AUDIT_SHA256 = "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b"


def common_prefix_chars(left: str, right: str) -> int:
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return index
    return min(len(left), len(right))


def bucket_summary(rows: list[tuple[dict, dict]]) -> dict:
    counts: Counter[str] = Counter()
    prefixes: list[int] = []
    fractions: list[float] = []
    for left, right in rows:
        a, b = left["response_text"], right["response_text"]
        prefix = common_prefix_chars(a, b)
        prefixes.append(prefix)
        fractions.append(prefix / max(1, min(len(a), len(b))))
        counts["pairs"] += 1
        counts["exact_text"] += a == b
        counts["exact_response_hash"] += left["response_sha256"] == right["response_sha256"]
        counts["same_prediction"] += left["prediction"] == right["prediction"]
        counts["same_correctness"] += left["correct"] == right["correct"]
        counts["common_first_128_chars"] += prefix >= 128
        counts["common_first_512_chars"] += prefix >= 512
    return {
        **dict(sorted(counts.items())),
        "median_common_prefix_chars": median(prefixes) if prefixes else None,
        "median_common_prefix_fraction_of_shorter_text": median(fractions) if fractions else None,
    }


def analyze(root: Path = ROOT) -> dict:
    audit_path = root / "hotpath-quality-cache10r13-dual-audit.json"
    if sha256(audit_path) != AUDIT_SHA256:
        raise ValueError("frozen r13 dual-audit hash drift")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit["evidence_valid"] is not True:
        raise ValueError("r13 quality evidence invalid")
    baseline, candidate = Path(audit["baseline"]["root"]), Path(audit["candidate"]["root"])
    for arm, path in ((audit["baseline"], baseline), (audit["candidate"], candidate)):
        if sha256(path / "arm-result.json") != arm["arm_result_sha256"]:
            raise ValueError(f"arm-result hash drift: {path}")
    cold = {(row["index"], row["repetition"])
            for row in audit["strict_c1_c2_hot_coverage"]["cold_issues"]}
    if len(cold) != 13:
        raise ValueError("frozen cold-request cardinality drift")
    buckets: dict[str, list[tuple[dict, dict]]] = {
        "baseline_within": [], "candidate_within": [],
        "baseline_within_matched_hot": [], "candidate_within_hot_only": [],
        "cross_arm_hot": [], "cross_arm_cold": [],
    }
    samples: Counter[str] = Counter()
    for index in range(127):
        prior = json.loads((baseline / "samples" / f"{index:03}.json").read_text(encoding="utf-8"))
        treated = json.loads((candidate / "samples" / f"{index:03}.json").read_text(encoding="utf-8"))
        if (prior["index"] != index or treated["index"] != index
                or prior["sample_id"] != treated["sample_id"]
                or prior["prompt_sha256"] != treated["prompt_sha256"]):
            raise ValueError(f"sample identity drift: {index}")
        by_arm: list[dict[int, dict]] = []
        within_medians: dict[str, float] = {}
        for arm, name in ((prior, "baseline"), (treated, "candidate")):
            rows = {int(row["repetition"]): row for row in arm["scores"]}
            if len(arm["scores"]) != 3 or set(rows) != {1, 2, 3}:
                raise ValueError(f"repetition identity drift: {name} {index}")
            samples[f"{name}_unanimous_prediction"] += len({row["prediction"] for row in rows.values()}) == 1
            samples[f"{name}_unanimous_correctness"] += len({row["correct"] for row in rows.values()}) == 1
            within_prefixes = []
            for left, right in ((1, 2), (1, 3), (2, 3)):
                buckets[f"{name}_within"].append((rows[left], rows[right]))
                within_prefixes.append(common_prefix_chars(
                    rows[left]["response_text"], rows[right]["response_text"]))
            within_medians[name] = median(within_prefixes)
            by_arm.append(rows)
        samples["baseline_within_prefix_longer"] += within_medians["baseline"] > within_medians["candidate"]
        samples["candidate_within_prefix_longer"] += within_medians["candidate"] > within_medians["baseline"]
        samples["within_prefix_tie"] += within_medians["baseline"] == within_medians["candidate"]
        for left, right in ((1, 2), (1, 3), (2, 3)):
            if (index, left) not in cold and (index, right) not in cold:
                buckets["baseline_within_matched_hot"].append(
                    (by_arm[0][left], by_arm[0][right]))
                buckets["candidate_within_hot_only"].append(
                    (by_arm[1][left], by_arm[1][right]))
        for repetition in (1, 2, 3):
            base, hypic = by_arm[0][repetition], by_arm[1][repetition]
            if base["request_sha256"] != hypic["request_sha256"]:
                raise ValueError(f"paired request drift: {index}:{repetition}")
            cohort = "cold" if (index, repetition) in cold else "hot"
            buckets[f"cross_arm_{cohort}"].append((base, hypic))
    output = {name: bucket_summary(rows) for name, rows in buckets.items()}
    if (output["baseline_within"]["pairs"] != 381
            or output["candidate_within"]["pairs"] != 381
            or output["baseline_within_matched_hot"]["pairs"]
            != output["candidate_within_hot_only"]["pairs"]
            or output["cross_arm_hot"]["pairs"] != 368
            or output["cross_arm_cold"]["pairs"] != 13):
        raise ValueError("paired cardinality drift")
    return {
        "schema": "hypic-r13-response-variability/v1",
        "quality_audit_sha256": AUDIT_SHA256,
        "scope": "descriptive within-arm and cross-arm text/answer variability; no causal attribution or quality reclassification",
        "sample_counts": dict(sorted(samples.items())),
        "pair_buckets": output,
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), sort_keys=True))
