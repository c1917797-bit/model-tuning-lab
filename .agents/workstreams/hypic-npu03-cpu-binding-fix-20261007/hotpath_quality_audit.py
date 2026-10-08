#!/usr/bin/env python3
"""Independent, fail-closed audit of the prospective HYPIC hot-path quality arms."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
AUDIT_CAMPAIGN = os.environ.get("HYPIC_HOTPATH_AUDIT_CAMPAIGN", "original")
if AUDIT_CAMPAIGN not in {"original", "reserve", "cache10", "cache10r1", "cache10r2"}:
    raise RuntimeError("unrecognized hot-path audit campaign")
if AUDIT_CAMPAIGN in {"reserve", "cache10", "cache10r1", "cache10r2"}:
    os.environ["HYPIC_QUALITY_ATTEMPT"] = (
        "hotpath-reserve-full-baseline" if AUDIT_CAMPAIGN == "reserve" else
        f"hotpath-{AUDIT_CAMPAIGN}-full-baseline"
    )
import binding_off_quality as quality

ROOT_SUFFIX = ("hotpath-reserve-full" if AUDIT_CAMPAIGN == "reserve" else
               f"hotpath-{AUDIT_CAMPAIGN}-full" if AUDIT_CAMPAIGN.startswith("cache10") else
               "hotpath-full")
BASE = quality.ROOT / f"quality-context-41984-{ROOT_SUFFIX}-baseline"
CAND = quality.ROOT / f"quality-context-41984-{ROOT_SUFFIX}-hypic"
OUT = quality.ROOT / ("hotpath-quality-reserve-full-audit.json" if AUDIT_CAMPAIGN == "reserve"
                      else f"hotpath-quality-{AUDIT_CAMPAIGN}-full-audit.json"
                      if AUDIT_CAMPAIGN.startswith("cache10")
                      else "hotpath-quality-full-audit.json")
FROZEN = quality.ROOT / "quality-context-41984-clean2/quality/no-cache/longbenchv2.run1.jsonl"
FROZEN_SHA = "812a4281c167327ae69b96766e550f58ffb905c889c60bc0a649850ec5cc5810"
EXPECTED = 127
REPEATS = 3


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frozen_cases() -> list[dict]:
    require(quality.sha256(FROZEN) == FROZEN_SHA, "frozen clean2 row hash drift")
    require(quality.sha256(quality.EVALUATOR) == quality.EVALUATOR_SHA,
            "evaluator hash drift")
    spec = importlib.util.spec_from_file_location("frozen_quality_evaluator", quality.EVALUATOR)
    require(spec is not None and spec.loader is not None, "evaluator import missing")
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    samples = evaluator.load_samples("longbenchv2", quality.DATASETS["longbenchv2"][0])
    old_rows = [json.loads(line) for line in FROZEN.read_text().splitlines() if line]
    require(len(samples) == len(old_rows) == EXPECTED, "frozen sample count drift")
    result = []
    for index, (sample, old) in enumerate(zip(samples, old_rows)):
        prompt, reference = evaluator.build_case("longbenchv2", sample)
        measured = old["usage"]["prompt_tokens"]
        require(old["index"] == index and old["sample_id"] == sample["_id"],
                f"frozen identity drift at {index}")
        boundary = min(16384, ((measured - 2048) // 16) * 16)
        result.append({
            "index": index, "sample_id": sample["_id"], "prompt": prompt,
            "reference": reference, "prompt_tokens": measured,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "boundary": boundary, "difficulty": sample.get("difficulty"),
            "length": sample.get("length"),
        })
    return result, evaluator


def payload_hash(item: dict, max_tokens: int) -> str:
    payload = {
        "model": quality.MODEL_NAME,
        "messages": [{"role": "user", "content": item["prompt"]}],
        "max_tokens": max_tokens, "temperature": 0, "seed": 0,
        "ignore_eos": False, "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "vllm_xargs": {"hypic_segment_ends": [item["boundary"], item["prompt_tokens"]]},
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def frozen_pair_seam() -> dict:
    left = quality.spec("no-cache")
    right = quality.spec("hypic-only")
    require(sorted(left[1]) == sorted(right[1]), "arm bind mounts differ")
    normalized_left = left[3].replace("/no-cache", "/ARM")
    normalized_right = right[3].replace("/hypic-only", "/ARM")
    require(normalized_left == normalized_right, "arm serving commands differ")
    baseline_env = {key: value for key, value in
                    (entry.split("=", 1) for entry in left[2])}
    candidate_env = {key: value for key, value in
                     (entry.split("=", 1) for entry in right[2])}
    differences = {key: [baseline_env.get(key), candidate_env.get(key)]
                   for key in baseline_env.keys() | candidate_env.keys()
                   if baseline_env.get(key) != candidate_env.get(key)}
    require(differences == {
        "VLLM_ASCEND_HYPIC_ENABLE": ["0", "1"],
        "VLLM_ASCEND_HYPIC_EVIDENCE_FILE": [
            f"/results/{quality.QROOT.name}/no-cache/hypic-evidence.jsonl",
            f"/results/{quality.QROOT.name}/hypic-only/hypic-evidence.jsonl",
        ],
    }, "frozen arm environment differs beyond HYPIC and evidence path")
    return {"enable": differences["VLLM_ASCEND_HYPIC_ENABLE"],
            "binds_equal": True, "normalized_commands_equal": True}


def audit_arm(root: Path, arm: str, cases: list[dict], evaluator: object,
              *, expected: int = EXPECTED, mode: str = "full") -> dict:
    require(root.is_dir(), f"{arm}: root absent")
    require(len(cases) == expected, f"{arm}: auditor case count drift")
    contract = load_json(root / "contract.json")
    result = load_json(root / "arm-result.json")
    start = load_json(root / arm / "service-start.json")
    stop = load_json(root / arm / "service-stop.json")
    guard = load_json(root / arm / "lane-guard.json")
    require(contract["arm"] == arm and contract["mode"] == mode, f"{arm}: mode drift")
    require(contract["sample_indexes"] == list(range(expected)), f"{arm}: sample set drift")
    require(contract["repetitions"] == REPEATS and contract["concurrency"] == 8,
            f"{arm}: concurrency/repeat drift")
    require(contract["warm_requests_per_sample"] == 2
            and contract["max_output_tokens"] == 2048
            and contract["temperature"] == contract["seed"] == 0
            and contract["ignore_eos"] is False
            and contract["enable_thinking"] is False, f"{arm}: generation contract drift")
    require(contract["evaluator_sha256"] == quality.EVALUATOR_SHA
            and contract["dataset_sha256"] == quality.DATASETS["longbenchv2"][2]
            and contract["baseline_row_sha256"] == FROZEN_SHA,
            f"{arm}: frozen inputs drift")
    require(result["error"] is None and result["completed_samples"] == expected
            and result["scored_rows"] == expected * REPEATS, f"{arm}: incomplete controller")
    require(start["fingerprint"] == contract["fingerprint"],
            f"{arm}: service fingerprint drift")
    workers = start["worker_pid_by_physical_npu"]
    require(set(workers) == {"0", "1", "2", "3"}
            and len(set(workers.values())) == 4
            and sorted(workers.values()) == guard["expected_worker_pids"],
            f"{arm}: physical worker/guard identity drift")
    require(start["container_id"] == stop["container_id"]
            and stop["container_removed"] and stop["owned_npus_released"]
            and stop["port_released"] and stop["lane_available"]
            and not stop["foreign_npu_processes"] and not stop["service_log_error"],
            f"{arm}: exact service release unproven")
    require(guard["samples"] > 0 and not guard["foreign"]
            and not guard["probe_errors"], f"{arm}: lane guard not clean")
    require(result["service_stop_sha256"] == quality.sha256(root / arm / "service-stop.json")
            and result["lane_guard_sha256"] == quality.sha256(root / arm / "lane-guard.json"),
            f"{arm}: guard/release hash drift")
    rows = []
    ids = set()
    for item in cases:
        path = root / "samples" / f"{item['index']:03d}.json"
        require(path.is_file(), f"{arm}: sample {item['index']} absent")
        row = load_json(path)
        for key in ("index", "sample_id", "reference", "prompt_sha256",
                    "prompt_tokens", "difficulty", "length"):
            require(row[key] == item[key], f"{arm}: sample {item['index']} {key} drift")
        require(row["arm"] == arm and row["mode"] == mode
                and row["segment_ends"] == [item["boundary"], item["prompt_tokens"]],
                f"{arm}: sample {item['index']} segment drift")
        require(len(row["warm"]) == 2 and len(row["scores"]) == REPEATS,
                f"{arm}: sample {item['index']} warm/score count drift")
        for warm in row["warm"]:
            require(warm["request_sha256"] == payload_hash(item, 1)
                    and warm["usage"]["prompt_tokens"] == item["prompt_tokens"]
                    and 0 <= warm["usage"]["completion_tokens"] <= 1,
                    f"{arm}: sample {item['index']} warm request drift")
            require(warm["request_id"] not in ids, f"{arm}: duplicate request ID")
            ids.add(warm["request_id"])
        for repeat, scored in enumerate(row["scores"], 1):
            require(scored["repetition"] == repeat
                    and scored["request_sha256"] == payload_hash(item, 2048)
                    and scored["usage"]["prompt_tokens"] == item["prompt_tokens"]
                    and 0 <= scored["usage"]["completion_tokens"] <= 2048,
                    f"{arm}: sample {item['index']} score request drift")
            require(scored["request_id"] not in ids, f"{arm}: duplicate request ID")
            ids.add(scored["request_id"])
            response = scored["response_text"]
            require(isinstance(response, str)
                    and scored["response_sha256"] == hashlib.sha256(response.encode()).hexdigest(),
                    f"{arm}: sample {item['index']} response hash drift")
            prediction, correct = evaluator.score_case("longbenchv2", response, item["reference"])
            require(scored["prediction"] == prediction and scored["correct"] is bool(correct),
                    f"{arm}: sample {item['index']} score drift")
            rows.append({
                "index": item["index"], "repetition": repeat,
                "request_id": scored["request_id"], "correct": bool(correct),
                "prediction": prediction, "finish_reason": scored["finish_reason"],
                "completion_tokens": scored["usage"]["completion_tokens"],
                "difficulty": item["difficulty"], "length": item["length"],
            })
    require(len(list((root / "samples").glob("*.json"))) == expected,
            f"{arm}: extra sample artifact")
    require(len(rows) == expected * REPEATS and len(ids) == expected * (2 + REPEATS),
            f"{arm}: request cardinality drift")
    evidence = root / arm / "hypic-evidence.jsonl"
    events = [json.loads(line) for line in evidence.read_text().splitlines() if line] if evidence.exists() else []
    if evidence.exists():
        require(result["hypic_evidence_sha256"] == quality.sha256(evidence),
                f"{arm}: event hash drift")
    hot = [event for event in events if event.get("event") == "worker_hot_path"]
    if arm == "hypic-only":
        boundary_ids = [event.get("request_id") for event in events
                        if event.get("event") == "explicit_segment_boundary_active"]
        for scored in rows:
            rid = scored["request_id"]
            matches = [bid for bid in boundary_ids if bid == rid or
                       (isinstance(bid, str) and bid.startswith(rid + "-"))]
            require(len(matches) == 1, f"{arm}: scored boundary join failed at {scored['index']}")
        verified = sum(int(event.get("verified_hot_requests", 0)) for event in events
                       if event.get("event") == "complete_hybrid_repair")
        require(verified >= len(rows), f"{arm}: verified hot coverage {verified}/{len(rows)}")
        first = load_json(root / "samples/000.json")
        require(not first["warm_events"]["hot_worker_pids"]
                and len(first["first_scored_events"]["hot_worker_pids"]) == 4
                and first["first_scored_events"]["verified_hot_requests"] >= 1,
                f"{arm}: serialized hot-path sentinel failed")
    else:
        require(not hot, "no-cache arm emitted worker hot event")
        verified = 0
    return {
        "root": str(root), "contract_sha256": quality.sha256(root / "contract.json"),
        "arm_result_sha256": quality.sha256(root / "arm-result.json"),
        "container_id": start["container_id"], "guard_samples": guard["samples"],
        "scored_rows": len(rows), "verified_hot_requests": verified,
        "worker_hot_event_count": len(hot),
        "correct": sum(row["correct"] for row in rows),
        "length_limit": sum(row["finish_reason"] == "length" for row in rows),
        "rows": rows, "fingerprint": contract["fingerprint"],
    }


def decide(base: dict, cand: dict) -> dict:
    require(base["fingerprint"] == cand["fingerprint"], "arm environment fingerprint differs")
    require(base["container_id"] != cand["container_id"], "arms did not use fresh services")
    b = {(r["index"], r["repetition"]): r for r in base["rows"]}
    c = {(r["index"], r["repetition"]): r for r in cand["rows"]}
    require(b.keys() == c.keys(), "paired row keys differ")
    improved = sum(not b[key]["correct"] and c[key]["correct"] for key in b)
    regressed = sum(b[key]["correct"] and not c[key]["correct"] for key in b)
    strata = {}
    cliffs = []
    for field in ("difficulty", "length"):
        strata[field] = {}
        for value in sorted({str(row[field]) for row in base["rows"]}):
            base_runs = []
            cand_runs = []
            for repeat in range(1, REPEATS + 1):
                br = [r for r in base["rows"] if str(r[field]) == value and r["repetition"] == repeat]
                cr = [r for r in cand["rows"] if str(r[field]) == value and r["repetition"] == repeat]
                require(len(br) == len(cr) and br, f"{field}/{value}: stratum missing")
                base_runs.append(sum(r["correct"] for r in br) / len(br))
                cand_runs.append(sum(r["correct"] for r in cr) / len(cr))
            candidate_mean = sum(cand_runs) / REPEATS
            cliff = candidate_mean < min(base_runs)
            strata[field][value] = {
                "baseline_run_accuracy": base_runs, "candidate_run_accuracy": cand_runs,
                "candidate_below_baseline_range": cliff,
            }
            if cliff:
                cliffs.append(f"{field}={value}")
    delta_pp = 100 * (cand["correct"] - base["correct"]) / (EXPECTED * REPEATS)
    return {
        "baseline_correct": base["correct"], "candidate_correct": cand["correct"],
        "baseline_accuracy_pct": 100 * base["correct"] / (EXPECTED * REPEATS),
        "candidate_accuracy_pct": 100 * cand["correct"] / (EXPECTED * REPEATS),
        "delta_pp": delta_pp, "paired_improved": improved,
        "paired_regressed": regressed,
        "baseline_run_correct": [sum(r["correct"] for r in base["rows"]
                                    if r["repetition"] == i) for i in range(1, REPEATS + 1)],
        "candidate_run_correct": [sum(r["correct"] for r in cand["rows"]
                                     if r["repetition"] == i) for i in range(1, REPEATS + 1)],
        "baseline_length_limit": base["length_limit"],
        "candidate_length_limit": cand["length_limit"],
        "strata": strata, "category_cliffs": cliffs,
        "decision": "PASS" if delta_pp >= 0 and not cliffs else "REJECT_OR_QUALIFY",
    }


def main() -> int:
    pair_seam = frozen_pair_seam()
    cases, evaluator = frozen_cases()
    baseline = audit_arm(BASE, "no-cache", cases, evaluator)
    candidate = audit_arm(CAND, "hypic-only", cases, evaluator)
    if AUDIT_CAMPAIGN.startswith("cache10"):
        for arm in (baseline, candidate):
            require(arm["fingerprint"].get("gpu_memory_utilization") == 0.85
                    and arm["fingerprint"].get("material_cache_max_mb") == 3584
                    and arm["fingerprint"].get("max_materialized_segments") == 10,
                    "cache10 service fingerprint drift")
    decision = decide(baseline, candidate)
    report = {
        "schema": "hypic-hotpath-quality-audit/v1",
        "evidence_valid": True, "quality": decision,
        "frozen_pair_seam": pair_seam,
        "baseline": {k: v for k, v in baseline.items() if k != "rows"},
        "candidate": {k: v for k, v in candidate.items() if k != "rows"},
        "scope": "LongBench-v2 explicit-boundary, c8, physical NPU0-3, 2048 output cap",
    }
    quality.write_json(OUT, report)
    print(json.dumps({"audit": str(OUT), "quality": decision["decision"],
                      "baseline_correct": baseline["correct"],
                      "candidate_correct": candidate["correct"],
                      "delta_pp": decision["delta_pp"],
                      "category_cliffs": decision["category_cliffs"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
