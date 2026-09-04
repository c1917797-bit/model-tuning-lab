#!/usr/bin/env python3

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/analyze_qwen35_candidate_vs_original.py"
ORIGINAL = Path(
    "/cache/austinov/eval-runs/"
    "exp-20260904-qwen35-query-rewrite-3x-e2e/"
    "tp4-dev-decodegraph/quick32-v3"
)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    candidate = root / "candidate"
    candidate.mkdir()
    for concurrency in (1, 5, 8, 16):
        source = ORIGINAL / f"c{concurrency}-r1.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["ttft_ms"]["p50"] *= 0.49
        payload["tpot_ms"]["p50"] *= 0.49
        (candidate / source.name).write_text(
            json.dumps(payload), encoding="utf-8"
        )
    report_path = root / "decision.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--candidate-dir",
            str(candidate),
            "--candidate-id",
            "fixture",
            "--output",
            str(report_path),
        ],
        check=False,
    )
    assert result.returncode == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["final_target_met"] is True
    assert report["decision"] == "final-target-met"
    assert len(report["artifact_sha256"]) == 8

    shutil.copyfile(ORIGINAL / "c1-r1.json", candidate / "c1-r1.json")
    payload = json.loads((candidate / "c1-r1.json").read_text())
    payload["response_sha256"][0] = "0" * 64
    (candidate / "c1-r1.json").write_text(json.dumps(payload))
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--candidate-dir",
            str(candidate),
            "--candidate-id",
            "incorrect-fixture",
            "--output",
            str(report_path),
        ],
        check=False,
    )
    assert result.returncode == 3
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["decision"] == "hold-exact-hash-drift"
    assert report["correctness_exact_hash_match"] is False
    assert report["correctness_gate_status"] == "semantic-business-check-required"

print("PASS: fixed-original analyzer")
