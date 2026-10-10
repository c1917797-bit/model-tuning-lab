#!/usr/bin/env python3
"""Independent raw-row audit of the original-source r18 GSM8K safety pair."""

from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from r18_c32_gsm8k_adapter import check_preregistration, configure


PREREG = check_preregistration()
quality = configure("no-cache")
BASE = Path(PREREG["arm_roots"]["no-cache"])
CAND = Path(PREREG["arm_roots"]["hypic-only"])
OUT = quality.ROOT / "hypic-r18-c32-2048-gsm8k-paired-audit.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frozen_evaluator():
    spec = importlib.util.spec_from_file_location("r18_frozen_gsm8k_eval", quality.EVALUATOR)
    require(spec is not None and spec.loader is not None, "GSM8K evaluator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen_samples() -> list[dict]:
    path, count, digest = quality.DATASETS["gsm8k"]
    require(quality.sha256(path) == digest == PREREG["dataset_sha256"],
            "GSM8K dataset hash drift")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line]
    require(len(rows) == count == 1319, "GSM8K sample count drift")
    return rows


def expected_reference(sample: dict) -> str:
    answer = str(sample["answer"])
    require("#### " in answer, "GSM8K answer delimiter absent")
    return answer.split("#### ", 1)[1].replace(",", "")


def pair_seam() -> dict:
    original_root = quality.QROOT
    try:
        quality.QROOT = BASE
        left = quality.spec("no-cache")
        right = quality.spec("hypic-only")
    finally:
        quality.QROOT = original_root
    require(sorted(left[1]) == sorted(right[1]), "GSM8K arm binds differ")
    require(left[3].replace("/no-cache", "/ARM") ==
            right[3].replace("/hypic-only", "/ARM"),
            "GSM8K arm commands differ")
    left_env = dict(item.split("=", 1) for item in left[2])
    right_env = dict(item.split("=", 1) for item in right[2])
    changes = {key: [left_env.get(key), right_env.get(key)]
               for key in left_env.keys() | right_env.keys()
               if left_env.get(key) != right_env.get(key)}
    require(set(changes) == {"VLLM_ASCEND_HYPIC_ENABLE",
                             "VLLM_ASCEND_HYPIC_EVIDENCE_FILE"}
            and changes["VLLM_ASCEND_HYPIC_ENABLE"] == ["0", "1"],
            "GSM8K arms differ beyond HYPIC switch and evidence path")
    return {"only_treatment_switch": ["0", "1"],
            "normalized_commands_equal": True, "binds_equal": True}


