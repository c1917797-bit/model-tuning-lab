#!/usr/bin/env python3
"""Independently audit the reserve c8 stress gate; never emit a quality verdict."""

from __future__ import annotations

import json
import os

os.environ["HYPIC_HOTPATH_AUDIT_CAMPAIGN"] = "reserve"
STRESS_CAMPAIGN = os.environ.get("HYPIC_HOTPATH_QUALITY_CAMPAIGN", "reserve")
if STRESS_CAMPAIGN not in {"reserve", "reserve2"}:
    raise RuntimeError("unrecognized reserve stress campaign")

from hotpath_quality_audit import audit_arm, frozen_cases, quality, require


ROOT = quality.ROOT / ("quality-context-41984-hotpath-reserve-stress2-hypic"
                       if STRESS_CAMPAIGN == "reserve2" else
                       "quality-context-41984-hotpath-reserve-stress-hypic")


def main() -> int:
    cases, evaluator = frozen_cases()
    result = audit_arm(ROOT, "hypic-only", cases[:9], evaluator,
                       expected=9, mode="stress")
    require(result["fingerprint"].get("gpu_memory_utilization") == 0.85,
            "stress did not use the reserved common service setting")
    print(json.dumps({
        "schema": "hypic-hotpath-reserve-stress-audit/v1",
        "stress_pass": True,
        "not_quality_verdict": True,
        "scored_rows": result["scored_rows"],
        "verified_hot_requests": result["verified_hot_requests"],
        "guard_samples": result["guard_samples"],
        "contract_sha256": result["contract_sha256"],
        "arm_result_sha256": result["arm_result_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
