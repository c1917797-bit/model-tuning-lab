#!/usr/bin/env python3
"""Default read-only command planning. Explicit execution runs only frozen CPU selector."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from post_reference_contract import (AUDIT, CAPTURE, LOCK, MANIFEST, PLANS, PROJECT, REPO,
    absent_output, calibration_command, finalized, frozen_modules, full_evidence,
    manifest_identity, require, sha)

def prepare(python, output):
    frozen_modules()
    manifest_identity()
    absent_output(output)
    return {
        "schema": "damp-post-reference-preparation/v1", "status": "plan-only",
        "source_lock_present": LOCK.is_file(), "parent_result_present": (AUDIT/"RESULT.json").is_file(),
        "reference_admitted": False, "selector_executed": False,
        "manifest": str(MANIFEST), "capture_root": str(CAPTURE), "source_lock": str(LOCK),
        "command": calibration_command(python, output),
        "environment": {"PYTHONDONTWRITEBYTECODE": "1", "DAMP_CALIBRATION_CPU_ONLY": "1",
            "PYTHONPATH": str(PROJECT/"calibration")+":"+str(PROJECT/"collector")},
        "after_selector": "independent calibrated_plan_admission_v2; do not relabel offline plans for smoke PlanStore",
        "not_proven": ["actual final-plan NPU", "cache lifecycle", "model graph",
                       "matched E2E performance", "task accuracy", "model weight byte identity"]
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default="/usr/local/python3.12.13/bin/python3")
    parser.add_argument("--output-dir", type=Path, default=PLANS)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--source-lock-sha256")
    parser.add_argument("--parent-result-sha256")
    args = parser.parse_args()
    packet = prepare(args.python, args.output_dir)
    if not args.execute:
        print(json.dumps(packet, sort_keys=True, allow_nan=False)); return 0
    require(os.environ.get("DAMP_POST_REFERENCE_CPU_EXECUTE") == "1",
            "explicit CPU-only execute opt-in required; MAIN controls container/executable")
    # The adapter never signs SOURCE_LOCK or writes into original capture/evidence.
    capture = full_evidence(args.source_lock_sha256, args.parent_result_sha256)
    del capture
    env = dict(os.environ, **packet["environment"])
    env["ASCEND_RT_VISIBLE_DEVICES"] = ""
    env["CUDA_VISIBLE_DEVICES"] = ""
    child = subprocess.run(packet["command"], cwd=REPO, env=env, timeout=8*3600)
    require(child.returncode == 0, "selector failed; partial outputs remain nonservable")
    # Never claim plan tensors or NPU validation from a child exit alone.
    print(json.dumps({"status": "selector-returned-zero",
        "plan_index": str(args.output_dir/"PLAN_INDEX.json"),
        "plan_index_sha256": sha(args.output_dir/"PLAN_INDEX.json"),
        "calibrated_admission_pending": True, "serve_ready": False}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
