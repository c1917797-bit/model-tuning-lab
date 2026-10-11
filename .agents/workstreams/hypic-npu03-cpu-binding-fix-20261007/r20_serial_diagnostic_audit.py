#!/usr/bin/env python3
"""Independent raw-artifact audit for the bounded r20 serial diagnostic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import r20_serial_diagnostic as r20

PREREG = r20.preregistration()
CONTROLLER = r20.configure("no-cache", PREREG)
QUALITY = CONTROLLER.quality
BASE = Path(PREREG["arm_roots"]["no-cache"])
CAND = Path(PREREG["arm_roots"]["hypic-only"])
OUT = QUALITY.ROOT / "hypic-r20-serial-diagnostic-paired-audit.json"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def common_prefix(left: str, right: str) -> int:
    return next((i for i, (a, b) in enumerate(zip(left, right)) if a != b),
                min(len(left), len(right)))


def payload_hash(item: dict, max_tokens: int) -> str:
    payload = {
        "model": QUALITY.MODEL_NAME,
        "messages": [{"role": "user", "content": item["prompt"]}],
        "max_tokens": max_tokens, "temperature": 0, "seed": 0,
        "ignore_eos": False, "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "vllm_xargs": {
            "hypic_segment_ends": [item["boundary"], item["prompt_tokens"]]},
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def one_switch_seam() -> dict:
    left = QUALITY.spec("no-cache")
    right = QUALITY.spec("hypic-only")
    require(sorted(left[1]) == sorted(right[1]), "arm bind mounts differ")
    require(left[3].replace("/no-cache", "/ARM") ==
            right[3].replace("/hypic-only", "/ARM"),
            "arm serving commands differ")
    baseline_env = dict(entry.split("=", 1) for entry in left[2])
    candidate_env = dict(entry.split("=", 1) for entry in right[2])
    differences = {
        key: [baseline_env.get(key), candidate_env.get(key)]
        for key in baseline_env.keys() | candidate_env.keys()
        if baseline_env.get(key) != candidate_env.get(key)
    }
    require(differences == {
        "VLLM_ASCEND_HYPIC_ENABLE": ["0", "1"],
        "VLLM_ASCEND_HYPIC_EVIDENCE_FILE": [
            f"/results/{QUALITY.QROOT.name}/no-cache/hypic-evidence.jsonl",
            f"/results/{QUALITY.QROOT.name}/hypic-only/hypic-evidence.jsonl",
        ],
    }, "arm environment differs beyond HYPIC and evidence path")
    return {"enable": ["0", "1"], "binds_equal": True,
            "normalized_commands_equal": True}


def audit_short_canary(root: Path, arm: str) -> dict:
    path = root / arm / "r19-short-canary.json"
    record = read(path)
    responses = record.get("responses", [])
    require(record.get("schema") == "hypic-r19-short-canary/v1"
            and record.get("arm") == arm
            and record.get("max_output_tokens") == 128
            and len(responses) == 3
            and len(set(responses)) == 1
            and record.get("within_arm_exact") is True
            and record.get("response_sha256") ==
                [hashlib.sha256(value.encode()).hexdigest() for value in responses],
            f"{arm}: short canary drift")
    return {"request_sha256": record["request_sha256"],
            "response_sha256": record["response_sha256"],
            "file_sha256": QUALITY.sha256(path)}


def audit_arm(root: Path, arm: str, cases: list[dict], evaluator: object) -> dict:
    require(root.is_dir(), f"{arm}: root absent")
    contract = read(root / "contract.json")
    result = read(root / "arm-result.json")
    start = read(root / arm / "service-start.json")
    stop = read(root / arm / "service-stop.json")
    guard = read(root / arm / "lane-guard.json")
    require(contract.get("arm") == arm and contract.get("mode") == "full"
            and contract.get("sample_indexes") == list(r20.INDEXES)
            and contract.get("repetitions") == 3
            and contract.get("concurrency") == 1
            and contract.get("warm_requests_per_sample") == 2
            and contract.get("max_output_tokens") == 2048,
            f"{arm}: workload contract drift")
    require(contract.get("evaluator_sha256") == PREREG["evaluator_sha256"]
            and contract.get("dataset_sha256") == PREREG["dataset_sha256"]
            and contract.get("fingerprint") == start.get("fingerprint"),
            f"{arm}: source or evaluator fingerprint drift")
    fp = contract["fingerprint"]
    require(fp.get("image") == PREREG["image"]
            and fp.get("source_commit") == PREREG["source_commit"]
            and fp.get("plugin_source_root") == PREREG["source_root"]
            and fp.get("model_index_sha256") == PREREG["model_index_sha256"]
            and fp.get("physical_npus") == PREREG["physical_npus"]
            and fp.get("gpu_memory_utilization") == 0.85
            and fp.get("material_cache_max_mb") == 3584
            and fp.get("max_materialized_segments") == 10,
            f"{arm}: frozen serving identity drift")
    allowed_error = {None}
    if arm == "hypic-only":
        allowed_error.add("RuntimeError: candidate scored boundary/hot coverage incomplete")
    require(result.get("error") in allowed_error
            and result.get("completed_samples") == 3
            and result.get("scored_rows") == 9,
            f"{arm}: incomplete controller or unexpected failure")
    require(start.get("container_id") == stop.get("container_id")
            and stop.get("container_removed") is True
            and stop.get("owned_npus_released") is True
            and stop.get("port_released") is True
            and stop.get("lane_available") is True
            and not stop.get("foreign_npu_processes")
            and not stop.get("service_log_error"),
            f"{arm}: exact owned release unproven")
    workers = start.get("worker_pid_by_physical_npu", {})
    namespace_workers = start.get("worker_namespace_pid_by_physical_npu", {})
    require(set(workers) == {"0", "1", "2", "3"}
            and len(set(workers.values())) == 4
            and set(namespace_workers) == {"0", "1", "2", "3"}
            and len(set(namespace_workers.values())) == 4
            and sorted(workers.values()) == guard.get("expected_worker_pids")
            and guard.get("samples", 0) > 0
            and not guard.get("foreign") and not guard.get("probe_errors"),
            f"{arm}: physical isolation proof failed")
    require(result.get("service_stop_sha256") == QUALITY.sha256(root / arm / "service-stop.json")
            and result.get("lane_guard_sha256") == QUALITY.sha256(root / arm / "lane-guard.json"),
            f"{arm}: release or guard receipt drift")
    attestation_path = root / arm / f"source-attestation.{start['container_id'][:12]}.json"
    attestation = read(attestation_path)
    source = QUALITY.python_source_digest(
        Path(PREREG["source_root"]) / "hypic_vllm_ascend")
    require(start.get("source_attestation_sha256") == QUALITY.sha256(attestation_path)
            and read(root / arm / "source-attestation.json") == attestation
            and attestation.get("container_id") == start["container_id"]
            and attestation.get("selected_source_commit") == PREREG["source_commit"]
            and attestation.get("python_files") == source["python_files"]
            and attestation.get("python_tree_sha256") == source["python_tree_sha256"]
            and f"{PREREG['source_root']}:/source-hypic:ro"
                in attestation.get("actual_binds", []),
            f"{arm}: live plugin source attestation drift")
    raw_events = root / arm / "hypic-evidence.jsonl"
    events = [json.loads(line) for line in raw_events.read_text().splitlines() if line] if raw_events.exists() else []
    if raw_events.exists():
        require(result.get("hypic_evidence_sha256") == QUALITY.sha256(raw_events),
                f"{arm}: event hash drift")
    boundary_ids = {e.get("request_id") for e in events
                    if e.get("event") == "explicit_segment_boundary_active"}
    hot_by_request: dict[str, set[int]] = {}
    for event in events:
        if event.get("event") == "worker_hot_request_verified":
            rid = event.get("request_id")
            pid = event.get("pid")
            if isinstance(rid, str) and isinstance(pid, int):
                hot_by_request.setdefault(rid, set()).add(pid)
    rows = []
    ids = set()
    for item in cases:
        path = root / "samples" / f"{item['index']:03d}.json"
        require(path.is_file(), f"{arm}: sample {item['index']} absent")
        sample = read(path)
        for key in ("index", "sample_id", "reference", "prompt_sha256",
                    "prompt_tokens", "difficulty", "length"):
            require(sample.get(key) == item[key],
                    f"{arm}: sample {item['index']} {key} drift")
        require(sample.get("arm") == arm and sample.get("mode") == "full"
                and sample.get("segment_ends") == [item["boundary"], item["prompt_tokens"]]
                and len(sample.get("warm", [])) == 2
                and len(sample.get("scores", [])) == 3,
                f"{arm}: sample {item['index']} boundary or request count drift")
        for warm in sample["warm"]:
            require(warm.get("request_sha256") == payload_hash(item, 1)
                    and warm.get("usage", {}).get("prompt_tokens") == item["prompt_tokens"],
                    f"{arm}: warm payload drift")
            ids.add(warm["request_id"])
        for repeat, score in enumerate(sample["scores"], 1):
            require(score.get("repetition") == repeat
                    and score.get("request_sha256") == payload_hash(item, 2048)
                    and score.get("usage", {}).get("prompt_tokens") == item["prompt_tokens"]
                    and isinstance(score.get("usage", {}).get("completion_tokens"), int)
                    and 0 <= score["usage"]["completion_tokens"] <= 2048,
                    f"{arm}: scored payload drift")
            text = score.get("response_text")
            require(isinstance(text, str)
                    and score.get("response_sha256") == hashlib.sha256(text.encode()).hexdigest(),
                    f"{arm}: response hash drift")
            prediction, correct = evaluator.score_case("longbenchv2", text, item["reference"])
            require(score.get("prediction") == prediction
                    and score.get("correct") is bool(correct),
                    f"{arm}: scorer replay drift")
            rid = score["request_id"]
            ids.add(rid)
            joins = [(internal, pids) for internal, pids in hot_by_request.items()
                     if internal == rid or internal.startswith(rid + "-")]
            proved_hot = (len(joins) == 1
                          and joins[0][1] == set(namespace_workers.values()))
            boundary = sum(isinstance(bid, str) and
                           (bid == rid or bid.startswith(rid + "-"))
                           for bid in boundary_ids)
            if arm == "hypic-only":
                require(boundary == 1, f"{arm}: scored boundary missing/duplicate")
            else:
                require(not joins, "no-cache arm emitted scored hot proof")
            rows.append({
                "index": item["index"], "repetition": repeat,
                "request_id": rid, "correct": bool(correct),
                "prediction": prediction, "finish_reason": score["finish_reason"],
                "completion_tokens": score["usage"]["completion_tokens"],
                "response_text": text, "proved_hot": proved_hot,
            })
    require(len(list((root / "samples").glob("*.json"))) == 3
            and len(rows) == 9 and len(ids) == 15,
            f"{arm}: missing/duplicate request artifacts")
    return {
        "root": str(root), "fingerprint": fp, "container_id": start["container_id"],
        "contract_sha256": QUALITY.sha256(root / "contract.json"),
        "arm_result_sha256": QUALITY.sha256(root / "arm-result.json"),
        "guard_samples": guard["samples"], "controller_error": result["error"],
        "correct": sum(row["correct"] for row in rows),
        "length_limit": sum(row["finish_reason"] == "length" for row in rows),
        "proved_hot": sum(row["proved_hot"] for row in rows),
        "rows": rows,
    }


def main() -> int:
    if sys.argv[1:] not in (["--check"], ["--run"]):
        raise RuntimeError("r20 audit requires --check or --run")
    cases, evaluator = CONTROLLER.cases()
    seam = one_switch_seam()
    if sys.argv[1:] == ["--check"]:
        require(not BASE.exists() and not CAND.exists() and not OUT.exists(),
                "r20 root or audit output already exists")
        print(json.dumps({"preflight_valid": True, "device_run_started": False,
                          "indexes": [x["index"] for x in cases], "seam": seam},
                         sort_keys=True))
        return 0
    require(not OUT.exists(), "r20 audit output already exists")
    baseline = audit_arm(BASE, "no-cache", cases, evaluator)
    candidate = audit_arm(CAND, "hypic-only", cases, evaluator)
    require(baseline["fingerprint"] == candidate["fingerprint"]
            and baseline["container_id"] != candidate["container_id"],
            "r20 arms do not form a fresh one-switch pair")
    canaries = {arm: audit_short_canary(root, arm)
                for arm, root in (("no-cache", BASE), ("hypic-only", CAND))}
    require(canaries["no-cache"]["request_sha256"] ==
            canaries["hypic-only"]["request_sha256"]
            and canaries["no-cache"]["response_sha256"] ==
                canaries["hypic-only"]["response_sha256"],
            "r20 short canary mismatch")
    b = {(r["index"], r["repetition"]): r for r in baseline["rows"]}
    c = {(r["index"], r["repetition"]): r for r in candidate["rows"]}
    require(b.keys() == c.keys(), "r20 paired row identities differ")
    paired = []
    for key in sorted(b):
        left, right = b[key], c[key]
        paired.append({
            "index": key[0], "repetition": key[1],
            "baseline_correct": left["correct"],
            "candidate_correct": right["correct"],
            "baseline_finish_reason": left["finish_reason"],
            "candidate_finish_reason": right["finish_reason"],
            "baseline_tokens": left["completion_tokens"],
            "candidate_tokens": right["completion_tokens"],
            "candidate_proved_hot": right["proved_hot"],
            "shared_prefix_characters": common_prefix(
                left["response_text"], right["response_text"]),
        })
    report = {
        "schema": "hypic-r20-serial-diagnostic-audit/v1",
        "evidence_valid": True,
        "scope": "post-hoc-selected three-sample serial mechanism diagnostic only",
        "preregistration_sha256": QUALITY.sha256(r20.PREREG),
        "one_switch_seam": seam,
        "short_canary": canaries,
        "baseline": {k: v for k, v in baseline.items() if k != "rows"},
        "candidate": {k: v for k, v in candidate.items() if k != "rows"},
        "paired": paired,
        "interpretation_boundary": "No three-sample result can overturn r19, prove population quality, or establish repaired-source adoption.",
    }
    QUALITY.write_json(OUT, report)
    print(json.dumps({"audit": str(OUT), "baseline_correct": baseline["correct"],
                      "candidate_correct": candidate["correct"],
                      "candidate_proved_hot": candidate["proved_hot"],
                      "candidate_length_limit": candidate["length_limit"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
