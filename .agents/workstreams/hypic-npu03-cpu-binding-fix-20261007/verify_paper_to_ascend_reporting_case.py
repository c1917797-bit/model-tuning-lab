#!/usr/bin/env python3
"""Read-only replay of the HYPIC reporting case; never infers a final report."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def git(*args: str) -> str:
    result = subprocess.run(("git", *args), cwd=REPO, text=True,
                            capture_output=True, check=False)
    require(result.returncode == 0, result.stderr)
    return result.stdout.strip()


def checked_bytes(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected,
            f"SHA256 drift: {path}")
    return raw


def main() -> int:
    require(git("rev-parse", "origin/main") == MAIN, "main moved")
    for path, blob in (
        (".agents/skills/paper-to-ascend-reporting/SKILL.md",
         "7902b3f9c96ebd6b77a35b328333ad3834fe4a9f"),
        (".agents/skills/paper-to-ascend-reporting/references/report-template.md",
         "40582e499b5589893524df3b74aabfeebe040f8c"),
        (".agents/skills.registry.yaml",
         "2611864bbcf719d57920aae03ff9eb85521526b4"),
    ):
        require(git("rev-parse", f"{MAIN}:{path}") == blob,
                f"main reporting contract drift: {path}")

    performance = json.loads(checked_bytes(
        ROOT / "performance-independent-audit.json",
        "de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1"))
    require(performance["all_six_units_valid"] is True
            and performance["quality_decision"] == "not-measured"
            and abs(performance["paper_effect"]["tpot_saved_pct"]
                    - 22.35616395806199) < 1e-8,
            "historical performance attribution drift")
    natural = json.loads(checked_bytes(
        ROOT / "quality-context-41984-clean2/quality-natural-scope-audit.json",
        "61bcccd926459b8ee57cfc3860a5b30c581c7e7b525fe3b746b52146c2c0dbf0"))
    require(natural["all_twelve_rows_and_receipts_valid"] is True
            and natural["formal_acceptance_claim"] is False
            and natural["activation"]["distinct_worker_hot_pids"] == [],
            "natural quality scope drift")

    env = os.environ.copy()
    env["HYPIC_STRESS_AUDIT_CAMPAIGN"] = "cache10r12"
    result = subprocess.run(
        (sys.executable, "-B", str(HERE / "audit_cache10r11_stress.py")),
        cwd=HERE, env=env, text=True, capture_output=True, check=False)
    require(result.returncode == 2 and bool(result.stdout.strip()),
            f"r12 independent audit did not reach expected negative gate: {result.stderr}")
    r12 = json.loads(result.stdout)
    require(r12["reason"] == "scored-request-hot-path-proof-missing"
            and r12["evidence_sha256"] ==
            "4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60"
            and r12["scored_rows"] == 57
            and r12["diagnostic"]["four_worker_verified_requests"] == 52
            and r12["guard_samples"] == 279,
            "r12 strict activation/isolation boundary drift")

    report = (HERE / "PAPER_TO_ASCEND_REPORTING_CASE_20261009.md").read_text()
    for required in ("Status: **progress / partial-evidence**",
                     "Current measured r12", "Historical same-lane reference",
                     "Historical natural-task reference", "Paper claim",
                     "not measured", "no no-cache arm",
                     "final-report completion gate is", "Forbidden:"):
        require(required in report, f"report boundary absent: {required}")
    print(json.dumps({
        "schema": "paper-to-ascend-reporting-real-task-case/v1",
        "historical_performance_units": 6,
        "historical_natural_quality_units": 12,
        "r12_scored": 57,
        "r12_four_worker_hot": 52,
        "current_matched_quality_pair": False,
        "final_report_ready": False,
        "long_term_acceptance": "partial-evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