def audit_arm(root: Path, arm: str, samples: list[dict], evaluator) -> dict:
    require(root.is_dir(), f"{arm}: GSM8K root absent")
    contract = read(root / "contract.json")
    result = read(root / "arm-result.json")
    start = read(root / arm / "service-start.json")
    stop = read(root / arm / "service-stop.json")
    guard = read(root / arm / "lane-guard.json")
    fp = contract["fingerprint"]
    require(contract.get("schema") == "hypic-r18-c32-gsm8k-arm-contract/v1"
            and contract.get("arm") == arm
            and contract.get("dataset_sha256") == PREREG["dataset_sha256"]
            and contract.get("evaluator_sha256") == PREREG["evaluator_sha256"]
            and (contract.get("sample_count"), contract.get("repetitions"),
                 contract.get("concurrency"), contract.get("max_output_tokens"))
                == (1319, 3, 32, 2048)
            and contract.get("ignore_eos") is False
            and contract.get("enable_thinking") is False
            and contract.get("temperature") == contract.get("seed") == 0,
            f"{arm}: GSM8K contract drift")
    require(fp.get("source_commit") == PREREG["source_commit"]
            and fp.get("image") == PREREG["image"]
            and fp.get("model_index_sha256") == PREREG["model_index_sha256"]
            and fp.get("physical_npus") == [0, 1, 2, 3]
            and fp.get("gpu_memory_utilization") == 0.85
            and fp.get("material_cache_max_mb") == 3584
            and fp.get("max_materialized_segments") == 10
            and fp.get("unit_order") == [["gsm8k", i] for i in range(1, 4)]
            and start.get("fingerprint") == fp,
            f"{arm}: GSM8K service fingerprint drift")
    require(result.get("schema") == "hypic-r18-c32-gsm8k-arm-result/v1"
            and result.get("arm") == arm and result.get("error") is None
            and result.get("completed_units") == 3
            and result.get("contract_sha256") == quality.sha256(root / "contract.json")
            and result.get("service_stop_sha256") ==
                quality.sha256(root / arm / "service-stop.json")
            and result.get("lane_guard_sha256") ==
                quality.sha256(root / arm / "lane-guard.json"),
            f"{arm}: GSM8K controller terminal evidence invalid")
    workers = start.get("worker_pid_by_physical_npu", {})
    require(set(workers) == {"0", "1", "2", "3"}
            and len(set(workers.values())) == 4
            and sorted(workers.values()) == guard.get("expected_worker_pids")
            and guard.get("samples", 0) > 0
            and guard.get("foreign") == [] and guard.get("probe_errors") == [],
            f"{arm}: GSM8K physical worker or continuous isolation drift")
    require(start.get("container_id") == stop.get("container_id")
            == result.get("container_id")
            and all(stop.get(key) is True for key in
                    ("container_removed", "owned_npus_released", "port_released",
                     "lane_available"))
            and stop.get("foreign_npu_processes") == []
            and stop.get("service_log_error") is None,
            f"{arm}: exact GSM8K resource release unproven")
    attestation_path = root / arm / f"source-attestation.{start['container_id'][:12]}.json"
    attestation = read(attestation_path)
    source_root = Path(fp["plugin_source_root"])
    source = quality.python_source_digest(source_root / "hypic_vllm_ascend")
    original_root = quality.QROOT
    try:
        quality.QROOT = root
        _, expected_binds, _, expected_command = quality.spec(arm)
    finally:
        quality.QROOT = original_root
    require(start.get("source_attestation_sha256") == quality.sha256(attestation_path)
            and read(root / arm / "source-attestation.json") == attestation
            and attestation.get("selected_source_commit") == PREREG["source_commit"]
            and attestation.get("container_id") == start["container_id"]
            and attestation.get("image") == PREREG["image"]
            and attestation.get("python_files") == source["python_files"]
            and attestation.get("python_tree_sha256") == source["python_tree_sha256"]
            and sorted(attestation.get("actual_binds", [])) == sorted(expected_binds)
            and attestation.get("actual_command") == ["bash", "-lc", expected_command],
            f"{arm}: GSM8K live original-source attestation drift")
    units = []
    all_rows = []
    original_root = quality.QROOT
    try:
        quality.QROOT = root
        for repeat in range(1, 4):
            summary = quality.validate_unit(arm, "gsm8k", repeat)
            directory = root / "quality" / arm
            stem = f"gsm8k.run{repeat}"
            details_path = directory / f"{stem}.jsonl"
            receipt_path = directory / f"{stem}.receipt.json"
            receipt = read(receipt_path)
            require(receipt == result["unit_receipts"][repeat - 1]
                    and receipt.get("container_id") == start["container_id"]
                    and receipt.get("details_sha256") == quality.sha256(details_path),
                    f"{arm}/run{repeat}: unit receipt drift")
            rows = [json.loads(line) for line in details_path.read_text().splitlines() if line]
            require(len(rows) == 1319, f"{arm}/run{repeat}: raw row count drift")
            correct = 0
            length = 0
            for index, (row, sample) in enumerate(zip(rows, samples)):
                reference = expected_reference(sample)
                response = row.get("response_text")
                require(row.get("index") == index and row.get("sample_id") == sample.get("_id")
                        and row.get("reference") == reference
                        and row.get("ok") is True and row.get("error") is None
                        and isinstance(response, str)
                        and row.get("response_sha256") == hashlib.sha256(response.encode()).hexdigest()
                        and row.get("finish_reason") in {"stop", "length"},
                        f"{arm}/run{repeat}: raw identity or response drift at {index}")
                prediction, rescored = evaluator.score_case("gsm8k", response, reference)
                require(row.get("prediction") == prediction
                        and row.get("correct") is bool(rescored),
                        f"{arm}/run{repeat}: scorer drift at {index}")
                correct += bool(rescored)
                length += row["finish_reason"] == "length"
                all_rows.append({"index": index, "repeat": repeat,
                                 "correct": bool(rescored),
                                 "prompt_tokens": row["usage"]["prompt_tokens"],
                                 "finish_reason": row["finish_reason"]})
            require(summary["correct"] == correct
                    and summary["finish_reasons"].get("length", 0) == length,
                    f"{arm}/run{repeat}: independent score arithmetic drift")
            units.append({"repeat": repeat, "correct": correct,
                          "length_limit": length,
                          "summary_sha256": quality.sha256(directory / f"{stem}.summary.json"),
                          "details_sha256": quality.sha256(details_path),
                          "receipt_sha256": quality.sha256(receipt_path)})
    finally:
        quality.QROOT = original_root
    require(len(all_rows) == 1319 * 3, f"{arm}: total GSM8K rows incomplete")
    return {"root": str(root), "container_id": start["container_id"],
            "contract_sha256": quality.sha256(root / "contract.json"),
            "arm_result_sha256": quality.sha256(root / "arm-result.json"),
            "guard_samples": guard["samples"],
            "source_attestation_sha256": quality.sha256(attestation_path),
            "units": units, "rows": all_rows, "fingerprint": fp}


