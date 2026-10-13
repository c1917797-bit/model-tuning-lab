#!/usr/bin/env python3
"""Prospective 4429e35 descriptive performance; immutable legacy primitives only."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import statistics

WS = Path(__file__).resolve().parent
ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
CAMPAIGN = "current4429-performance-20261013"
SOURCE = "/cache/cch/hypic_vllm_ascend-hotproof-20261008"
COMMIT = "4429e35177979c874bf053ab29789e4773f39b22"
DEADLINE = datetime.fromisoformat("2026-10-13T08:47:14+00:00")
QUALITY = ROOT / "hypic-r19-c32-2048-longbench-paired-audit.json"
QUALITY_SHA = "40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b"
PINS = {
 "binding_off_quality.py": "714012b683142201fc4cf40d734f4d48f53210d7ade93479bf550e27020db0c4",
 "binding_off_service.py": "73d2bfe0ce626ce0fc628337204cef4bfd6248a76f149f96175c31346f3f7c56",
 "hotpath_cache10_matched_performance.py": "110d393e2236e593243e528d2620c5ab3803b87d822273c575ec9292e0a4efd3",
 "audit_hotpath_cache10_matched_performance.py": "6ea2f64909c3601521f43cf40b2e9de14af9b72f8554fff9d90db15f0474aa6b",
 "hotpath_request_id_benchmark.py": "0d88b054a91e4985f131187d84899d76d57a1da1d97f842c2f51052534abc6ac",
}
ORDER = (("no-cache","screen"),("hypic-only","screen"),
         ("hypic-only","repeat2"),("no-cache","repeat2"),
         ("no-cache","repeat3"),("hypic-only","repeat3"))

def require(value, message):
    if not value:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def root_for(arm, phase):
    require((arm, phase) in ORDER, "unknown phase")
    return ROOT / f"performance-context-41984-{CAMPAIGN}-{arm}-{phase}"

def validate_inputs():
    for name, digest in PINS.items():
        require(sha(WS / name) == digest, f"frozen dependency drift: {name}")
    require(sha(QUALITY) == QUALITY_SHA, "r19 negative quality evidence changed")

def setup(arm, phase):
    validate_inputs()
    # Import an existing recognized cache10 configuration without touching its root;
    # then bind every mutable identity to this new, prospective campaign.
    os.environ["HYPIC_QUALITY_ATTEMPT"] = "hotpath-cache10perf-no-cache-screen"
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = SOURCE
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = COMMIT
    import binding_off_quality as q
    import binding_off_service as s
    import hotpath_cache10_matched_performance as p
    import audit_hotpath_cache10_matched_performance as audit
    attempt = f"hotpath-cache10-{CAMPAIGN}-{arm}-{phase}"
    q.ATTEMPT = attempt
    q.QROOT = root_for(arm, phase)
    q.EXPERIMENT = f"{CAMPAIGN}-{arm}-{phase}"
    q.RESERVE_ATTEMPTS = frozenset({attempt})
    p.SOURCE_ROOT, p.SOURCE_COMMIT = SOURCE, COMMIT
    p.entry_gate = lambda quality: QUALITY_SHA if sha(QUALITY) == QUALITY_SHA else fail_quality()
    # Independently audit earlier phases; never select a historical retry root.
    p.earlier_phases = lambda quality, a, ph: [
        audit.audit_phase(*previous, QUALITY_SHA)
        for previous in ORDER[:ORDER.index((a, ph))]]
    audit.SOURCE_ROOT, audit.SOURCE_COMMIT = SOURCE, COMMIT
    audit.root_for = root_for
    require(tuple(p.ORDER) == ORDER, "phase order drift")
    require(q.QROOT.name.startswith("performance-context-41984-current4429-"),
            "historical output root forbidden")
    return q, s, p, audit

def fail_quality():
    raise RuntimeError("frozen r19 audit changed")

def audit_one(arm, phase):
    _, _, _, audit = setup(arm, phase)
    return audit.audit_phase(arm, phase, QUALITY_SHA)

def audit_all():
    validate_inputs()
    phases = [audit_one(*pair) for pair in ORDER]
    require(len({p["container_id"] for p in phases}) == 6, "container reused")
    require(all(p["normalized_spec"] == phases[0]["normalized_spec"] for p in phases),
            "paired serving configuration differs")
    times = [datetime.fromisoformat(p["created_at_utc"]) for p in phases]
    require(times == sorted(times), "phase order differs")
    metrics = tuple(phases[0]["metrics"])
    per_arm = {a: [p["metrics"] for p in phases if p["arm"] == a]
               for a in ("no-cache", "hypic-only")}
    medians = {a: {k: statistics.median(row[k] for row in rows) for k in metrics}
               for a, rows in per_arm.items()}
    b, c = medians["no-cache"], medians["hypic-only"]
    hot = sum(p["request_coverage"]["four_worker_verified_requests"]
              for p in phases if p["arm"] == "hypic-only")
    require(0 <= hot <= 120, "hot coverage count invalid")
    report = {
      "schema": "hypic-current4429-descriptive-performance/v1",
      "campaign": CAMPAIGN, "source_commit": COMMIT,
      "all_six_phases_valid": True, "quality_audit_sha256": QUALITY_SHA,
      "quality_decision": "REJECT_OR_QUALIFY", "deployment_allowed": False,
      "purpose": "user-authorized speed characterization despite quality rejection",
      "physical_npus": [0,1,2,3], "performance_estimand": "all-request-deployed",
      "strict_hot_coverage": {"verified": hot, "expected": 120,
                              "decision": "PASS" if hot == 120 else "FAIL"},
      "medians": medians, "per_arm": per_arm,
      "paired_baseline_minus_candidate": [
        {k: per_arm["no-cache"][i][k]-per_arm["hypic-only"][i][k] for k in metrics}
        for i in range(3)],
      "effect": {
        "weighted_tpot_saved_ms": b["tpot_weighted_ms"]-c["tpot_weighted_ms"],
        "weighted_tpot_saved_pct": 100*(1-c["tpot_weighted_ms"]/b["tpot_weighted_ms"]),
        "ttft_p95_saved_s": (b["ttft_p95_ms"]-c["ttft_p95_ms"])/1000,
        "throughput_ratio": c["output_tokens_per_second"]/b["output_tokens_per_second"]},
      "phases": [{k:v for k,v in p.items() if k != "normalized_spec"} for p in phases]}
    output = ROOT / f"{CAMPAIGN}-audit.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"path": str(output), "sha256": sha(output),
                      "effect": report["effect"], "quality_decision": report["quality_decision"]}))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("no-cache","hypic-only"), default="no-cache")
    parser.add_argument("--phase", choices=("screen","repeat2","repeat3"), default="screen")
    parser.add_argument("--action", choices=("check","run","audit-phase","audit-all"), default="check")
    args = parser.parse_args()
    if args.action == "audit-all":
        audit_all()
        return
    q, s, p, audit = setup(args.arm, args.phase)
    if args.action == "audit-phase":
        print(json.dumps(audit.audit_phase(args.arm, args.phase, QUALITY_SHA), sort_keys=True))
        return
    require(not q.QROOT.exists(), "new root exists: do not rerun or overwrite")
    fingerprint = q.preflight()
    require(fingerprint["source_commit"] == COMMIT, "source identity drift")
    seam = p.pair_seam(q)
    require(s.sha256(s.BENCHMARK) == s.BENCHMARK_SHA, "frozen benchmark drift")
    if args.action == "check":
        print(json.dumps({"campaign": CAMPAIGN, "root":str(q.QROOT), "fingerprint":fingerprint,
                          "pair_seam":seam, "quality_decision":"REJECT_OR_QUALIFY",
                          "descriptive_performance_authorized":True},sort_keys=True))
        return
    require(datetime.now(timezone.utc) < DEADLINE, "deadline reached; no new phase")
    # Existing controller bounds startup/benchmark and always releases exact ownership.
    # Its r13 schema strings identify the reused record format, NOT r13 evidence.
    p.run_phase(q, s, args.arm, args.phase)

if __name__ == "__main__":
    main()

