#!/usr/bin/env python3
"""Replay the immutable six-phase HYPIC matched-performance audit."""

from audit_hotpath_cache10_matched_performance import (
    ORDER,
    OUT,
    QUALITY_AUDIT,
    ROOT,
    audit_phase,
    load,
    sha256,
)


EXPECTED_AUDIT_SHA256 = "d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062"
EXPECTED_RETRY21_RESULT_SHA256 = (
    "a0c88a883dda5513c4fe579e70d5be0028bb338963bcd9ee1d7d5f6d1183e05e"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    require(OUT.is_file(), "six-phase independent audit is absent")
    require(sha256(OUT) == EXPECTED_AUDIT_SHA256, "independent audit hash drift")
    report = load(OUT)
    quality_sha = sha256(ROOT / QUALITY_AUDIT)
    phases = [audit_phase(arm, phase, quality_sha) for arm, phase in ORDER]
    observed = {(item["arm"], item["phase"]): item for item in phases}
    frozen = {(item["arm"], item["phase"]): item for item in report["phases"]}
    require(set(observed) == set(frozen) == set(ORDER), "phase set drift")
    for key in ORDER:
        require(observed[key]["root"] == frozen[key]["root"], f"{key}: root drift")
        require(
            observed[key]["result_sha256"] == frozen[key]["result_sha256"],
            f"{key}: result hash drift",
        )
        require(observed[key]["metrics"] == frozen[key]["metrics"], f"{key}: metric drift")
    retry21 = observed[("hypic-only", "repeat3")]
    require(
        retry21["result_sha256"] == EXPECTED_RETRY21_RESULT_SHA256,
        "retry21 result hash drift",
    )
    require(
        retry21["request_coverage"]["four_worker_verified_requests"] == 40,
        "retry21 four-worker coverage drift",
    )
    require(report["all_six_phases_valid"] is True, "six-phase validity drift")
    require(report["deployed_effect_screen_pass"] is True, "effect screen drift")
    require(
        report["strict_c1_c2_hot_coverage"]
        == {
            "decision": "PASS",
            "expected_measured_requests": 120,
            "four_worker_verified_measured_requests": 120,
        },
        "strict performance hot coverage drift",
    )
    require(
        report["deployed_quality_decision"] == "REJECT_OR_QUALIFY"
        and report["strict_quality_decision"] == "NOT_ACCEPTED_HOT_COVERAGE",
        "quality boundary drift",
    )
    print(
        "six-phase HYPIC performance audit replay passed: "
        "6/6 phases, 120/120 strict hot requests, quality remains qualified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
