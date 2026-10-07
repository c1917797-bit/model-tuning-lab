#!/usr/bin/env python3
"""Audit every paired 2048-token quality row against frozen samples and receipts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import statistics
from collections import Counter
from pathlib import Path

from binding_off_quality import (
    ARMS, DATASETS, EVALUATOR, QROOT, UNIT_ORDER, preflight, sha256,
    validate_unit, write_json,
)
from binding_off_service import frozen_source

AUDIT_PATH = QROOT / "quality-independent-audit.json"


def frozen_pair_seam() -> dict:
    environments = {}
    for arm in ARMS:
        items = frozen_source(arm)["Config"]["Env"]
        environments[arm] = {key: value for key, value in
                             (item.split("=", 1) for item in items)}
    baseline = environments["no-cache"]
    treatment = environments["hypic-only"]
    differences = {key: [baseline.get(key), treatment.get(key)]
                   for key in baseline.keys() | treatment.keys()
                   if baseline.get(key) != treatment.get(key)
                   and key != "VLLM_ASCEND_HYPIC_EVIDENCE_FILE"}
    if differences != {"VLLM_ASCEND_HYPIC_ENABLE": ["0", "1"]}:
        raise RuntimeError(f"frozen quality arms differ beyond HYPIC enable: {differences}")
    return differences


def frozen_evaluator():
    spec = importlib.util.spec_from_file_location("frozen_quality_evaluator", EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("frozen quality evaluator cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def samples_for(dataset: str) -> list[dict]:
    path = DATASETS[dataset][0]
    if dataset == "longbenchv2":
        rows = json.loads(path.read_text(encoding="utf-8"))
    else:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) != DATASETS[dataset][1]:
        raise RuntimeError(f"{dataset}: frozen sample count changed")
    return rows


def service_receipt(arm: str, fingerprint: dict) -> dict:
    directory = QROOT / arm
    start = json.loads((directory / "service-start.json").read_text())
    stop = json.loads((directory / "service-stop.json").read_text())
    if (start.get("arm") != arm or stop.get("arm") != arm
            or start.get("container_id") != stop.get("container_id")
            or start.get("fingerprint") != json.loads(json.dumps(fingerprint))
            or set(start.get("worker_pid_by_physical_npu", {})) != {"0", "1", "2", "3"}
            or len(set(start["worker_pid_by_physical_npu"].values())) != 4
            or not all(stop.get(key) is True for key in
                       ("container_removed", "owned_npus_released", "port_released"))):
        raise RuntimeError(f"{arm}: service identity, worker proof or release receipt invalid")
    log_path = directory / f"service.full.{start['container_id'][:12]}.log"
    if (stop.get("service_log_error") is not None
            or stop.get("service_log_sha256") != sha256(log_path)):
        raise RuntimeError(f"{arm}: service log capture missing or hash mismatch")
    binding_off = False
    binding_plan_seen = False
    with log_path.open(errors="replace") as stream:
        for line in stream:
            binding_off |= "'enable_cpu_binding': False" in line
            binding_plan_seen |= "The CPU allocation plan is as follows:" in line
    if not binding_off or binding_plan_seen:
        raise RuntimeError(f"{arm}: binding-off activation missing")
    result = {"container_id": start["container_id"],
              "service_start_sha256": sha256(directory / "service-start.json"),
              "service_stop_sha256": sha256(directory / "service-stop.json"),
              "service_log_sha256": sha256(log_path),
              "physical_worker_pids": start["worker_pid_by_physical_npu"]}
    if arm == "hypic-only":
        evidence = directory / "hypic-evidence.jsonl"
        if not evidence.exists() or evidence.stat().st_size == 0:
            raise RuntimeError("HYPIC quality activation evidence is absent")
        events = Counter()
        with evidence.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    events[json.loads(line)["event"]] += 1
        if (events["plugin_build_active"] < 1
                or events["worker_hot_path"] < 4
                or events["runtime_scheduler_active"] < 1):
            raise RuntimeError(f"HYPIC quality runtime activation insufficient: {dict(events)}")
        result["hypic_evidence_sha256"] = sha256(evidence)
        result["hypic_evidence_bytes"] = evidence.stat().st_size
        result["hypic_activation_counts"] = {
            key: events[key] for key in
            ("plugin_build_active", "worker_hot_path", "runtime_scheduler_active")}
    return result


def expected_reference(dataset: str, sample: dict) -> str:
    if dataset == "longbenchv2":
        return str(sample["answer"]).strip()
    return str(sample["answer"]).split("#### ")[1].replace(",", "")


def audit_unit(arm: str, dataset: str, repeat: int, samples: list[dict],
               scorer) -> tuple[dict, list[dict]]:
    summary = validate_unit(arm, dataset, repeat)
    stem = f"{dataset}.run{repeat}"
    directory = QROOT / "quality" / arm
    details_path = directory / f"{stem}.jsonl"
    summary_path = directory / f"{stem}.summary.json"
    receipt_path = directory / f"{stem}.receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get("summary_sha256") != sha256(summary_path)
            or receipt.get("details_sha256") != sha256(details_path)
            or receipt.get("container_id") is None
            or receipt.get("requests") != len(samples)):
        raise RuntimeError(f"{arm}/{stem}: unit receipt mismatch")
    rows = [json.loads(line) for line in details_path.read_text(encoding="utf-8").splitlines() if line]
    if [row["index"] for row in rows] != list(range(len(samples))):
        raise RuntimeError(f"{arm}/{stem}: unordered, missing or duplicate indexes")
    correct = 0
    completion_tokens = 0
    categories: dict[str, dict[str, list[bool]]] = {"difficulty": {}, "length": {}}
    for row, sample in zip(rows, samples):
        reference = expected_reference(dataset, sample)
        prediction, rescored = scorer(dataset, row["response_text"], reference)
        if (row.get("reference") != reference or row.get("sample_id") != sample.get("_id")
                or row.get("prediction") != prediction or row.get("correct") is not rescored
                or row.get("difficulty") != sample.get("difficulty")
                or row.get("length") != sample.get("length")
                or row.get("response_sha256") != hashlib.sha256(
                    row["response_text"].encode("utf-8")).hexdigest()):
            raise RuntimeError(f"{arm}/{stem}: sample/scorer mismatch at index {row['index']}")
        correct += rescored
        completion_tokens += row["usage"]["completion_tokens"]
        if dataset == "longbenchv2":
            for field in categories:
                categories[field].setdefault(str(sample.get(field)), []).append(rescored)
    finish = dict(Counter(str(row.get("finish_reason")) for row in rows))
    if (summary["correct"] != correct
            or summary["completion_tokens"] != completion_tokens
            or summary["finish_reasons"] != finish
            or not math.isclose(summary["accuracy_pct"], 100 * correct / len(samples),
                                abs_tol=1e-9, rel_tol=1e-9)):
        raise RuntimeError(f"{arm}/{stem}: summary arithmetic mismatch")
    computed_categories = {
        field: {key: 100 * sum(values) / len(values) for key, values in groups.items()}
        for field, groups in categories.items()
    } if dataset == "longbenchv2" else {}
    if computed_categories != summary["category_accuracy_pct"]:
        raise RuntimeError(f"{arm}/{stem}: category arithmetic mismatch")
    result = {
        "accuracy_pct": summary["accuracy_pct"], "correct": correct,
        "requests": len(samples), "completion_tokens": completion_tokens,
        "length_limit_count": finish.get("length", 0),
        "length_limit_rate_pct": 100 * finish.get("length", 0) / len(samples),
        "category_accuracy_pct": computed_categories,
        "summary_sha256": sha256(summary_path), "details_sha256": sha256(details_path),
        "receipt_sha256": sha256(receipt_path),
    }
    return result, rows


def describe_delta(label: str, baseline: list[float], treatment: list[float]) -> dict:
    base_mean = statistics.mean(baseline)
    treated_mean = statistics.mean(treatment)
    delta = treated_mean - base_mean
    return {"metric": label, "baseline_runs": baseline, "treatment_runs": treatment,
            "baseline_mean": base_mean, "treatment_mean": treated_mean,
            "delta": delta, "baseline_range": [min(baseline), max(baseline)]}


def main() -> int:
    fingerprint = preflight()
    arm_variable = frozen_pair_seam()
    evaluator = frozen_evaluator()
    sample_map = {dataset: samples_for(dataset) for dataset in DATASETS}
    service = {arm: service_receipt(arm, fingerprint) for arm in ARMS}
    units: dict[str, dict[str, list[dict]]] = {arm: {dataset: [] for dataset in DATASETS}
                                                for arm in ARMS}
    raw: dict[str, dict[str, dict[int, list[dict]]]] = {
        arm: {dataset: {} for dataset in DATASETS} for arm in ARMS}
    for arm in ARMS:
        for dataset, repeat in UNIT_ORDER:
            result, rows = audit_unit(arm, dataset, repeat, sample_map[dataset],
                                      evaluator.score_case)
            units[arm][dataset].append(result)
            raw[arm][dataset][repeat] = rows
            if json.loads((QROOT / "quality" / arm /
                           f"{dataset}.run{repeat}.receipt.json").read_text())[
                               "container_id"] != service[arm]["container_id"]:
                raise RuntimeError(f"{arm}/{dataset}.run{repeat}: wrong service container")
    pairwise = {}
    for dataset in DATASETS:
        pairwise[dataset] = []
        for repeat in (1, 2, 3):
            base = raw["no-cache"][dataset][repeat]
            treated = raw["hypic-only"][dataset][repeat]
            counts = Counter()
            for left, right in zip(base, treated):
                if (left["index"] != right["index"]
                        or left["reference"] != right["reference"]
                        or left.get("sample_id") != right.get("sample_id")
                        or left["usage"]["prompt_tokens"] != right["usage"]["prompt_tokens"]):
                    raise RuntimeError(f"{dataset}/run{repeat}: paired input identity mismatch")
                counts["win" if right["correct"] and not left["correct"] else
                       "loss" if left["correct"] and not right["correct"] else
                       "both_correct" if left["correct"] else "both_wrong"] += 1
            pairwise[dataset].append({"run": repeat, **dict(counts)})
    deltas = []
    for dataset in DATASETS:
        deltas.append(describe_delta(f"{dataset}.accuracy_pct",
                     [u["accuracy_pct"] for u in units["no-cache"][dataset]],
                     [u["accuracy_pct"] for u in units["hypic-only"][dataset]]))
        deltas.append(describe_delta(f"{dataset}.length_limit_rate_pct",
                     [u["length_limit_rate_pct"] for u in units["no-cache"][dataset]],
                     [u["length_limit_rate_pct"] for u in units["hypic-only"][dataset]]))
    for field in ("difficulty", "length"):
        keys = units["no-cache"]["longbenchv2"][0]["category_accuracy_pct"][field]
        for key in sorted(keys):
            deltas.append(describe_delta(f"longbenchv2.{field}.{key}.accuracy_pct",
                         [u["category_accuracy_pct"][field][key]
                          for u in units["no-cache"]["longbenchv2"]],
                         [u["category_accuracy_pct"][field][key]
                          for u in units["hypic-only"]["longbenchv2"]]))
    adverse = [item for item in deltas if
               (item["delta"] > 1e-9 if item["metric"].endswith("length_limit_rate_pct")
                else item["delta"] < -1e-9)]
    beyond_range = [item["metric"] for item in adverse if
                    (item["treatment_mean"] > item["baseline_range"][1]
                     if item["metric"].endswith("length_limit_rate_pct")
                     else item["treatment_mean"] < item["baseline_range"][0])]
    decision = "pass" if not adverse else "regression" if beyond_range else "inconclusive"
    report = {
        "schema": "hypic-bindingoff-quality-independent-audit/v1",
        "all_twelve_units_valid": True, "paired_input_identity_valid": True,
        "frozen_fingerprint": fingerprint, "only_arm_variable": arm_variable,
        "service": service,
        "per_unit": units, "pairwise": pairwise, "deltas": deltas,
        "adverse_metrics": [item["metric"] for item in adverse],
        "beyond_baseline_range": beyond_range,
        "quality_gate_pass": decision == "pass", "quality_decision": decision,
        "scoring_note": "Raw responses independently re-scored with the pinned, hash-verified evaluator; arithmetic, sample identity and receipts checked separately.",
    }
    write_json(AUDIT_PATH, report)
    print(json.dumps({"report": str(AUDIT_PATH), "decision": decision,
                      "adverse_metrics": report["adverse_metrics"],
                      "beyond_baseline_range": beyond_range}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