def main() -> int:
    require(not OUT.exists(), "r18 GSM8K audit output exists; never overwrite")
    require(quality.sha256(quality.EVALUATOR) == PREREG["evaluator_sha256"],
            "GSM8K evaluator SHA drift")
    seam = pair_seam()
    samples = frozen_samples()
    evaluator = frozen_evaluator()
    baseline = audit_arm(BASE, "no-cache", samples, evaluator)
    candidate = audit_arm(CAND, "hypic-only", samples, evaluator)
    require(baseline["fingerprint"] == candidate["fingerprint"]
            and baseline["container_id"] != candidate["container_id"],
            "GSM8K arm environment or service identity mismatch")
    for repeat in range(1, 4):
        b = [row for row in baseline["rows"] if row["repeat"] == repeat]
        c = [row for row in candidate["rows"] if row["repeat"] == repeat]
        require([row["prompt_tokens"] for row in b] ==
                [row["prompt_tokens"] for row in c],
                f"GSM8K run{repeat}: paired prompt-token identity drift")
    base_runs = [unit["correct"] for unit in baseline["units"]]
    cand_runs = [unit["correct"] for unit in candidate["units"]]
    base_length = [unit["length_limit"] for unit in baseline["units"]]
    cand_length = [unit["length_limit"] for unit in candidate["units"]]
    pass_quality = (sum(cand_runs) / 3 >= min(base_runs)
                    and sum(cand_length) / 3 <= max(base_length))
    pairwise = Counter()
    for left, right in zip(baseline["rows"], candidate["rows"]):
        require((left["index"], left["repeat"]) ==
                (right["index"], right["repeat"]),
                "GSM8K paired index mismatch")
        pairwise["improved" if right["correct"] and not left["correct"] else
                 "regressed" if left["correct"] and not right["correct"] else
                 "unchanged"] += 1
    report = {
        "schema": "hypic-r18-c32-gsm8k-audit/v1", "evidence_valid": True,
        "scope": "GSM8K off-path runtime-enabled safety, c32 max-2048 physical NPU0-3",
        "source_commit": PREREG["source_commit"], "one_switch_seam": seam,
        "baseline": {key: value for key, value in baseline.items() if key != "rows"},
        "candidate": {key: value for key, value in candidate.items() if key != "rows"},
        "baseline_correct_by_run": base_runs,
        "candidate_correct_by_run": cand_runs,
        "baseline_length_limit_by_run": base_length,
        "candidate_length_limit_by_run": cand_length,
        "delta_percentage_points": 100 * (sum(cand_runs) - sum(base_runs)) / (1319 * 3),
        "pairwise": dict(pairwise),
        "quality_decision": "PASS" if pass_quality else "REJECT_OR_QUALIFY",
        "hot_path_attribution": "not claimed for GSM8K natural payload",
    }
    quality.write_json(OUT, report)
    print(json.dumps({"audit": str(OUT),
                      "quality_decision": report["quality_decision"],
                      "baseline_correct_by_run": base_runs,
                      "candidate_correct_by_run": cand_runs}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
