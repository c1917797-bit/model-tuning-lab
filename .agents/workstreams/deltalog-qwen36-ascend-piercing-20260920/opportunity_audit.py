#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_PROFILE_SHA256 = "b3bddd3b1a8b96571f20c59d801aa21da3da673f875f86a3b04318afbdb480a8"
PAPER_MAX_LOCAL_SPEEDUP = 1.86
OPTIMISTIC_WRITE_REDUCTION = 0.50
TARGET_SPEEDUP = 1.10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def amdahl_speedup(fraction: float, reduction: float) -> float:
    return 1.0 / (1.0 - fraction * reduction)


def reduction_from_speedup(speedup: float) -> float:
    if speedup <= 1.0:
        raise ValueError("speedup must exceed one")
    return 1.0 - 1.0 / speedup


def required_fraction(target_speedup: float, local_reduction: float) -> float:
    return (1.0 - 1.0 / target_speedup) / local_reduction


def is_recurrent(operator: dict) -> bool:
    identity = f"{operator['name']} {operator['type']}".lower()
    return "recurrentgateddeltarule" in identity


def audit(profile_path: Path) -> dict:
    observed_hash = sha256(profile_path)
    if observed_hash != EXPECTED_PROFILE_SHA256:
        raise RuntimeError(f"profile hash mismatch: {observed_hash}")
    profile = json.loads(profile_path.read_text())
    records = [record for record in profile["records"] if record["phase"] == "decode"]
    if len(records) != 4 or sorted(record["rank"] for record in records) != [0, 1, 2, 3]:
        raise RuntimeError("expected four decode ranks")

    paper_reduction = reduction_from_speedup(PAPER_MAX_LOCAL_SPEEDUP)
    ranks = []
    for record in records:
        interval = float(record["npu_interval_union_ms"])
        recurrent_ms = sum(
            float(operator["kernel_sum_ms"])
            for operator in record["top_operators"]
            if is_recurrent(operator)
        )
        if recurrent_ms <= 0:
            raise RuntimeError(f"missing recurrent operator on rank {record['rank']}")
        fraction = recurrent_ms / interval
        ranks.append({
            "rank": record["rank"],
            "npu_interval_union_ms": interval,
            "recurrent_ms": recurrent_ms,
            "recurrent_fraction": fraction,
            "paper_local_speedup_bound": amdahl_speedup(fraction, paper_reduction),
            "optimistic_half_reduction_bound": amdahl_speedup(fraction, OPTIMISTIC_WRITE_REDUCTION),
            "perfect_recurrent_deletion_bound": amdahl_speedup(fraction, 1.0),
        })

    fractions = [rank["recurrent_fraction"] for rank in ranks]
    required = required_fraction(TARGET_SPEEDUP, paper_reduction)
    summary = {
        "recurrent_fraction_percent_range": [100 * min(fractions), 100 * max(fractions)],
        "paper_local_reduction_percent": 100 * paper_reduction,
        "paper_local_speedup_bound_range": [
            min(rank["paper_local_speedup_bound"] for rank in ranks),
            max(rank["paper_local_speedup_bound"] for rank in ranks),
        ],
        "optimistic_half_reduction_bound_range": [
            min(rank["optimistic_half_reduction_bound"] for rank in ranks),
            max(rank["optimistic_half_reduction_bound"] for rank in ranks),
        ],
        "perfect_recurrent_deletion_bound_range": [
            min(rank["perfect_recurrent_deletion_bound"] for rank in ranks),
            max(rank["perfect_recurrent_deletion_bound"] for rank in ranks),
        ],
        "recurrent_fraction_required_for_target_percent": 100 * required,
        "observed_to_required_fraction_ratio_range": [min(fractions) / required, max(fractions) / required],
    }
    return {
        "schema": "deltalog-opportunity-audit/v1",
        "status": "complete",
        "profile_path": str(profile_path),
        "profile_sha256": observed_hash,
        "profile_concurrency": 16,
        "performance_contract": "32768 input / 16384 shared / 1024 output / 40 requests / concurrency 16",
        "paper_max_local_speedup": PAPER_MAX_LOCAL_SPEEDUP,
        "target_speedup": TARGET_SPEEDUP,
        "ranks": ranks,
        "summary": summary,
        "decision": "no-go" if max(rank["perfect_recurrent_deletion_bound"] for rank in ranks) < TARGET_SPEEDUP else "needs-target-npu-canary",
        "interpretation": "Optimistic screen over measured concurrency-16 NPU intervals, not E2E. Paper batch-64/256 shares are intentionally not substituted for target evidence.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise RuntimeError(f"refusing to overwrite {args.output_dir}")
    result = audit(args.profile)
    args.output_dir.mkdir(parents=True)
    output = args.output_dir / "opportunity-audit.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(output)
    print(json.dumps(result["summary"], sort_keys=True))
    if result["decision"] != "no-go":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
