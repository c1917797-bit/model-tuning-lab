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

    control = root / "semantic-control"
    semantic_candidate = root / "semantic-candidate"
    control.mkdir()
    semantic_candidate.mkdir()
    quality = {
        "reference_field": "answer",
        "raw_exact_matches": 24,
        "normalized_whitespace_exact_matches": 25,
        "normalized_character_similarity": {
            "mean": 0.94,
            "p50": 0.95,
        },
    }
    for concurrency in (1, 5, 8, 16):
        source = ORIGINAL / f"c{concurrency}-r1.json"
        control_payload = json.loads(source.read_text(encoding="utf-8"))
        control_payload["reference_quality"] = quality
        (control / source.name).write_text(json.dumps(control_payload))
        candidate_payload = json.loads(source.read_text(encoding="utf-8"))
        candidate_payload["ttft_ms"]["p50"] *= 0.49
        candidate_payload["tpot_ms"]["p50"] *= 0.49
        candidate_payload["response_sha256"] = ["1" * 64] * 32
        candidate_payload["reference_quality"] = {
            **quality,
            "raw_exact_matches": 23,
            "normalized_whitespace_exact_matches": 24,
            "normalized_character_similarity": {
                "mean": 0.925,
                "p50": 0.935,
            },
        }
        (semantic_candidate / source.name).write_text(
            json.dumps(candidate_payload)
        )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--candidate-dir",
            str(semantic_candidate),
            "--candidate-id",
            "semantic-pass-fixture",
            "--semantic-control-dir",
            str(control),
            "--require-retained-tpot-improvement",
            "--output",
            str(report_path),
        ],
        check=False,
    )
    assert result.returncode == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["decision"] == "final-target-met"
    assert report["correctness_exact_hash_match"] is False
    assert report["semantic_quality_gate_met"] is True
    assert report["retained_tpot_improvement_met"] is True
    assert len(report["artifact_sha256"]) == 12

    degraded = json.loads(
        (semantic_candidate / "c5-r1.json").read_text(encoding="utf-8")
    )
    degraded["reference_quality"]["normalized_character_similarity"][
        "mean"
    ] = 0.80
    (semantic_candidate / "c5-r1.json").write_text(json.dumps(degraded))
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--candidate-dir",
            str(semantic_candidate),
            "--candidate-id",
            "semantic-fail-fixture",
            "--semantic-control-dir",
            str(control),
            "--require-retained-tpot-improvement",
            "--output",
            str(report_path),
        ],
        check=False,
    )
    assert result.returncode == 3
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["decision"] == "hold-semantic-quality-regression"
    assert report["semantic_quality_gate_met"] is False

    for concurrency in (1, 5, 8, 16):
        path = candidate / f"c{concurrency}-r1.json"
        if path.exists():
            path.unlink()
    shutil.copyfile(ORIGINAL / "c1-r1.json", candidate / "c1-r1.json")
    partial = json.loads((ORIGINAL / "c5-r1.json").read_text())
    partial["completed"] = 25
    partial["errors"] = 7
    partial["finish_reasons"] = {"stop": 25}
    partial["response_sha256"] = partial["response_sha256"][:25]
    partial["error_types"] = ["RuntimeError"]
    partial["error_reasons"] = {"stream stalled": 7}
    (candidate / "c5-r1.json").write_text(json.dumps(partial))
    candidate_run = root / "candidate-run.json"
    candidate_run.write_text(
        json.dumps(
            {
                "status": "failed",
                "failed_cell": {"concurrency": 5, "repetition": 1},
            }
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--candidate-dir",
            str(candidate),
            "--candidate-id",
            "runtime-failure-fixture",
            "--candidate-run",
            str(candidate_run),
            "--allow-incomplete",
            "--output",
            str(report_path),
        ],
        check=False,
    )
    assert result.returncode == 4
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["decision"] == "reject-runtime-failure"
    assert report["runtime_gate_met"] is False
    assert report["candidate_run_status"] == "failed"
    assert report["cells"]["5"]["completed_requests"] == 25
    assert report["cells"]["8"]["status"] == "not-run"
    assert report["correctness_gate_status"] == "not-evaluable-runtime-failure"

print("PASS: fixed-original analyzer")
