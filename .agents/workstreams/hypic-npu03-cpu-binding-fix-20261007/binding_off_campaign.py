#!/usr/bin/env python3
"""Run both independently guarded quality arms in the frozen paired order."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from binding_off_quality import QROOT, preflight, write_json

ARMS = ("no-cache", "hypic-only")
CONTROLLER = Path(__file__).with_name("binding_off_quality.py")


def receipt(stage: str, **details: object) -> None:
    QROOT.mkdir(parents=True, exist_ok=True)
    record = {"schema": "hypic-bindingoff-quality-campaign/v1", "stage": stage,
              "at_utc": datetime.now(timezone.utc).isoformat(), **details}
    write_json(QROOT / "campaign-status.json", record)
    print(json.dumps(record, sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    fingerprint = preflight()
    if not args.run:
        print(json.dumps({"arms": ARMS, "fingerprint": fingerprint}, sort_keys=True))
        return 0
    receipt("preflight-passed", arms=ARMS, fingerprint=fingerprint)
    for arm in ARMS:
        receipt("arm-starting", arm=arm)
        result = subprocess.run([sys.executable, str(CONTROLLER), "--arm", arm, "--run"],
                                check=False)
        if result.returncode:
            receipt("arm-failed", arm=arm, exit_code=result.returncode)
            return result.returncode
        receipt("arm-complete", arm=arm)
    receipt("both-arms-complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
