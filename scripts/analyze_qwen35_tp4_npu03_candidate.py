#!/usr/bin/env python3
"""Compare a TP4/NPU0-3 candidate with the frozen three-repeat reference."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-summary", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--target-speedup", type=float, default=2.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    baseline = json.loads(args.baseline_summary.read_text())
    cells = {}
    runtime_ok = True
    performance_ok = True
    percentiles = ("p50", "p95", "p99")
    for concurrency in (1, 5, 8, 16):
        paths = sorted(args.candidate_dir.glob(f"c{concurrency}-r*.json"))
        if not paths:
            raise FileNotFoundError(f"missing c{concurrency} candidate artifact")
        repeats = [json.loads(path.read_text()) for path in paths]
        repeat_ok = [
            item.get("requests") == 32
            and item.get("completed") == 32
            and item.get("errors") == 0
            and item.get("natural_eos") is True
            and item.get("finish_reasons") == {"stop": 32}
            for item in repeats
        ]
        runtime_ok &= all(repeat_ok)
        base = baseline["cells"][str(concurrency)]
        baseline_repeats = [
            json.loads(Path(path).read_text()) for path in base["repeat_files"]
        ]
        latency = {}
        all_latency_targets = True
        tail_non_regression = True
        for metric in ("ttft_ms", "tpot_ms"):
            latency[metric] = {}
            for percentile in percentiles:
                baseline_value = statistics.median(
                    item[metric][percentile] for item in baseline_repeats
                )
                candidate_value = statistics.median(
                    item[metric][percentile] for item in repeats
                )
                speedup = baseline_value / candidate_value
                latency[metric][percentile] = {
                    "baseline_ms": baseline_value,
                    "candidate_ms": candidate_value,
                    "speedup": speedup,
                    "target_met": speedup >= args.target_speedup,
                }
                all_latency_targets &= speedup >= args.target_speedup
                if percentile != "p50":
                    tail_non_regression &= speedup >= 1.0
        cell_pass = (
            all(repeat_ok)
            and all_latency_targets
        )
        performance_ok &= cell_pass
        cells[str(concurrency)] = {
            "candidate_repetitions": len(paths),
            "candidate_artifacts": [
                {"path": str(path), "sha256": sha256(path)}
                for path in paths
            ],
            "runtime_valid": all(repeat_ok),
            "latency": latency,
            "tail_non_regression": tail_non_regression,
            "performance_pass": cell_pass,
        }

    if not runtime_ok:
        decision = "reject-runtime-validity"
    elif not performance_ok:
        decision = "iterate-performance"
    else:
        decision = "hold-quality-unproven"
    report = {
        "schema": "qwen35-tp4-npu03-candidate-decision/v1",
        "candidate_id": args.candidate_id,
        "baseline_summary": {
            "path": str(args.baseline_summary),
            "sha256": sha256(args.baseline_summary),
        },
        "target_speedup": args.target_speedup,
        "runtime_valid": runtime_ok,
        "performance_target_met": performance_ok,
        "quality_gate": {
            "status": "unproven",
            "reason": (
                "query_rewrite answer fields are empty; transport success, "
                "natural EOS, and reference similarity do not prove 精读无损"
            ),
        },
        "decision": decision,
        "cells": cells,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if performance_ok and runtime_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
