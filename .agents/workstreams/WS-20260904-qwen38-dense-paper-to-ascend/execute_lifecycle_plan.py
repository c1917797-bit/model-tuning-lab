#!/usr/bin/env python3
"""Fail-closed one-shot lifecycle executor; dry-run is the default."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

AUTHORIZATION = "I_OWN_NPU0_3_AND_AUTHORIZE_BASELINE_REPLACEMENT"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temp, path)


def journal_value(
    *,
    plan_hash: str,
    preflight_hash: str,
    completed: list[str],
    current_cell: str | None,
    status: str,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "schema": "paper-to-ascend-lifecycle-journal/v1",
        "plan_sha256": plan_hash,
        "preflight_report_sha256": preflight_hash,
        "completed_cells": completed,
        "current_cell": current_cell,
        "status": status,
        "error": error,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def validate_resume_journal(
    journal: dict[str, Any],
    *,
    plan_hash: str,
    preflight_hash: str,
    labels: list[str],
) -> list[str]:
    if journal.get("schema") != "paper-to-ascend-lifecycle-journal/v1":
        raise ValueError("resume journal schema is invalid")
    if journal.get("plan_sha256") != plan_hash:
        raise ValueError("resume journal is bound to a different lifecycle plan")
    if journal.get("preflight_report_sha256") != preflight_hash:
        raise ValueError("resume journal is bound to a different preflight report")
    if journal.get("status") not in {"running", "failed"}:
        raise ValueError("resume journal status must be running or failed")
    completed = journal.get("completed_cells")
    if not isinstance(completed, list) or any(
        not isinstance(label, str) for label in completed
    ):
        raise ValueError("resume journal completed_cells is invalid")
    if completed != labels[: len(completed)]:
        raise ValueError("resume journal completed_cells is not an exact plan prefix")
    if len(completed) >= len(labels):
        raise ValueError("resume journal has no incomplete cell")
    return completed


def substitute(argv: list[str], run_index: int) -> list[str]:
    return [item.replace("{run_index}", str(run_index)) for item in argv]


def run(argv: list[str], *, dry_run: bool) -> None:
    print(json.dumps({"argv": argv, "dry_run": dry_run}, ensure_ascii=False))
    if not dry_run:
        subprocess.run(argv, check=True)


def wait_health(url: str, timeout_seconds: int, *, dry_run: bool) -> None:
    print(json.dumps({"health_url": url, "timeout_seconds": timeout_seconds, "dry_run": dry_run}))
    if dry_run:
        return
    deadline = time.monotonic() + timeout_seconds
    last_error = "no response"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return
                last_error = f"HTTP {response.status}"
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = str(exc)
        time.sleep(2)
    raise RuntimeError(f"health did not reach HTTP 200: {url}: {last_error}")


def execute_cell(cell: dict[str, Any], *, dry_run: bool, health_timeout: int) -> None:
    label = f"{cell['model_id']}/{cell['group']}"
    print(json.dumps({"cell": label, "phase": "performance"}))
    performance_started = False
    try:
        run(cell["start_argv"], dry_run=dry_run)
        performance_started = True
        wait_health(cell["health_url"], health_timeout, dry_run=dry_run)
        run(cell["warmup_argv"], dry_run=dry_run)
        for run_index in range(1, 4):
            run(substitute(cell["performance_argv"], run_index), dry_run=dry_run)
    finally:
        if performance_started:
            run(cell["stop_argv"], dry_run=dry_run)

    print(json.dumps({"cell": label, "phase": "quality"}))
    quality_started = False
    try:
        run(cell["start_argv"], dry_run=dry_run)
        quality_started = True
        wait_health(cell["health_url"], health_timeout, dry_run=dry_run)
        for run_index in range(1, 4):
            run(substitute(cell["quality_argv"], run_index), dry_run=dry_run)
    finally:
        if quality_started:
            run(cell["stop_argv"], dry_run=dry_run)


def execute_cells(
    cells: list[dict[str, Any]],
    labels: list[str],
    *,
    dry_run: bool,
    health_timeout: int,
    journal_path: Path | None,
    plan_hash: str,
    preflight_hash: str,
    completed: list[str],
    cell_executor: Callable[..., None] = execute_cell,
) -> list[str]:
    completed = list(completed)
    for cell, label in zip(cells, labels):
        if label in completed:
            print(json.dumps({"cell": label, "resume_skip": True}))
            continue
        if not dry_run:
            assert journal_path is not None
            atomic_json(
                journal_path,
                journal_value(
                    plan_hash=plan_hash,
                    preflight_hash=preflight_hash,
                    completed=completed,
                    current_cell=label,
                    status="running",
                ),
            )
        try:
            cell_executor(
                cell, dry_run=dry_run, health_timeout=health_timeout
            )
        except Exception as exc:
            if not dry_run:
                assert journal_path is not None
                atomic_json(
                    journal_path,
                    journal_value(
                        plan_hash=plan_hash,
                        preflight_hash=preflight_hash,
                        completed=completed,
                        current_cell=label,
                        status="failed",
                        error=f"{type(exc).__name__}: {exc}",
                    ),
                )
            raise
        completed.append(label)
        if not dry_run:
            assert journal_path is not None
            atomic_json(
                journal_path,
                journal_value(
                    plan_hash=plan_hash,
                    preflight_hash=preflight_hash,
                    completed=completed,
                    current_cell=None,
                    status="running",
                ),
            )
    if not dry_run:
        assert journal_path is not None
        atomic_json(
            journal_path,
            journal_value(
                plan_hash=plan_hash,
                preflight_hash=preflight_hash,
                completed=completed,
                current_cell=None,
                status="complete",
            ),
        )
    return completed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--preflight-report", type=Path)
    parser.add_argument("--authorization", default="")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--journal", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--health-timeout-seconds", type=int, default=600)
    parser.add_argument("--max-preflight-age-seconds", type=int, default=300)
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    verified = subprocess.run(
        [sys.executable, str(here / "verify_lifecycle_plan.py"), "--plan", str(args.plan)],
        check=False,
        text=True,
        capture_output=True,
    )
    try:
        verification = json.loads(verified.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"lifecycle verifier emitted invalid JSON: {exc}")
    if verified.returncode != 0 or verification.get("valid") is not True:
        print(verified.stdout, end="")
        return 2
    plan_hash = hashlib.sha256(args.plan.read_bytes()).hexdigest()
    if verification.get("plan_sha256") != plan_hash:
        raise SystemExit("lifecycle plan changed during verification")
    plan = load_json(args.plan)
    labels = [f"{cell['model_id']}/{cell['group']}" for cell in plan["cells"]]
    if len(labels) != len(set(labels)):
        raise SystemExit("lifecycle plan contains duplicate cell labels")

    preflight_hash = ""
    if args.execute:
        if args.authorization != AUTHORIZATION:
            raise SystemExit("exact NPU0-3 replacement authorization is required")
        if args.preflight_report is None:
            raise SystemExit("--preflight-report is required with --execute")
        preflight = load_json(args.preflight_report)
        if preflight.get("schema") != "paper-to-ascend-preflight/v1" or preflight.get("ready") is not True:
            raise SystemExit("preflight report is not ready")
        try:
            generated = datetime.fromisoformat(str(preflight["generated_at_utc"]))
            if generated.tzinfo is None:
                raise ValueError("timezone missing")
            age = (datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds()
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"preflight timestamp invalid: {exc}") from exc
        if age < 0 or age > args.max_preflight_age_seconds:
            raise SystemExit(f"preflight report is stale or future-dated: age_seconds={age:.1f}")
        preflight_hash = hashlib.sha256(args.preflight_report.read_bytes()).hexdigest()
        if plan.get("preflight_report_sha256") != preflight_hash:
            raise SystemExit("lifecycle plan is not bound to this preflight report")
        for field in (
            "runtime_config_sha256",
            "frozen_inputs_sha256",
            "treatment_matrix_sha256",
        ):
            if plan.get(field) != preflight.get(field):
                raise SystemExit(f"lifecycle plan/preflight mismatch: {field}")
        if args.journal is None:
            raise SystemExit("--journal is required with --execute")
        if args.resume:
            if not args.journal.is_file():
                raise SystemExit("--resume requires an existing journal")
            try:
                completed = validate_resume_journal(
                    load_json(args.journal),
                    plan_hash=plan_hash,
                    preflight_hash=preflight_hash,
                    labels=labels,
                )
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
        else:
            if args.journal.exists():
                raise SystemExit(
                    "fresh execution refuses to overwrite an existing journal"
                )
            completed = []
    else:
        if args.resume:
            raise SystemExit("--resume requires --execute")
        if args.journal is not None:
            raise SystemExit("--journal is accepted only with --execute")
        completed = []

    dry_run = not args.execute
    completed = execute_cells(
        plan["cells"],
        labels,
        dry_run=dry_run,
        health_timeout=args.health_timeout_seconds,
        journal_path=args.journal,
        plan_hash=plan_hash,
        preflight_hash=preflight_hash,
        completed=completed,
    )
    print(json.dumps({"complete": True, "dry_run": dry_run, "cells": len(plan["cells"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
