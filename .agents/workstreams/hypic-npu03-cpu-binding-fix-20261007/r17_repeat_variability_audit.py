#!/usr/bin/env python3
"""Read-only exploratory repeat-variability audit of terminal r17 artifacts."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from math import comb
from pathlib import Path


ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
AUDIT = ROOT / "hypic-r17-cap1024-full-quality-audit.json"
AUDIT_SHA256 = "493f9773d31a49e4f0b7e9c7ba73ea12e9722b4a7409e95c5ea05965b12853b3"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def arm_rows(audit: dict, field: str, arm: str) -> list[dict]:
    record = audit[field]
    root = Path(record["root"])
    require(root.parent == ROOT and root.name.endswith(
        "baseline" if arm == "no-cache" else "hypic"), "r17 root drift")
    require(sha256(root / "contract.json") == record["contract_sha256"]
            and sha256(root / "arm-result.json") == record["arm_result_sha256"],
            f"{arm}: terminal receipt drift")
    rows = []
    for index in range(127):
        sample = read(root / "samples" / f"{index:03d}.json")
        scores = sample.get("scores", [])
        require(sample.get("index") == index and sample.get("arm") == arm
                and len(scores) == 3
                and [s.get("repetition") for s in scores] == [1, 2, 3],
                f"{arm}: sample {index} identity drift")
        for score in scores:
            response = score.get("response_text")
            require(isinstance(response, str)
                    and score.get("response_sha256") ==
                        hashlib.sha256(response.encode("utf-8")).hexdigest()
                    and isinstance(score.get("correct"), bool)
                    and score.get("finish_reason") in {"stop", "length"},
                    f"{arm}: sample {index} raw response drift")
        rows.append(sample)
    require(sum(s["correct"] for x in rows for s in x["scores"]) ==
            record["correct"]
            and sum(s["finish_reason"] == "length"
                    for x in rows for s in x["scores"]) == record["length_limit"]
            and len(rows) * 3 == record["scored_rows"] == 381,
            f"{arm}: terminal aggregate drift")
    return rows


def main() -> None:
    require(sha256(AUDIT) == AUDIT_SHA256, "immutable r17 audit hash drift")
    audit = read(AUDIT)
    require(audit.get("evidence_valid") is True
            and audit.get("source_commit") ==
                "3ad0967589304cd8fc4e7cff02f48ecc6125c89f",
            "r17 audit identity drift")
    baseline = arm_rows(audit, "baseline", "no-cache")
    candidate = arm_rows(audit, "candidate", "hypic-only")
    paired_variability = Counter()
    paired_flips = Counter()
    stable_text = Counter()
    mixed_length = Counter()
    exact_cross_arm_text = 0
    for left, right in zip(baseline, candidate):
        require((left["sample_id"], left["prompt_sha256"],
                 left["prompt_tokens"], left["reference"]) ==
                (right["sample_id"], right["prompt_sha256"],
                 right["prompt_tokens"], right["reference"]),
                "r17 paired sample identity drift")
        a, b = left["scores"], right["scores"]
        unstable_a = len({s["correct"] for s in a}) > 1
        unstable_b = len({s["correct"] for s in b}) > 1
        paired_variability[(unstable_a, unstable_b)] += 1
        for arm, scores in (("no-cache", a), ("hypic-only", b)):
            stable_text[arm] += len({s["response_sha256"] for s in scores}) == 1
            mixed_length[arm] += len({s["finish_reason"] for s in scores}) > 1
        for first, second in zip(a, b):
            paired_flips["gain" if second["correct"] and not first["correct"]
                         else "loss" if first["correct"] and not second["correct"]
                         else "same"] += 1
            exact_cross_arm_text += (
                first["response_sha256"] == second["response_sha256"])
    candidate_only = paired_variability[(False, True)]
    baseline_only = paired_variability[(True, False)]
    discordant = candidate_only + baseline_only
    exploratory_p = min(1.0, 2 * sum(comb(discordant, k)
                                     for k in range(min(candidate_only,
                                                        baseline_only) + 1))
                        / 2 ** discordant)
    print(json.dumps({
        "schema": "hypic-r17-repeat-variability-exploratory/v1",
        "immutable_audit_sha256": AUDIT_SHA256,
        "scope": "post-hoc cap-1024/c8 repeat variability; not r18 acceptance",
        "paired_variability": {
            "neither": paired_variability[(False, False)],
            "candidate_only": candidate_only,
            "baseline_only": baseline_only,
            "both": paired_variability[(True, True)],
        },
        "paired_correct_flips": dict(paired_flips),
        "identical_text_across_arms": exact_cross_arm_text,
        "within_arm_identical_text_samples": dict(stable_text),
        "within_arm_mixed_length_samples": dict(mixed_length),
        "exploratory_mcnemar_exact_two_sided_p": exploratory_p,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
