#!/usr/bin/env python3
"""Run and independently recheck a paired 2048-token quality ruler at 41984 context."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import signal
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from baseline_registry import quality_entries
from profile_service import ROOT, sha256
from quality_context_service import CONTEXT, IMAGE, QROOT, SOURCE_COMMIT, inspect, NAMES, start, stop


HERE = Path(__file__).resolve().parent
EVALUATOR = HERE.parent / "WS-20260904-qwen38-dense-paper-to-ascend" / "hypic_quality_eval.py"
DATASETS = {
    "longbenchv2": (Path("/cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json"), 127),
    "gsm8k": (Path("/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl"), 1319),
}
MODEL_DIR = Path("/cache/efim/Qwen3.6-27B")
MODEL_NAME = "qwen36-hypic-e2e-2048"
BASE_URL = "http://127.0.0.1:8223"
DEADLINE = datetime.fromisoformat("2026-10-07T11:24:37+00:00")
QUALITY_DECISION_RULE = (
    "Pass only with nonnegative three-run mean accuracy deltas for both datasets, "
    "nonnegative LongBench difficulty/length category deltas, and no increase "
    "in length-limit finish rate. A negative signal beyond the matching baseline "
    "three-run range is regression; one within that range is inconclusive."
)


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def status(stage: str, **detail: object) -> None:
    value = {
        "schema": "hypic-quality-context-controller-status/v1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        **detail,
    }
    write(QROOT / "controller-status.json", value)
    print(json.dumps(value, sort_keys=True), flush=True)


def remaining_seconds() -> int:
    return int((DEADLINE - datetime.now(timezone.utc)).total_seconds())


def contract() -> tuple[dict, dict]:
    parent = read(ROOT / "baseline-contract.json")
    parent_fp = parent["fingerprint"]
    canonical_parent = json.dumps(parent_fp, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical_parent).hexdigest() != parent.get("fingerprint_sha256"):
        raise RuntimeError("parent baseline fingerprint hash mismatch")
    if (parent_fp["image_digest"] != IMAGE or parent_fp["source_commit"] != SOURCE_COMMIT
            or parent_fp["quality_protocol"]["max_out_len"] != 2048):
        raise RuntimeError("parent experiment identity drift")
    model_index = MODEL_DIR / "model.safetensors.index.json"
    if sha256(model_index) != parent_fp["model_index_sha256"]:
        raise RuntimeError("model index hash differs from parent baseline")
    for shard in parent_fp["model_shards"]:
        info = (MODEL_DIR / shard["name"]).stat()
        if info.st_size != shard["size"] or info.st_mtime_ns != shard["mtime_ns"]:
            raise RuntimeError(f"model shard metadata drift: {shard['name']}")
    for dataset, (path, _) in DATASETS.items():
        if sha256(path) != parent_fp[f"{'longbench' if dataset == 'longbenchv2' else 'gsm8k'}_sha256"]:
            raise RuntimeError(f"{dataset}: dataset hash drift")
    if sha256(EVALUATOR) != parent_fp["quality_evaluator_sha256"]:
        raise RuntimeError("quality evaluator hash drift")
    source_snapshot = ROOT / "environment-and-container-snapshot.txt"
    fingerprint = {
        "parent_baseline_fingerprint_sha256": parent["fingerprint_sha256"],
        "source_snapshot_sha256": sha256(source_snapshot),
        "source_commit": SOURCE_COMMIT,
        "image": IMAGE,
        "model_index_sha256": parent_fp["model_index_sha256"],
        "longbench_sha256": parent_fp["longbench_sha256"],
        "gsm8k_sha256": parent_fp["gsm8k_sha256"],
        "quality_evaluator_sha256": parent_fp["quality_evaluator_sha256"],
        "physical_npus": [0, 1, 2, 3],
        "tensor_parallel_size": 4,
        "max_model_len": CONTEXT,
        "max_num_batched_tokens": CONTEXT,
        "quality_max_output_tokens": 2048,
        "longbench_historical_max_prompt_tokens": 39642,
        "longbench_max_prompt_plus_cap": 41690,
        "concurrency": 32,
        "repetitions_per_dataset_per_arm": 3,
        "datasets": {"longbenchv2": 127, "gsm8k": 1319},
        "separate_from_performance_baseline": True,
    }
    payload = json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode()
    value = {
        "schema": "hypic-quality-context-contract/v1",
        "fingerprint": fingerprint,
        "fingerprint_sha256": hashlib.sha256(payload).hexdigest(),
    }
    path = QROOT / "quality-context-contract.json"
    if path.exists():
        if read(path) != value:
            raise RuntimeError("frozen quality-context contract changed")
    else:
        write(path, value)
    return parent, value


def validate_one(arm: str, dataset: str, index: int, parent: dict) -> dict:
    data_path, expected = DATASETS[dataset]
    directory = QROOT / "quality" / arm
    stem = f"{dataset}.run{index}"
    summary_path = directory / f"{stem}.summary.json"
    details_path = directory / f"{stem}.jsonl"
    summary = read(summary_path)
    scorer = ("supplied_ais_bench_first_option_postprocess" if dataset == "longbenchv2"
              else "supplied_ais_bench_gsm8k_numeric_postprocess")
    expected_fields = {
        "schema": "hypic-quality-eval/v1", "dataset": dataset, "run_id": f"run{index}",
        "data_sha256": sha256(data_path),
        "evaluator_script_sha256": sha256(EVALUATOR),
        "scorer": scorer, "model": MODEL_NAME, "base_url": BASE_URL,
        "concurrency": 32, "max_out_len": 2048, "temperature": 0,
        "seed": 0, "ignore_eos": False, "enable_thinking": False,
        "requests": expected, "successful": expected, "failed": 0,
    }
    for key, value in expected_fields.items():
        if summary.get(key) != value:
            raise ValueError(f"{summary_path}: {key} mismatch")
    if Path(summary.get("details_path", "")).resolve() != details_path.resolve():
        raise ValueError("quality detail path mismatch")
    if summary.get("details_sha256") != sha256(details_path):
        raise ValueError("quality detail hash mismatch")
    rows = [json.loads(line) for line in details_path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) != expected or sorted(row.get("index") for row in rows) != list(range(expected)):
        raise ValueError("quality sample indexes missing or duplicated")
    for row in rows:
        response = row.get("response_text")
        usage = row.get("usage") or {}
        if not (
            row.get("ok") is True and row.get("error") is None
            and isinstance(response, str)
            and row.get("response_sha256") == hashlib.sha256(response.encode()).hexdigest()
            and isinstance(usage.get("prompt_tokens"), int) and usage["prompt_tokens"] > 0
            and isinstance(usage.get("completion_tokens"), int)
            and 0 <= usage["completion_tokens"] <= 2048
        ):
            raise ValueError(f"invalid quality row: {arm}/{dataset}/run{index}/{row.get('index')}")
    correct = sum(row.get("correct") is True for row in rows)
    completions = sum(row["usage"]["completion_tokens"] for row in rows)
    accuracy = 100 * correct / expected
    if not (
        summary.get("correct") == correct
        and summary.get("completion_tokens") == completions
        and isinstance(summary.get("accuracy_pct"), (int, float))
        and math.isclose(summary["accuracy_pct"], accuracy, rel_tol=1e-9, abs_tol=1e-9)
        and sum(summary.get("finish_reasons", {}).values()) == expected
    ):
        raise ValueError("quality summary and raw rows disagree")
    return summary


def run_one(arm: str, dataset: str, index: int, parent: dict) -> None:
    data_path, _ = DATASETS[dataset]
    directory = QROOT / "quality" / arm
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{dataset}.run{index}"
    summary_path = directory / f"{stem}.summary.json"
    if summary_path.exists():
        validate_one(arm, dataset, index, parent)
        status("quality-run-reused", arm=arm, dataset=dataset, run=index,
               summary_sha256=sha256(summary_path))
        return
    if remaining_seconds() < 3600:
        raise RuntimeError("quality deadline safety margin reached before next run")
    status("quality-run-running", arm=arm, dataset=dataset, run=index)
    command = [
        sys.executable, str(EVALUATOR), "--dataset", dataset, "--data", str(data_path),
        "--base-url", BASE_URL, "--model", MODEL_NAME, "--output-dir", str(directory),
        "--run-id", f"run{index}", "--concurrency", "32", "--max-out-len", "2048",
        "--seed", "0", "--timeout", "2400", "--retries", "2",
    ]
    log_path = directory / f"{stem}.log"
    with log_path.open("a", encoding="utf-8") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                timeout=min(7200, max(1, remaining_seconds() - 600)),
                                check=False)
    if result.returncode:
        raise RuntimeError(f"{arm}/{stem}: evaluator exit {result.returncode}; see {log_path}")
    validate_one(arm, dataset, index, parent)
    status("quality-run-verified", arm=arm, dataset=dataset, run=index,
           summary_sha256=sha256(summary_path), details_sha256=sha256(directory / f"{stem}.jsonl"))


def freeze_arm(arm: str, parent: dict, quality_contract: dict) -> None:
    entries = quality_entries(QROOT, parent, arm)
    registry_path = QROOT / f"{arm}-quality-registry.json"
    registry = {
        "schema": "hypic-quality-context-arm-registry/v1",
        "arm": arm,
        "contract_sha256": quality_contract["fingerprint_sha256"],
        "raw_artifacts": entries,
    }
    if registry_path.exists():
        if read(registry_path) != registry:
            raise RuntimeError(f"{arm} frozen quality registry drift")
    else:
        write(registry_path, registry)
    status("quality-arm-frozen", arm=arm, registry_sha256=sha256(registry_path))


def audit(parent: dict, quality_contract: dict) -> dict:
    rows: dict[str, dict[str, list[dict]]] = {}
    for arm in ("no-cache", "hypic-only"):
        freeze_arm(arm, parent, quality_contract)
        started = read(QROOT / arm / "service-start.json")
        stopped = read(QROOT / arm / "service-stop.json")
        if not (
            started.get("schema") == "hypic-quality-context-service-start/v1"
            and started.get("arm") == arm
            and started.get("container") == NAMES[arm]
            and started.get("container_id") == stopped.get("container_id")
            and started.get("image") == IMAGE
            and started.get("source_snapshot_sha256")
            == quality_contract["fingerprint"]["source_snapshot_sha256"]
            and started.get("max_model_len") == CONTEXT
            and started.get("max_num_batched_tokens") == CONTEXT
            and started.get("physical_npus") == [0, 1, 2, 3]
            and started.get("health_passed") is True
            and isinstance(started.get("worker_pid_by_physical_npu"), dict)
            and set(started["worker_pid_by_physical_npu"]) == {"0", "1", "2", "3"}
            and len(set(started["worker_pid_by_physical_npu"].values())) == 4
            and all(isinstance(pid, int) and pid > 0
                    for pid in started["worker_pid_by_physical_npu"].values())
            and started.get("npu_smi_at_health_sha256")
            == sha256(QROOT / arm / "npu-smi-at-health.txt")
            and started.get("docker_top_at_health_sha256")
            == sha256(QROOT / arm / "docker-top-at-health.txt")
            and stopped.get("schema") == "hypic-quality-context-service-stop/v1"
            and stopped.get("arm") == arm
            and stopped.get("container") == NAMES[arm]
            and stopped.get("owned_npus_released") is True
            and stopped.get("port_released") is True
            and stopped.get("container_removed") is True
        ):
            raise ValueError(f"{arm}: service identity or release receipt mismatch")
        rows[arm] = {}
        for dataset in DATASETS:
            rows[arm][dataset] = [validate_one(arm, dataset, index, parent) for index in (1, 2, 3)]
    paired_counts = {dataset: {"wins": 0, "losses": 0, "unchanged": 0} for dataset in DATASETS}
    for dataset in DATASETS:
        for index in (1, 2, 3):
            paths = [QROOT / "quality" / arm / f"{dataset}.run{index}.jsonl"
                     for arm in ("no-cache", "hypic-only")]
            paired = [[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
                      for path in paths]
            for baseline, treatment in zip(*paired):
                if (baseline.get("index") != treatment.get("index")
                        or baseline.get("sample_id") != treatment.get("sample_id")
                        or baseline.get("reference") != treatment.get("reference")
                        or (baseline.get("usage") or {}).get("prompt_tokens")
                        != (treatment.get("usage") or {}).get("prompt_tokens")):
                    raise ValueError(f"{dataset}/run{index}: cross-arm sample/protocol drift")
                outcome = ("wins" if treatment["correct"] and not baseline["correct"]
                           else "losses" if baseline["correct"] and not treatment["correct"]
                           else "unchanged")
                paired_counts[dataset][outcome] += 1
    accuracy = {
        arm: {
            dataset: {
                "run_accuracy_pct": [row["accuracy_pct"] for row in rows[arm][dataset]],
                "mean_accuracy_pct": statistics.mean(row["accuracy_pct"] for row in rows[arm][dataset]),
                "run_range_pct": (max(row["accuracy_pct"] for row in rows[arm][dataset])
                                  - min(row["accuracy_pct"] for row in rows[arm][dataset])),
                "run_stdev_pct": statistics.stdev(row["accuracy_pct"] for row in rows[arm][dataset]),
            }
            for dataset in DATASETS
        }
        for arm in rows
    }
    delta = {
        dataset: accuracy["hypic-only"][dataset]["mean_accuracy_pct"]
        - accuracy["no-cache"][dataset]["mean_accuracy_pct"]
        for dataset in DATASETS
    }
    signals = []

    def check_signal(scope: str, baseline_values: list[float], candidate_values: list[float],
                     lower_is_worse: bool = True) -> None:
        baseline_mean = statistics.mean(baseline_values)
        candidate_mean = statistics.mean(candidate_values)
        directional_delta = ((candidate_mean - baseline_mean) if lower_is_worse
                             else (baseline_mean - candidate_mean))
        baseline_range = max(baseline_values) - min(baseline_values)
        if directional_delta < 0:
            signals.append({
                "scope": scope,
                "directional_delta_pct": directional_delta,
                "baseline_run_range_pct": baseline_range,
                "classification": ("regression" if -directional_delta > baseline_range
                                   else "inconclusive"),
            })

    for dataset in DATASETS:
        baseline = rows["no-cache"][dataset]
        candidate = rows["hypic-only"][dataset]
        check_signal(f"{dataset}:accuracy", [row["accuracy_pct"] for row in baseline],
                     [row["accuracy_pct"] for row in candidate])
        expected = DATASETS[dataset][1]
        check_signal(f"{dataset}:length-limit-rate",
                     [100 * row["finish_reasons"].get("length", 0) / expected for row in baseline],
                     [100 * row["finish_reasons"].get("length", 0) / expected for row in candidate],
                     lower_is_worse=False)
    for field in ("difficulty", "length"):
        baseline_keys = set(rows["no-cache"]["longbenchv2"][0]["category_accuracy_pct"][field])
        for arm in ("no-cache", "hypic-only"):
            for row in rows[arm]["longbenchv2"]:
                if set(row["category_accuracy_pct"][field]) != baseline_keys:
                    raise ValueError(f"LongBench {field} category keys drift")
        for value in sorted(baseline_keys):
            check_signal(f"longbenchv2:{field}:{value}",
                         [row["category_accuracy_pct"][field][value]
                          for row in rows["no-cache"]["longbenchv2"]],
                         [row["category_accuracy_pct"][field][value]
                          for row in rows["hypic-only"]["longbenchv2"]])
    quality_classification = ("regression" if any(signal["classification"] == "regression"
                                              for signal in signals)
                              else "inconclusive" if signals else "pass")
    report = {
        "schema": "hypic-paired-2048-quality-context-audit/v1",
        "quality_evidence_complete": True,
        "performance_gate_overridden": False,
        "context_contract_sha256": quality_contract["fingerprint_sha256"],
        "accuracy": accuracy,
        "delta_percentage_points": delta,
        "no_negative_accuracy_delta_observed": all(value >= 0 for value in delta.values()),
        "quality_decision_rule": QUALITY_DECISION_RULE,
        "quality_classification": quality_classification,
        "negative_or_uncertain_signals": signals,
        "paired_sample_counts": paired_counts,
        "baseline_registry_sha256": sha256(QROOT / "no-cache-quality-registry.json"),
        "treatment_registry_sha256": sha256(QROOT / "hypic-only-quality-registry.json"),
    }
    write(QROOT / "quality-context-audit.json", report)
    return report


def interrupt(_signal: int, _frame: object) -> None:
    raise RuntimeError("quality controller interrupted; executing owned-resource cleanup")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run", "audit-only"))
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    QROOT.mkdir(parents=True, exist_ok=True)
    lock = (QROOT / "controller.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    parent, quality_contract = contract()
    if args.mode == "audit-only":
        report = audit(parent, quality_contract)
        print(json.dumps(report, sort_keys=True), flush=True)
        return 0
    for arm in ("no-cache", "hypic-only"):
        if remaining_seconds() < 3600:
            status("deadline-before-arm", arm=arm)
            return 2
        status("quality-arm-starting", arm=arm)
        error = None
        try:
            start(arm)
            for dataset in DATASETS:
                for index in (1, 2, 3):
                    run_one(arm, dataset, index, parent)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            status("quality-arm-failed", arm=arm, error=error)
        finally:
            if inspect(NAMES[arm]) is not None:
                try:
                    stop(arm)
                    status("quality-arm-released", arm=arm, prior_error=error)
                except Exception as exc:
                    status("quality-cleanup-failed", arm=arm, prior_error=error,
                           cleanup_error=f"{type(exc).__name__}: {exc}")
                    return 3
        if error:
            return 2
        freeze_arm(arm, parent, quality_contract)
    report = audit(parent, quality_contract)
    status("quality-complete-and-released", audit_sha256=sha256(QROOT / "quality-context-audit.json"),
           delta_percentage_points=report["delta_percentage_points"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
