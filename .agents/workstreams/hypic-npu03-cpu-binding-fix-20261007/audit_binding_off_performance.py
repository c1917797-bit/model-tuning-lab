#!/usr/bin/env python3
"""Independently recompute the six binding-off performance units from raw rows."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path

import yaml

ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
EXPERIMENT = Path(__file__).resolve().parents[2] / "experiments/exp-20261007-hypic-npu03-cpu-binding-fix.yaml"
PHASES = ("screen", "repeat2", "repeat3")
RECORDS = {
    "no-cache": ("screen_20261007", "repeat2_20261007", "repeat3_20261007"),
    "hypic-only": ("hypic_screen_20261007", "hypic_repeat2_20261007", "hypic_repeat3_20261007"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    # The frozen benchmark uses nearest rank, not linear interpolation.
    return ordered[math.ceil(len(ordered) * pct / 100) - 1]


def check_close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-6):
        raise RuntimeError(f"{label} disagrees with raw rows: {actual} != {expected}")


def audit_unit(arm: str, phase: str, ledger: dict) -> tuple[dict, dict, dict]:
    directory = ROOT / arm / phase
    hashes = ledger["artifacts"]
    for file, field in (("performance.json", "performance_sha256"),
                        ("contract.json", "contract_sha256"),
                        ("service.activation.log", "activation_log_sha256"),
                        ("cleanup.json", "cleanup_sha256")):
        if sha256(directory / file) != hashes[field]:
            raise RuntimeError(f"{arm}/{phase}: {file} hash mismatch")
    report = json.loads((directory / "performance.json").read_text())
    summary = report["summary"]
    config = report["config"]
    rows = report["results"]
    contract = json.loads((directory / "contract.json").read_text())
    cleanup = json.loads((directory / "cleanup.json").read_text())
    if (len(rows) != 40 or sorted(row["index"] for row in rows) != list(range(40))
            or any(row["ok"] is not True or row["error"] is not None
                   or row["output_tokens"] != 1024 or row["requested_output_tokens"] != 1024
                   or row["finish_reason"] != "length"
                   or not isinstance(row["output_sha256"], str)
                   or len(row["output_sha256"]) != 64 for row in rows)):
        raise RuntimeError(f"{arm}/{phase}: raw result rows invalid")
    if config != {"base_url": "http://127.0.0.1:8223", "concurrency": 16,
                  "ignore_eos": True, "input_tokens": 32768,
                  "model": "qwen36-hypic-e2e-2048", "output_tokens": 1024,
                  "prefix_tokens": 16384, "requests": 40,
                  "segment_boundary_transport": "vllm_xargs.hypic_segment_ends",
                  "segment_ends": [16384, 32768],
                  "warmup_mode": "concurrent_materialization_gate", "warmup_requests": 2}:
        raise RuntimeError(f"{arm}/{phase}: benchmark contract drift")
    tpot = [(row["duration_s"] * 1000 - row["ttft_ms"]) / 1023 for row in rows]
    weighted = sum(row["duration_s"] * 1000 - row["ttft_ms"] for row in rows) / (40 * 1023)
    check_close(weighted, summary["tpot_weighted_ms"], "weighted TPOT")
    check_close(percentile(tpot, 95), summary["tpot_p95_ms"], "TPOT P95")
    check_close(percentile([row["ttft_ms"] for row in rows], 95),
                summary["ttft_p95_ms"], "TTFT P95")
    check_close(40960 / summary["benchmark_duration_s"],
                summary["output_tokens_per_second"], "output throughput")
    if (summary["successful"] != 40 or summary["failed"] != 0
            or summary["fixed_output_verified"] is not True
            or summary["output_tokens"] != 40960
            or len(report["warmup_results"]) != 2):
        raise RuntimeError(f"{arm}/{phase}: summary success/warmup gate failed")
    if arm == "hypic-only" and (summary.get("hot_path_verified") is not True
                                or summary.get("hot_path_missing") != []
                                or summary.get("run_evidence_event_counts", {}).get("worker_hot_path", 0) < 4):
        raise RuntimeError(f"{arm}/{phase}: HYPIC activation gate failed")
    if (contract.get("arm") != arm or contract.get("phase") != phase
            or contract.get("image") != "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
            or contract.get("source_commit") != "3ad0967589304cd8fc4e7cff02f48ecc6125c89f"
            or contract.get("benchmark_sha256") != "cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822"
            or contract.get("cpuset") != "112-191"
            or contract.get("physical_npus") != [0, 1, 2, 3]
            or contract.get("only_serving_change") != "--additional-config '{\"enable_cpu_binding\":false}'"
            or cleanup.get("container_id") != contract.get("container_id")
            or not all(cleanup.get(key) is True for key in
                       ("container_removed", "owned_npus_released", "port_released"))):
        raise RuntimeError(f"{arm}/{phase}: service identity or cleanup mismatch")
    activation = (directory / "service.activation.log").read_text()
    if ("'enable_cpu_binding': False" not in activation
            or "The CPU allocation plan is as follows:" in activation):
        raise RuntimeError(f"{arm}/{phase}: binding-off activation mismatch")
    values = {key: summary[key] for key in
              ("tpot_weighted_ms", "tpot_p95_ms", "ttft_p95_ms",
               "output_tokens_per_second", "benchmark_duration_s")}
    return values, contract, config


def main() -> int:
    ledgers = yaml.safe_load(EXPERIMENT.read_text())
    result: dict[str, list[dict]] = {}
    contracts: dict[str, list[dict]] = {}
    configs = []
    for arm in RECORDS:
        result[arm] = []
        contracts[arm] = []
        for phase, key in zip(PHASES, RECORDS[arm]):
            values, contract, config = audit_unit(arm, phase, ledgers[key])
            result[arm].append(values)
            contracts[arm].append(contract)
            configs.append(config)
    if any(config != configs[0] for config in configs[1:]):
        raise RuntimeError("cross-arm benchmark config differs")
    normalized = []
    for arm in RECORDS:
        for contract in contracts[arm]:
            normalized.append(contract["serving_command"].replace(f"/results/{arm}", "/results/ARM"))
    if any(command != normalized[0] for command in normalized[1:]):
        raise RuntimeError("cross-arm serving command differs beyond artifact path")
    metrics = ("tpot_weighted_ms", "tpot_p95_ms", "ttft_p95_ms",
               "output_tokens_per_second", "benchmark_duration_s")
    medians = {arm: {key: statistics.median(item[key] for item in values)
                     for key in metrics} for arm, values in result.items()}
    no_cache = medians["no-cache"]
    hypic = medians["hypic-only"]
    effect = {"tpot_saved_ms": no_cache["tpot_weighted_ms"] - hypic["tpot_weighted_ms"],
              "tpot_saved_pct": 100 * (1 - hypic["tpot_weighted_ms"] / no_cache["tpot_weighted_ms"]),
              "ttft_p95_saved_s": (no_cache["ttft_p95_ms"] - hypic["ttft_p95_ms"]) / 1000,
              "throughput_ratio": hypic["output_tokens_per_second"] / no_cache["output_tokens_per_second"]}
    report = {"schema": "hypic-bindingoff-performance-independent-audit/v1",
              "all_six_units_valid": True, "quality_decision": "not-measured",
              "per_run": result, "medians": medians, "paper_effect": effect,
              "preregistered_paper_effect_gate_pass": effect["tpot_saved_ms"] >= 10
              and effect["ttft_p95_saved_s"] >= 10,
              "normalized_serving_command_identical": True}
    output = ROOT / "performance-independent-audit.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
