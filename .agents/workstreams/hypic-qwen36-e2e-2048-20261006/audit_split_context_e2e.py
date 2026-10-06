#!/usr/bin/env python3
"""Independently audit six original performance and twelve paired 2048 quality units.

Evidence completeness is deliberately separate from the paper-only performance
acceptance decision, which remains failed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "WS-20260904-qwen38-dense-paper-to-ascend"))
from audit_hypic_historical_reproduction import (  # noqa: E402
    audit_performance, audit_quality, atomic_json, load_object, sha256,
)


ROOT = Path("/cache/cch/hypic-qwen36-e2e-2048-20261006")
QROOT = ROOT / "quality-context-41984"
DEADLINE = datetime.fromisoformat("2026-10-07T11:39:37+00:00")
ARMS = ("no-cache", "hypic-only")
DATASETS = ("longbenchv2", "gsm8k")
NAMES = (
    "qwen36_hypic2048_matmulallreduce_npu0_3_v1",
    "qwen36_hypic2048_quality41984_baseline_npu0_3_v1",
    "qwen36_hypic2048_quality41984_treatment_npu0_3_v1",
)


def canonical_hash(value: dict) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def inspect_service_receipts(contract: dict, errors: list[str]) -> None:
    expected_source = contract["fingerprint"]["source_snapshot_sha256"]
    for arm in ARMS:
        try:
            started = load_object(QROOT / arm / "service-start.json")
            stopped = load_object(QROOT / arm / "service-stop.json")
            expected_name = NAMES[1 if arm == "no-cache" else 2]
            if not (
                started.get("schema") == "hypic-quality-context-service-start/v1"
                and started.get("container") == expected_name
                and started.get("container_id") == stopped.get("container_id")
                and started.get("arm") == arm
                and started.get("source_snapshot_sha256") == expected_source
                and started.get("image") == contract["fingerprint"]["image"]
                and started.get("max_model_len") == 41984
                and started.get("max_num_batched_tokens") == 41984
                and started.get("physical_npus") == [0, 1, 2, 3]
                and started.get("health_passed") is True
                and stopped.get("schema") == "hypic-quality-context-service-stop/v1"
                and stopped.get("container") == expected_name
                and stopped.get("arm") == arm
                and stopped.get("owned_npus_released") is True
                and stopped.get("port_released") is True
                and stopped.get("container_removed") is True
                and datetime.fromisoformat(stopped["stopped_at"]) <= DEADLINE
            ):
                errors.append(f"{arm}: paired-context service or release receipt mismatch")
            npu_path = QROOT / arm / "npu-smi-at-health.txt"
            top_path = QROOT / arm / "docker-top-at-health.txt"
            npu_text = npu_path.read_text(encoding="utf-8")
            top_text = top_path.read_text(encoding="utf-8")
            observed = {
                match.group(1): int(match.group(2))
                for match in re.finditer(
                    r"^\|\s*([0-3])\s+0\s*\|\s*(\d+)\s*\|\s*VLLMWorker_TP\b",
                    npu_text, re.M,
                )
            }
            container_pids = {
                int(parts[0]) for line in top_text.splitlines()[1:]
                if (parts := line.split()) and parts[0].isdigit()
            }
            if not (
                started.get("npu_smi_at_health_sha256") == sha256(npu_path)
                and started.get("docker_top_at_health_sha256") == sha256(top_path)
                and started.get("worker_pid_by_physical_npu") == observed
                and set(observed) == {"0", "1", "2", "3"}
                and len(set(observed.values())) == 4
                and set(observed.values()).issubset(container_pids)
            ):
                errors.append(f"{arm}: physical worker PID/container proof mismatch")
        except Exception as exc:
            errors.append(f"{arm}: service receipt unreadable: {exc}")


def inspect_quality_decision(quality_root: Path, errors: list[str]) -> str | None:
    """Recompute the predeclared classification without importing its controller."""
    try:
        reported = load_object(quality_root / "quality-context-audit.json")
        summaries = {
            arm: {
                dataset: [load_object(quality_root / "quality" / arm /
                                      f"{dataset}.run{index}.summary.json")
                          for index in (1, 2, 3)]
                for dataset in DATASETS
            }
            for arm in ARMS
        }
        for arm in ARMS:
            for index in (1, 2, 3):
                path = quality_root / "quality" / arm / f"longbenchv2.run{index}.jsonl"
                raw = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                       if line]
                if len(raw) != 127:
                    errors.append(f"{arm}/LongBench/run{index}: category source row count mismatch")
                summary = summaries[arm]["longbenchv2"][index - 1]
                for field in ("difficulty", "length"):
                    groups: dict[str, list[dict]] = {}
                    for row in raw:
                        groups.setdefault(str(row.get(field)), []).append(row)
                    recomputed = {
                        category: 100 * sum(row.get("correct") is True for row in members) / len(members)
                        for category, members in groups.items()
                    }
                    observed = summary["category_accuracy_pct"][field]
                    if (set(observed) != set(recomputed)
                            or any(not math.isclose(observed[category], score,
                                                    rel_tol=1e-9, abs_tol=1e-9)
                                   for category, score in recomputed.items())):
                        errors.append(f"{arm}/LongBench/run{index}: {field} category accuracy differs from raw rows")
        signals: list[tuple[str, str]] = []

        def classify(scope: str, baseline: list[float], treatment: list[float],
                     higher_is_better: bool = True) -> None:
            change = statistics.mean(treatment) - statistics.mean(baseline)
            if not higher_is_better:
                change = -change
            if change < 0:
                variation = max(baseline) - min(baseline)
                signals.append((scope, "regression" if -change > variation else "inconclusive"))

        for dataset in DATASETS:
            baseline = summaries["no-cache"][dataset]
            treatment = summaries["hypic-only"][dataset]
            classify(f"{dataset}:accuracy", [row["accuracy_pct"] for row in baseline],
                     [row["accuracy_pct"] for row in treatment])
            expected = 127 if dataset == "longbenchv2" else 1319
            classify(f"{dataset}:length-limit-rate",
                     [100 * row["finish_reasons"].get("length", 0) / expected for row in baseline],
                     [100 * row["finish_reasons"].get("length", 0) / expected for row in treatment],
                     higher_is_better=False)
        for field in ("difficulty", "length"):
            categories = set(summaries["no-cache"]["longbenchv2"][0]
                             ["category_accuracy_pct"][field])
            for arm in ARMS:
                for row in summaries[arm]["longbenchv2"]:
                    if set(row["category_accuracy_pct"][field]) != categories:
                        errors.append(f"LongBench {field} category key drift")
            for category in sorted(categories):
                classify(f"longbenchv2:{field}:{category}",
                         [row["category_accuracy_pct"][field][category]
                          for row in summaries["no-cache"]["longbenchv2"]],
                         [row["category_accuracy_pct"][field][category]
                          for row in summaries["hypic-only"]["longbenchv2"]])
        expected_classification = ("regression" if any(level == "regression" for _, level in signals)
                                   else "inconclusive" if signals else "pass")
        observed_signals = sorted((item["scope"], item["classification"])
                                  for item in reported["negative_or_uncertain_signals"])
        if not (
            reported.get("schema") == "hypic-paired-2048-quality-context-audit/v1"
            and reported.get("quality_evidence_complete") is True
            and reported.get("quality_classification") == expected_classification
            and observed_signals == sorted(signals)
        ):
            errors.append("paired quality classification differs from independent recomputation")
        return expected_classification
    except Exception as exc:
        errors.append(f"paired quality decision unreadable: {type(exc).__name__}: {exc}")
        return None


def inspect_live_release(errors: list[str]) -> dict:
    evidence = {}
    try:
        npu = subprocess.run(["npu-smi", "info"], text=True, capture_output=True,
                             timeout=30, check=True).stdout
        evidence["npu_smi_sha256"] = hashlib.sha256(npu.encode()).hexdigest()
        if any(f"No running processes found in NPU {index}" not in npu for index in range(4)):
            errors.append("physical NPU0-3 still has active processes")
    except Exception as exc:
        errors.append(f"npu-smi release check failed: {exc}")
    try:
        port = subprocess.run(["ss", "-ltn", "sport", ":8223"], text=True,
                              capture_output=True, timeout=30, check=True).stdout
        evidence["port_snapshot_sha256"] = hashlib.sha256(port.encode()).hexdigest()
        if ":8223" in port:
            errors.append("service port 8223 is still listening")
    except Exception as exc:
        errors.append(f"port release check failed: {exc}")
    for name in NAMES:
        result = subprocess.run(["docker", "inspect", name], text=True,
                                capture_output=True, timeout=30, check=False)
        if result.returncode == 0:
            errors.append(f"owned experiment container still exists: {name}")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    quality_root = root / "quality-context-41984"
    output = (args.output or root / "hypic-e2e-2048-evidence-audit.json").resolve()
    errors: list[str] = []
    performance: list[dict] = []
    quality: list[dict] = []
    quality_classification: str | None = None
    release: dict = {}
    data_hashes: set[str] = set()
    evaluator_hashes: set[str] = set()
    try:
        parent = load_object(root / "baseline-contract.json")
        quality_contract = load_object(quality_root / "quality-context-contract.json")
        fp = quality_contract["fingerprint"]
        if parent.get("fingerprint_sha256") != canonical_hash(parent["fingerprint"]):
            errors.append("parent performance baseline contract hash mismatch")
        if quality_contract.get("fingerprint_sha256") != canonical_hash(fp):
            errors.append("paired quality-context contract hash mismatch")
        if not (
            fp.get("parent_baseline_fingerprint_sha256") == parent.get("fingerprint_sha256")
            and fp.get("max_model_len") == 41984
            and fp.get("max_num_batched_tokens") == 41984
            and fp.get("quality_max_output_tokens") == 2048
            and fp.get("longbench_max_prompt_plus_cap") == 41690
            and fp.get("physical_npus") == [0, 1, 2, 3]
            and fp.get("separate_from_performance_baseline") is True
        ):
            errors.append("paired quality identity differs from frozen contract")
        if sha256(root / "environment-and-container-snapshot.txt") != fp.get("source_snapshot_sha256"):
            errors.append("frozen container snapshot hash mismatch")
        performance_gate = load_object(root / "performance-gate.json")
        if performance_gate.get("passed") is not False:
            errors.append("paper-only performance rejection was changed")
        perf_hashes = performance_gate.get("run_sha256", {})
        aggregate = {
            "performance_runs": {
                arm: [
                    {"path": str(root / arm / f"performance.run{index}.json"),
                     "sha256": perf_hashes[arm][index - 1]}
                    for index in (1, 2, 3)
                ]
                for arm in ARMS
            },
            "quality_runs": {},
        }
        performance = audit_performance(root, aggregate, errors)
        for arm in ARMS:
            registry = load_object(quality_root / f"{arm}-quality-registry.json")
            entries = registry.get("raw_artifacts", [])
            mapping = {item["path"]: item["sha256"] for item in entries}
            expected = {
                f"quality/{arm}/{dataset}.run{index}.{suffix}"
                for dataset in DATASETS for index in (1, 2, 3)
                for suffix in ("summary.json", "jsonl")
            }
            if not (
                registry.get("schema") == "hypic-quality-context-arm-registry/v1"
                and registry.get("arm") == arm
                and registry.get("contract_sha256") == quality_contract["fingerprint_sha256"]
                and len(entries) == len(expected)
                and set(mapping) == expected
            ):
                errors.append(f"{arm}: baseline/treatment quality registry identity or members mismatch")
            for rel, expected_hash in mapping.items():
                path = (quality_root / rel).resolve()
                if not path.is_relative_to(quality_root) or not path.is_file() or sha256(path) != expected_hash:
                    errors.append(f"{arm}: frozen raw hash mismatch: {rel}")
            aggregate["quality_runs"][arm] = {
                dataset: [
                    {"path": str(quality_root / "quality" / arm / f"{dataset}.run{index}.summary.json"),
                     "sha256": mapping.get(f"quality/{arm}/{dataset}.run{index}.summary.json")}
                    for index in (1, 2, 3)
                ]
                for dataset in DATASETS
            }
        quality, data_hashes, evaluator_hashes = audit_quality(
            quality_root, aggregate, errors, 2048
        )
        quality_classification = inspect_quality_decision(quality_root, errors)
        if data_hashes != {fp["longbench_sha256"], fp["gsm8k_sha256"]}:
            errors.append("quality dataset hashes differ from frozen contract")
        if evaluator_hashes != {fp["quality_evaluator_sha256"]}:
            errors.append("quality evaluator hash differs from frozen contract")
        for dataset in DATASETS:
            for index in (1, 2, 3):
                paths = [quality_root / "quality" / arm / f"{dataset}.run{index}.jsonl"
                         for arm in ARMS]
                paired = [[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
                          for path in paths]
                if len(paired[0]) != len(paired[1]):
                    errors.append(f"{dataset}/run{index}: paired row count drift")
                    continue
                for baseline, treatment in zip(*paired):
                    if (
                        baseline.get("index") != treatment.get("index")
                        or baseline.get("sample_id") != treatment.get("sample_id")
                        or baseline.get("reference") != treatment.get("reference")
                        or baseline.get("difficulty") != treatment.get("difficulty")
                        or baseline.get("length") != treatment.get("length")
                        or (baseline.get("usage") or {}).get("prompt_tokens")
                        != (treatment.get("usage") or {}).get("prompt_tokens")
                    ):
                        errors.append(f"{dataset}/run{index}: paired sample protocol drift")
                        break
        inspect_service_receipts(quality_contract, errors)
        release = inspect_live_release(errors)
    except Exception as exc:
        errors.append(f"independent audit could not complete: {type(exc).__name__}: {exc}")
    payload = {
        "schema": "hypic-split-context-independent-evidence-audit/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": not errors and len(performance) == 6 and len(quality) == 12,
        "expected_units": 18,
        "accepted_units": len(performance) + len(quality) if not errors else 0,
        "performance_context": 40960,
        "quality_context": 41984,
        "quality_max_output_tokens": 2048,
        "quality_classification": quality_classification,
        "paper_only_performance_accepted": False,
        "evidence_integrity_not_algorithm_acceptance": True,
        "performance": performance,
        "quality": quality,
        "dataset_sha256": sorted(data_hashes),
        "evaluator_sha256": sorted(evaluator_hashes),
        "live_release": release,
        "source_auditor_sha256": sha256(
            HERE.parent / "WS-20260904-qwen38-dense-paper-to-ascend"
            / "audit_hypic_historical_reproduction.py"
        ),
        "errors": errors,
    }
    atomic_json(output, payload)
    print(json.dumps({"ok": payload["ok"], "accepted_units": payload["accepted_units"],
                      "errors": errors}, sort_keys=True))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
