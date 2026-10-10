#!/usr/bin/env python3
"""Read-only replay of the immutable r16 original-source quality verdict."""

from __future__ import annotations

import hashlib
import json

import audit_r16_original_source_full as r16


EXPECTED_AUDIT_SHA256 = (
    "52914becb93266ac4a27e8491b40bf8456b566ee8f828038250098bfec33a4ee"
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    raw = r16.OUT.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPECTED_AUDIT_SHA256,
            "immutable r16 audit hash drift")
    report = json.loads(raw)
    cases, evaluator = r16.frozen_cases()
    require(len(cases) == 127 and r16.frozen_pair_seam() == report["pair_seam"],
            "frozen case or pair seam drift")
    baseline = r16.audit_arm(
        r16.BASE, "no-cache", cases, evaluator,
        require_source_attestation=True)
    candidate = r16.audit_arm(
        r16.CAND, "hypic-only", cases, evaluator,
        allow_hot_shortfall=True, require_source_attestation=True)
    paired = r16.decide(baseline, candidate)
    without_rows = lambda arm: {key: value for key, value in arm.items()
                                if key != "rows"}
    require(without_rows(baseline) == report["baseline"]
            and without_rows(candidate) == report["candidate"]
            and paired == report["all_request_quality"],
            "raw roots do not replay to frozen paired audit")
    require(report["evidence_valid"] is True
            and report["source_commit"] == r16.SOURCE_COMMIT
            and report["quality_decision"] == "REJECT_OR_QUALIFY"
            and (baseline["correct"], candidate["correct"]) == (224, 210)
            and candidate["verified_hot_requests"] == 364
            and (baseline["guard_samples"], candidate["guard_samples"]) ==
                (999, 1078),
            "r16 terminal decision/evidence drift")
    print(json.dumps({
        "r16_replay_valid": True,
        "quality_decision": report["quality_decision"],
        "correct_baseline_candidate": [224, 210],
        "aggregate_hot": [364, 381],
        "audit_sha256": EXPECTED_AUDIT_SHA256,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
