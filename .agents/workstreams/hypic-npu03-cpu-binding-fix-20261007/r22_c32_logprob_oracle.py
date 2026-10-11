#!/usr/bin/env python3
"""Same-source c32 output-logprob oracle for r19 sample 082, diagnostic only."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import r19_repaired_c32_longbench_adapter as r19

HERE = Path(__file__).resolve().parent
PREREG = HERE / "HYPIC_R22_C32_LOGPROB_ORACLE_PREREGISTRATION_20261011.json"
ROOT_NAME = "hotpath-cache10r22-c32-logprob"
INDEXES = tuple(range(64, 96))
TRACE_INDEX = 82


def preregistration() -> dict:
    contract = json.loads(PREREG.read_text(encoding="utf-8"))
    if (
        contract.get("schema") != "hypic-r22-c32-logprob-oracle-preregistration/v1"
        or contract.get("sample_indexes_in_order") != list(INDEXES)
        or contract.get("traced_sample_index") != TRACE_INDEX
        or contract.get("source_root") != r19.SOURCE_ROOT
        or contract.get("source_commit") != r19.SOURCE_COMMIT
        or contract.get("arms") != ["no-cache", "hypic-only"]
        or contract.get("physical_npus") != [0, 1, 2, 3]
        or contract.get("max_output_tokens") != 2048
        or contract.get("repetitions_per_sample") != 3
        or contract.get("sample_concurrency") != 32
        or contract.get("warm_requests_per_sample") != 2
        or contract.get("trace_request_parameters") !=
            {"logprobs": True, "top_logprobs": 5}
        or contract.get("execution_state") != "frozen-offline-preflight-pending"
    ):
        raise RuntimeError("r22 preregistration drift")
    required = {
        "r22_c32_logprob_oracle.py",
        "r22_c32_logprob_oracle_audit.py",
        "test_r22_c32_logprob_oracle.py",
    }
    frozen = contract.get("file_sha256", {})
    if set(frozen) != required:
        raise RuntimeError("r22 file hash set incomplete")
    for name, expected in frozen.items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"r22 frozen file drift: {name}")
    return contract


def traced_request(item: dict, max_tokens: int, original, quality,
                   request_timeout: int) -> dict:
    if item["index"] != TRACE_INDEX or max_tokens != 2048:
        return original(item, max_tokens)
    payload = {
        "model": quality.MODEL_NAME,
        "messages": [{"role": "user", "content": item["prompt"]}],
        "max_tokens": max_tokens, "temperature": 0, "seed": 0,
        "ignore_eos": False, "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "vllm_xargs": {
            "hypic_segment_ends": [item["boundary"], item["prompt_tokens"]]},
        "logprobs": True, "top_logprobs": 5,
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    request = Request(
        quality.BASE_URL + "/v1/chat/completions", data=encoded,
        headers={"Content-Type": "application/json"}, method="POST")
    started = time.monotonic()
    try:
        with urlopen(request, timeout=request_timeout) as response:
            data = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(
            f"sample {item['index']} logprob HTTP {exc.code}: {detail}") from exc
    usage = data.get("usage") or {}
    choice = data["choices"][0]
    content = (choice.get("logprobs") or {}).get("content")
    if (
        usage.get("prompt_tokens") != item["prompt_tokens"]
        or not isinstance(usage.get("completion_tokens"), int)
        or not 0 <= usage["completion_tokens"] <= max_tokens
        or not isinstance(content, list)
        or not content
        or not all(isinstance(row, dict) and
                   isinstance(row.get("logprob"), (int, float)) and
                   isinstance(row.get("top_logprobs"), list)
                   for row in content)
    ):
        raise RuntimeError(
            f"sample {item['index']} logprob or token accounting unavailable")
    response_text = str(choice["message"].get("content") or "")
    return {
        "request_id": data.get("id"),
        "request_sha256": hashlib.sha256(encoded).hexdigest(),
        "response_text": response_text,
        "response_sha256": hashlib.sha256(response_text.encode()).hexdigest(),
        "usage": usage,
        "finish_reason": choice.get("finish_reason"),
        "duration_s": time.monotonic() - started,
        "token_logprobs": content,
    }


def configure(arm: str, contract: dict):
    if arm not in contract["arms"]:
        raise RuntimeError("r22 arm must be no-cache or hypic-only")
    r19.check_preregistration()
    r19.ROOT_NAME = ROOT_NAME
    controller = r19.configure(arm)
    quality = controller.quality
    suffix = "baseline" if arm == "no-cache" else "hypic"
    attempt = f"{ROOT_NAME}-{suffix}"
    if (
        quality.ATTEMPT != attempt
        or str(quality.QROOT) != contract["arm_roots"][arm]
        or controller.REPETITIONS != 3
        or controller.MAX_OUTPUT != 2048
    ):
        raise RuntimeError("r22 controller attempt/cap drift")
    quality.EXPERIMENT = f"hypic-npu03-r22-logprob-oracle-20261011-{suffix}"
    controller.CAMPAIGN = "cache10r22-c32-logprob"
    controller.CONCURRENCY = 32
    original_cases = controller.cases
    original_request = controller.request_one

    def selected_cases():
        all_cases, evaluator = original_cases()
        selected = [all_cases[index] for index in INDEXES]
        for item, frozen in zip(selected, contract["sample_identity"]):
            if any(item.get(key) != frozen[key] for key in frozen):
                raise RuntimeError(f"r22 sample identity drift at {item['index']}")
        return selected, evaluator

    controller.cases = selected_cases
    controller.request_one = lambda item, max_tokens: traced_request(
        item, max_tokens, original_request, quality, controller.REQUEST_TIMEOUT)
    return controller


def offline_check(arm: str, contract: dict, controller) -> dict:
    quality = controller.quality
    if quality.QROOT.exists():
        raise RuntimeError("r22 immutable output root already exists")
    items, _ = controller.cases()
    fp = quality.preflight()
    if (
        len(items) != 32
        or fp["source_commit"] != contract["source_commit"]
        or fp["plugin_source_root"] != contract["source_root"]
        or fp["image"] != contract["image"]
        or fp["model_index_sha256"] != contract["model_index_sha256"]
        or fp["evaluator_sha256"] != contract["evaluator_sha256"]
        or fp["datasets"]["longbenchv2"]["sha256"] != contract["dataset_sha256"]
        or fp["physical_npus"] != [0, 1, 2, 3]
        or fp["max_model_len"] != contract["max_model_len"]
        or fp["max_output_tokens"] != 2048
        or fp["gpu_memory_utilization"] != contract["gpu_memory_utilization"]
        or fp["material_cache_max_mb"] != contract["material_cache_max_mb"]
        or fp["max_materialized_segments"] != contract["max_materialized_segments"]
        or controller.CONCURRENCY != 32
    ):
        raise RuntimeError("r22 offline workload/source identity drift")
    if len(quality.spec(arm)) != 4:
        raise RuntimeError("r22 serving spec unavailable")
    return {
        "arm": arm, "root": str(quality.QROOT),
        "source_commit": fp["source_commit"],
        "sample_indexes": [item["index"] for item in items],
        "concurrency": controller.CONCURRENCY,
        "max_output_tokens": controller.MAX_OUTPUT,
        "device_run_started": False,
    }


def main() -> int:
    if sys.argv[1:] not in (["--check"], ["--run"]):
        raise RuntimeError("r22 requires --check or --run")
    contract = preregistration()
    arm = os.environ.get("HYPIC_R22_ARM", "")
    controller = configure(arm, contract)
    check = offline_check(arm, contract, controller)
    if sys.argv[1:] == ["--check"]:
        print(json.dumps(check, sort_keys=True))
        return 0
    return controller.main()


if __name__ == "__main__":
    raise SystemExit(main())
