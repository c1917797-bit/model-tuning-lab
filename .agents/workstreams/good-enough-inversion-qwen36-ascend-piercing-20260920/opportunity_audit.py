#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_TIMING_SHA256 = "5d32bf31804152fa283dca5e449332908029f913b5cedd47f104378fb3d14d98"
PAPER_BEST_LOCAL_SPEEDUP = 5.2
TARGET_SPEEDUP = 1.10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def amdahl_speedup(fraction: float, local_speedup: float) -> float:
    return 1.0 / ((1.0 - fraction) + fraction / local_speedup)


def required_fraction(target_speedup: float, local_speedup: float) -> float:
    return (1.0 - 1.0 / target_speedup) / (1.0 - 1.0 / local_speedup)


def audit(mxr_task_path: Path, timing_path: Path) -> dict:
    observed_hash = sha256(timing_path)
    if observed_hash != EXPECTED_TIMING_SHA256:
        raise RuntimeError(f"timing hash mismatch: {observed_hash}")
    timing = json.loads(timing_path.read_text())
    if timing.get("schema") != "mst.mxr.triangular-inverse-timing/v1" or not timing.get("ok"):
        raise RuntimeError("unexpected timing schema or failed source evidence")
    mxr_task = json.loads(mxr_task_path.read_text())
    result = mxr_task["terminal_result"]["triangular_inverse"]
    fractions = [value / 100.0 for value in result["service_prefill_fraction_percent_range"]]
    if result["decode_coverage_percent"] != 0.0:
        raise RuntimeError("expected zero decode coverage")
    paper_bounds = [amdahl_speedup(fraction, PAPER_BEST_LOCAL_SPEEDUP) for fraction in fractions]
    deletion_bounds = [amdahl_speedup(fraction, float("inf")) for fraction in fractions]
    required = required_fraction(TARGET_SPEEDUP, PAPER_BEST_LOCAL_SPEEDUP)
    summary = {
        "target_prefill_inversion_fraction_percent_range": [100 * min(fractions), 100 * max(fractions)],
        "paper_5_2x_prefill_npu_bound_range": [min(paper_bounds), max(paper_bounds)],
        "perfect_inversion_deletion_prefill_npu_bound_range": [min(deletion_bounds), max(deletion_bounds)],
        "affected_fraction_required_for_1_10x_percent": 100 * required,
        "observed_to_required_fraction_ratio_range": [min(fractions) / required, max(fractions) / required],
        "decode_coverage_percent": 0.0,
    }
    return {
        "schema": "good-enough-inversion-opportunity-audit/v1",
        "status": "complete",
        "paper_best_local_speedup": PAPER_BEST_LOCAL_SPEEDUP,
        "target_speedup": TARGET_SPEEDUP,
        "source_timing_path": str(timing_path),
        "source_timing_sha256": observed_hash,
        "source_mxr_task": str(mxr_task_path),
        "summary": summary,
        "decision": "no-go" if max(deletion_bounds) < TARGET_SPEEDUP else "needs-target-npu-approximation-gate",
        "interpretation": "Prefill-NPU upper bound only; full E2E is lower because the method has zero decode coverage. The approximation has not been implemented or quality-tested.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mxr-task", type=Path, required=True)
    parser.add_argument("--timing", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise RuntimeError(f"refusing to overwrite {args.output_dir}")
    result = audit(args.mxr_task, args.timing)
    args.output_dir.mkdir(parents=True)
    output = args.output_dir / "opportunity-audit.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(output)
    print(json.dumps(result["summary"], sort_keys=True))
    if result["decision"] != "no-go":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
