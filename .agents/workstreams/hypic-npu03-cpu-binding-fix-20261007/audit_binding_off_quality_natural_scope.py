#!/usr/bin/env python3
"""Recompute natural-task scores without weakening the frozen hot-path gate.

Run the original audit_binding_off_quality.py first. If it rejects the quality
arm for missing worker-hot events, this separate report preserves independently
verified natural-task rows and release evidence as *descriptive* results only.
It never writes quality-independent-audit.json or claims formal acceptance.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import audit_binding_off_quality as original


REPORT = original.QROOT / "quality-natural-scope-audit.json"


def treatment_service(fingerprint: dict) -> tuple[dict, bool, str | None]:
    """Preserve the original release/guard checks even if activation fails.

    The original service_receipt validates identity, four worker PIDs, release,
    the uninterrupted lane guard and service-log hash before it checks HYPIC
    activation. Catch only that last, explicit activation error.
    """

    try:
        return original.service_receipt("hypic-only", fingerprint), True, None
    except RuntimeError as exc:
        error = str(exc)
        if not error.startswith("HYPIC quality runtime activation insufficient:"):
            raise
    directory = original.QROOT / "hypic-only"
    start = json.loads((directory / "service-start.json").read_text())
    stop = json.loads((directory / "service-stop.json").read_text())
    guard = json.loads((directory / "lane-guard.json").read_text())
    evidence = directory / "hypic-evidence.jsonl"
    log = directory / f"service.full.{start['container_id'][:12]}.log"
    return {
        "container_id": start["container_id"],
        "physical_worker_pids": start["worker_pid_by_physical_npu"],
        "pre_activation_service_checks_passed": True,
        "service_start_sha256": original.sha256(directory / "service-start.json"),
        "service_stop_sha256": original.sha256(directory / "service-stop.json"),
        "lane_guard_sha256": original.sha256(directory / "lane-guard.json"),
        "lane_guard_samples": guard["samples"],
        "service_log_sha256": original.sha256(log),
        "hypic_evidence_sha256": original.sha256(evidence),
        "release": {key: stop[key] for key in
                    ("container_removed", "owned_npus_released",
                     "port_released", "lane_available")},
    }, False, error


def event_counts() -> dict:
    evidence = original.QROOT / "hypic-only" / "hypic-evidence.jsonl"
    counts: Counter[str] = Counter()
    hot_pids: set[int] = set()
    with evidence.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            event = json.loads(line)
            counts[event["event"]] += 1
            if event["event"] == "worker_hot_path":
                pid = event.get("pid")
                if isinstance(pid, int) and pid > 0:
                    hot_pids.add(pid)
    return {"events": dict(counts), "distinct_worker_hot_pids": sorted(hot_pids)}


def input_identity(row: dict) -> tuple:
    return (row["index"], row.get("sample_id"), row["reference"],
            row["usage"]["prompt_tokens"])


def main() -> int:
    if original.QROOT.name != "quality-context-41984-clean2":
        raise RuntimeError("set HYPIC_QUALITY_ATTEMPT=clean2")
    fingerprint = original.preflight()
    arm_variable = original.frozen_pair_seam()
    evaluator = original.frozen_evaluator()
    samples = {dataset: original.samples_for(dataset) for dataset in original.DATASETS}
    service = {"no-cache": original.service_receipt("no-cache", fingerprint)}
    treatment, hot_gate, hot_error = treatment_service(fingerprint)
    service["hypic-only"] = treatment
    units = {arm: {dataset: [] for dataset in original.DATASETS}
             for arm in original.ARMS}
    raw = {arm: {dataset: {} for dataset in original.DATASETS}
           for arm in original.ARMS}
    for arm in original.ARMS:
        for dataset, repeat in original.UNIT_ORDER:
            unit, rows = original.audit_unit(
                arm, dataset, repeat, samples[dataset], evaluator.score_case)
            receipt = json.loads((original.QROOT / "quality" / arm /
                                  f"{dataset}.run{repeat}.receipt.json").read_text())
            if receipt["container_id"] != service[arm]["container_id"]:
                raise RuntimeError(f"{arm}/{dataset}.run{repeat}: wrong service container")
            units[arm][dataset].append(unit)
            raw[arm][dataset][repeat] = rows
    pairwise: dict[str, list[dict]] = {}
    for dataset in original.DATASETS:
        baseline_identity = [input_identity(row) for row in raw["no-cache"][dataset][1]]
        for arm in original.ARMS:
            for repeat in (1, 2, 3):
                if [input_identity(row) for row in raw[arm][dataset][repeat]] != baseline_identity:
                    raise RuntimeError(f"{arm}/{dataset}.run{repeat}: input identity drift")
        pairwise[dataset] = []
        for repeat in (1, 2, 3):
            counts: Counter[str] = Counter()
            for base, treated in zip(raw["no-cache"][dataset][repeat],
                                     raw["hypic-only"][dataset][repeat]):
                counts["win" if treated["correct"] and not base["correct"] else
                       "loss" if base["correct"] and not treated["correct"] else
                       "both_correct" if base["correct"] else "both_wrong"] += 1
            pairwise[dataset].append({"run": repeat, **dict(counts)})
    deltas = []
    for dataset in original.DATASETS:
        for metric in ("accuracy_pct", "length_limit_rate_pct"):
            deltas.append(original.describe_delta(
                f"{dataset}.{metric}",
                [unit[metric] for unit in units["no-cache"][dataset]],
                [unit[metric] for unit in units["hypic-only"][dataset]]))
    for field in ("difficulty", "length"):
        keys = units["no-cache"]["longbenchv2"][0]["category_accuracy_pct"][field]
        for key in sorted(keys):
            deltas.append(original.describe_delta(
                f"longbenchv2.{field}.{key}.accuracy_pct",
                [unit["category_accuracy_pct"][field][key]
                 for unit in units["no-cache"]["longbenchv2"]],
                [unit["category_accuracy_pct"][field][key]
                 for unit in units["hypic-only"]["longbenchv2"]]))
    adverse = [item for item in deltas if
               (item["delta"] > 1e-9 if item["metric"].endswith("length_limit_rate_pct")
                else item["delta"] < -1e-9)]
    beyond_range = [item["metric"] for item in adverse if
                    (item["treatment_mean"] > item["baseline_range"][1]
                     if item["metric"].endswith("length_limit_rate_pct")
                     else item["treatment_mean"] < item["baseline_range"][0])]
    score_pattern = "nonadverse" if not adverse else (
        "beyond_baseline_range" if beyond_range else "within_baseline_range")
    report = {
        "schema": "hypic-bindingoff-quality-natural-scope-audit/v1",
        "scope": "descriptive natural-task scores; not original hot-path quality acceptance",
        "formal_acceptance_claim": False,
        "original_auditor_sha256": original.sha256(Path(original.__file__)),
        "frozen_fingerprint": fingerprint,
        "only_arm_variable": arm_variable,
        "all_twelve_rows_and_receipts_valid": True,
        "paired_and_repeated_input_identity_valid": True,
        "service": service,
        "activation": {"formal_hotpath_gate_pass": hot_gate,
                       "failure": hot_error, **event_counts()},
        "per_unit": units,
        "pairwise": pairwise,
        "deltas": deltas,
        "adverse_metrics": [item["metric"] for item in adverse],
        "beyond_baseline_range": beyond_range,
        "natural_task_score_pattern": score_pattern,
    }
    original.write_json(REPORT, report)
    print(json.dumps({"report": str(REPORT), "formal_hotpath_gate_pass": hot_gate,
                      "natural_task_score_pattern": score_pattern,
                      "adverse_metrics": report["adverse_metrics"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
