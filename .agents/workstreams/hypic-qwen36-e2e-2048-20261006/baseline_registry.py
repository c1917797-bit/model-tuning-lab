#!/usr/bin/env python3
"""Freeze and revalidate completed baseline artifacts without rerunning them."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from assess_hypic_e2e_gates import validate_performance_record


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: JSON object required")
    return data


def entry(root: Path, path: Path) -> dict:
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"artifact outside baseline root or absent: {path}")
    return {"path": str(resolved.relative_to(root)), "sha256": sha256(resolved)}


def performance_entries(root: Path) -> list[dict]:
    result = []
    for index in (1, 2, 3):
        path = root / "no-cache" / f"performance.run{index}.json"
        validate_performance_record(read(path), "no-cache", index)
        result.append(entry(root, path))
    return result


def quality_entries(root: Path, contract: dict) -> list[dict]:
    expected_data = {
        "longbenchv2": (127, contract["fingerprint"]["longbench_sha256"],
                        "supplied_ais_bench_first_option_postprocess"),
        "gsm8k": (1319, contract["fingerprint"]["gsm8k_sha256"],
                  "supplied_ais_bench_gsm8k_numeric_postprocess"),
    }
    evaluator_hash = contract["fingerprint"]["quality_evaluator_sha256"]
    result = []
    for dataset, (expected, dataset_hash, scorer) in expected_data.items():
        for index in (1, 2, 3):
            stem = f"{dataset}.run{index}"
            directory = root / "quality" / "no-cache"
            summary_path = directory / f"{stem}.summary.json"
            details_path = directory / f"{stem}.jsonl"
            summary = read(summary_path)
            expected_summary = {
                "schema": "hypic-quality-eval/v1",
                "dataset": dataset,
                "run_id": f"run{index}",
                "data_sha256": dataset_hash,
                "evaluator_script_sha256": evaluator_hash,
                "scorer": scorer,
                "model": "qwen36-hypic-e2e-2048",
                "base_url": "http://127.0.0.1:8223",
                "concurrency": 32,
                "max_out_len": 2048,
                "temperature": 0,
                "seed": 0,
                "ignore_eos": False,
                "enable_thinking": False,
                "requests": expected,
                "successful": expected,
                "failed": 0,
            }
            for key, value in expected_summary.items():
                if summary.get(key) != value:
                    raise ValueError(f"{summary_path}: {key} mismatch")
            if Path(summary.get("details_path", "")).resolve() != details_path.resolve():
                raise ValueError(f"{summary_path}: details path mismatch")
            if summary.get("details_sha256") != sha256(details_path):
                raise ValueError(f"{summary_path}: details hash mismatch")
            rows = [json.loads(line) for line in details_path.read_text(encoding="utf-8").splitlines() if line]
            if len(rows) != expected or sorted(row.get("index") for row in rows) != list(range(expected)):
                raise ValueError(f"{details_path}: incomplete or duplicate sample indexes")
            for row in rows:
                response = row.get("response_text")
                if not (
                    row.get("ok") is True
                    and row.get("error") is None
                    and isinstance(response, str)
                    and row.get("response_sha256") == hashlib.sha256(response.encode("utf-8")).hexdigest()
                    and isinstance((row.get("usage") or {}).get("completion_tokens"), int)
                    and 0 <= row["usage"]["completion_tokens"] <= 2048
                ):
                    raise ValueError(f"{details_path}: invalid raw sample {row.get('index')}")
            correct = sum(row.get("correct") is True for row in rows)
            completion_tokens = sum(row["usage"]["completion_tokens"] for row in rows)
            unique_responses = len({row["response_sha256"] for row in rows})
            accuracy = 100 * correct / expected
            if not (
                summary.get("correct") == correct
                and summary.get("completion_tokens") == completion_tokens
                and summary.get("unique_response_sha256") == unique_responses
                and isinstance(summary.get("accuracy_pct"), (int, float))
                and math.isclose(summary["accuracy_pct"], accuracy, rel_tol=1e-9, abs_tol=1e-9)
                and sum(summary.get("finish_reasons", {}).values()) == expected
            ):
                raise ValueError(f"{summary_path}: raw/summary mismatch")
            result.extend((entry(root, summary_path), entry(root, details_path)))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("performance", "quality"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    contract = read(root / "baseline-contract.json")
    fingerprint = contract.get("fingerprint")
    if not isinstance(fingerprint, dict):
        raise ValueError("baseline contract lacks fingerprint")
    canonical = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))
    fingerprint_hash = hashlib.sha256(canonical.encode()).hexdigest()
    if contract.get("fingerprint_sha256") != fingerprint_hash:
        raise ValueError("baseline contract fingerprint hash mismatch")
    lock = (root / "baseline-registry.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    path = root / "baseline-registry.json"
    if path.exists():
        registry = read(path)
        if registry.get("schema") != "hypic-baseline-registry/v1" or registry.get("fingerprint_sha256") != fingerprint_hash:
            raise ValueError("baseline registry identity mismatch")
    else:
        registry = {
            "schema": "hypic-baseline-registry/v1",
            "fingerprint_sha256": fingerprint_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    measured = performance_entries(root)
    if "performance" in registry and registry["performance"] != measured:
        raise ValueError("frozen performance baseline hash or raw contract changed")
    changed = "performance" not in registry
    registry["performance"] = measured
    if args.phase == "quality":
        measured_quality = quality_entries(root, contract)
        if "quality" in registry and registry["quality"] != measured_quality:
            raise ValueError("frozen quality baseline hash or raw contract changed")
        changed = changed or "quality" not in registry
        registry["quality"] = measured_quality
    if changed:
        temporary = root / "baseline-registry.json.tmp"
        temporary.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)
    print(f"baseline registry {'FROZEN' if changed else 'MATCH'} {args.phase} {fingerprint_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
