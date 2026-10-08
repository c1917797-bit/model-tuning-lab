#!/usr/bin/env python3
"""Prospective matched LongBench-v2 in-path quality arm on physical NPU0-3.

Run one arm at a time. Raw responses stay under the external artifact root.
This controller deliberately refuses to reuse a partial root: a failed arm
must be audited and a new matched attempt declared before restarting.
"""

from __future__ import annotations

import concurrent.futures
import fcntl
import hashlib
import importlib.util
import json
import os
import signal
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ARM = os.environ.get("HYPIC_HOTPATH_QUALITY_ARM", "")
MODE = os.environ.get("HYPIC_HOTPATH_QUALITY_MODE", "")
CAMPAIGN = os.environ.get("HYPIC_HOTPATH_QUALITY_CAMPAIGN", "original")
SHARD = os.environ.get("HYPIC_HOTPATH_QUALITY_SHARD", "")
SHARD0_IDS = tuple([*range(53), 54, 55, 56])
CLEAN_SET_RECEIPT = (
    "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
    "hotpath-cache10r2-clean-set-audit.json"
)
CLEAN_SET_RECEIPT_SHA = "99f2578adddd041f7a84fe441a1ac02b754b2c1a8217054e80e855b67e7f55bd"
ORIGINAL_PAIRS = {
    ("hypic-only", "pilot"),
    ("hypic-only", "pilot2"),
    ("no-cache", "full"),
    ("hypic-only", "full"),
}
RESERVE_PAIRS = {("hypic-only", "stress"), ("no-cache", "full"),
                 ("hypic-only", "full")}
if not ((CAMPAIGN == "original" and (ARM, MODE) in ORIGINAL_PAIRS)
        or (CAMPAIGN == "reserve" and (ARM, MODE) in RESERVE_PAIRS)
        or (CAMPAIGN == "cache10" and (ARM, MODE) in RESERVE_PAIRS)
        or (CAMPAIGN in {"cache10r1", "cache10r2", "cache10r3", "cache10r4", "cache10r5", "cache10r6", "cache10r7", "cache10r8", "cache10r9"}
            and (ARM, MODE) in {("no-cache", "full"), ("hypic-only", "full")})
        or (CAMPAIGN == "cache10split" and (ARM, MODE, SHARD) in {
            ("no-cache", "full", "0"), ("no-cache", "full", "1"),
            ("hypic-only", "full", "1")})
        or (CAMPAIGN == "reserve2" and (ARM, MODE) == ("hypic-only", "stress"))):
    raise RuntimeError("unrecognized hot-path quality campaign/arm/mode")
if CAMPAIGN == "cache10split":
    os.environ["HYPIC_QUALITY_ATTEMPT"] = (
        f"hotpath-cache10split-{'baseline' if ARM == 'no-cache' else 'hypic'}-shard{SHARD}"
    )
elif CAMPAIGN in {"cache10r1", "cache10r2", "cache10r3", "cache10r4", "cache10r5", "cache10r6", "cache10r7", "cache10r8", "cache10r9"}:
    os.environ["HYPIC_QUALITY_ATTEMPT"] = (
        f"hotpath-{CAMPAIGN}-full-baseline" if ARM == "no-cache" else
        f"hotpath-{CAMPAIGN}-full-hypic"
    )
elif CAMPAIGN == "cache10":
    os.environ["HYPIC_QUALITY_ATTEMPT"] = (
        "hotpath-cache10-stress-hypic" if MODE == "stress" else
        "hotpath-cache10-full-baseline" if ARM == "no-cache" else
        "hotpath-cache10-full-hypic"
    )
elif CAMPAIGN == "reserve2":
    os.environ["HYPIC_QUALITY_ATTEMPT"] = "hotpath-reserve-stress2-hypic"
elif CAMPAIGN == "reserve":
    os.environ["HYPIC_QUALITY_ATTEMPT"] = (
        "hotpath-reserve-stress-hypic" if MODE == "stress" else
        "hotpath-reserve-full-baseline" if ARM == "no-cache" else
        "hotpath-reserve-full-hypic"
    )
