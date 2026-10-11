#!/usr/bin/env python3
"""Independent raw-artifact audit for the bounded r22 output-logprob oracle."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import sys

import r22_c32_logprob_oracle as r22

CONTRACT = r22.preregistration()
CONTROLLER = r22.configure("no-cache", CONTRACT)
QUALITY = CONTROLLER.quality
BASE = Path(CONTRACT["arm_roots"]["no-cache"])
CAND = Path(CONTRACT["arm_roots"]["hypic-only"])
OUT = QUALITY.ROOT / "hypic-r22-c32-logprob-oracle-paired-audit.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def request_hash(item: dict, max_tokens: int) -> str:
    payload = {
        "model": QUALITY.MODEL_NAME,
        "messages": [{"role": "user", "content": item["prompt"]}],
        "max_tokens": max_tokens, "temperature": 0, "seed": 0,
        "ignore_eos": False, "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "vllm_xargs": {
            "hypic_segment_ends": [item["boundary"], item["prompt_tokens"]]},
    }
    if item["index"] == r22.TRACE_INDEX and max_tokens == 2048:
        payload.update(CONTRACT["trace_request_parameters"])
    return hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def seam() -> dict:
    left, right = QUALITY.spec("no-cache"), QUALITY.spec("hypic-only")
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


def _api_id_match(scored_id: str, internal_id: str) -> bool:
    return internal_id == scored_id or internal_id.startswith(scored_id + "-")


def _canary(root: Path, arm: str) -> dict:
    path = root / arm / "r19-short-canary.json"
    row = read(path)
    texts = row.get("responses", [])
    require(row.get("schema") == "hypic-r19-short-canary/v1"
            and row.get("arm") == arm and len(texts) == 3
            and len(set(texts)) == 1
            and row.get("response_sha256") ==
                [hashlib.sha256(text.encode()).hexdigest() for text in texts],
            f"{arm}: short canary invalid")
    return {"request_sha256": row["request_sha256"],
            "response_sha256": row["response_sha256"],
            "file_sha256": QUALITY.sha256(path)}


def audit_arm(root: Path, arm: str, cases: list[dict], evaluator) -> dict:
    require(root.is_dir(), f"{arm}: result root absent")
    contract = read(root / "contract.json")
    result = read(root / "arm-result.json")
    start = read(root / arm / "service-start.json")
    stop = read(root / arm / "service-stop.json")
    guard = read(root / arm / "lane-guard.json")
    require(contract.get("arm") == arm and contract.get("mode") == "full"
            and contract.get("sample_indexes") == list(r22.INDEXES)
            and contract.get("repetitions") == 3
            and contract.get("concurrency") == 32
            and contract.get("warm_requests_per_sample") == 2
            and contract.get("max_output_tokens") == 2048,
            f"{arm}: frozen workload drift")
    require(contract.get("evaluator_sha256") == CONTRACT["evaluator_sha256"]
            and contract.get("dataset_sha256") == CONTRACT["dataset_sha256"]
            and contract.get("fingerprint") == start.get("fingerprint"),
            f"{arm}: source or evaluator fingerprint drift")
    fp = contract["fingerprint"]
    require(fp.get("image") == CONTRACT["image"]
            and fp.get("source_commit") == CONTRACT["source_commit"]
            and fp.get("plugin_source_root") == CONTRACT["source_root"]
            and fp.get("model_index_sha256") == CONTRACT["model_index_sha256"]
            and fp.get("physical_npus") == [0, 1, 2, 3]
            and fp.get("gpu_memory_utilization") == 0.85
            and fp.get("material_cache_max_mb") == 3584
            and fp.get("max_materialized_segments") == 10,
            f"{arm}: serving identity drift")
    errors = {None}
    if arm == "hypic-only":
        errors.add("RuntimeError: candidate scored boundary/hot coverage incomplete")
    require(result.get("error") in errors
            and result.get("completed_samples") == 32
            and result.get("scored_rows") == 96,
            f"{arm}: controller incomplete or unexpected failure")
    require(start.get("container_id") == stop.get("container_id")
            and stop.get("container_removed") is True
            and stop.get("owned_npus_released") is True
            and stop.get("port_released") is True
            and stop.get("lane_available") is True
            and not stop.get("foreign_npu_processes")
            and not stop.get("service_log_error"),
            f"{arm}: exact owned release failed")
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
    require(result.get("service_stop_sha256") ==
                QUALITY.sha256(root / arm / "service-stop.json")
            and result.get("lane_guard_sha256") ==
                QUALITY.sha256(root / arm / "lane-guard.json"),
            f"{arm}: guard/release hashes drift")
    attestation_path = root / arm / (
        f"source-attestation.{start['container_id'][:12]}.json")
    attestation = read(attestation_path)
    source = QUALITY.python_source_digest(
        Path(CONTRACT["source_root"]) / "hypic_vllm_ascend")
    require(start.get("source_attestation_sha256") ==
                QUALITY.sha256(attestation_path)
            and read(root / arm / "source-attestation.json") == attestation
            and attestation.get("container_id") == start["container_id"]
            and attestation.get("selected_source_commit") ==
                CONTRACT["source_commit"]
            and attestation.get("python_files") == source["python_files"]
            and attestation.get("python_tree_sha256") ==
                source["python_tree_sha256"]
            and f"{CONTRACT['source_root']}:/source-hypic:ro" in
                attestation.get("actual_binds", []),
            f"{arm}: source attestation drift")
    evidence = root / arm / "hypic-evidence.jsonl"
    events = [json.loads(line) for line in evidence.read_text().splitlines()
              if line] if evidence.exists() else []
    if evidence.exists():
        require(result.get("hypic_evidence_sha256") == QUALITY.sha256(evidence),
                f"{arm}: event hash drift")
    boundary_ids = [e.get("request_id") for e in events
                    if e.get("event") == "explicit_segment_boundary_active"]
    hot_events = [e for e in events
                  if e.get("event") == "worker_hot_request_verified"]
    rows = []
    request_ids = set()
    for item in cases:
        path = root / "samples" / f"{item['index']:03d}.json"
        require(path.is_file(), f"{arm}: sample {item['index']} absent")
        sample = read(path)
        for key in ("index", "sample_id", "reference", "prompt_sha256",
                    "prompt_tokens", "difficulty", "length"):
            require(sample.get(key) == item[key],
                    f"{arm}: sample {item['index']} {key} drift")
        require(sample.get("arm") == arm and sample.get("mode") == "full"
                and sample.get("segment_ends") ==
                    [item["boundary"], item["prompt_tokens"]]
                and len(sample.get("warm", [])) == 2
                and len(sample.get("scores", [])) == 3,
                f"{arm}: sample {item['index']} request count drift")
        for warm in sample["warm"]:
            require(warm.get("request_sha256") == request_hash(item, 1)
                    and warm.get("usage", {}).get("prompt_tokens") ==
                        item["prompt_tokens"],
                    f"{arm}: warm payload drift")
            request_ids.add(warm["request_id"])
        for repetition, scored in enumerate(sample["scores"], 1):
            require(scored.get("repetition") == repetition
                    and scored.get("request_sha256") ==
                        request_hash(item, 2048)
                    and scored.get("usage", {}).get("prompt_tokens") ==
                        item["prompt_tokens"]
                    and isinstance(scored.get("usage", {}).get(
                        "completion_tokens"), int)
                    and 0 <= scored["usage"]["completion_tokens"] <= 2048,
                    f"{arm}: scored request drift")
            text = scored.get("response_text")
            require(isinstance(text, str)
                    and scored.get("response_sha256") ==
                        hashlib.sha256(text.encode()).hexdigest(),
                    f"{arm}: response hash drift")
            prediction, correct = evaluator.score_case(
                "longbenchv2", text, item["reference"])
            require(scored.get("prediction") == prediction
                    and scored.get("correct") is bool(correct),
                    f"{arm}: scorer replay drift")
            trace = scored.get("token_logprobs")
            if item["index"] == r22.TRACE_INDEX:
                require(isinstance(trace, list) and trace
                        and all(isinstance(token, dict)
                                and isinstance(token.get("logprob"),
                                               (int, float))
                                and isinstance(token.get("top_logprobs"), list)
                                for token in trace),
                        f"{arm}: sample 082 logprob trace absent")
            else:
                require(trace is None, f"{arm}: unselected sample traced")
            rid = scored["request_id"]
            request_ids.add(rid)
            matches = [e for e in hot_events
                       if isinstance(e.get("request_id"), str)
                       and _api_id_match(rid, e["request_id"])]
            internal = {e["request_id"] for e in matches}
            proved_hot = (len(internal) == 1
                          and {e.get("pid") for e in matches} ==
                              set(namespace_workers.values()))
            boundary = sum(
                isinstance(value, str) and _api_id_match(rid, value)
                for value in boundary_ids)
            if arm == "hypic-only":
                require(boundary == 1,
                        f"{arm}: scored boundary missing/duplicate")
            else:
                require(not matches, "no-cache emitted hot proof")
            rows.append({
                "index": item["index"], "repetition": repetition,
                "request_id": rid, "correct": bool(correct),
                "prediction": prediction, "finish_reason": scored["finish_reason"],
                "completion_tokens": scored["usage"]["completion_tokens"],
                "response_sha256": scored["response_sha256"],
                "response_text": text,
                "token_logprobs": trace,
                "proved_hot": proved_hot,
            })
    require(len(list((root / "samples").glob("*.json"))) == 32
            and len(rows) == 96 and len(request_ids) == 160,
            f"{arm}: missing or duplicate request artifacts")
    return {
        "root": str(root), "fingerprint": fp,
        "container_id": start["container_id"],
        "contract_sha256": QUALITY.sha256(root / "contract.json"),
        "arm_result_sha256": QUALITY.sha256(root / "arm-result.json"),
        "guard_samples": guard["samples"],
        "controller_error": result["error"],
        "correct": sum(row["correct"] for row in rows),
        "proved_hot": sum(row["proved_hot"] for row in rows),
        "rows": rows,
    }


def _tokens(row: dict) -> list[str]:
    return [str(token.get("token")) for token in row["token_logprobs"]]


def _first_difference(left: list[str], right: list[str]) -> int | None:
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return index
    return min(len(left), len(right)) if len(left) != len(right) else None


def _margin(token: dict) -> float | None:
    values = [row.get("logprob") for row in token.get("top_logprobs", [])
              if isinstance(row.get("logprob"), (int, float))]
    ordered = sorted(values, reverse=True)
    return ordered[0] - ordered[1] if len(ordered) >= 2 else None


def _within_arm(rows: list[dict]) -> list[dict]:
    traced = [row for row in rows if row["index"] == r22.TRACE_INDEX]
    return [
        {"left_repeat": a["repetition"], "right_repeat": b["repetition"],
         "first_different_token": _first_difference(_tokens(a), _tokens(b))}
        for a, b in itertools.combinations(traced, 2)
    ]


def main() -> int:
    if sys.argv[1:] not in (
        ["--check"], ["--arm", "no-cache"], ["--arm", "hypic-only"],
        ["--pair"],
    ):
        raise RuntimeError("r22 audit requires --check, --arm ARM, or --pair")
    cases, evaluator = CONTROLLER.cases()
    switch = seam()
    if sys.argv[1:] == ["--check"]:
        require(not BASE.exists() and not CAND.exists() and not OUT.exists(),
                "r22 output root already exists")
        print(json.dumps({"preflight_valid": True, "device_run_started": False,
                          "indexes": [item["index"] for item in cases],
                          "one_switch_seam": switch}, sort_keys=True))
        return 0
    if sys.argv[1] == "--arm":
        arm = sys.argv[2]
        root = BASE if arm == "no-cache" else CAND
        audited = audit_arm(root, arm, cases, evaluator)
        print(json.dumps({
            "arm": arm, "root": str(root),
            "arm_result_sha256": audited["arm_result_sha256"],
            "scored_rows": len(audited["rows"]),
            "guard_samples": audited["guard_samples"],
            "sample_082_hot_proofs": sum(
                row["proved_hot"] for row in audited["rows"]
                if row["index"] == r22.TRACE_INDEX),
        }, sort_keys=True))
        return 0
    require(not OUT.exists(), "r22 paired audit already exists")
    baseline = audit_arm(BASE, "no-cache", cases, evaluator)
    candidate = audit_arm(CAND, "hypic-only", cases, evaluator)
    require(baseline["fingerprint"] == candidate["fingerprint"]
            and baseline["container_id"] != candidate["container_id"],
            "r22 arms are not a fresh source-matched pair")
    canaries = {
        arm: _canary(root, arm)
        for arm, root in (("no-cache", BASE), ("hypic-only", CAND))
    }
    require(canaries["no-cache"]["request_sha256"] ==
                canaries["hypic-only"]["request_sha256"]
            and canaries["no-cache"]["response_sha256"] ==
                canaries["hypic-only"]["response_sha256"],
            "r22 short canary mismatch")
    left = {(r["index"], r["repetition"]): r for r in baseline["rows"]}
    right = {(r["index"], r["repetition"]): r for r in candidate["rows"]}
    require(left.keys() == right.keys(), "r22 paired row identities differ")
    paired_082 = []
    for repetition in range(1, 4):
        a, b = left[(r22.TRACE_INDEX, repetition)], right[(
            r22.TRACE_INDEX, repetition)]
        tokens_a, tokens_b = _tokens(a), _tokens(b)
        difference = _first_difference(tokens_a, tokens_b)
        paired_082.append({
            "repetition": repetition,
            "baseline_correct": a["correct"],
            "candidate_correct": b["correct"],
            "candidate_proved_hot": b["proved_hot"],
            "baseline_finish_reason": a["finish_reason"],
            "candidate_finish_reason": b["finish_reason"],
            "first_different_token": difference,
            "baseline_margin_at_difference": (
                _margin(a["token_logprobs"][difference])
                if difference is not None and difference < len(tokens_a)
                else None),
            "candidate_margin_at_difference": (
                _margin(b["token_logprobs"][difference])
                if difference is not None and difference < len(tokens_b)
                else None),
        })
    report = {
        "schema": "hypic-r22-c32-logprob-oracle-audit/v1",
        "evidence_valid": True,
        "scope": "bounded output-numerics diagnostic, not KV/GDN causal proof or full quality",
        "preregistration_sha256": QUALITY.sha256(r22.PREREG),
        "one_switch_seam": switch,
        "short_canary": canaries,
        "baseline": {k: v for k, v in baseline.items() if k != "rows"},
        "candidate": {k: v for k, v in candidate.items() if k != "rows"},
        "paired_082": paired_082,
        "within_arm_082": {
            "no-cache": _within_arm(baseline["rows"]),
            "hypic-only": _within_arm(candidate["rows"]),
        },
        "interpretation_boundary": (
            "A 32-sample wave without r19's prior two waves is not an exact "
            "r19 replay. A missing hot-proven wrong sample is inconclusive; "
            "logprob differences do not identify a KV/GDN component or "
            "overturn r19's full-quality rejection."),
    }
    QUALITY.write_json(OUT, report)
    print(json.dumps({
        "audit": str(OUT),
        "baseline_correct": baseline["correct"],
        "candidate_correct": candidate["correct"],
        "sample_082_hot_proofs": sum(
            row["candidate_proved_hot"] for row in paired_082),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
