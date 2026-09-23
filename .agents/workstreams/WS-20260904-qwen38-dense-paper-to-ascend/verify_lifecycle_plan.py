#!/usr/bin/env python3
"""Validate and render the non-executing two-model G1-G4 lifecycle plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.parse
from pathlib import Path
from typing import Any

MODELS = ("qwen38-27b", "qwen35-4b")
GROUPS = ("G1", "G2", "G3", "G4")
CAPTURE_KEYS = {
    "VLLM_ASCEND_GDN_RRQR_CAPTURE_ENABLE",
    "VLLM_ASCEND_GDN_RRQR_CAPTURE_DIR",
    "VLLM_ASCEND_GDN_RRQR_MAX_TOKENS",
    "VLLM_ASCEND_GDN_RRQR_MAX_CAPTURES_PER_LAYER",
}
FORBIDDEN = re.compile(
    r"qwen38_gdn_fused_candidate|davinci[4-7](?:\D|$)|NPU4-7|CPU0-95",
    re.IGNORECASE,
)
ALLOWED_EVALUATION_EXECUTABLES = {"python", "python3", "ais_bench"}
PROTECTED_PORTS = {8210}


def resolved_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and "REQUIRED" not in value


def resolved_argv(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(resolved_string(item) for item in value)


def evaluation_argv_allowed(value: Any) -> bool:
    if not resolved_argv(value):
        return False
    executable = os.path.basename(value[0])
    return executable in ALLOWED_EVALUATION_EXECUTABLES or executable.startswith("python3.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        return 2
    if plan.get("schema") != "paper-to-ascend-lifecycle-plan/v1":
        errors.append("lifecycle plan schema mismatch")
    for field in (
        "preflight_report_sha256",
        "runtime_config_sha256",
        "frozen_inputs_sha256",
        "treatment_matrix_sha256",
    ):
        if re.fullmatch(r"[0-9a-f]{64}", str(plan.get(field))) is None:
            errors.append(f"{field} must be lowercase SHA256")
    if plan.get("host_npus") != [0, 1, 2, 3]:
        errors.append("host_npus must be exactly [0, 1, 2, 3]")
    if plan.get("cpu_set") != "112-191":
        errors.append("cpu_set must be exactly 112-191")
    for field in ("performance_repetitions", "quality_repetitions"):
        if plan.get(field) != 3:
            errors.append(f"{field} must equal 3")
    for field in ("restart_between_phases", "health_200_before_each_phase"):
        if plan.get(field) is not True:
            errors.append(f"{field} must be true")
    capture = plan.get("capture_environment")
    if not isinstance(capture, dict) or set(capture) != CAPTURE_KEYS:
        errors.append("capture_environment keys must match the complete capture variable set")
    elif any(capture[key] not in (None, "", False) for key in CAPTURE_KEYS):
        errors.append("all capture_environment values must be disabled")

    cells = plan.get("cells")
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    service_names: set[str] = set()
    if not isinstance(cells, list):
        errors.append("cells must be a list")
        cells = []
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            errors.append(f"cell {index} must be an object")
            continue
        identity = (str(cell.get("model_id")), str(cell.get("group")))
        if identity in indexed:
            errors.append(f"duplicate cell: {identity}")
        indexed[identity] = cell
        for field in ("service_name", "health_url"):
            if not resolved_string(cell.get(field)):
                errors.append(f"{identity}: {field} unresolved")
        service_name = cell.get("service_name")
        if resolved_string(service_name):
            if not service_name.startswith("paper-"):
                errors.append(f"{identity}: service_name must start with paper-")
            if service_name in service_names:
                errors.append(f"{identity}: duplicate service_name: {service_name}")
            service_names.add(service_name)
        health_url = cell.get("health_url")
        if resolved_string(health_url):
            parsed = urllib.parse.urlparse(health_url)
            if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
                errors.append(f"{identity}: health_url must use loopback HTTP")
            try:
                port = parsed.port
            except ValueError:
                port = None
                errors.append(f"{identity}: health_url port is invalid")
            if port is None:
                errors.append(f"{identity}: health_url must include an explicit port")
            elif port in PROTECTED_PORTS:
                errors.append(f"{identity}: health_url uses protected port {port}")
        digest = cell.get("service_config_sha256")
        if not resolved_string(digest) or re.fullmatch(r"[0-9a-f]{64}", str(digest)) is None:
            errors.append(f"{identity}: service_config_sha256 must be lowercase SHA256")
        for field in (
            "start_argv", "stop_argv", "warmup_argv", "performance_argv", "quality_argv"
        ):
            if not resolved_argv(cell.get(field)):
                errors.append(f"{identity}: {field} unresolved")
        for field in ("warmup_argv", "performance_argv", "quality_argv"):
            if resolved_argv(cell.get(field)) and not evaluation_argv_allowed(cell[field]):
                errors.append(
                    f"{identity}: {field} executable must be Python or ais_bench"
                )
        if resolved_string(cell.get("service_name")):
            expected_start = ["docker", "start", cell["service_name"]]
            expected_stop = ["docker", "stop", cell["service_name"]]
            if cell.get("start_argv") != expected_start:
                errors.append(f"{identity}: start_argv must equal {expected_start}")
            if cell.get("stop_argv") != expected_stop:
                errors.append(f"{identity}: stop_argv must equal {expected_stop}")
        serialized = json.dumps(cell, ensure_ascii=False)
        if FORBIDDEN.search(serialized):
            errors.append(f"{identity}: contains protected-lane token")
        if any(key in serialized for key in CAPTURE_KEYS):
            errors.append(f"{identity}: embeds capture environment in a run cell")

    expected = {(model, group) for model in MODELS for group in GROUPS}
    if set(indexed) != expected:
        errors.append(
            f"cells must be exactly two models x G1-G4; missing={sorted(expected-set(indexed))}, extra={sorted(set(indexed)-expected)}"
        )

    steps: list[dict[str, Any]] = []
    if not errors:
        for model in MODELS:
            for group in GROUPS:
                cell = indexed[(model, group)]
                phases = [
                    "start-performance-service",
                    "wait-health-200",
                    "warmup",
                    "performance-run-1",
                    "performance-run-2",
                    "performance-run-3",
                    "stop-performance-service",
                    "restart-identical-service-for-quality",
                    "wait-health-200",
                    "quality-run-1",
                    "quality-run-2",
                    "quality-run-3",
                    "stop-quality-service",
                ]
                steps.append(
                    {
                        "model_id": model,
                        "group": group,
                        "service_name": cell["service_name"],
                        "service_config_sha256": cell["service_config_sha256"],
                        "phases": phases,
                    }
                )
    report = {
        "schema": "paper-to-ascend-lifecycle-plan-verification/v1",
        "valid": not errors,
        "executes_commands": False,
        "plan_sha256": hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        "cell_count": len(indexed),
        "ordered_cells": steps,
        "errors": errors,
    }
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
