#!/usr/bin/env python3
"""Independent closure audit for the physical-NPU HYPIC workstream."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEADLINE = datetime.fromisoformat("2026-10-07T11:39:37+00:00")
ANSWER = "ZEBRA-41729"
ARMS = ("no-cache", "hypic-only")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def obj(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    def read(name: str, rel: str) -> dict[str, Any] | None:
        path = root / rel
        try:
            return obj(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            check(name, False, str(exc))
            return None

    contract = read("baseline_contract_present", "baseline-contract.json")
    baseline_hash = None
    if contract is not None:
        fp = contract.get("fingerprint")
        if isinstance(fp, dict):
            canonical = json.dumps(fp, sort_keys=True, separators=(",", ":"))
            baseline_hash = hashlib.sha256(canonical.encode()).hexdigest()
            check(
                "baseline_fingerprint_integrity",
                contract.get("fingerprint_sha256") == baseline_hash,
                baseline_hash,
            )
            check(
                "baseline_physical_topology",
                fp.get("physical_devices")
                == [f"/dev/davinci{i}" for i in range(4)],
            )
            check(
                "quality_ruler_2048",
                fp.get("quality_protocol", {}).get("max_out_len") == 2048
                and fp.get("quality_protocol", {}).get("ignore_eos") is False
                and fp.get("quality_protocol", {}).get("repetitions") == 3,
            )
            check(
                "performance_ruler",
                fp.get("performance_protocol")
                == {
                    "input_tokens": 32768,
                    "prefix_tokens": 16384,
                    "output_tokens": 1024,
                    "requests": 40,
                    "concurrency": 16,
                    "warmup_requests": 2,
                    "repetitions": 3,
                },
            )
        else:
            check("baseline_fingerprint_integrity", False, "missing fingerprint")

    registry = read("baseline_registry_present", "baseline-registry.json")
    if registry is not None:
        check(
            "baseline_registry_identity",
            registry.get("schema") == "hypic-baseline-registry/v1"
            and registry.get("fingerprint_sha256") == baseline_hash,
        )
        expected_performance = {
            f"no-cache/performance.run{index}.json" for index in (1, 2, 3)
        }
        expected_quality = {
            f"quality/no-cache/{dataset}.run{index}.{suffix}"
            for dataset in ("longbenchv2", "gsm8k")
            for index in (1, 2, 3)
            for suffix in ("summary.json", "jsonl")
        }
        for phase, expected in (
            ("performance", expected_performance),
            ("quality", expected_quality),
        ):
            entries = registry.get(phase)
            if not isinstance(entries, list):
                check(f"baseline_registry_{phase}", False, "missing phase")
                continue
            paths = [row.get("path") for row in entries if isinstance(row, dict)]
            check(
                f"baseline_registry_{phase}_members",
                len(entries) == len(expected)
                and len(paths) == len(expected)
                and all(isinstance(rel, str) for rel in paths)
                and set(paths) == expected,
            )
            for row in entries:
                if not isinstance(row, dict):
                    continue
                rel = row.get("path")
                if not isinstance(rel, str) or rel not in expected:
                    continue
                path = (root / rel).resolve()
                check(
                    f"baseline_registry_hash:{rel}",
                    path.is_relative_to(root) and path.is_file()
                    and row.get("sha256") == sha256(path),
                )

    canary = read("canary_gate_present", "canary-gate.json")
    canary_runs = {
        arm: read(f"{arm}_canary_present", f"{arm}/semantic-canary.json")
        for arm in ARMS
    }
    if canary is not None and all(canary_runs.values()):
        base, treatment = (canary_runs[arm] for arm in ARMS)
        check("canary_gate_pass", canary.get("passed") is True and canary.get("failures") == [])
        check(
            "canary_exact_response",
            base.get("prompt_token_sha256") == treatment.get("prompt_token_sha256")
            and base.get("response_text_sha256") == treatment.get("response_text_sha256")
            and ANSWER in str(base.get("response_text", ""))
            and ANSWER in str(treatment.get("response_text", "")),
        )
        for arm in ARMS:
            path = root / arm / "semantic-canary.json"
            check(
                f"{arm}_canary_hash",
                canary.get("artifact_sha256", {}).get(arm) == sha256(path),
            )

    base_events = root / "no-cache/canary.hypic-evidence.jsonl"
    treatment_events = root / "hypic-only/canary.hypic-evidence.jsonl"
    check(
        "disabled_control_no_treatment_marker",
        base_events.is_file() and base_events.stat().st_size == 0,
    )
    try:
        events = [
            json.loads(line)
            for line in treatment_events.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        active_pids = {
            row.get("pid") for row in events
            if row.get("event") == "plugin_build_active"
            and isinstance(row.get("pid"), int)
        }
        check("enabled_process_activation", len(active_pids) >= 5, str(sorted(active_pids)))
        check(
            "canary_segment_reuse_event",
            any(row.get("event") == "independent_segment_reuse_observed" for row in events),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        check("enabled_process_activation", False, str(exc))

    perf = read("performance_gate_present", "performance-gate.json")
    if perf is not None:
        check("performance_gate_pass", perf.get("passed") is True and perf.get("failures") == [])
        for arm in ARMS:
            hashes = perf.get("run_sha256", {}).get(arm, [])
            for index in (1, 2, 3):
                path = root / arm / f"performance.run{index}.json"
                try:
                    payload = obj(path)
                    summary = payload["summary"]
                    check(
                        f"{arm}_performance_run{index}",
                        len(hashes) == 3
                        and hashes[index - 1] == sha256(path)
                        and summary.get("successful") == 40
                        and summary.get("failed") == 0
                        and summary.get("fixed_output_verified") is True,
                    )
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
                    check(f"{arm}_performance_run{index}", False, str(exc))

    independent = read(
        "independent_18_unit_audit_present",
        "hypic-e2e-2048-evidence-audit.json",
    )
    if independent is not None:
        check(
            "independent_18_unit_audit_pass",
            independent.get("ok") is True
            and independent.get("accepted_units") == 18
            and independent.get("quality_max_output_tokens") == 2048
            and independent.get("errors") == [],
        )

    iteration = read("optimization_iteration_present", "optimization-iteration.json")
    if iteration is not None:
        iteration_raw = iteration.get("raw_sha256")
        if not isinstance(iteration_raw, dict):
            iteration_raw = {}
        check(
            "optimization_iteration_measured",
            iteration.get("baseline_fingerprint_sha256") == baseline_hash
            and iteration.get("status") in ("accepted", "rejected", "partial-component")
            and iteration.get("measured") is True,
        )
        check(
            "optimization_iteration_raw_manifest",
            len(iteration_raw) >= 2,
        )
        for rel, expected in iteration_raw.items():
            path = (root / rel).resolve()
            check(
                f"iteration_raw_hash:{rel}",
                path.is_relative_to(root) and path.is_file()
                and sha256(path) == expected,
            )

    rollback = read("rollback_evidence_present", "rollback-evidence.json")
    if rollback is not None:
        rollback_raw = rollback.get("raw_sha256")
        if not isinstance(rollback_raw, dict):
            rollback_raw = {}
        check(
            "rollback_disabled_control",
            rollback.get("disabled_request_passed") is True
            and rollback.get("treatment_marker_absent") is True,
        )
        check(
            "rollback_resource_release",
            rollback.get("owned_npus_released") is True
            and rollback.get("port_released") is True
            and rollback.get("owned_containers_removed") is True,
        )
        required_rollback_files = {
            "rollback/disabled-canary.json",
            "rollback/disabled-evidence.jsonl",
            "rollback/npu-smi-after.txt",
            "rollback/port-after.txt",
        }
        check(
            "rollback_raw_manifest",
            required_rollback_files.issubset(rollback_raw),
        )
        for rel, expected in rollback_raw.items():
            path = (root / rel).resolve()
            check(
                f"rollback_raw_hash:{rel}",
                path.is_relative_to(root) and path.is_file()
                and sha256(path) == expected,
            )
        try:
            npu_snapshot = (root / "rollback/npu-smi-after.txt").read_text()
            check(
                "rollback_npu_snapshot",
                all(
                    f"No running processes found in NPU {index}" in npu_snapshot
                    for index in range(4)
                ),
            )
        except OSError as exc:
            check("rollback_npu_snapshot", False, str(exc))
        try:
            port_snapshot = (root / "rollback/port-after.txt").read_text()
            check(
                "rollback_port_snapshot",
                "8223" not in port_snapshot,
            )
        except OSError as exc:
            check("rollback_port_snapshot", False, str(exc))
        try:
            finished = datetime.fromisoformat(rollback["completed_at"])
            check("before_24h_deadline", finished <= DEADLINE, finished.isoformat())
        except (KeyError, TypeError, ValueError) as exc:
            check("before_24h_deadline", False, str(exc))

    payload = {
        "schema": "hypic-e2e-closure-audit/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "deadline": DEADLINE.isoformat(),
        "ok": bool(checks) and all(item["passed"] for item in checks),
        "checks": checks,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": payload["ok"], "failed_checks": payload["failed_checks"]}))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
