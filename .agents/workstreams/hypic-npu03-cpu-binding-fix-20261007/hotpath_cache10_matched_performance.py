#!/usr/bin/env python3
"""One exact-owned phase of the prospective r13 matched performance pair.

Inspect is offline. Live phases require the independent full quality audit and
run serially in the preregistered order; a partial phase is never resumed.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


ORDER = (
    ("no-cache", "screen"),
    ("hypic-only", "screen"),
    ("hypic-only", "repeat2"),
    ("no-cache", "repeat2"),
    ("no-cache", "repeat3"),
    ("hypic-only", "repeat3"),
)
EXPECTED_CONFIG = {
    "base_url": "http://127.0.0.1:8223",
    "concurrency": 16, "ignore_eos": True,
    "input_tokens": 32768, "model": "qwen36-hypic-e2e-2048",
    "output_tokens": 1024, "prefix_tokens": 16384,
    "requests": 40, "segment_boundary_transport": "vllm_xargs.hypic_segment_ends",
    "segment_ends": [16384, 32768],
    "warmup_mode": "concurrent_materialization_gate", "warmup_requests": 2,
}
QUALITY_AUDIT = "hotpath-quality-cache10r13-dual-audit.json"
SOURCE_ROOT = "/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008"
SOURCE_COMMIT = "c12060cd47e7575ead059983d7a8bb4704165c98"
REQUEST_ID_BENCHMARK = Path(__file__).with_name("hotpath_request_id_benchmark.py")
REQUEST_ID_BENCHMARK_SHA = "0d88b054a91e4985f131187d84899d76d57a1da1d97f842c2f51052534abc6ac"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def json_at(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pair_seam(quality: object) -> dict:
    left = quality.spec("no-cache")
    right = quality.spec("hypic-only")
    require(sorted(left[1]) == sorted(right[1]), "pair mounts differ")
    require(left[3].replace("/no-cache", "/ARM")
            == right[3].replace("/hypic-only", "/ARM"),
            "pair commands differ beyond arm path")
    a = dict(entry.split("=", 1) for entry in left[2])
    b = dict(entry.split("=", 1) for entry in right[2])
    changes = {key: [a.get(key), b.get(key)]
               for key in a.keys() | b.keys() if a.get(key) != b.get(key)}
    require(changes == {
        "VLLM_ASCEND_HYPIC_ENABLE": ["0", "1"],
        "VLLM_ASCEND_HYPIC_EVIDENCE_FILE": [
            f"/results/{quality.QROOT.name}/no-cache/hypic-evidence.jsonl",
            f"/results/{quality.QROOT.name}/hypic-only/hypic-evidence.jsonl",
        ],
    }, "pair environment differs beyond HYPIC enablement/evidence path")
    return {"normalized_command_equal": True, "mounts_equal": True,
            "enablement_only": True}


def entry_gate(quality: object) -> str:
    path = quality.ROOT / QUALITY_AUDIT
    require(path.is_file(), "cache10r13 independent full quality audit absent")
    audit = json_at(path)
    require(audit.get("evidence_valid") is True
            and audit.get("pair_seam", {}).get("normalized_commands_equal") is True
            and audit.get("source_commit") == SOURCE_COMMIT
            and audit.get("strict_c1_c2_hot_coverage", {}).get("expected_scored_requests") == 381,
            "cache10r13 paired quality evidence is not independently valid")
    for arm, field, suffix in (
        ("no-cache", "baseline", "baseline"),
        ("hypic-only", "candidate", "hypic"),
    ):
        root = quality.ROOT / f"quality-context-41984-hotpath-cache10r13-full-{suffix}"
        item = audit[field]
        require(item["scored_rows"] == 381
                and item["contract_sha256"] == quality.sha256(root / "contract.json")
                and item["arm_result_sha256"] == quality.sha256(root / "arm-result.json")
                and item["fingerprint"].get("source_commit") == SOURCE_COMMIT
                and item["fingerprint"].get("gpu_memory_utilization") == 0.85
                and item["fingerprint"].get("material_cache_max_mb") == 3584
                and item["fingerprint"].get("max_materialized_segments") == 10,
                f"{arm}: full quality audit or service identity drift")
    return quality.sha256(path)


def earlier_phases(quality: object, arm: str, phase: str) -> None:
    for previous_arm, previous_phase in ORDER[:ORDER.index((arm, phase))]:
        attempt = f"hotpath-cache10perf-{previous_arm}-{previous_phase}"
        root = quality.ROOT / quality.PERFORMANCE_ATTEMPTS[attempt]
        result = json_at(root / "arm-result.json")
        stop = json_at(root / previous_arm / "service-stop.json")
        guard = json_at(root / previous_arm / "lane-guard.json")
        require(result.get("error") is None and result.get("valid") is True
                and stop.get("container_removed") is True
                and stop.get("owned_npus_released") is True
                and stop.get("port_released") is True
                and stop.get("lane_available") is True
                and not guard.get("foreign") and not guard.get("probe_errors"),
                f"earlier performance phase {previous_arm}/{previous_phase} invalid")


def validate_report(path: Path, arm: str, *,
                    require_request_ids: bool = True) -> dict:
    report = json_at(path)
    require(report.get("config") == EXPECTED_CONFIG, "benchmark config drift")
    rows = report.get("results", [])
    summary = report.get("summary", {})
    require(len(rows) == 40 and sorted(row.get("index") for row in rows) == list(range(40)),
            "40 unique measured rows absent")
    require(all(row.get("ok") is True and row.get("error") is None
                and row.get("output_tokens") == 1024
                and row.get("requested_output_tokens") == 1024
                and row.get("finish_reason") == "length"
                and isinstance(row.get("ttft_ms"), (int, float))
                and isinstance(row.get("output_sha256"), str)
                and len(row["output_sha256"]) == 64 for row in rows),
            "one or more fixed-output rows invalid")
    require(summary.get("successful") == 40 and summary.get("failed") == 0
            and summary.get("output_tokens") == 40960
            and summary.get("fixed_output_verified") is True
            and len(report.get("warmup_results", [])) == 2,
            "benchmark summary/warmup invalid")
    if require_request_ids:
        ids = [row.get("request_id") for row in rows]
        warm_ids = [row.get("request_id") for row in report["warmup_results"]]
        require(all(isinstance(value, str) and value.startswith("cmpl-")
                    for value in ids + warm_ids)
                and len(set(ids + warm_ids)) == 42,
                "measured/warmup request IDs missing or duplicated")
    if arm == "hypic-only":
        require(summary.get("hot_path_verified") is True
                and not summary.get("hot_path_missing")
                and summary.get("run_evidence_event_counts", {}).get("worker_hot_path", 0) >= 4,
                "measured HYPIC hot path not proven")
    else:
        require(summary.get("run_evidence_event_counts", {}).get("worker_hot_path", 0) == 0,
                "baseline emitted worker-hot event")
    return {key: summary[key] for key in
            ("tpot_weighted_ms", "tpot_p95_ms", "ttft_p95_ms",
             "output_tokens_per_second", "benchmark_duration_s")}


def run_benchmark(quality: object, service: object, arm: str,
                  guard: object, container_id: str) -> dict:
    root = quality.QROOT
    output = root / "performance.json"
    command = [
        "python3", str(REQUEST_ID_BENCHMARK),
        "--base-url", quality.BASE_URL, "--model", quality.MODEL_NAME,
        "--input-tokens", "32768", "--prefix-tokens", "16384",
        "--output-tokens", "1024", "--requests", "40", "--concurrency", "16",
        "--warmup-requests", "2", "--timeout", "2400",
        "--json-output", str(output),
        "--evidence-file", str(root / arm / "hypic-evidence.jsonl"),
    ]
    if arm == "hypic-only":
        command.append("--require-hot-path")
    quality.write_json(root / "benchmark-command.json", {
        "argv": command, "benchmark_sha256": service.BENCHMARK_SHA,
        "request_id_adapter_sha256": quality.sha256(REQUEST_ID_BENCHMARK),
        "at_utc": datetime.now(timezone.utc).isoformat()})
    with (root / "benchmark.stdout.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 7200
            while process.poll() is None:
                guard.assert_clean()
                if time.monotonic() >= deadline:
                    raise RuntimeError("benchmark exceeded 7200 s phase limit")
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
            guard.assert_clean()
            require(process.returncode == 0,
                    f"benchmark exit {process.returncode}; inspect benchmark.stdout.log")
        except Exception:
            if process.poll() is None:
                quality.stop_owned_for_abort(arm, container_id)
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=30)
            raise
    return validate_report(output, arm)


def cleanup_before_health(quality: object, arm: str, container_id: str) -> None:
    """Release only the exact created container if no health proof exists."""
    name = quality.name_for(arm)
    item = quality.inspect(name)
    require(item is not None and item["Id"] == container_id,
            "pre-health container identity changed; leave it untouched")
    quality.owned(item, arm, container_id)
    if item["State"]["Status"] == "running":
        quality.run("docker", "stop", "--time", "30", container_id)
    quality.run("docker", "rm", container_id)
    require(quality.inspect(name) is None, "pre-health exact container not removed")
    quality.write_json(quality.QROOT / arm / "pre-health-release.json", {
        "container_id": container_id, "container_removed": True,
        "worker_release_proven": False,
        "at_utc": datetime.now(timezone.utc).isoformat(),
    })


def run_phase(quality: object, service: object, arm: str, phase: str) -> int:
    fingerprint = quality.preflight()
    require(fingerprint.get("gpu_memory_utilization") == 0.85
            and fingerprint.get("material_cache_max_mb") == 3584
            and fingerprint.get("max_materialized_segments") == 10,
            "cache10 service identity drift")
    seam = pair_seam(quality)
    quality_audit_sha256 = entry_gate(quality)
    earlier_phases(quality, arm, phase)
    require(not quality.QROOT.exists(), "phase root exists; never overwrite/resume")
    quality.assert_lane_available()
    quality.QROOT.mkdir(parents=True)
    with (quality.QROOT / "controller.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        signal.signal(signal.SIGTERM, quality.interrupt)
        signal.signal(signal.SIGINT, quality.interrupt)
        _, binds, env, command = quality.spec(arm)
        contract = {
            "schema": "hypic-cache10r13-matched-performance-contract/v1",
            "arm": arm, "phase": phase, "order_index": ORDER.index((arm, phase)),
            "fingerprint": fingerprint, "pair_seam": seam,
            "quality_audit_sha256": quality_audit_sha256,
            "benchmark_sha256": service.BENCHMARK_SHA,
            "request_id_adapter_sha256": quality.sha256(REQUEST_ID_BENCHMARK),
            "benchmark_config": EXPECTED_CONFIG,
            "serving_binds": binds, "serving_env": env,
            "serving_command": command,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        quality.write_json(quality.QROOT / "contract.json", contract)
        container_id = ""
        guard = None
        metrics = None
        problems: list[str] = []
        try:
            container_id = quality.create(arm)
            guard = quality.ForeignProcessGuard(
                arm, {}, owned_container_id=container_id)
            guard.start()
            quality.start(arm, container_id, fingerprint, guard=guard)
            start = json_at(quality.QROOT / arm / "service-start.json")
            guard.set_expected_workers(start["worker_pid_by_physical_npu"])
            guard.assert_clean()
            metrics = run_benchmark(quality, service, arm, guard, container_id)
            guard.assert_clean()
        except Exception as exc:
            problems.append(f"{type(exc).__name__}: {exc}")
        finally:
            if guard is not None:
                try:
                    guard.close()
                    record = json_at(quality.QROOT / arm / "lane-guard.json")
                    require(record["samples"] > 0 and not record["foreign"]
                            and not record["probe_errors"], "lane guard invalid")
                except Exception as exc:
                    problems.append(f"guard close: {type(exc).__name__}: {exc}")
            if container_id:
                try:
                    if (quality.QROOT / arm / "service-start.json").is_file():
                        quality.cleanup(arm, container_id)
                    else:
                        cleanup_before_health(quality, arm, container_id)
                        problems.append("service did not reach proven health")
                except Exception as exc:
                    problems.append(f"cleanup: {type(exc).__name__}: {exc}")
            result = {
                "schema": "hypic-cache10r13-matched-performance-arm/v1",
                "arm": arm, "phase": phase, "valid": not problems,
                "error": "; ".join(problems) if problems else None,
                "metrics": metrics,
                "container_id": container_id or None,
                "performance_sha256": quality.sha256(quality.QROOT / "performance.json")
                    if (quality.QROOT / "performance.json").is_file() else None,
                "hypic_evidence_sha256": quality.sha256(
                    quality.QROOT / arm / "hypic-evidence.jsonl")
                    if (quality.QROOT / arm / "hypic-evidence.jsonl").is_file() else None,
                "contract_sha256": quality.sha256(quality.QROOT / "contract.json"),
                "at_utc": datetime.now(timezone.utc).isoformat(),
            }
            quality.write_json(quality.QROOT / "arm-result.json", result)
            print(json.dumps(result, sort_keys=True), flush=True)
    if problems:
        raise RuntimeError("; ".join(problems))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("no-cache", "hypic-only"), required=True)
    parser.add_argument("--phase", choices=("screen", "repeat2", "repeat3"), required=True)
    parser.add_argument("--environmental-retry1", action="store_true",
                        help="one immutable retry only for hypic-only/repeat3 when the original failed before health/benchmark")
    parser.add_argument("--environmental-retry2", action="store_true",
                        help="final immutable retry after retry1 also fails before health/benchmark from foreign lane use")
    parser.add_argument("--environmental-retry3", action="store_true",
                        help="third immutable retry after retry2 also fails before health/benchmark from foreign lane use")
    parser.add_argument("--environmental-retry4", action="store_true",
                        help="one amended immutable retry after retry3 also fails before health/benchmark from foreign lane use")
    parser.add_argument("--environmental-retry5", action="store_true",
                        help="one new immutable retry after retry4 is invalidated by verified foreign physical-NPU use")
    parser.add_argument("--environmental-retry6", action="store_true",
                        help="one user-authorized immutable retry after retry5 is invalidated by verified foreign physical-NPU use")
    parser.add_argument("--environmental-retry7", action="store_true",
                        help="one corrected launch after retry6's executor timeout before any scored request")
    parser.add_argument("--environmental-retry8", action="store_true",
                        help="new immutable launch after retry7's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry9", action="store_true",
                        help="new immutable launch after retry8's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry10", action="store_true",
                        help="new immutable launch after retry9's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry11", action="store_true",
                        help="new immutable launch after retry10's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry12", action="store_true",
                        help="new immutable launch after retry11's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry13", action="store_true",
                        help="new immutable launch after retry12's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry14", action="store_true",
                        help="new immutable launch after retry13's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry15", action="store_true",
                        help="new immutable launch after retry14's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry16", action="store_true",
                        help="new immutable launch after retry15's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry17", action="store_true",
                        help="new immutable launch after retry16's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry18", action="store_true",
                        help="new immutable launch after retry17's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry19", action="store_true",
                        help="new immutable launch after retry18's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry20", action="store_true",
                        help="one new immutable opportunistic launch after retry19's pre-health foreign-process guard failure")
    parser.add_argument("--environmental-retry21", action="store_true",
                        help="one new immutable opportunistic launch after retry20's pre-health foreign-process guard failure")
    parser.add_argument("--run", action="store_true",
                        help="start an owned NPU0-3 service; otherwise inspect offline")
    args = parser.parse_args()
    attempt = f"hotpath-cache10perf-{args.arm}-{args.phase}"
    retry_flags = (args.environmental_retry1, args.environmental_retry2,
                   args.environmental_retry3, args.environmental_retry4,
                   args.environmental_retry5, args.environmental_retry6,
                   args.environmental_retry7, args.environmental_retry8,
                   args.environmental_retry9, args.environmental_retry10,
                   args.environmental_retry11, args.environmental_retry12,
                   args.environmental_retry13, args.environmental_retry14,
                   args.environmental_retry15, args.environmental_retry16,
                     args.environmental_retry17, args.environmental_retry18,
                     args.environmental_retry19, args.environmental_retry20,
                     args.environmental_retry21)
    require(sum(retry_flags) <= 1, "select exactly one environmental retry amendment")
    if any(retry_flags):
        require((args.arm, args.phase) == ("hypic-only", "repeat3"),
                "environmental retry is authorized only for hypic-only/repeat3")
        failed_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
            "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3")
        failed_result = json_at(failed_root / "arm-result.json")
        require(failed_result.get("valid") is False
                and failed_result.get("performance_sha256") is None
                and failed_result.get("metrics") is None
                and "lane guard" in str(failed_result.get("error", "")).lower()
                and not (failed_root / "hypic-only" / "service-start.json").exists()
                and not (failed_root / "hypic-only" / "benchmark-command.json").exists(),
                "original phase was not an environmental pre-measurement failure")
        if args.environmental_retry21:
            retry20_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry20")
            expected = {
                "contract.json": "58ab99d5742582a6e66b256844324742480dc882bff77edf91910711796c750f",
                "arm-result.json": "8a5c6cdbda2344615dae10f14e10bfcc36924c6b567004311aebcdb4a58f9046",
                "hypic-only/lane-guard.json": "4efe09fe5750e112356e6029fad68e712358f993f9474bd58035720492b72690",
                "hypic-only/pre-health-release.json": "c184f1d0af692b0b93b3deaef12cc4a49c3269f0dae66141d522ef11a6135576",
                "hypic-only/hypic-evidence.jsonl": "7c94c68175fa496a766ca9c5670787c0680a81bcc1798b29f0ed01ab9f51ba59",
            }
            require(all(hashlib.sha256((retry20_root / rel).read_bytes()).hexdigest() == digest
                        for rel, digest in expected.items()),
                    "retry20 environmental receipts changed")
            retry20_result = json_at(retry20_root / "arm-result.json")
            retry20_guard = json_at(retry20_root / "hypic-only" / "lane-guard.json")
            retry20_release = json_at(retry20_root / "hypic-only" / "pre-health-release.json")
            foreign = [p for sample in retry20_guard.get("foreign", [])
                       for p in sample.get("processes", [])]
            require(retry20_result.get("valid") is False
                    and retry20_result.get("metrics") is None
                    and retry20_result.get("performance_sha256") is None
                    and "lane guard" in str(retry20_result.get("error", "")).lower()
                    and retry20_guard.get("samples") == 36
                    and not retry20_guard.get("probe_errors")
                    and any(p.get("physical_npu") == 3 and p.get("pid") == 1890601
                            and p.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for p in foreign)
                    and retry20_release.get("container_removed") is True
                    and retry20_release.get("container_id") ==
                    "ea9357cfc3af46cc01a413bf9d0392e368b5381e9436899e3bcff2d7f7df74cc"
                    and not (retry20_root / "hypic-only" / "service-start.json").exists()
                    and not (retry20_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry20_root / "performance.json").exists(),
                    "retry20 was not an audited pre-health foreign-process failure")
            attempt += "-retry21"
        elif args.environmental_retry20:
            retry19_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry19")
            expected = {
                "contract.json": "fe59917a8ddf62cb538e7a5e9ef30d63d2eae8d14fd5f3798a495211d303b8f9",
                "arm-result.json": "25cce108c805d785d4ac01b092990bafced2a3409667cdf1fa2813d572d78506",
                "hypic-only/lane-guard.json": "f4d59b8e9553aa1b526af1e3d6b9e03d5e9a6b90cb9175c9f14f1958eeee91e5",
                "hypic-only/pre-health-release.json": "e938b1a0e99c76d281bf781909bc4392b853f3af424c3a33f925f54125ae59e7",
                "hypic-only/hypic-evidence.jsonl": "9df31bb84fa849c581e7815390e9e120b8fcb2ff2152050463b1c9db9ad15ffd",
            }
            require(all(hashlib.sha256((retry19_root / rel).read_bytes()).hexdigest() == digest
                        for rel, digest in expected.items()),
                    "retry19 environmental receipts changed")
            retry19_result = json_at(retry19_root / "arm-result.json")
            retry19_guard = json_at(retry19_root / "hypic-only" / "lane-guard.json")
            retry19_release = json_at(retry19_root / "hypic-only" / "pre-health-release.json")
            foreign = [p for sample in retry19_guard.get("foreign", [])
                       for p in sample.get("processes", [])]
            require(retry19_result.get("valid") is False
                    and retry19_result.get("metrics") is None
                    and retry19_result.get("performance_sha256") is None
                    and "lane guard" in str(retry19_result.get("error", "")).lower()
                    and retry19_guard.get("samples") == 46
                    and not retry19_guard.get("probe_errors")
                    and any(p.get("physical_npu") == 2 and p.get("pid") == 1731309
                            and p.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for p in foreign)
                    and retry19_release.get("container_removed") is True
                    and retry19_release.get("container_id") ==
                    "2e92362738a88715789c8bb291fbc0d162a8dde19576529a25668e6a62c23973"
                    and not (retry19_root / "hypic-only" / "service-start.json").exists()
                    and not (retry19_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry19_root / "performance.json").exists(),
                    "retry19 was not an audited pre-health foreign-process failure")
            attempt += "-retry20"
        elif args.environmental_retry19:
            retry18_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry18")
            expected = {
                "contract.json": "c03c8fdf79ffe02ed42ee2e80558479e372b2be0959128795e83c6dbe7dd322a",
                "arm-result.json": "c0bd15e0a0a6340e338bcbf05a5f4791139d747589ad63b1351cb67f198bd4bc",
                "hypic-only/lane-guard.json": "6ae72bebd66aba903dd9f8bfebf90561374bd2699363428268b97d4f498f553b",
                "hypic-only/pre-health-release.json": "413c9d8d3b2af629b5c6732c0eeba857299ea28794d9245d8ae2b2a365a5048c",
                "hypic-only/hypic-evidence.jsonl": "26eaf6cda31342ba6742045a15ca34039c0d3598dad61a2508cbcdb8400e568c",
            }
            require(all(hashlib.sha256((retry18_root / rel).read_bytes()).hexdigest() == digest
                        for rel, digest in expected.items()),
                    "retry18 environmental receipts changed")
            retry18_result = json_at(retry18_root / "arm-result.json")
            retry18_guard = json_at(retry18_root / "hypic-only" / "lane-guard.json")
            retry18_release = json_at(retry18_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry18_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry18_result.get("valid") is False
                    and retry18_result.get("metrics") is None
                    and retry18_result.get("performance_sha256") is None
                    and "lane guard" in str(retry18_result.get("error", "")).lower()
                    and retry18_guard.get("samples") == 80
                    and not retry18_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 1
                            and item.get("pid") == 1420898
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry18_release.get("container_removed") is True
                    and retry18_release.get("container_id") ==
                    "71ace370461d0090de57c1239f26015231e6252b0000ab3dc104ef27710b4f83"
                    and not (retry18_root / "hypic-only" / "service-start.json").exists()
                    and not (retry18_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry18_root / "performance.json").exists(),
                    "retry18 was not an audited pre-health foreign-process failure")
            attempt += "-retry19"
        elif args.environmental_retry18:
            retry17_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry17")
            require(hashlib.sha256((retry17_root / "contract.json").read_bytes()).hexdigest() ==
                    "78065f257df89c1eb032b22f4372d5a21793b97084657b8ea56324cca7cc7d22"
                    and hashlib.sha256((retry17_root / "arm-result.json").read_bytes()).hexdigest() ==
                    "04c59278c0720e531e88dc0936a4b4a04f991ed178bf9e06472045dd14b49e46"
                    and hashlib.sha256((retry17_root / "hypic-only" / "lane-guard.json").read_bytes()).hexdigest() ==
                    "f0276d28026a9b7da0218db46093521aa70be4077d2c77c9f0654f7011b168b6"
                    and hashlib.sha256((retry17_root / "hypic-only" / "pre-health-release.json").read_bytes()).hexdigest() ==
                    "bb665f2c1afa4db4f3eb5acd143c79fdf0cb44e16e646ccfdce6f6feeaf63898",
                    "retry17 environmental receipts changed")
            retry17_result = json_at(retry17_root / "arm-result.json")
            retry17_guard = json_at(retry17_root / "hypic-only" / "lane-guard.json")
            retry17_release = json_at(retry17_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry17_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry17_result.get("valid") is False
                    and retry17_result.get("metrics") is None
                    and retry17_result.get("performance_sha256") is None
                    and "lane guard" in str(retry17_result.get("error", "")).lower()
                    and retry17_guard.get("samples") == 26
                    and not retry17_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 0
                            and item.get("pid") == 1198578
                            and item.get("container_id") ==
                            "87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa"
                            for item in foreign)
                    and retry17_release.get("container_removed") is True
                    and not (retry17_root / "hypic-only" / "service-start.json").exists()
                    and not (retry17_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry17_root / "performance.json").exists(),
                    "retry17 was not an audited pre-health foreign-process failure")
            attempt += "-retry18"
        elif args.environmental_retry17:
            retry16_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry16")
            retry16_result = json_at(retry16_root / "arm-result.json")
            retry16_guard = json_at(retry16_root / "hypic-only" / "lane-guard.json")
            retry16_release = json_at(retry16_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry16_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry16_result.get("valid") is False
                    and retry16_result.get("metrics") is None
                    and retry16_result.get("performance_sha256") is None
                    and "lane guard" in str(retry16_result.get("error", "")).lower()
                    and retry16_guard.get("samples") == 22
                    and not retry16_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 2
                            and item.get("pid") == 1032336
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry16_release.get("container_removed") is True
                    and not (retry16_root / "hypic-only" / "service-start.json").exists()
                    and not (retry16_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry16_root / "performance.json").exists(),
                    "retry16 was not an audited pre-health foreign-process failure")
            attempt += "-retry17"
        elif args.environmental_retry16:
            retry15_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry15")
            retry15_result = json_at(retry15_root / "arm-result.json")
            retry15_guard = json_at(retry15_root / "hypic-only" / "lane-guard.json")
            retry15_release = json_at(retry15_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry15_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry15_result.get("valid") is False
                    and retry15_result.get("metrics") is None
                    and retry15_result.get("performance_sha256") is None
                    and "lane guard" in str(retry15_result.get("error", "")).lower()
                    and retry15_guard.get("samples") == 4
                    and not retry15_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 2
                            and item.get("pid") == 865188
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry15_release.get("container_removed") is True
                    and not (retry15_root / "hypic-only" / "service-start.json").exists()
                    and not (retry15_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry15_root / "performance.json").exists(),
                    "retry15 was not an audited pre-health foreign-process failure")
            attempt += "-retry16"
        elif args.environmental_retry15:
            retry14_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry14")
            retry14_result = json_at(retry14_root / "arm-result.json")
            retry14_guard = json_at(retry14_root / "hypic-only" / "lane-guard.json")
            retry14_release = json_at(retry14_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry14_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry14_result.get("valid") is False
                    and retry14_result.get("metrics") is None
                    and retry14_result.get("performance_sha256") is None
                    and "lane guard" in str(retry14_result.get("error", "")).lower()
                    and retry14_guard.get("samples") == 18
                    and not retry14_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 1
                            and item.get("pid") == 242978
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry14_release.get("container_removed") is True
                    and not (retry14_root / "hypic-only" / "service-start.json").exists()
                    and not (retry14_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry14_root / "performance.json").exists(),
                    "retry14 was not an audited pre-health foreign-process failure")
            attempt += "-retry15"
        elif args.environmental_retry14:
            retry13_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry13")
            retry13_result = json_at(retry13_root / "arm-result.json")
            retry13_guard = json_at(retry13_root / "hypic-only" / "lane-guard.json")
            retry13_release = json_at(retry13_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry13_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry13_result.get("valid") is False
                    and retry13_result.get("metrics") is None
                    and retry13_result.get("performance_sha256") is None
                    and "lane guard" in str(retry13_result.get("error", "")).lower()
                    and retry13_guard.get("samples") == 2
                    and not retry13_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 0
                            and item.get("pid") == 202622
                            and item.get("container_id") ==
                            "87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa"
                            for item in foreign)
                    and retry13_release.get("container_removed") is True
                    and not (retry13_root / "hypic-only" / "service-start.json").exists()
                    and not (retry13_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry13_root / "performance.json").exists(),
                    "retry13 was not an audited pre-health foreign-process failure")
            attempt += "-retry14"
        elif args.environmental_retry13:
            retry12_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry12")
            retry12_result = json_at(retry12_root / "arm-result.json")
            retry12_guard = json_at(retry12_root / "hypic-only" / "lane-guard.json")
            retry12_release = json_at(retry12_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry12_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry12_result.get("valid") is False
                    and retry12_result.get("metrics") is None
                    and retry12_result.get("performance_sha256") is None
                    and "lane guard" in str(retry12_result.get("error", "")).lower()
                    and retry12_guard.get("samples") == 14
                    and not retry12_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 1
                            and item.get("pid") == 91292
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry12_release.get("container_removed") is True
                    and not (retry12_root / "hypic-only" / "service-start.json").exists()
                    and not (retry12_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry12_root / "performance.json").exists(),
                    "retry12 was not an audited pre-health foreign-process failure")
            attempt += "-retry13"
        elif args.environmental_retry12:
            retry12_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry12")
            retry12_result = json_at(retry12_root / "arm-result.json")
            retry12_guard = json_at(retry12_root / "hypic-only" / "lane-guard.json")
            retry12_release = json_at(retry12_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry12_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry12_result.get("valid") is False
                    and retry12_result.get("metrics") is None
                    and retry12_result.get("performance_sha256") is None
                    and "lane guard" in str(retry12_result.get("error", "")).lower()
                    and retry12_guard.get("samples") == 14
                    and not retry12_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 1
                            and item.get("pid") == 91292
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry12_release.get("container_removed") is True
                    and not (retry12_root / "hypic-only" / "service-start.json").exists()
                    and not (retry12_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry12_root / "performance.json").exists(),
                    "retry12 was not an audited pre-health foreign-process failure")
            attempt += "-retry13"
        elif args.environmental_retry12:
            retry11_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry11")
            retry11_result = json_at(retry11_root / "arm-result.json")
            retry11_guard = json_at(retry11_root / "hypic-only" / "lane-guard.json")
            retry11_release = json_at(retry11_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry11_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry11_result.get("valid") is False
                    and retry11_result.get("metrics") is None
                    and retry11_result.get("performance_sha256") is None
                    and "lane guard" in str(retry11_result.get("error", "")).lower()
                    and retry11_guard.get("samples") == 4
                    and not retry11_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 2
                            and item.get("pid") == 4177138
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry11_release.get("container_removed") is True
                    and not (retry11_root / "hypic-only" / "service-start.json").exists()
                    and not (retry11_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry11_root / "performance.json").exists(),
                    "retry11 was not an audited pre-health foreign-process failure")
            attempt += "-retry12"
        elif args.environmental_retry11:
            retry10_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry10")
            retry10_result = json_at(retry10_root / "arm-result.json")
            retry10_guard = json_at(retry10_root / "hypic-only" / "lane-guard.json")
            retry10_release = json_at(retry10_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry10_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry10_result.get("valid") is False
                    and retry10_result.get("metrics") is None
                    and retry10_result.get("performance_sha256") is None
                    and "lane guard" in str(retry10_result.get("error", "")).lower()
                    and retry10_guard.get("samples") == 14
                    and not retry10_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 1
                            and item.get("pid") == 4117079
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry10_release.get("container_removed") is True
                    and not (retry10_root / "hypic-only" / "service-start.json").exists()
                    and not (retry10_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry10_root / "performance.json").exists(),
                    "retry10 was not an audited pre-health foreign-process failure")
            attempt += "-retry11"
        elif args.environmental_retry10:
            retry9_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry9")
            retry9_result = json_at(retry9_root / "arm-result.json")
            retry9_guard = json_at(retry9_root / "hypic-only" / "lane-guard.json")
            retry9_release = json_at(retry9_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry9_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry9_result.get("valid") is False
                    and retry9_result.get("metrics") is None
                    and retry9_result.get("performance_sha256") is None
                    and "lane guard" in str(retry9_result.get("error", "")).lower()
                    and retry9_guard.get("samples") == 12
                    and not retry9_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 2
                            and item.get("pid") == 4049211
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry9_release.get("container_removed") is True
                    and not (retry9_root / "hypic-only" / "service-start.json").exists()
                    and not (retry9_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry9_root / "performance.json").exists(),
                    "retry9 was not an audited pre-health foreign-process failure")
            attempt += "-retry10"
        elif args.environmental_retry9:
            retry8_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry8")
            retry8_result = json_at(retry8_root / "arm-result.json")
            retry8_guard = json_at(retry8_root / "hypic-only" / "lane-guard.json")
            retry8_release = json_at(retry8_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry8_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry8_result.get("valid") is False
                    and retry8_result.get("metrics") is None
                    and retry8_result.get("performance_sha256") is None
                    and "lane guard" in str(retry8_result.get("error", "")).lower()
                    and retry8_guard.get("samples") == 4
                    and not retry8_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 0
                            and item.get("pid") == 3967272
                            and item.get("container_id") is None
                            for item in foreign)
                    and retry8_release.get("container_removed") is True
                    and not (retry8_root / "hypic-only" / "service-start.json").exists()
                    and not (retry8_root / "hypic-only" / "benchmark-command.json").exists()
                    and not (retry8_root / "performance.json").exists(),
                    "retry8 was not an audited pre-health foreign-process failure")
            attempt += "-retry9"
        elif args.environmental_retry8:
            retry7_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry7")
            retry7_result = json_at(retry7_root / "arm-result.json")
            retry7_guard = json_at(retry7_root / "hypic-only" / "lane-guard.json")
            retry7_release = json_at(retry7_root / "hypic-only" / "pre-health-release.json")
            foreign = [
                process
                for sample in retry7_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry7_result.get("valid") is False
                    and retry7_result.get("metrics") is None
                    and retry7_result.get("performance_sha256") is None
                    and retry7_guard.get("samples") == 18
                    and not retry7_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 1
                            and item.get("pid") == 3843558
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry7_release.get("container_removed") is True
                    and not (retry7_root / "performance.json").exists()
                    and not (retry7_root / "hypic-only" / "benchmark-command.json").exists(),
                    "retry7 was not a pre-health foreign-process isolation failure")
            attempt += "-retry8"
        elif args.environmental_retry7:
            retry6_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry6")
            retry6_contract = json_at(retry6_root / "contract.json")
            retry6_evidence = retry6_root / "hypic-only" / "hypic-evidence.jsonl"
            startup_events = []
            if retry6_evidence.is_file():
                startup_events = [
                    json.loads(line)
                    for line in retry6_evidence.read_text().splitlines()
                    if line.strip()
                ]
            allowed_events = {
                "plugin_build_active", "hypic_capability_contract",
                "hypic_upstream_parity_contract", "material_cache_configured",
            }
            require(retry6_contract.get("phase") == "repeat3"
                    and retry6_contract.get("arm") == "hypic-only"
                    and startup_events
                    and all(row.get("event") in allowed_events for row in startup_events)
                    and not (retry6_root / "performance.json").exists()
                    and not (retry6_root / "arm-result.json").exists()
                    and not (retry6_root / "hypic-only" / "benchmark-command.json").exists(),
                    "retry6 was not a pre-measurement executor timeout")
            attempt += "-retry7"
        elif args.environmental_retry6:
            retry5_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry5")
            retry5_contract = json_at(retry5_root / "contract.json")
            retry5_guard = json_at(retry5_root / "hypic-only" / "lane-guard.json")
            retry5_evidence = retry5_root / "hypic-only" / "hypic-evidence.jsonl"
            retry5_foreign = [
                process
                for sample in retry5_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            require(retry5_contract.get("phase") == "repeat3"
                    and retry5_contract.get("arm") == "hypic-only"
                    and retry5_guard.get("samples") == 2
                    and not retry5_guard.get("probe_errors")
                    and any(item.get("physical_npu") == 0
                            and item.get("pid") == 3539167
                            and item.get("container_id") ==
                            "87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa"
                            for item in retry5_foreign)
                    and retry5_evidence.is_file()
                    and retry5_evidence.stat().st_size == 0
                    and not (retry5_root / "performance.json").exists()
                    and not (retry5_root / "arm-result.json").exists(),
                    "retry5 was not an audited pre-measurement foreign-process failure")
            attempt += "-retry6"
        elif args.environmental_retry5:
            retry4_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry4")
            retry4_result = json_at(retry4_root / "arm-result.json")
            retry4_guard = json_at(retry4_root / "hypic-only" / "lane-guard.json")
            retry4_release = json_at(retry4_root / "hypic-only" / "service-stop.json")
            retry4_report = json_at(retry4_root / "performance.json")
            foreign = [
                process
                for sample in retry4_guard.get("foreign", [])
                for process in sample.get("processes", [])
            ]
            rows = retry4_report.get("results", [])
            require(retry4_result.get("valid") is False
                    and retry4_result.get("metrics") is None
                    and retry4_result.get("performance_sha256")
                    and "lane guard" in str(retry4_result.get("error", "")).lower()
                    and len(rows) == 40
                    and sum(row.get("ok") is True for row in rows) == 16
                    and sum(row.get("ok") is not True for row in rows) == 24
                    and any(item.get("physical_npu") == 1
                            and item.get("pid") == 3079008
                            and item.get("container_id") ==
                            "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"
                            for item in foreign)
                    and retry4_release.get("container_removed") is True
                    and retry4_release.get("owned_npus_released") is True
                    and retry4_release.get("port_released") is True
                    and retry4_release.get("lane_available") is True,
                    "retry4 was not independently invalidated by foreign NPU use with exact cleanup")
            attempt += "-retry5"
        elif args.environmental_retry4:
            retry3_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry3")
            retry3_result = json_at(retry3_root / "arm-result.json")
            retry3_guard = json_at(retry3_root / "hypic-only" / "lane-guard.json")
            retry3_release = json_at(retry3_root / "hypic-only" / "pre-health-release.json")
            require(retry3_result.get("valid") is False
                    and retry3_result.get("performance_sha256") is None
                    and retry3_result.get("metrics") is None
                    and "lane guard" in str(retry3_result.get("error", "")).lower()
                    and not (retry3_root / "hypic-only" / "service-start.json").exists()
                    and not (retry3_root / "hypic-only" / "benchmark-command.json").exists()
                    and retry3_release.get("container_removed") is True
                    and retry3_guard.get("foreign")
                    and not retry3_guard.get("probe_errors"),
                    "retry3 was not an isolated pre-health environmental failure")
            attempt += "-retry4"
        elif args.environmental_retry3:
            retry2_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry2")
            retry2_result = json_at(retry2_root / "arm-result.json")
            retry2_guard = json_at(retry2_root / "hypic-only" / "lane-guard.json")
            retry2_release = json_at(retry2_root / "hypic-only" / "pre-health-release.json")
            require(retry2_result.get("valid") is False
                    and retry2_result.get("performance_sha256") is None
                    and retry2_result.get("metrics") is None
                    and "lane guard" in str(retry2_result.get("error", "")).lower()
                    and not (retry2_root / "hypic-only" / "service-start.json").exists()
                    and not (retry2_root / "hypic-only" / "benchmark-command.json").exists()
                    and retry2_release.get("container_removed") is True
                    and retry2_guard.get("foreign")
                    and not retry2_guard.get("probe_errors"),
                    "retry2 was not an isolated pre-health environmental failure")
            attempt += "-retry3"
        elif args.environmental_retry2:
            retry1_root = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007") / (
                "performance-context-41984-hotpath-cache10perf-hypic-only-repeat3-retry1")
            retry1_result = json_at(retry1_root / "arm-result.json")
            retry1_guard = json_at(retry1_root / "hypic-only" / "lane-guard.json")
            retry1_release = json_at(retry1_root / "hypic-only" / "pre-health-release.json")
            require(retry1_result.get("valid") is False
                    and retry1_result.get("performance_sha256") is None
                    and retry1_result.get("metrics") is None
                    and "lane guard" in str(retry1_result.get("error", "")).lower()
                    and not (retry1_root / "hypic-only" / "service-start.json").exists()
                    and not (retry1_root / "hypic-only" / "benchmark-command.json").exists()
                    and retry1_release.get("container_removed") is True
                    and retry1_guard.get("foreign")
                    and not retry1_guard.get("probe_errors"),
                    "retry1 was not an isolated pre-health environmental failure")
            attempt += "-retry2"
        else:
            attempt += "-retry1"
    os.environ["HYPIC_QUALITY_ATTEMPT"] = attempt
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = SOURCE_ROOT
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = SOURCE_COMMIT
    import binding_off_quality as quality
    import binding_off_service as service
    require(quality.ATTEMPT == attempt, "quality helper attempt drift")
    require(service.sha256(service.BENCHMARK) == service.BENCHMARK_SHA,
            "frozen benchmark source drift")
    require(quality.sha256(REQUEST_ID_BENCHMARK) == REQUEST_ID_BENCHMARK_SHA,
            "frozen request-ID benchmark adapter drift")
    if not args.run:
        fingerprint = quality.preflight()
        print(json.dumps({"arm": args.arm, "phase": args.phase,
                          "attempt_root": str(quality.QROOT),
                          "pair_seam": pair_seam(quality),
                          "fingerprint": fingerprint}, sort_keys=True))
        return 0
    return run_phase(quality, service, args.arm, args.phase)


if __name__ == "__main__":
    raise SystemExit(main())
