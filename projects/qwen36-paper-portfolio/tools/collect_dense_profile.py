#!/usr/bin/env python3
"""Drive separated Qwen3.6 prefill/decode captures for four TP ranks."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from urllib.request import Request, urlopen


DRIVER_SHA256 = "cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def post(url: str, payload: dict, timeout: float):
    return urlopen(
        Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        ),
        timeout=timeout,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-driver", type=Path, required=True)
    parser.add_argument("--service-dir", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8230")
    parser.add_argument("--timeout", type=float, default=1800)
    args = parser.parse_args()
    output = args.service_dir / "profile-client.json"
    events_path = args.service_dir / "profile-client.events.jsonl"
    if output.exists() or events_path.exists():
        parser.error("preserve prior client artifacts")
    manifest_path = args.service_dir / "service-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest.get("variant") != "qwen36-dense"
        or manifest.get("profiler_config", {}).get("max_iterations") != 30
    ):
        raise RuntimeError("service manifest differs from the frozen profile")
    if digest(args.benchmark_driver) != DRIVER_SHA256:
        raise RuntimeError("frozen prompt driver changed")
    spec = importlib.util.spec_from_file_location(
        "qwen36_profile_prompt_driver", args.benchmark_driver
    )
    driver = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = driver
    spec.loader.exec_module(driver)

    def event(kind: str, **detail) -> None:
        record = {"event": kind, "epoch_s": time.time(), **detail}
        with events_path.open("a") as stream:
            stream.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)

    event("waiting_for_service")
    deadline = time.monotonic() + args.timeout
    while True:
        try:
            with urlopen(args.base_url + "/health", timeout=5) as response:
                if response.status == 200:
                    break
        except OSError:
            pass
        if (args.service_dir / "service-exit.json").exists():
            raise RuntimeError("service exited before readiness")
        if time.monotonic() >= deadline:
            raise TimeoutError("service readiness timed out")
        time.sleep(5)
    event("service_ready")
    config = SimpleNamespace(
        base_url=args.base_url,
        model="qwen36-dense-profile",
        input_tokens=32768,
        prefix_tokens=16384,
        requests=16,
        warmup_requests=2,
        timeout=args.timeout,
        respect_eos=False,
    )
    prompts = driver._build_prompts(config)
    prompt_sha = [hashlib.sha256(json.dumps(p).encode()).hexdigest() for p in prompts]

    def checked(result, tokens: int) -> dict:
        if not result.ok or result.output_tokens != tokens or result.finish_reason != "length":
            raise RuntimeError(f"request validity check failed: {asdict(result)}")
        return asdict(result)

    def control(path: str) -> None:
        with post(args.base_url + path, {}, args.timeout) as response:
            response.read()
            if response.status != 200:
                raise RuntimeError("profiler endpoint failed")

    def trace_dirs() -> set[str]:
        return {
            str(path.relative_to(args.service_dir))
            for path in (args.service_dir / "traces").glob("*ascend_pt")
        }

    results: dict = {"warmup": [], "prefill": {}, "decode": {}}
    for index in range(2):
        results["warmup"].append(
            checked(driver._stream_completion(config, index, prompts[index], None, 64), 64)
        )
    event("single_request_warmup_complete")

    before = trace_dirs()
    control("/start_profile")
    event("prefill_profile_started", requests=1, input_tokens=32768, output_tokens=1)
    try:
        result = driver._stream_completion(config, 2, prompts[2], None, 1)
        if not result.ok or result.output_tokens != 1:
            raise RuntimeError(f"prefill request failed: {asdict(result)}")
        results["prefill"]["request"] = asdict(result)
    finally:
        control("/stop_profile")
    results["prefill"]["trace_dirs"] = sorted(trace_dirs() - before)
    event("prefill_profile_stopped", trace_dirs=results["prefill"]["trace_dirs"])

    barrier = threading.Barrier(16)
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [
            pool.submit(
                driver._stream_completion,
                config,
                index + 2,
                prompts[index + 2],
                barrier,
                64,
            )
            for index in range(16)
        ]
        results["warmup_concurrent"] = [checked(future.result(), 64) for future in futures]
    event("concurrent_warmup_complete", concurrency=16)

    counts = [0] * 16
    done = [False] * 16
    condition = threading.Condition()
    barrier = threading.Barrier(16)

    def stream_request(index: int) -> dict:
        payload = {
            "model": "qwen36-dense-profile",
            "prompt": prompts[index + 2],
            "max_tokens": 256,
            "ignore_eos": True,
            "temperature": 0,
            "seed": 0,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        barrier.wait(timeout=args.timeout)
        started = time.time()
        usage = None
        finish = None
        chunks: list[str] = []
        try:
            with post(args.base_url + "/v1/completions", payload, args.timeout) as response:
                for raw in response:
                    if not raw.startswith(b"data:"):
                        continue
                    body = raw[5:].strip()
                    if body == b"[DONE]":
                        break
                    data = json.loads(body)
                    if data.get("usage"):
                        usage = data["usage"].get("completion_tokens")
                    for choice in data.get("choices", []):
                        finish = choice.get("finish_reason") or finish
                        value = choice.get("text") or ""
                        if value:
                            chunks.append(value)
                            with condition:
                                counts[index] += 1
                                condition.notify_all()
            if usage != 256 or finish != "length":
                raise RuntimeError(
                    f"decode request {index}: usage={usage}, finish={finish}"
                )
            return {
                "index": index,
                "output_tokens": usage,
                "finish_reason": finish,
                "output_sha256": hashlib.sha256("".join(chunks).encode()).hexdigest(),
                "started_epoch_s": started,
                "finished_epoch_s": time.time(),
            }
        finally:
            with condition:
                done[index] = True
                condition.notify_all()

    before = trace_dirs()
    profile_started = False
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(stream_request, index) for index in range(16)]
        try:
            deadline = time.monotonic() + args.timeout
            with condition:
                while min(counts) < 8:
                    if any(done):
                        raise RuntimeError("a request ended before stable decode")
                    if time.monotonic() >= deadline:
                        raise TimeoutError("stable decode wait timed out")
                    condition.wait(timeout=1)
                if any(done) or max(counts) > 200:
                    raise RuntimeError("insufficient remaining decode window")
                results["decode"]["nonempty_chunks_at_trigger"] = list(counts)
            control("/start_profile")
            profile_started = True
            event(
                "decode_profile_started",
                concurrency=16,
                worker_step_limit=30,
                nonempty_chunks_at_trigger=results["decode"][
                    "nonempty_chunks_at_trigger"
                ],
            )
            results["decode"]["requests"] = [future.result() for future in futures]
        finally:
            if profile_started:
                control("/stop_profile")
    results["decode"]["trace_dirs"] = sorted(trace_dirs() - before)
    event("decode_profile_stopped", trace_dirs=results["decode"]["trace_dirs"])
    for phase in ("prefill", "decode"):
        if len(results[phase]["trace_dirs"]) != 4:
            raise RuntimeError(f"{phase}: expected four rank traces")
    report = {
        "schema": "qwen36-dense-profile-client/v1",
        "status": "requests_complete",
        "service_manifest_sha256": digest(manifest_path),
        "benchmark_driver": str(args.benchmark_driver),
        "benchmark_driver_sha256": digest(args.benchmark_driver),
        "client_sha256": digest(Path(__file__)),
        "prompt_sha256": prompt_sha,
        "profile_steps": 30,
        "input_tokens": 32768,
        "prefix_tokens": 16384,
        "decode_concurrency": 16,
        "decode_output_tokens": 256,
        "prefill_concurrency": 1,
        "prefill_output_tokens": 1,
        "scope": "diagnostic only; acceptance benchmarks keep fixed 1024 outputs",
        "results": results,
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    event("client_complete", output=str(output))


if __name__ == "__main__":
    main()
