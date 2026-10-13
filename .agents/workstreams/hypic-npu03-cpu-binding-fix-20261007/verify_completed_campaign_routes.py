#!/usr/bin/env python3
"""Read-only regression for five stale HYPIC next-action routes; not Skill acceptance."""
import hashlib
import json
from pathlib import Path

WS = Path(__file__).resolve().parent
CAMPAIGN = "current4429-performance-20261013"
AGGREGATE_SHA = "67ba6cf14fc9bed993acbdf421eb438f22d56957f3e56baad170a4bb871e53fe"
EXPECTED = {
 "ascend-canary-implementation": "partial-evidence",
 "ascend-npu-environment-orientation": "partial-evidence",
 "ascend-inference-tuning-loop": "partial-evidence",
 "ascend-model-quality-evaluation": "partial-evidence",
 "paper-ingestion": "verified",
}
STALE = (
 "already-running native recovery controls",
 "on a fresh, actually clean physical npu0-3 window",
 "immediately re-prove direct routing and physical process/port state",
 "is in progress under current_source_performance_checkpoint",
 "pending same-source performance decision",
)

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def check(checkpoint, cases, aggregate):
    require(checkpoint["campaign"] == CAMPAIGN
            and checkpoint["state"] == "six-phases-audited-performance-complete"
            and checkpoint["completed_phases"] == 6
            and checkpoint["controller_operation"] is None,
            "not the completed campaign")
    require(aggregate["campaign"] == CAMPAIGN
            and aggregate["all_six_phases_valid"] is True
            and len(aggregate["phases"]) == 6,
            "terminal raw audit missing")
    require(checkpoint["source_commit"] == aggregate["source_commit"],
            "source identity mismatch")
    require(checkpoint["quality_decision"] == aggregate["quality_decision"]
            == "REJECT_OR_QUALIFY"
            and checkpoint["deployment_allowed"] is False
            and aggregate["deployment_allowed"] is False,
            "quality/deployment verdict drift")
    require(set(cases) == set(EXPECTED), "case inventory drift")
    for name, acceptance in EXPECTED.items():
        case = cases[name]
        policy = case["current_campaign_resume"]
        require(case["skill"] == name and case["long_term_acceptance"] == acceptance,
                "routing repair cannot promote Skill")
        require(policy == {
            "campaign": CAMPAIGN,
            "aggregate_sha256": AGGREGATE_SHA,
            "next_action_kind": "offline-evidence-review",
            "new_device_work_authorized": False,
            "historical_observations_unchanged": True,
            "regression": "verify_completed_campaign_routes.py",
        }, "unsafe or stale resume policy")
        require(case["next_gate"] and not any(x in case["next_gate"].lower() for x in STALE),
                "stale executable next_gate")
    return {"checked_case_routes": len(cases), "new_device_work_authorized": False,
            "skill_acceptance_promoted": False, "quality_decision_changed": False}

def main():
    task = json.loads((WS / "task.json").read_text())
    checkpoint = task["current_source_performance_checkpoint"]
    path = Path(checkpoint["aggregate"]["path"])
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == AGGREGATE_SHA
            == checkpoint["aggregate"]["sha256"], "raw aggregate drift")
    cases = {name: json.loads((WS / "skill-cases" / (name + ".json")).read_text())
             for name in EXPECTED}
    print(json.dumps(check(checkpoint, cases, json.loads(raw)), sort_keys=True))

if __name__ == "__main__":
    main()