else:
    os.environ["HYPIC_QUALITY_ATTEMPT"] = (
        "hotpath-pilot2-hypic" if MODE == "pilot2" else
        "hotpath-pilot-hypic" if MODE == "pilot" else
        "hotpath-full-baseline" if ARM == "no-cache" else
        "hotpath-full-hypic"
    )
import binding_off_quality as quality


BASELINE = (quality.ROOT / "quality-context-41984-clean2" / "quality" /
            "no-cache" / "longbenchv2.run1.jsonl")
BASELINE_SHA256 = "812a4281c167327ae69b96766e550f58ffb905c889c60bc0a649850ec5cc5810"
DATASET = "longbenchv2"
MAX_OUTPUT = 2048
WARM_COUNT = 2
REPETITIONS = 1 if MODE.startswith("pilot") else 3
CONCURRENCY = 1 if MODE.startswith("pilot") else 8
REQUEST_TIMEOUT = 900


def frozen_evaluator():
    spec = importlib.util.spec_from_file_location("hypic_frozen_quality_eval", quality.EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("frozen evaluator import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cases() -> tuple[list[dict], object]:
    if quality.sha256(BASELINE) != BASELINE_SHA256:
        raise RuntimeError("frozen clean2 row hash drift")
    baseline = [json.loads(line) for line in BASELINE.read_text().splitlines() if line]
    if len(baseline) != 127 or sorted(row["index"] for row in baseline) != list(range(127)):
        raise RuntimeError("frozen baseline sample index set drift")
    evaluator = frozen_evaluator()
    samples = evaluator.load_samples(DATASET, quality.DATASETS[DATASET][0])
    if len(samples) != 127:
        raise RuntimeError("LongBench sample count drift")
    items = []
    for index, (sample, row) in enumerate(zip(samples, baseline)):
        measured = row["usage"]["prompt_tokens"]
        if (row["index"] != index or row["sample_id"] != sample["_id"]
                or not isinstance(measured, int) or measured < 6144
                or measured + MAX_OUTPUT > quality.CONTEXT):
            raise RuntimeError(f"sample {index} identity/capacity drift")
        prompt, reference = evaluator.build_case(DATASET, sample)
        boundary = min(16384, ((measured - 2048) // 16) * 16)
        if boundary < 4096 or boundary >= measured:
            raise RuntimeError(f"sample {index} has invalid segment boundary")
        items.append({
            "index": index, "sample_id": sample["_id"], "prompt": prompt,
            "reference": reference, "prompt_tokens": measured,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "boundary": boundary, "difficulty": sample.get("difficulty"),
            "length": sample.get("length"),
        })
    if MODE.startswith("pilot"):
        shortest = min(items, key=lambda item: item["prompt_tokens"])["index"]
        longest = max(items, key=lambda item: item["prompt_tokens"])["index"]
        selected = [0, shortest, longest]
        if len(set(selected)) != 3:
            raise RuntimeError("pilot sample selection not unique")
        items = [items[index] for index in selected]
    elif MODE == "stress":
        # Recreate the first c8 wave that failed at sample 7, without
        # shortening or changing the subsequent full matched ruler.
        items = [items[index] for index in range(9)]
    elif CAMPAIGN == "cache10split":
        receipt_path = Path(CLEAN_SET_RECEIPT)
        if quality.sha256(receipt_path) != CLEAN_SET_RECEIPT_SHA:
            raise RuntimeError("clean-set audit receipt hash drift")
        receipt = json.loads(receipt_path.read_text())
        if (receipt.get("partial_rows_valid") is not True
                or receipt.get("original_arm_valid") is not False
                or tuple(receipt.get("sample_indices", [])) != SHARD0_IDS):
            raise RuntimeError("clean-set audit receipt contents drift")
        selected = set(SHARD0_IDS if SHARD == "0" else
                       set(range(127)) - set(SHARD0_IDS))
        items = [item for item in items if item["index"] in selected]
        if len(items) != (56 if SHARD == "0" else 71):
            raise RuntimeError("split quality sample count drift")
    return items, evaluator


def request_one(item: dict, max_tokens: int) -> dict:
    payload = {
        "model": quality.MODEL_NAME,
        "messages": [{"role": "user", "content": item["prompt"]}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": 0,
        "ignore_eos": False,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "vllm_xargs": {"hypic_segment_ends": [item["boundary"], item["prompt_tokens"]]},
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = Request(
        quality.BASE_URL + "/v1/chat/completions", data=encoded,
        headers={"Content-Type": "application/json"}, method="POST")
    started = time.monotonic()
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"sample {item['index']} HTTP {exc.code}: {detail}") from exc
    usage = data.get("usage") or {}
    if (usage.get("prompt_tokens") != item["prompt_tokens"]
            or not isinstance(usage.get("completion_tokens"), int)
            or not 0 <= usage["completion_tokens"] <= max_tokens):
        raise RuntimeError(f"sample {item['index']} token accounting drift: {usage}")
    response_text = str(data["choices"][0]["message"].get("content") or "")
    return {
        "request_id": data.get("id"),
        "request_sha256": hashlib.sha256(encoded).hexdigest(),
        "response_text": response_text,
        "response_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
        "usage": usage,
        "finish_reason": data["choices"][0].get("finish_reason"),
        "duration_s": time.monotonic() - started,
    }


def events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("rb") as stream:
        lines = stream.read().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def events_since(path: Path, offset: int) -> list[dict]:
    if not path.exists():
        return []
    with path.open("rb") as stream:
        stream.seek(offset)
        lines = stream.read().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def event_summary(rows: list[dict]) -> dict:
    return {
        "counts": dict(Counter(row.get("event") for row in rows)),
        "hot_worker_pids": sorted({row["pid"] for row in rows
                                   if row.get("event") == "worker_hot_path"
                                   and isinstance(row.get("pid"), int)}),
        "verified_hot_requests": sum(int(row.get("verified_hot_requests", 0))
                                     for row in rows if row.get("event") == "complete_hybrid_repair"),
        "verified_skipped_tokens": sum(int(row.get("verified_skipped_tokens", 0))
                                       for row in rows if row.get("event") == "complete_hybrid_repair"),
    }


def scored_boundary_match(scored_id: str, boundary_ids: set[str]) -> bool:
    """API ID is the scheduler ID prefix before its internal request suffix."""
    if not isinstance(scored_id, str) or not scored_id.startswith("chatcmpl-"):
        return False
    matches = [item for item in boundary_ids
               if item == scored_id or item.startswith(scored_id + "-")]
    return len(matches) == 1


def run_sample(item: dict, evaluator: object) -> dict:
    evidence = quality.QROOT / ARM / "hypic-evidence.jsonl"
    before_warm = evidence.stat().st_size if evidence.exists() else 0
    warm = [request_one(item, 1) for _ in range(WARM_COUNT)]
    warm_events = event_summary(events_since(evidence, before_warm))
    before_first_score = evidence.stat().st_size if evidence.exists() else 0
    scores = []
    first_scored_events = None
    for repetition in range(1, REPETITIONS + 1):
        response = request_one(item, MAX_OUTPUT)
        if repetition == 1:
            first_scored_events = event_summary(events_since(evidence, before_first_score))
        prediction, correct = evaluator.score_case(
            DATASET, response["response_text"], item["reference"])
        scores.append({"repetition": repetition, "prediction": prediction,
                       "correct": bool(correct), **response})
    return {
        "schema": "hypic-hotpath-longbench-sample/v1",
        "arm": ARM, "mode": MODE, "index": item["index"],
        "sample_id": item["sample_id"], "prompt_sha256": item["prompt_sha256"],
        "reference": item["reference"], "prompt_tokens": item["prompt_tokens"],
        "segment_ends": [item["boundary"], item["prompt_tokens"]],
        "difficulty": item["difficulty"], "length": item["length"],
        "warm": [{key: value for key, value in row.items() if key != "response_text"}
                 for row in warm],
        "warm_events": warm_events,
        "first_scored_events": first_scored_events,
        "scores": scores,
    }


def monitored_samples(items: list[dict], evaluator: object,
                      guard: quality.ForeignProcessGuard, container_id: str,
                      accept: object) -> None:
    """Check isolation while requests are in flight, not only after a sample."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {pool.submit(run_sample, item, evaluator) for item in items}
        pending = set(futures)
        try:
            while pending:
                done, pending = concurrent.futures.wait(
                    pending, timeout=10, return_when=concurrent.futures.FIRST_COMPLETED)
                guard.assert_clean()
                for future in done:
                    accept(future.result())
        except Exception as exc:
            for future in futures:
                future.cancel()
            try:
                # The executor joins active HTTP requests on exit. Stop only
                # this exact owned service so those requests can unblock.
                quality.stop_owned_for_abort(ARM, container_id)
            except Exception as stop_exc:
                raise RuntimeError(f"{exc}; exact owned abort stop failed: {stop_exc}") from exc
            raise


def progress(stage: str, **details: object) -> None:
    record = {"stage": stage, "at_utc": datetime.now(timezone.utc).isoformat(),
              "arm": ARM, "mode": MODE, **details}
    quality.write_json(quality.QROOT / "progress.json", record)
    print(json.dumps(record, sort_keys=True), flush=True)


def main() -> int:
    if (CAMPAIGN == "cache10split"
            and os.environ.get("HYPIC_HOTPATH_SPLIT_USER_APPROVED") != "yes"):
        raise RuntimeError(
            "cache10split is a revised protocol; require explicit user method "
            "approval before setting HYPIC_HOTPATH_SPLIT_USER_APPROVED=yes"
        )
    if quality.QROOT.exists():
        raise RuntimeError(f"attempt root already exists: {quality.QROOT}; never overwrite")
    fingerprint = quality.preflight()
    items, evaluator = cases()
    quality.assert_lane_available()
    quality.QROOT.mkdir(parents=True)
    with (quality.QROOT / "controller.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        signal.signal(signal.SIGTERM, quality.interrupt)
        signal.signal(signal.SIGINT, quality.interrupt)
        contract = {
            "schema": "hypic-hotpath-longbench-contract/v1",
            "arm": ARM, "mode": MODE, "fingerprint": fingerprint,
            "baseline_row_sha256": BASELINE_SHA256,
            "evaluator_sha256": quality.EVALUATOR_SHA,
            "dataset_sha256": quality.DATASETS[DATASET][2],
            "sample_indexes": [item["index"] for item in items],
            "split_shard": SHARD if CAMPAIGN == "cache10split" else None,
            "clean_set_receipt_sha256": (CLEAN_SET_RECEIPT_SHA
                                         if CAMPAIGN == "cache10split" else None),
            "sample_identity": [{key: item[key] for key in
                                 ("index", "sample_id", "prompt_sha256", "prompt_tokens", "boundary")}
                                for item in items],
            "repetitions": REPETITIONS, "concurrency": CONCURRENCY,
            "warm_requests_per_sample": WARM_COUNT,
            "max_output_tokens": MAX_OUTPUT, "temperature": 0,
            "seed": 0, "ignore_eos": False, "enable_thinking": False,
        }
        quality.write_json(quality.QROOT / "contract.json", contract)
        result = {"schema": "hypic-hotpath-longbench-arm/v1", "contract": contract,
                  "completed_samples": 0, "scored_rows": 0, "error": None}
        container_id = ""
        guard = None
        error = None
        evidence = quality.QROOT / ARM / "hypic-evidence.jsonl"
        try:
            progress("service-starting")
            container_id = quality.create(ARM)
            guard = quality.ForeignProcessGuard(ARM, {}, owned_container_id=container_id)
            guard.start()
            quality.start(ARM, container_id, fingerprint, guard=guard)
            start = json.loads((quality.QROOT / ARM / "service-start.json").read_text())
            guard.set_expected_workers(start["worker_pid_by_physical_npu"])
            guard.assert_clean()
            progress("service-ready", container_id=container_id)
            sample_dir = quality.QROOT / "samples"
            sample_dir.mkdir()

            # The first sample is serialized so its scored hot-path events
            # cannot be mistaken for another request's events.
            first = items[0]
            first_rows = []
            monitored_samples([first], evaluator, guard, container_id, first_rows.append)
            first_row = first_rows[0]
            result["first_sample_warm_events"] = first_row["warm_events"]
            result["first_sample_scored_events"] = first_row["first_scored_events"]
            if ARM == "hypic-only":
                if (result["first_sample_warm_events"]["hot_worker_pids"]
                        or len(result["first_sample_scored_events"]["hot_worker_pids"]) != 4
                        or result["first_sample_scored_events"]["verified_hot_requests"] < 1):
                    raise RuntimeError("first sample did not prove four-worker scored hot path")
            elif result["first_sample_scored_events"]["hot_worker_pids"]:
                raise RuntimeError("baseline unexpectedly emitted worker-hot events")
            quality.write_json(sample_dir / f"{first['index']:03d}.json", first_row)
            result["completed_samples"] = 1
            result["scored_rows"] = REPETITIONS
            progress("sentinel-complete", index=first["index"],
                     correct=sum(row["correct"] for row in first_row["scores"]))

            def accept_row(row: dict) -> None:
                quality.write_json(sample_dir / f"{row['index']:03d}.json", row)
                if (MODE.startswith("pilot") and ARM == "hypic-only"
                        and row["first_scored_events"]["verified_hot_requests"] < 1):
                    raise RuntimeError(f"pilot sample {row['index']} did not hit scored hot path")
                result["completed_samples"] += 1
                result["scored_rows"] += REPETITIONS
                if result["completed_samples"] % 5 == 0 or result["completed_samples"] == len(items):
                    progress("samples-running", completed=result["completed_samples"],
                             expected=len(items))

            monitored_samples(items[1:], evaluator, guard, container_id, accept_row)
            guard.assert_clean()
            all_events = events(evidence)
            result["events"] = event_summary(all_events)
            if ARM == "hypic-only":
                scored_ids = {score["request_id"] for path in sample_dir.glob("*.json")
                              for score in json.loads(path.read_text())["scores"]}
                boundary_ids = {row.get("request_id") for row in all_events
                                if row.get("event") == "explicit_segment_boundary_active"}
                if (not all(scored_boundary_match(value, boundary_ids)
                            for value in scored_ids)
                        or result["events"]["verified_hot_requests"] < result["scored_rows"]):
                    raise RuntimeError("candidate scored boundary/hot coverage incomplete")
            elif result["events"]["hot_worker_pids"]:
                raise RuntimeError("baseline emitted worker-hot event")
            progress("all-samples-complete", samples=result["completed_samples"],
                     scored_rows=result["scored_rows"])
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
            result["quality_pass_claim"] = False
            result["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            for key, path in {
                "service_stop": quality.QROOT / ARM / "service-stop.json",
                "lane_guard": quality.QROOT / ARM / "lane-guard.json",
            }.items():
                if path.exists():
                    result[key] = json.loads(path.read_text())
                    result[key + "_sha256"] = quality.sha256(path)
            if evidence.exists():
                result["hypic_evidence_sha256"] = quality.sha256(evidence)
            quality.write_json(quality.QROOT / "arm-result.json", result)
            progress("arm-complete" if error is None else "arm-failed", error=error,
                     completed=result["completed_samples"], expected=len(items))
    if error:
        raise RuntimeError(error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
