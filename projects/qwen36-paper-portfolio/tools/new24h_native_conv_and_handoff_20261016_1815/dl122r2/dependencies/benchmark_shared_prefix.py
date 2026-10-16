#!/usr/bin/env python3
"""Exercise a shared exact prefix and identify the serving cache tier."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class RequestResult:
    index: int
    ok: bool
    ttft_ms: float | None
    duration_s: float
    output_tokens: int | None
    output_sha256: str | None = None
    error: str | None = None
    requested_output_tokens: int | None = None
    finish_reason: str | None = None


@dataclass(frozen=True)
class PromptCase:
    prompt: list[int] | str
    segment_ends: tuple[int, ...]


_REPORT_FIELD = re.compile(r"\b([a-z_]+)=([0-9]+)\b")
_PLUGIN_BUILD = re.compile(
    r"HYPIC plugin build active: version=([^\s]+) module=([^\s]+)"
)
_EXPECTED_PLUGIN_VERSION = "0.8.5"
_WARMUP_EVIDENCE = (
    "plugin_build_active",
    "runtime_scheduler_active",
    "explicit_segment_boundary_active",
    "position_independent_observation",
    "position_independent_reuse_observed",
    "position_independent_producer_isolated",
    "position_independent_producer_scheduled",
    "position_independent_materialization_plan_created",
    "position_independent_materialization",
    "position_independent_materialization_dispatched",
    "materialization_ready",
    "qwen_mrope_geometry_registered",
)


def _valid_gdn_grouped_head_evidence(item: dict[str, Any]) -> bool:
    try:
        qk_heads = int(item.get("tp_local_query_key_heads", 0) or 0)
        value_heads = int(item.get("tp_local_value_heads", 0) or 0)
        group_size = int(item.get("value_head_group_size", 0) or 0)
    except (TypeError, ValueError):
        return False
    return (
        qk_heads > 0
        and value_heads >= qk_heads
        and value_heads % qk_heads == 0
        and group_size == value_heads // qk_heads
    )


def _valid_gdn_aclnn_evidence(item: dict[str, Any]) -> bool:
    """Require the only save-new-value mode accepted by AscendC 0.23."""

    try:
        discarded_passes = int(item.get("discarded_auxiliary_value_passes", -1))
    except (TypeError, ValueError):
        return False
    return item.get("aclnn_save_new_value") is True and discarded_passes == 2


def _validated_ranges(
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[tuple[int, int], ...] | None:
    if not isinstance(value, list) or (not value and not allow_empty):
        return None
    ranges: list[tuple[int, int]] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            return None
        try:
            start, end = int(item[0]), int(item[1])
        except (TypeError, ValueError):
            return None
        if start < 0 or end <= start:
            return None
        ranges.append((start, end))
    return tuple(ranges)


def _is_complete_partition(ranges: tuple[tuple[int, int], ...]) -> bool:
    return bool(ranges) and ranges[0][0] == 0 and all(
        left[1] == right[0] for left, right in zip(ranges, ranges[1:])
    )


def _valid_mamba_alignment_evidence(item: dict[str, Any]) -> bool:
    """Prove that hybrid-cache adaptation preserves every prompt token."""

    if item.get("event") != "mamba_aligned_segment_partition":
        return False
    try:
        block_size = int(item.get("block_size", 0) or 0)
        semantic_count = int(item.get("semantic_segments", 0) or 0)
        runtime_count = int(item.get("runtime_segments", 0) or 0)
        split_count = int(item.get("split_segments", -1))
        core_tokens = int(item.get("reusable_core_tokens", -1))
        residual_tokens = int(item.get("cold_residual_tokens", -1))
    except (TypeError, ValueError):
        return False
    semantic = _validated_ranges(item.get("semantic_ranges"))
    runtime = _validated_ranges(item.get("runtime_ranges"))
    cores = _validated_ranges(
        item.get("reusable_core_ranges"),
        allow_empty=True,
    )
    residuals = _validated_ranges(
        item.get("cold_residual_ranges"),
        allow_empty=True,
    )
    if semantic is None or runtime is None or block_size <= 0:
        return False
    if cores is None or residuals is None:
        return False
    if not _is_complete_partition(semantic) or not _is_complete_partition(runtime):
        return False
    if semantic_count != len(semantic) or runtime_count != len(runtime):
        return False
    if split_count != runtime_count - semantic_count:
        return False
    if semantic[-1] != runtime[-1] or semantic[-1][1] != runtime[-1][1]:
        return False
    if item.get("token_partition_preserved") is not True:
        return False
    if any(end <= start or (end - start) % block_size for start, end in cores):
        return False
    if any(
        end <= start or end - start >= block_size for start, end in residuals
    ):
        return False
    cacheable_runtime = sorted(runtime[:-1])
    if sorted((*cores, *residuals)) != cacheable_runtime:
        return False
    return (
        sum(end - start for start, end in cores) == core_tokens
        and sum(end - start for start, end in residuals) == residual_tokens
    )


def _post_json(url: str, payload: dict[str, Any], timeout: float):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urlopen(request, timeout=timeout)


def _tokenize(base_url: str, model: str, text: str, timeout: float) -> list[int]:
    with _post_json(
        f"{base_url}/tokenize",
        {"model": model, "prompt": text, "add_special_tokens": False},
        timeout,
    ) as response:
        data = json.load(response)
    tokens = data.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        raise RuntimeError(f"/tokenize returned no tokens: {data!r}")
    return [int(token) for token in tokens]


def _tokens_at_least(
    base_url: str,
    model: str,
    seed: str,
    count: int,
    timeout: float,
) -> list[int]:
    repeats = max(1, math.ceil(count / 8))
    while True:
        tokens = _tokenize(base_url, model, seed * repeats, timeout)
        if len(tokens) >= count:
            return tokens[:count]
        repeats *= 2


def _build_prompts(args) -> list[list[int]]:
    prefix_seed = (
        "Reusable technical context. The cached boundary state must remain "
        "identical across requests. Record value 17.\n"
    )
    shared_prefix = _tokens_at_least(
        args.base_url,
        args.model,
        prefix_seed,
        args.prefix_tokens,
        args.timeout,
    )
    tail_length = args.input_tokens - args.prefix_tokens
    prompts: list[list[int]] = []
    total = args.requests + args.warmup_requests
    for index in range(total):
        tail_seed = (
            f"Unique request {index:05d}. This suffix deliberately differs "
            "from every other request. Continue processing this context.\n"
        )
        tail = _tokens_at_least(
            args.base_url,
            args.model,
            tail_seed,
            tail_length,
            args.timeout,
        )
        prompts.append(shared_prefix + tail)
    return prompts


def _stream_completion(
    args,
    index: int,
    prompt: list[int] | str | PromptCase,
    barrier: threading.Barrier | None,
    max_tokens: int,
) -> RequestResult:
    started = time.perf_counter()
    first_token_at: float | None = None
    output_tokens: int | None = None
    output_parts: list[str] = []
    finish_reason: str | None = None
    if isinstance(prompt, PromptCase):
        prompt_value = prompt.prompt
        segment_ends = prompt.segment_ends
    else:
        prompt_value = prompt
        segment_ends = (args.prefix_tokens, args.input_tokens)
    payload = {
        "model": args.model,
        "prompt": prompt_value,
        "max_tokens": max_tokens,
        "temperature": 0,
        "seed": 0,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if max_tokens > 1 and not bool(getattr(args, "respect_eos", False)):
        payload["ignore_eos"] = True
    if segment_ends:
        payload["vllm_xargs"] = {
            "hypic_segment_ends": ",".join(str(end) for end in segment_ends),
        }
    try:
        if barrier is not None:
            barrier.wait(timeout=args.timeout)
            started = time.perf_counter()
        with _post_json(
            f"{args.base_url}/v1/completions",
            payload,
            args.timeout,
        ) as response:
            for raw_line in response:
                line = raw_line.strip()
                if not line.startswith(b"data:"):
                    continue
                body = line[5:].strip()
                if body == b"[DONE]":
                    break
                data = json.loads(body)
                usage = data.get("usage")
                if (
                    isinstance(usage, dict)
                    and usage.get("completion_tokens") is not None
                ):
                    output_tokens = int(usage["completion_tokens"])
                choices = data.get("choices") or []
                for choice in choices:
                    if choice.get("finish_reason") is not None:
                        finish_reason = str(choice["finish_reason"])
                    text = choice.get("text")
                    if text is None:
                        text = (choice.get("delta") or {}).get("content")
                    if text:
                        output_parts.append(str(text))
                        if first_token_at is None:
                            first_token_at = time.perf_counter()
        finished = time.perf_counter()
        # A one-token priming request can legitimately emit a token whose
        # decoded text is empty (for example a control/special token).  The
        # final usage chunk is authoritative that the engine executed the
        # requested token, which is sufficient for cache warmup.  Keep the
        # stricter non-empty-text requirement for measured requests so TTFT
        # and output hashes retain their original meaning.
        if (
            first_token_at is None
            and max_tokens == 1
            and output_tokens == 1
        ):
            first_token_at = finished
        if first_token_at is None:
            raise RuntimeError("stream completed without a non-empty output token")
        return RequestResult(
            index=index,
            ok=True,
            ttft_ms=(first_token_at - started) * 1000,
            duration_s=finished - started,
            output_tokens=output_tokens,
            output_sha256=hashlib.sha256(
                "".join(output_parts).encode("utf-8")
            ).hexdigest(),
            requested_output_tokens=max_tokens,
            finish_reason=finish_reason,
        )
    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        ValueError,
        RuntimeError,
    ) as exc:
        finished = time.perf_counter()
        detail = str(exc)
        if isinstance(exc, HTTPError):
            try:
                detail = f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}"
            except Exception:
                detail = f"HTTP {exc.code}: {exc.reason}"
        return RequestResult(
            index=index,
            ok=False,
            ttft_ms=None,
            duration_s=finished - started,
            output_tokens=None,
            error=detail,
            requested_output_tokens=max_tokens,
            finish_reason=finish_reason,
        )


def _run_measured(
    args,
    prompts: list[list[int] | str | PromptCase],
) -> tuple[list[RequestResult], float]:
    results: list[RequestResult] = []
    started = time.perf_counter()
    for offset in range(0, len(prompts), args.concurrency):
        batch = prompts[offset : offset + args.concurrency]
        barrier = threading.Barrier(len(batch)) if len(batch) > 1 else None
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            futures = [
                executor.submit(
                    _stream_completion,
                    args,
                    offset + local_index,
                    prompt,
                    barrier,
                    args.output_tokens,
                )
                for local_index, prompt in enumerate(batch)
            ]
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                status = "ok" if result.ok else f"failed: {result.error}"
                ttft = "n/a" if result.ttft_ms is None else f"{result.ttft_ms:.1f} ms"
                print(f"request={result.index:03d} status={status} ttft={ttft}")
    return sorted(
        results, key=lambda result: result.index
    ), time.perf_counter() - started


def _run_warmups(
    args,
    prompts: list[list[int] | str | PromptCase],
) -> list[RequestResult]:
    """Submit all priming requests together so reuse is visible before dequeue."""

    barrier = threading.Barrier(len(prompts))
    results: list[RequestResult] = []
    with ThreadPoolExecutor(max_workers=len(prompts)) as executor:
        futures = [
            executor.submit(
                _stream_completion,
                args,
                -(index + 1),
                prompt,
                barrier,
                1,
            )
            for index, prompt in enumerate(prompts)
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            warmup = -result.index
            if result.ok:
                print(f"warmup={warmup} ttft={result.ttft_ms:.1f} ms")
            else:
                print(f"warmup={warmup} failed: {result.error}")
    return sorted(results, key=lambda result: result.index, reverse=True)


def _nearest_rank_percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = min(
        len(ordered) - 1,
        max(0, math.ceil(len(ordered) * float(percentile)) - 1),
    )
    return ordered[index]


def _summary(
    results: list[RequestResult],
    duration_s: float,
    *,
    concurrency: int | None = None,
) -> dict[str, Any]:
    successful = [result for result in results if result.ok]
    ttfts = [result.ttft_ms for result in successful if result.ttft_ms is not None]
    output_tokens = sum(result.output_tokens or 0 for result in successful)
    expected_output_tokens = sum(
        int(result.requested_output_tokens or 0) for result in successful
    )
    completed_output_requests = sum(
        1
        for result in successful
        if result.requested_output_tokens is not None
        and result.output_tokens == result.requested_output_tokens
    )
    finish_reasons = Counter(
        result.finish_reason or "missing" for result in successful
    )
    decode_durations_s = [
        max(0.0, result.duration_s - (result.ttft_ms or 0.0) / 1000.0)
        for result in successful
        if result.ttft_ms is not None
        and result.output_tokens is not None
        and result.output_tokens > 1
    ]
    decode_intervals = sum(
        int(result.output_tokens) - 1
        for result in successful
        if result.ttft_ms is not None
        and result.output_tokens is not None
        and result.output_tokens > 1
    )
    tpots = [
        max(0.0, result.duration_s - (result.ttft_ms or 0.0) / 1000.0)
        * 1000.0
        / (result.output_tokens - 1)
        for result in successful
        if result.ttft_ms is not None
        and result.output_tokens is not None
        and result.output_tokens > 1
    ]
    request_durations_ms = [result.duration_s * 1000.0 for result in successful]
    summary: dict[str, Any] = {
        "requests": len(results),
        "successful": len(successful),
        "failed": len(results) - len(successful),
        "benchmark_duration_s": duration_s,
        "output_tokens": output_tokens,
        "expected_output_tokens": expected_output_tokens,
        "output_token_completion_ratio": (
            output_tokens / expected_output_tokens if expected_output_tokens else 0
        ),
        "fixed_output_requests": completed_output_requests,
        "fixed_output_verified": bool(successful)
        and completed_output_requests == len(successful),
        "finish_reasons": dict(sorted(finish_reasons.items())),
        "output_tokens_per_second": output_tokens / duration_s if duration_s else 0,
    }
    if ttfts:
        summary.update(
            {
                "ttft_mean_ms": statistics.fmean(ttfts),
                "ttft_median_ms": statistics.median(ttfts),
                "ttft_p95_ms": _nearest_rank_percentile(ttfts, 0.95),
                "ttft_max_ms": max(ttfts),
            }
        )
    if tpots:
        summary.update(
            {
                "tpot_mean_ms": statistics.fmean(tpots),
                "tpot_median_ms": statistics.median(tpots),
                "tpot_p95_ms": _nearest_rank_percentile(tpots, 0.95),
                "tpot_max_ms": max(tpots),
            }
        )
    if decode_intervals:
        summary["tpot_weighted_ms"] = (
            sum(decode_durations_s) * 1000.0 / decode_intervals
        )
    if request_durations_ms:
        summary.update(
            {
                "request_duration_mean_ms": statistics.fmean(
                    request_durations_ms
                ),
                "request_duration_median_ms": statistics.median(
                    request_durations_ms
                ),
                "request_duration_p95_ms": _nearest_rank_percentile(
                    request_durations_ms,
                    0.95,
                ),
                "request_duration_max_ms": max(request_durations_ms),
            }
        )
    if concurrency is not None and int(concurrency) > 0 and successful:
        wave_maxima_s: dict[int, float] = {}
        for result in successful:
            wave = max(0, int(result.index)) // int(concurrency)
            wave_maxima_s[wave] = max(
                wave_maxima_s.get(wave, 0.0),
                float(result.duration_s),
            )
        wave_durations_s = list(wave_maxima_s.values())
        summary.update(
            {
                "measured_concurrency": int(concurrency),
                "measured_waves": len(wave_durations_s),
                "wave_duration_mean_s": statistics.fmean(wave_durations_s),
                "wave_duration_p95_s": _nearest_rank_percentile(
                    wave_durations_s,
                    0.95,
                ),
                "wave_duration_max_s": max(wave_durations_s),
            }
        )
    return summary


def _service_log_offset(path: Path) -> int:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def _parse_evidence_lines(raw: bytes) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in raw.splitlines():
        try:
            value = json.loads(line)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict) and isinstance(value.get("event"), str):
            events.append(value)
    return events


def _read_evidence_events(
    path: Path | None,
    start_offset: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    if path is None:
        return [], [], 0
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return [], [], 0
    offset = start_offset if len(raw) >= start_offset else 0
    return (
        _parse_evidence_lines(raw[:offset]),
        _parse_evidence_lines(raw[offset:]),
        len(raw),
    )


def _event_reports_failure(event: dict[str, Any]) -> bool:
    if event.get("event") == "mamba_aligned_segment_partition":
        return not _valid_mamba_alignment_evidence(event)
    if event.get("event") in {
        "explicit_segment_boundary_rejected",
        "materialization_rejected",
        "position_independent_materialization_timeout",
        "position_independent_materialization_plan_skipped",
        "position_independent_producer_rejected",
    }:
        return True
    if event.get("event") != "materialization_report":
        return False
    try:
        return int(event.get("failed", 0) or 0) > 0
    except (TypeError, ValueError):
        return False


def _inspect_hot_path_log(
    path: Path | None,
    start_offset: int,
    *,
    evidence_path: Path | None = None,
    evidence_start_offset: int = 0,
) -> dict[str, Any]:
    """Inspect startup identity plus service-log bytes from this benchmark run."""

    try:
        if path is None:
            raise FileNotFoundError
        raw = path.read_bytes()
        size = len(raw)
        offset = start_offset if size >= start_offset else 0
        startup_content = raw[:offset].decode("utf-8", "replace")
        content = raw[offset:].decode("utf-8", "replace")
    except FileNotFoundError:
        startup_content = ""
        content = ""
        size = 0

    startup_events, run_events, evidence_size = _read_evidence_events(
        evidence_path,
        evidence_start_offset,
    )
    all_events = startup_events + run_events
    run_event_names = {str(item["event"]) for item in run_events}
    build_events = [
        item for item in all_events if item.get("event") == "plugin_build_active"
    ]
    runtime_events = [
        item for item in all_events if item.get("event") == "runtime_scheduler_active"
    ]
    capability_events = [
        item for item in all_events if item.get("event") == "hypic_capability_contract"
    ]
    upstream_parity_events = [
        item
        for item in all_events
        if item.get("event") == "hypic_upstream_parity_contract"
    ]

    build_matches = tuple(_PLUGIN_BUILD.finditer(startup_content + content))
    plugin_version = (
        str(build_events[-1].get("version"))
        if build_events
        else build_matches[-1].group(1)
        if build_matches
        else None
    )
    plugin_module = (
        str(build_events[-1].get("module"))
        if build_events
        else build_matches[-1].group(2)
        if build_matches
        else None
    )
    runtime_content = startup_content + content
    all_event_names = {str(item["event"]) for item in all_events}
    position_batches = [
        item for item in run_events if item.get("event") == "position_independent_batch"
    ]
    pi_observation = "independent_segment_observation" in run_event_names
    explicit_segment_boundary = "explicit_segment_boundary_active" in run_event_names
    pi_reuse = "independent_segment_reuse_observed" in run_event_names
    pi_producer_scheduled = "position_independent_producer_scheduled" in run_event_names
    pi_producer_isolated = "position_independent_producer_isolated" in run_event_names
    pi_materialization = (
        "position_independent_materialization_candidate" in run_event_names
        or any(
            int(item.get("materializations", 0) or 0) > 0 for item in position_batches
        )
    )
    pi_materialization_plan_created = (
        "position_independent_materialization_plan_created" in run_event_names
    )
    pi_materialization_dispatched = (
        "position_independent_materialization_dispatched" in run_event_names
    )
    pi_scheduler = any(
        int(item.get("segment_hits", 0) or 0) > 0
        and int(item.get("skipped_tokens", 0) or 0) > 0
        for item in position_batches
    )
    pi_relocated_hit = any(
        int(item.get("relocated_segment_hits", 0) or 0) > 0 for item in position_batches
    )
    pi_grouped_kv_replay = any(
        item.get("event") == "position_independent_kv_replay_grouped"
        and int(item.get("matching_placements", 0) or 0) > 0
        and int(item.get("host_material_passes_per_layer", 0) or 0) == 1
        for item in run_events
    )
    pi_attention_zero_copy = any(
        item.get("event") == "position_independent_attention"
        and item.get("zero_copy_phase_c") is True
        for item in run_events
    )
    pi_gdn_vectorized = any(
        item.get("event") == "position_independent_gdn"
        and item.get("vectorized_compose") is True
        and int(item.get("wy_preparations", 0) or 0) == 1
        and int(item.get("state_passes", 0) or 0) == 3
        and int(item.get("transition_composes", 0) or 0) > 0
        and int(item.get("compose_launches", 0) or 0) > 0
        and _valid_gdn_grouped_head_evidence(item)
        and _valid_gdn_aclnn_evidence(item)
        for item in run_events
    )
    mixed_native_decode_isolated = any(
        item.get("event") == "mixed_batch_native_decode_isolated"
        and int(item.get("decode_requests", 0) or 0) > 0
        and int(item.get("decode_tokens", 0) or 0) > 0
        and int(item.get("prefill_requests", 0) or 0) > 0
        and int(item.get("prefill_tokens", 0) or 0) > 0
        and int(item.get("decode_convolution_passes", 0) or 0) == 1
        and int(item.get("decode_state_passes", 0) or 0) == 1
        and int(item.get("pic_prefill_state_passes", 0) or 0) == 3
        and int(item.get("decode_rows_in_pic_state_passes", -1)) == 0
        and item.get("decode_kernel") == "npu_recurrent_gated_delta_rule"
        for item in run_events
    )
    position_dependent_prefix_hit = any(
        item.get("event") == "position_dependent_prefix_cache_hit"
        and int(item.get("requests", 0) or 0) > 0
        and int(item.get("tokens", 0) or 0) > 0
        for item in run_events
    )
    prefix_cache_hypic_combined_hit = any(
        item.get("event") == "prefix_cache_hypic_combined_hit"
        and bool(item.get("request_id"))
        and int(item.get("native_prefix_tokens", 0) or 0) > 0
        and int(item.get("base_computed_tokens", 0) or 0)
        >= int(item.get("native_prefix_tokens", 0) or 0)
        and int(item.get("public_segment_hits", 0) or 0) > 0
        and int(item.get("public_tokens_skipped", 0) or 0) > 0
        for item in run_events
    )
    mamba_alignment_events = [
        item
        for item in run_events
        if _valid_mamba_alignment_evidence(item)
    ]
    physical_budget_reclaimed = any(
        item.get("event") == "physical_token_budget_reclaimed"
        and int(item.get("additionally_admitted_tokens", 0) or 0) > 0
        for item in run_events
    )
    native_decode_passthrough = any(
        item.get("event") == "native_decode_scheduler_passthrough"
        and int(item.get("cumulative_steps", 0) or 0) > 0
        and int(item.get("requests", 0) or 0) > 0
        and int(item.get("tokens", 0) or 0)
        >= int(item.get("requests", 0) or 0)
        and int(item.get("cumulative_requests", 0) or 0)
        >= int(item.get("requests", 0) or 0)
        and int(item.get("cumulative_tokens", 0) or 0)
        >= int(item.get("requests", 0) or 0)
        and int(item.get("full_prompt_token_scans", -1)) == 0
        and item.get("pic_batch_plan_attached") is False
        and item.get("pic_model_dispatch") is False
        for item in run_events
    )
    mixed_decode_reclaim_suppressed = any(
        item.get("event") == "mixed_decode_budget_reclaim_suppressed"
        and int(item.get("running_decode_requests", 0) or 0) > 0
        and int(item.get("cumulative_steps", 0) or 0) > 0
        for item in run_events
    )
    mixed_decode_bounded_reclaim = any(
        item.get("event") == "mixed_decode_budget_reclaim_bounded"
        and int(item.get("running_decode_requests", 0) or 0) > 0
        and int(item.get("selected_requests", 0) or 0) >= 2
        and int(item.get("shared_material_hashes", 0) or 0) > 0
        and int(item.get("estimated_physical_tokens", 0) or 0) > 0
        and int(item.get("estimated_physical_tokens", 0) or 0)
        <= int(item.get("configured_physical_budget", 0) or 0)
        and int(item.get("expanded_logical_budget", 0) or 0)
        > int(item.get("configured_physical_budget", 0) or 0)
        for item in run_events
    )
    mixed_decode_hypic_admitted = any(
        item.get("event") == "mixed_decode_hypic_admitted"
        and int(item.get("physical_tokens", 0) or 0) > 0
        and int(item.get("skipped_tokens", 0) or 0) > 0
        and int(item.get("physical_tokens", 0) or 0)
        <= int(item.get("max_mixed_physical_tokens", 0) or 0)
        and int(item.get("skipped_tokens", 0) or 0) * 100
        >= int(item.get("physical_tokens", 0) or 0)
        * int(item.get("minimum_savings_percent", 0) or 0)
        for item in run_events
    )
    mixed_decode_shared_group_admitted = any(
        item.get("event") == "mixed_decode_shared_group_admitted"
        and int(item.get("admitted_requests", 0) or 0) >= 2
        and int(item.get("shared_material_hashes", 0) or 0) > 0
        and int(item.get("cumulative_physical_tokens", 0) or 0) > 0
        and int(item.get("cumulative_physical_tokens", 0) or 0)
        <= int(item.get("max_mixed_physical_tokens", 0) or 0)
        for item in run_events
    )
    gdn_npu_material = any(
        item.get("event") == "gdn_material_storage_selected"
        and item.get("device") == "npu"
        and float(item.get("projected_mib", 0) or 0) > 0
        for item in run_events
    )
    native_prefix_reclaim_yielded = any(
        item.get("event") == "physical_budget_reclaim_yielded_to_native_prefix"
        and int(item.get("native_prefix_tokens", 0) or 0) > 0
        and int(item.get("superseded_public_materials", 0) or 0) > 0
        for item in run_events
    )
    runtime_event_active = any(
        bool(item.get("add_request"))
        and bool(item.get("schedule"))
        and bool(item.get("update_from_output"))
        for item in runtime_events
    )
    capability_contract_active = any(
        bool(item.get("hot_reuse_complete")) and item.get("paper_complete") is False
        for item in capability_events
    )
    upstream_parity_contract_active = any(
        bool(item.get("qwen35_single_instance_complete"))
        and item.get("upstream_complete") is False
        and bool(item.get("hardware_verification_required"))
        for item in upstream_parity_events
    )

    evidence = {
        "plugin_build_active": plugin_version == _EXPECTED_PLUGIN_VERSION,
        "capability_contract_active": capability_contract_active,
        "upstream_parity_contract_active": upstream_parity_contract_active,
        "runtime_scheduler_active": (
            runtime_event_active
            or (
                "HYPIC runtime scheduler active:" in runtime_content
                and "add_request=True schedule=True update_from_output=True"
                in runtime_content
            )
        ),
        "admission_observation_active": (
            "HYPIC prefix observation active: trigger=admission" in content
            or pi_observation
            or any(
                item.get("event") == "prefix_observation_active"
                and item.get("trigger") == "admission"
                for item in run_events
            )
        ),
        "repeated_prefix_detected": (
            "HYPIC repeated queue-head prefix detected" in content
            or "repeated_prefix_detected" in run_event_names
            or pi_reuse
        ),
        "materialization_candidate": (
            "HYPIC materialization candidate" in content
            or "materialization_candidate" in run_event_names
            or pi_materialization
        ),
        "materialization_ready": "materialization_ready" in run_event_names,
        "scheduler_hot_path": (
            "HYPIC hot path active before scheduling" in content
            or "scheduler_hot_path" in run_event_names
            or pi_scheduler
        ),
        "worker_hot_path": (
            "HYPIC worker hot path verified" in content
            or "worker_hot_path" in run_event_names
        ),
        "physical_kv_layout": (
            "HYPIC resolved TP-local full-attention cache" in content
            or "physical_kv_layout" in run_event_names
        ),
        "complete_hybrid_repair": "complete_hybrid_repair" in run_event_names,
        "position_independent_observation": pi_observation,
        "explicit_segment_boundary_active": explicit_segment_boundary,
        "position_independent_reuse_observed": pi_reuse,
        "position_independent_producer_isolated": pi_producer_isolated,
        "position_independent_producer_scheduled": pi_producer_scheduled,
        "position_independent_materialization_plan_created": (
            pi_materialization_plan_created
        ),
        "position_independent_materialization": pi_materialization,
        "position_independent_materialization_dispatched": (
            pi_materialization_dispatched
        ),
        "position_independent_scheduler": pi_scheduler,
        "position_independent_attention": (
            "position_independent_attention" in all_event_names
        ),
        "position_independent_gdn": "position_independent_gdn" in all_event_names,
        "position_independent_kv_grouped_replay": pi_grouped_kv_replay,
        "position_independent_attention_zero_copy": pi_attention_zero_copy,
        "position_independent_gdn_vectorized": pi_gdn_vectorized,
        "mixed_batch_native_decode_isolated": mixed_native_decode_isolated,
        "native_decode_scheduler_passthrough": native_decode_passthrough,
        "qwen_mrope_geometry_registered": (
            "qwen_mrope_geometry_registered" in all_event_names
        ),
    }
    for line in content.splitlines():
        if "HYPIC materialization report:" not in line:
            continue
        fields = {name: int(value) for name, value in _REPORT_FIELD.findall(line)}
        if fields.get("ready", 0) > 0 and fields.get("failed", 0) == 0:
            evidence["materialization_ready"] = True
        if (
            fields.get("verified_hot_reqs", 0) > 0
            and fields.get("verified_skipped_tokens", 0) > 0
            and fields.get("full_attn_repairs", 0) > 0
            and fields.get("gdn_restores", 0) > 0
        ):
            evidence["complete_hybrid_repair"] = True

    missing = [name for name, present in evidence.items() if not present]
    all_event_counts = Counter(str(item["event"]) for item in all_events)
    run_event_counts = Counter(str(item["event"]) for item in run_events)
    failure_events = [item for item in run_events if _event_reports_failure(item)][-20:]
    return {
        "service_log": None if path is None else str(path),
        "service_log_start_offset": start_offset,
        "service_log_bytes_scanned": max(0, size - min(size, start_offset)),
        "expected_plugin_version": _EXPECTED_PLUGIN_VERSION,
        "plugin_version": plugin_version,
        "plugin_module": plugin_module,
        "evidence_file": None if evidence_path is None else str(evidence_path),
        "evidence_file_start_offset": evidence_start_offset,
        "evidence_file_bytes_scanned": max(
            0,
            evidence_size - min(evidence_size, evidence_start_offset),
        ),
        "evidence_process_ids": sorted(
            {
                int(item["pid"])
                for item in all_events
                if isinstance(item.get("pid"), int)
            }
        ),
        "evidence_event_counts": dict(sorted(all_event_counts.items())),
        "run_evidence_event_counts": dict(sorted(run_event_counts.items())),
        "evidence_failures": failure_events,
        "hot_path_evidence": evidence,
        "hot_path_verified": not missing,
        "hot_path_missing": missing,
        "position_independent_relocated_hit_verified": pi_relocated_hit,
        "position_dependent_prefix_hit_verified": position_dependent_prefix_hit,
        "prefix_cache_hypic_combined_hit_verified": (
            prefix_cache_hypic_combined_hit
        ),
        "mamba_alignment_partition_verified": bool(mamba_alignment_events),
        "mamba_alignment_block_sizes": sorted(
            {
                int(item["block_size"])
                for item in mamba_alignment_events
            }
        ),
        "mamba_alignment_adapted_requests": len(
            {
                str(item.get("request_id"))
                for item in mamba_alignment_events
                if item.get("adapted") is True
            }
        ),
        "mamba_alignment_max_reusable_core_tokens": max(
            (
                int(item.get("reusable_core_tokens", 0) or 0)
                for item in mamba_alignment_events
            ),
            default=0,
        ),
        "mamba_alignment_max_cold_residual_tokens": max(
            (
                int(item.get("cold_residual_tokens", 0) or 0)
                for item in mamba_alignment_events
            ),
            default=0,
        ),
        "physical_budget_reclaimed_verified": physical_budget_reclaimed,
        "native_decode_passthrough_verified": native_decode_passthrough,
        "mixed_batch_native_decode_isolation_verified": (
            mixed_native_decode_isolated
        ),
        "mixed_decode_latency_protection_verified": (
            (mixed_decode_reclaim_suppressed or mixed_decode_bounded_reclaim)
            and mixed_decode_hypic_admitted
        ),
        "mixed_decode_grouped_reclaim_verified": (
            mixed_decode_bounded_reclaim
            and mixed_decode_shared_group_admitted
        ),
        "gdn_npu_material_verified": gdn_npu_material,
        "native_prefix_redundancy_bypass_verified": native_prefix_reclaim_yielded,
        "native_prefix_reclaim_yield_verified": native_prefix_reclaim_yielded,
    }


def _wait_for_hot_path_log(
    path: Path | None,
    start_offset: int,
    *,
    evidence_path: Path | None = None,
    evidence_start_offset: int = 0,
    timeout: float = 5.0,
    accept_position_dependent: bool = False,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        result = _inspect_hot_path_log(
            path,
            start_offset,
            evidence_path=evidence_path,
            evidence_start_offset=evidence_start_offset,
        )
        accepted = result["hot_path_verified"] or (
            accept_position_dependent
            and result["position_dependent_prefix_hit_verified"]
        )
        if accepted or time.monotonic() >= deadline:
            return result
        time.sleep(0.25)


def _wait_for_warmup_materialization(
    path: Path | None,
    start_offset: int,
    *,
    evidence_path: Path | None = None,
    evidence_start_offset: int = 0,
    timeout: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        result = _inspect_hot_path_log(
            path,
            start_offset,
            evidence_path=evidence_path,
            evidence_start_offset=evidence_start_offset,
        )
        evidence = result["hot_path_evidence"]
        missing = [name for name in _WARMUP_EVIDENCE if not evidence.get(name)]
        result["warmup_materialization_verified"] = not missing
        result["warmup_materialization_missing"] = missing
        if result["evidence_failures"]:
            result["warmup_terminal_failure"] = True
            return result
        if not missing or time.monotonic() >= deadline:
            return result
        time.sleep(0.25)


def _compare_reference(
    results: list[RequestResult],
    reference_path: Path,
    current_config: dict[str, Any],
) -> dict[str, Any]:
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    reference_config = reference.get("config")
    if not isinstance(reference_config, dict):
        raise ValueError(f"reference JSON has no config object: {reference_path}")
    compared_config_keys = (
        "model",
        "input_tokens",
        "prefix_tokens",
        "output_tokens",
        "requests",
        "concurrency",
        "warmup_requests",
        "warmup_mode",
        "ignore_eos",
    )
    mismatched_config = {
        key: (reference_config.get(key), current_config.get(key))
        for key in compared_config_keys
        if reference_config.get(key) != current_config.get(key)
    }
    if mismatched_config:
        raise ValueError(
            "reference benchmark configuration differs from this run: "
            + json.dumps(mismatched_config, ensure_ascii=True, sort_keys=True)
        )
    reference_results = reference.get("results")
    if not isinstance(reference_results, list):
        raise ValueError(f"reference JSON has no results list: {reference_path}")
    by_index = {
        int(item["index"]): item
        for item in reference_results
        if isinstance(item, dict) and item.get("index") is not None
    }
    compared = 0
    matches = 0
    mismatches: list[int] = []
    for result in results:
        baseline = by_index.get(result.index)
        if (
            not result.ok
            or result.output_sha256 is None
            or not isinstance(baseline, dict)
            or not baseline.get("ok")
            or not baseline.get("output_sha256")
        ):
            continue
        compared += 1
        if result.output_sha256 == baseline["output_sha256"]:
            matches += 1
        else:
            mismatches.append(result.index)
    return {
        "reference_compared": compared,
        "reference_expected": len(results),
        "reference_exact_matches": matches,
        "reference_exact_match_rate": matches / compared if compared else None,
        "reference_mismatch_indices": mismatches,
    }


def _parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Warm and benchmark one same-position prefix through the OpenAI API."
        )
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:6666")
    parser.add_argument("--model", default="qwen3.5")
    parser.add_argument("--input-tokens", type=int, default=32768)
    parser.add_argument("--prefix-tokens", type=int, default=16384)
    parser.add_argument("--output-tokens", type=int, default=1024)
    parser.add_argument(
        "--respect-eos",
        action="store_true",
        help=(
            "allow early EOS for diagnostic generation; fixed-length performance "
            "acceptance is disabled only when this flag is explicit"
        ),
    )
    parser.add_argument("--requests", type=int, default=40)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--warmup-requests", type=int, default=2)
    parser.add_argument(
        "--warmup-evidence-timeout",
        type=float,
        default=30.0,
        help="seconds to wait for materialization proof before measured traffic",
    )
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument(
        "--service-log",
        type=Path,
        help="optional vLLM service log used as one HYPIC evidence channel",
    )
    parser.add_argument(
        "--evidence-file",
        type=Path,
        help="cross-process HYPIC JSONL evidence file configured on the service",
    )
    cache_gate = parser.add_mutually_exclusive_group()
    cache_gate.add_argument(
        "--require-hot-path",
        action="store_true",
        help="fail unless diagnostics prove position-independent hybrid repair",
    )
    cache_gate.add_argument(
        "--require-position-dependent-prefix-hit",
        action="store_true",
        help="fail unless diagnostics prove a native exact-prefix cache hit",
    )
    parser.add_argument(
        "--reference-json",
        type=Path,
        help="compare generated output hashes with an earlier baseline report",
    )
    args = parser.parse_args()
    if not 0 < args.prefix_tokens < args.input_tokens:
        parser.error("--prefix-tokens must be between 1 and --input-tokens - 1")
    for name in ("requests", "concurrency", "output_tokens"):
        if getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    if args.warmup_requests < 2:
        parser.error("--warmup-requests must be at least 2 to materialize a prefix")
    if args.warmup_evidence_timeout <= 0:
        parser.error("--warmup-evidence-timeout must be positive")
    if (
        (args.require_hot_path or args.require_position_dependent_prefix_hit)
        and args.service_log is None
        and args.evidence_file is None
    ):
        parser.error(
            "the selected cache evidence gate requires --service-log or --evidence-file"
        )
    args.base_url = args.base_url.rstrip("/")
    return args


def main() -> int:
    args = _parse_args()
    print(
        f"building prompts: input={args.input_tokens} prefix={args.prefix_tokens} "
        f"requests={args.requests} warmup={args.warmup_requests}"
    )
    prompts = _build_prompts(args)
    service_log_offset = (
        _service_log_offset(args.service_log) if args.service_log is not None else None
    )
    evidence_file_offset = (
        _service_log_offset(args.evidence_file)
        if args.evidence_file is not None
        else None
    )
    warmups = prompts[: args.warmup_requests]
    measured = prompts[args.warmup_requests :]
    run_config = {
        "base_url": args.base_url,
        "model": args.model,
        "input_tokens": args.input_tokens,
        "prefix_tokens": args.prefix_tokens,
        "output_tokens": args.output_tokens,
        "requests": args.requests,
        "concurrency": args.concurrency,
        "warmup_requests": args.warmup_requests,
        "warmup_mode": "concurrent_materialization_gate",
        "ignore_eos": not args.respect_eos,
        "segment_boundary_transport": "vllm_xargs.hypic_segment_ends",
        "segment_ends": [args.prefix_tokens, args.input_tokens],
    }

    warmup_results = _run_warmups(args, warmups)
    failed_warmups = [result for result in warmup_results if not result.ok]
    if failed_warmups:
        raise SystemExit(
            "warmup failed: "
            + "; ".join(f"{result.index}: {result.error}" for result in failed_warmups)
        )

    if args.require_hot_path and (
        args.service_log is not None or args.evidence_file is not None
    ):
        warmup_evidence = _wait_for_warmup_materialization(
            args.service_log,
            service_log_offset or 0,
            evidence_path=args.evidence_file,
            evidence_start_offset=evidence_file_offset or 0,
            timeout=args.warmup_evidence_timeout,
        )
        if not warmup_evidence["warmup_materialization_verified"]:
            summary = {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "benchmark_duration_s": 0.0,
                "output_tokens": 0,
                "output_tokens_per_second": 0.0,
                **warmup_evidence,
            }
            report = {
                "config": run_config,
                "summary": summary,
                "warmup_results": [asdict(result) for result in warmup_results],
                "results": [],
            }
            print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
            if args.json_output is not None:
                args.json_output.write_text(
                    json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True)
                    + "\n",
                    encoding="utf-8",
                )
            print(
                "measured traffic was not started because warmup materialization "
                "proof is incomplete",
            )
            return 1

    results, duration_s = _run_measured(args, measured)
    summary = _summary(results, duration_s, concurrency=args.concurrency)
    if args.reference_json is not None:
        summary.update(_compare_reference(results, args.reference_json, run_config))
    if args.service_log is not None or args.evidence_file is not None:
        summary.update(
            _wait_for_hot_path_log(
                args.service_log,
                service_log_offset or 0,
                evidence_path=args.evidence_file,
                evidence_start_offset=evidence_file_offset or 0,
                accept_position_dependent=(args.require_position_dependent_prefix_hit),
            )
        )
    report = {
        "config": run_config,
        "summary": summary,
        "warmup_results": [asdict(result) for result in warmup_results],
        "results": [asdict(result) for result in results],
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    if args.json_output is not None:
        args.json_output.write_text(
            json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    success = summary["failed"] == 0 and (
        args.respect_eos or bool(summary.get("fixed_output_verified"))
    )
    if args.reference_json is not None:
        success = success and (
            summary["reference_compared"] == summary["reference_expected"]
            and summary["reference_exact_matches"] == summary["reference_expected"]
        )
    if args.require_hot_path:
        success = success and bool(summary.get("hot_path_verified"))
    if args.require_position_dependent_prefix_hit:
        success = success and bool(
            summary.get("position_dependent_prefix_hit_verified")
        )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
