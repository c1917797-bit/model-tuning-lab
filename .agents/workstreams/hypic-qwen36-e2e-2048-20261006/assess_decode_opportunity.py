#!/usr/bin/env python3
"""Recompute a conditional decode-wave opportunity proxy from frozen raw runs.

This is candidate-screening evidence, not a profiler or a proven critical path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def assess_run(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document["results"]
    summary = document["summary"]
    if len(rows) != 40 or sorted(row["index"] for row in rows) != list(range(40)):
        raise ValueError(f"{path}: expected exactly indexes 0..39")
    if summary.get("successful") != 40 or summary.get("failed") != 0:
        raise ValueError(f"{path}: incomplete measured requests")
    waves: list[list[float]] = [[], [], []]
    for row in rows:
        if row.get("ok") is not True or row.get("output_tokens") != 1024:
            raise ValueError(f"{path}: invalid fixed-output request {row['index']}")
        duration = float(row["duration_s"])
        ttft = float(row["ttft_ms"]) / 1000
        if not (math.isfinite(duration) and math.isfinite(ttft) and 0 <= ttft <= duration):
            raise ValueError(f"{path}: invalid request timing {row['index']}")
        waves[row["index"] // 16].append(duration - ttft)
    if [len(wave) for wave in waves] != [16, 16, 8]:
        raise ValueError(f"{path}: unexpected wave sizes")
    wave_maxima = [max(wave) for wave in waves]
    return {
        "path": str(path),
        "sha256": sha256(path),
        "wave_max_decode_proxy_s": wave_maxima,
        "sum_wave_max_decode_proxy_s": sum(wave_maxima),
        "observed_duration_s": float(summary["benchmark_duration_s"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    gate_path = root / "performance-gate.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate.get("passed") is not False:
        raise ValueError("expected the rejected first-candidate performance gate")
    baseline_duration = float(gate["metrics"]["benchmark_duration_s"]["baseline_median"])
    baseline_throughput = float(gate["metrics"]["output_tokens_per_second"]["baseline_median"])
    duration_target = baseline_duration * 0.85
    throughput_duration_target = 40960 / (baseline_throughput * 1.20)
    runs = {
        arm: [assess_run(root / arm / f"performance.run{index}.json") for index in (1, 2, 3)]
        for arm in ("no-cache", "hypic-only")
    }
    for arm, items in runs.items():
        if [item["sha256"] for item in items] != gate["run_sha256"][arm]:
            raise ValueError(f"{arm}: raw run hash drift from performance gate")
    treatment_proxies = [item["sum_wave_max_decode_proxy_s"] for item in runs["hypic-only"]]
    report = {
        "schema": "hypic-decode-opportunity-diagnostic/v1",
        "experiment_id": "hypic-qwen36-e2e-2048-20261006",
        "performance_gate_sha256": sha256(gate_path),
        "method": "group fixed-output request indexes into 16/16/8 launch-order waves; subtract each request TTFT from its duration; sum the maximum residual per wave",
        "scope": "conditional screening proxy only; launch-order waves and unchanged decode work are assumptions; actual critical path requires NPU/CPU profile",
        "duration_target_s": duration_target,
        "throughput_target_equivalent_duration_s": throughput_duration_target,
        "runs": runs,
        "treatment_median_proxy_s": statistics.median(treatment_proxies),
        "all_treatment_proxies_above_both_targets": all(
            value > duration_target and value > throughput_duration_target
            for value in treatment_proxies
        ),
        "decision": "do not select a prefill-only retune without new evidence; profile decode/service critical path before a successor candidate",
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "median_proxy_s": report["treatment_median_proxy_s"], "above_targets": report["all_treatment_proxies_above_both_targets"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
