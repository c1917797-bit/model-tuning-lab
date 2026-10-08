#!/usr/bin/env python3
"""Read-only replay of r11/r12 stress differences after both raw audits."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
CAMPAIGNS = ("cache10r11", "cache10r12")
EXPECTED_AUDIT_SHA = {
    "cache10r11": "a9164c287c0d03c4220b404ee130cca5a677f83839882fc0f1da48e456421fcb",
    "cache10r12": "4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60",
}


def load(campaign: str) -> dict:
    env = os.environ.copy()
    env["HYPIC_STRESS_AUDIT_CAMPAIGN"] = campaign
    audited = subprocess.run(
        [sys.executable, "-B", str(HERE / "audit_cache10r11_stress.py")],
        cwd=HERE, env=env, capture_output=True, text=True, check=False,
    )
    if audited.returncode != 2 or not audited.stdout.strip():
        raise RuntimeError(f"{campaign} independent audit state changed: {audited.stderr}")
    summary = json.loads(audited.stdout)
    if (summary.get("reason") != "scored-request-hot-path-proof-missing"
            or summary.get("evidence_sha256") != EXPECTED_AUDIT_SHA[campaign]
            or summary.get("scored_rows") != 57
            or summary.get("not_quality_verdict") is not True):
        raise RuntimeError(f"{campaign} independent audit identity drift")
    sample_dir = ROOT / f"quality-context-41984-hotpath-{campaign}-stress-hypic/samples"
    rows = {int(path.stem): json.loads(path.read_text(encoding="utf-8"))
            for path in sample_dir.glob("*.json")}
    if sorted(rows) != [*range(75, 92), 107, 111]:
        raise RuntimeError(f"{campaign} sample identity drift")
    return {"audit": summary, "rows": rows}


def main() -> int:
    old, new = (load(campaign) for campaign in CAMPAIGNS)
    old_scores = {(index, score["repetition"]): score
                  for index, row in old["rows"].items() for score in row["scores"]}
    new_scores = {(index, score["repetition"]): score
                  for index, row in new["rows"].items() for score in row["scores"]}
    ids = sorted(old_scores)
    if ids != sorted(new_scores) or len(ids) != 57:
        raise RuntimeError("paired scored ID set drift")
    gained = [list(key) for key in ids
              if not old_scores[key]["correct"] and new_scores[key]["correct"]]
    lost = [list(key) for key in ids
            if old_scores[key]["correct"] and not new_scores[key]["correct"]]
    same_scored = sum(old_scores[key]["response_sha256"]
                      == new_scores[key]["response_sha256"] for key in ids)
    warm_cross = sum(
        old["rows"][index]["warm"][j]["response_sha256"]
        == new["rows"][index]["warm"][j]["response_sha256"]
        for index in old["rows"] for j in range(2)
    )
    warm_within = [
        sum(row["warm"][0]["response_sha256"] == row["warm"][1]["response_sha256"]
            for row in arm["rows"].values()) for arm in (old, new)
    ]
    report = {
        "schema": "hypic-r11-r12-stress-comparison/v1",
        "not_paired_quality_or_causal_verdict": True,
        "scored_rows": len(ids),
        "r11_correct": sum(old_scores[key]["correct"] for key in ids),
        "r12_correct": sum(new_scores[key]["correct"] for key in ids),
        "r11_four_worker_hot": old["audit"]["diagnostic"]["four_worker_verified_requests"],
        "r12_four_worker_hot": new["audit"]["diagnostic"]["four_worker_verified_requests"],
        "same_scored_response_sha": same_scored,
        "cross_source_same_one_token_observations": warm_cross,
        "within_source_same_one_token_pairs": warm_within,
        "gained_correct": gained,
        "lost_correct": lost,
    }
    expected = (27, 22, 53, 52, 0, 38, [19, 19], 2, 7)
    observed = (report["r11_correct"], report["r12_correct"],
                report["r11_four_worker_hot"], report["r12_four_worker_hot"],
                same_scored, warm_cross, warm_within, len(gained), len(lost))
    if observed != expected:
        raise RuntimeError(f"frozen r11/r12 comparison drift: {observed!r}")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
