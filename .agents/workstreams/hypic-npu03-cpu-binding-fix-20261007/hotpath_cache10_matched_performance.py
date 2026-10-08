#!/usr/bin/env python3
"""One exact-owned phase of the prospective r13 matched performance pair.

Inspect is offline. Live phases require the independent full quality audit and
run serially in the preregistered order; a partial phase is never resumed.
"""

from __future__ import annotations

import argparse
import fcntl
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


def validate_report(path: Path, arm: str) -> dict:
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
        "python3", str(service.BENCHMARK),
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
            "schema": "hypic-cache10-matched-performance-contract/v1",
            "arm": arm, "phase": phase, "order_index": ORDER.index((arm, phase)),
            "fingerprint": fingerprint, "pair_seam": seam,
            "quality_audit_sha256": quality_audit_sha256,
            "benchmark_sha256": service.BENCHMARK_SHA,
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
                "schema": "hypic-cache10-matched-performance-arm/v1",
                "arm": arm, "phase": phase, "valid": not problems,
                "error": "; ".join(problems) if problems else None,
                "metrics": metrics,
                "container_id": container_id or None,
                "performance_sha256": quality.sha256(quality.QROOT / "performance.json")
                    if (quality.QROOT / "performance.json").is_file() else None,
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
    parser.add_argument("--run", action="store_true",
                        help="start an owned NPU0-3 service; otherwise inspect offline")
    args = parser.parse_args()
    attempt = f"hotpath-cache10perf-{args.arm}-{args.phase}"
    os.environ["HYPIC_QUALITY_ATTEMPT"] = attempt
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = SOURCE_ROOT
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = SOURCE_COMMIT
    import binding_off_quality as quality
    import binding_off_service as service
    require(quality.ATTEMPT == attempt, "quality helper attempt drift")
    require(service.sha256(service.BENCHMARK) == service.BENCHMARK_SHA,
            "frozen benchmark source drift")
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
