#!/usr/bin/env python3
"""Read-only post-run replay of preregistered r14 and fixed r13 subset."""

from __future__ import annotations

import json
from pathlib import Path

from analyze_r13_response_variability import bucket_summary
from audit_cache10r14_variability import (
    BASE, CAND, INDEXES, OUT, audit_arm, frozen_cases, frozen_pair_seam,
    load, quality, require,
)


R13_AUDIT = quality.ROOT / "hotpath-quality-cache10r13-dual-audit.json"
R13_SHA = "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b"
R14_SHA = "c69692be92d70168a58fd896828a1ecadbe9bd4e0177200b728e2f23871b4cf4"
EXPECTED = {
    "r13_c8": {"baseline": (1, 416, 3), "candidate": (0, 85, 3)},
    "r14_c1": {"baseline": (1, 1229, 3), "candidate": (3, 1901, 3)},
}


def selected_rows(root: Path) -> dict[int, dict]:
    return {
        index: load(root / "samples" / f"{index:03d}.json")
        for index in INDEXES
    }


def summarize(rows: dict[int, dict]) -> tuple[dict, int]:
    pairs = []
    correct = 0
    for index in INDEXES:
        scores = rows[index]["scores"]
        require(len(scores) == 3, f"sample {index}: repetition drift")
        pairs.extend(((scores[0], scores[1]), (scores[0], scores[2]),
                      (scores[1], scores[2])))
        correct += sum(bool(score["correct"]) for score in scores)
    return bucket_summary(pairs), correct


def main() -> int:
    require(quality.sha256(R13_AUDIT) == R13_SHA, "r13 audit hash drift")
    require(quality.sha256(OUT) == R14_SHA, "r14 audit hash drift")
    r13, r14 = load(R13_AUDIT), load(OUT)
    require(r13["evidence_valid"] is True and r14["evidence_valid"] is True,
            "source audit invalid")
    require(r13["all_request_quality"]["decision"] == "REJECT_OR_QUALIFY"
            and r14["r13_quality_decision_unchanged"] == "REJECT_OR_QUALIFY",
            "frozen quality verdict drift")
    require(r14["sample_indexes"] == list(INDEXES)
            and r14["pair_seam"] == frozen_pair_seam(),
            "r14 selection or one-switch seam drift")
    all_cases, evaluator = frozen_cases()
    cases = [all_cases[index] for index in INDEXES]
    baseline = audit_arm(BASE, "no-cache", cases, evaluator)
    candidate = audit_arm(CAND, "hypic-only", cases, evaluator)
    require(baseline["summary"] == r14["baseline"]
            and candidate["summary"] == r14["candidate"]
            and candidate["summary"]["request_hot_coverage"][
                "four_worker_post_repair_verified_requests"] == 9,
            "r14 independent terminal replay drift")
    require(baseline["fingerprint"] == candidate["fingerprint"],
            "r14 service fingerprint drift")
    roots = {
        "r13_c8": {
            "baseline": Path(r13["baseline"]["root"]),
            "candidate": Path(r13["candidate"]["root"]),
        },
        "r14_c1": {"baseline": BASE, "candidate": CAND},
    }
    selected_cold = [
        issue for issue in r13["strict_c1_c2_hot_coverage"]["cold_issues"]
        if issue["index"] in INDEXES
    ]
    require(not selected_cold, "r13 selected candidate IDs include cold requests")
    observations = {}
    for campaign, by_arm in roots.items():
        observations[campaign] = {}
        rowsets = {arm: selected_rows(root) for arm, root in by_arm.items()}
        for arm, root in by_arm.items():
            original_audit = r13 if campaign == "r13_c8" else r14
            require(quality.sha256(root / "arm-result.json")
                    == original_audit[arm]["arm_result_sha256"],
                    f"{campaign}/{arm}: arm-result hash drift")
            summary, correct = summarize(rowsets[arm])
            exact, prefix, expected_correct = EXPECTED[campaign][arm]
            require(summary["pairs"] == 9
                    and summary["exact_text"] == exact
                    and summary["median_common_prefix_chars"] == prefix
                    and summary["same_prediction"] == 9
                    and summary["same_correctness"] == 9
                    and correct == expected_correct,
                    f"{campaign}/{arm}: selected response comparison drift")
            observations[campaign][arm] = {
                "exact_text_pairs": exact,
                "median_common_prefix_chars": prefix,
                "same_prediction_pairs": 9,
                "correct_responses": correct,
            }
        for index in INDEXES:
            left, right = rowsets["baseline"][index], rowsets["candidate"][index]
            for key in ("index", "sample_id", "prompt_sha256", "prompt_tokens",
                        "segment_ends", "reference"):
                require(left[key] == right[key],
                        f"{campaign} sample {index}: paired input drift")
            require([score["request_sha256"] for score in left["scores"]]
                    == [score["request_sha256"] for score in right["scores"]],
                    f"{campaign} sample {index}: paired scored payload drift")
    for index in INDEXES:
        for arm in ("baseline", "candidate"):
            old, new = (selected_rows(roots[campaign][arm])[index]
                        for campaign in ("r13_c8", "r14_c1"))
            for key in ("index", "sample_id", "prompt_sha256", "prompt_tokens",
                        "segment_ends", "reference"):
                require(old[key] == new[key],
                        f"{arm} sample {index}: cross-campaign input drift")
            require([score["request_sha256"] for score in old["scores"]]
                    == [score["request_sha256"] for score in new["scores"]],
                    f"{arm} sample {index}: cross-campaign payload drift")
    print(json.dumps({
        "schema": "hypic-cache10r14-variability-terminal-replay/v1",
        "evidence_valid": True,
        "r13_quality_decision_unchanged": "REJECT_OR_QUALIFY",
        "r14_candidate_request_hot_coverage": "9/9",
        "r13_selected_candidate_cold_requests": 0,
        "selected_sample_observations": observations,
        "causal_root_proven": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
