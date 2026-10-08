#!/usr/bin/env python3
"""Isolated NPU0-3 preflight for a prospective 2048-token HYPIC quality ruler.

This candidate-only canary does not contribute scored rows to clean2 or to a
future paired quality denominator. It reuses the proven exact-owned service
controller, then requires worker-hot events caused by its scored request.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import signal
import time
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ARM = os.environ.get("HYPIC_HOTPATH_CANARY_ARM", "hypic-only")
if ARM not in {"no-cache", "hypic-only"}:
    raise RuntimeError("HYPIC_HOTPATH_CANARY_ARM must be no-cache or hypic-only")
os.environ["HYPIC_QUALITY_ATTEMPT"] = (
    "hotpath-baseline" if ARM == "no-cache" else "hotpath-canary")
import binding_off_quality as quality


BASELINE = (quality.ROOT / "quality-context-41984-clean2" / "quality" /
            "no-cache" / "longbenchv2.run1.jsonl")
BASELINE_SHA256 = "812a4281c167327ae69b96766e550f58ffb905c889c60bc0a649850ec5cc5810"
SAMPLE_INDEX = 0
EXPECTED_SAMPLE_ID = "66ebed525a08c7b9b35e1cb4"
EXPECTED_PROMPT_TOKENS = 24616
BOUNDARY = 16384
WARM_REQUESTS = 2
MAX_OUTPUT = 2048


def frozen_evaluator():
    spec = importlib.util.spec_from_file_location("hypic_frozen_quality_eval", quality.EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("frozen quality evaluator cannot be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_case() -> tuple[str, str, str]:
    if quality.sha256(BASELINE) != BASELINE_SHA256:
        raise RuntimeError("clean2 baseline row bytes drifted")
    rows = [json.loads(line) for line in BASELINE.read_text().splitlines() if line]
    row = next((item for item in rows if item["index"] == SAMPLE_INDEX), None)
    if (row is None or row["sample_id"] != EXPECTED_SAMPLE_ID
            or row["usage"]["prompt_tokens"] != EXPECTED_PROMPT_TOKENS):
        raise RuntimeError("sample identity or measured prompt-token length drifted")
    evaluator = frozen_evaluator()
    path = quality.DATASETS["longbenchv2"][0]
    samples = evaluator.load_samples("longbenchv2", path)
    sample = samples[SAMPLE_INDEX]
    if sample["_id"] != EXPECTED_SAMPLE_ID:
        raise RuntimeError("frozen dataset sample identity drifted")
    prompt, reference = evaluator.build_case("longbenchv2", sample)
    return prompt, reference, evaluator.__file__


def request_one(prompt: str, max_tokens: int) -> dict:
    payload = {
        "model": quality.MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": 0,
        "ignore_eos": False,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "vllm_xargs": {"hypic_segment_ends": [BOUNDARY, EXPECTED_PROMPT_TOKENS]},
    }
    request = Request(
        quality.BASE_URL + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=900) as response:
            data = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"chat request HTTP {exc.code}: {detail}") from exc
    usage = data.get("usage") or {}
    if (usage.get("prompt_tokens") != EXPECTED_PROMPT_TOKENS
            or not isinstance(usage.get("completion_tokens"), int)
            or not 0 <= usage["completion_tokens"] <= max_tokens):
        raise RuntimeError(f"request token accounting drifted: {usage}")
    text = str(data["choices"][0]["message"].get("content") or "")
    return {
        "usage": usage,
        "finish_reason": data["choices"][0].get("finish_reason"),
        "response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "response_text": text if max_tokens == MAX_OUTPUT else None,
    }


def events_since(path: Path, offset: int) -> list[dict]:
    if not path.exists():
        return []
    with path.open("rb") as stream:
        stream.seek(offset)
        tail = stream.read()
    return [json.loads(line) for line in tail.splitlines() if line.strip()]


def progress(stage: str, **details: object) -> None:
    record = {"stage": stage, "at_utc": quality.datetime.now(quality.timezone.utc).isoformat(),
              **details}
    quality.write_json(quality.QROOT / "progress.json", record)
    print(json.dumps(record, sort_keys=True), flush=True)


def main() -> int:
    if quality.QROOT.exists():
        raise RuntimeError(f"canary root already exists: {quality.QROOT}; inspect, never overwrite")
    if not (0 < BOUNDARY < EXPECTED_PROMPT_TOKENS
            and BOUNDARY >= 4096
            and EXPECTED_PROMPT_TOKENS + MAX_OUTPUT <= quality.CONTEXT):
        raise RuntimeError("boundary or context capacity invalid")
    fingerprint = quality.preflight()
    prompt, reference, evaluator_path = source_case()
    quality.assert_lane_available()
    quality.QROOT.mkdir(parents=True)
    with (quality.QROOT / "controller.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        signal.signal(signal.SIGTERM, quality.interrupt)
        signal.signal(signal.SIGINT, quality.interrupt)
        result = {
            "schema": "hypic-hotpath-quality-canary/v1",
            "claim": "single-arm preflight, not paired quality acceptance",
            "arm": ARM,
            "fingerprint": fingerprint,
            "sample_index": SAMPLE_INDEX,
            "sample_id": EXPECTED_SAMPLE_ID,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "reference": reference,
            "evaluator_path": evaluator_path,
            "boundary_token_ends": [BOUNDARY, EXPECTED_PROMPT_TOKENS],
            "warm_requests": WARM_REQUESTS,
            "scored_max_output_tokens": MAX_OUTPUT,
        }
        container_id = ""
        guard = None
        error = None
        try:
            progress("service-starting")
            container_id = quality.create(ARM)
            quality.start(ARM, container_id, fingerprint)
            start = json.loads((quality.QROOT / ARM / "service-start.json").read_text())
            guard = quality.ForeignProcessGuard(ARM, start["worker_pid_by_physical_npu"])
            guard.start()
            progress("service-ready", container_id=container_id)
            result["warm"] = []
            for index in range(WARM_REQUESTS):
                item = request_one(prompt, 1)
                guard.assert_clean()
                result["warm"].append({key: value for key, value in item.items()
                                       if key != "response_text"})
                progress("warm-complete", index=index + 1, usage=item["usage"])
            evidence = quality.QROOT / ARM / "hypic-evidence.jsonl"
            if ARM == "hypic-only" and not evidence.exists():
                raise RuntimeError("HYPIC evidence file absent after warmup")
            warm_events = events_since(evidence, 0)
            result["warm_event_counts"] = dict(Counter(
                item.get("event") for item in warm_events))
            result["warm_worker_hot_pids"] = sorted({
                item["pid"] for item in warm_events
                if item.get("event") == "worker_hot_path"
                and isinstance(item.get("pid"), int)})
            if result["warm_worker_hot_pids"]:
                raise RuntimeError(
                    "warmup already emitted first-only worker-hot events; "
                    "cannot attribute them to the scored request")
            before_score = evidence.stat().st_size if evidence.exists() else 0
            progress("scored-running")
            scored = request_one(prompt, MAX_OUTPUT)
            guard.assert_clean()
            result["scored"] = scored
            progress("scored-complete", usage=scored["usage"])
            evaluator = frozen_evaluator()
            prediction, correct = evaluator.score_case(
                "longbenchv2", scored["response_text"], reference)
            result["scored"]["prediction"] = prediction
            result["scored"]["correct"] = correct
            events = []
            for _ in range(20):
                events = events_since(evidence, before_score)
                if len({item.get("pid") for item in events
                        if item.get("event") == "worker_hot_path"}) >= 4:
                    break
                time.sleep(1)
            hot = [item for item in events if item.get("event") == "worker_hot_path"]
            result["scored_event_counts"] = dict(Counter(
                item.get("event") for item in events))
            result["scored_worker_hot_pids"] = sorted({
                item["pid"] for item in hot if isinstance(item.get("pid"), int)})
            result["scored_skipped_prefix_tokens"] = [
                item.get("skipped_prefix_tokens") for item in hot]
            result["scored_hot_path_valid"] = (
                len(result["scored_worker_hot_pids"]) == 4
                and all(isinstance(value, int) and value >= 4096
                        for value in result["scored_skipped_prefix_tokens"]))
            guard.assert_clean()
            if ARM == "hypic-only" and not result["scored_hot_path_valid"]:
                raise RuntimeError("scored 2048-token request lacks four verified worker-hot events")
            if ARM == "no-cache" and result["scored_worker_hot_pids"]:
                raise RuntimeError("baseline unexpectedly emitted worker-hot events")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            if guard is not None:
                try:
                    guard.close()
                except Exception as exc:
                    error = f"{error}; guard close {exc}" if error else f"guard close {exc}"
            if container_id:
                try:
                    quality.cleanup(ARM, container_id)
                except Exception as exc:
                    error = f"{error}; cleanup {exc}" if error else f"cleanup {exc}"
            result["error"] = error
            result["formal_quality_acceptance"] = False
            stop = quality.QROOT / ARM / "service-stop.json"
            if stop.exists():
                result["service_stop_sha256"] = quality.sha256(stop)
                result["service_stop"] = json.loads(stop.read_text())
            guard_path = quality.QROOT / ARM / "lane-guard.json"
            if guard_path.exists():
                result["lane_guard_sha256"] = quality.sha256(guard_path)
                result["lane_guard"] = json.loads(guard_path.read_text())
            evidence = quality.QROOT / ARM / "hypic-evidence.jsonl"
            if evidence.exists():
                result["hypic_evidence_sha256"] = quality.sha256(evidence)
            quality.write_json(quality.QROOT / "canary-result.json", result)
            progress("canary-passed" if error is None else "canary-failed",
                     error=error, scored_hot_path_valid=result.get("scored_hot_path_valid"))
    if error:
        raise RuntimeError(error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
