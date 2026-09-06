#!/usr/bin/env python3
"""Fail-closed audit for the machine-readable Hypic evidence inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


HASH_PAIRS = (
    ("path", "sha256"),
    ("details_path", "details_sha256"),
    ("summary_path", "summary_sha256"),
    ("manifest_path", "manifest_sha256"),
    ("workload_path", "workload_sha256"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(raw: str, worktree: Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else worktree / path


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def audit_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"{path}: blank JSONL line {line_number}")
            json.loads(line)
            count += 1
    return count


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--worktree-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--allow-volatile",
        action="store_true",
        help="allow explicitly marked live-producer hash drift; never use for final audit",
    )
    args = parser.parse_args()

    evidence_path = args.evidence.resolve()
    worktree = args.worktree_root.resolve()
    document = load_json(evidence_path)
    errors: list[str] = []
    checked: list[dict[str, Any]] = []
    skipped_external: list[dict[str, str]] = []
    allowed_volatile: list[dict[str, str]] = []
    profile_payloads: dict[str, dict[str, int]] = {}

    if document.get("schema") != "paper-to-ascend-evidence/v1":
        errors.append("unexpected evidence schema")
    entries = document.get("evidence")
    if not isinstance(entries, list) or not entries:
        errors.append("evidence must be a non-empty list")
        entries = []

    for entry in entries:
        evidence_id = entry.get("id")
        if not isinstance(evidence_id, str) or not evidence_id:
            errors.append("evidence entry lacks a non-empty id")
            continue

        for path_key, hash_key in HASH_PAIRS:
            raw_path = entry.get(path_key)
            expected_hash = entry.get(hash_key)
            if raw_path is None and expected_hash is None:
                continue
            if not isinstance(raw_path, str) or not isinstance(expected_hash, str):
                errors.append(f"{evidence_id}: incomplete {path_key}/{hash_key} pair")
                continue
            if len(expected_hash) != 64 or expected_hash.lower() != expected_hash:
                errors.append(f"{evidence_id}: {hash_key} is not canonical SHA256")
                continue
            path = resolve_path(raw_path, worktree)
            if not path.is_file():
                errors.append(f"{evidence_id}: missing regular file {path}")
                continue
            if path.stat().st_size == 0:
                errors.append(f"{evidence_id}: empty file {path}")
                continue
            actual_hash = sha256_file(path)
            if actual_hash != expected_hash:
                if (
                    args.allow_volatile
                    and entry.get("hash_state") == "volatile-until-producer-stops"
                ):
                    allowed_volatile.append(
                        {
                            "evidence_id": evidence_id,
                            "path": str(path),
                            "recorded_sha256": expected_hash,
                            "current_sha256": actual_hash,
                        }
                    )
                else:
                    errors.append(
                        f"{evidence_id}: {path_key} hash mismatch "
                        f"(expected {expected_hash}, got {actual_hash})"
                    )
            checked.append(
                {
                    "evidence_id": evidence_id,
                    "kind": path_key,
                    "path": str(path),
                    "sha256": actual_hash,
                    "bytes": path.stat().st_size,
                }
            )

        source_path = entry.get("source_path")
        source_hash = entry.get("source_sha256")
        if source_path is not None or source_hash is not None:
            if not isinstance(source_path, str) or not isinstance(source_hash, str):
                errors.append(f"{evidence_id}: incomplete external source identity")
            else:
                skipped_external.append(
                    {
                        "evidence_id": evidence_id,
                        "path": source_path,
                        "expected_sha256": source_hash,
                        "reason": "source is outside chicaihong01; verify on the source host",
                    }
                )

        summary_raw = entry.get("summary_path")
        details_raw = entry.get("details_path")
        if isinstance(summary_raw, str) and isinstance(details_raw, str):
            summary_path = resolve_path(summary_raw, worktree)
            details_path = resolve_path(details_raw, worktree)
            if summary_path.is_file() and details_path.is_file():
                try:
                    summary = load_json(summary_path)
                    line_count = audit_jsonl(details_path)
                    requests = summary.get("requests")
                    successful = summary.get("successful")
                    failed = summary.get("failed")
                    if not all(isinstance(value, int) for value in (requests, successful, failed)):
                        errors.append(f"{evidence_id}: invalid request counters")
                    else:
                        if line_count != requests:
                            errors.append(
                                f"{evidence_id}: JSONL lines {line_count} != requests {requests}"
                            )
                        if successful + failed != requests:
                            errors.append(f"{evidence_id}: success/failure count mismatch")
                        if failed != 0:
                            errors.append(f"{evidence_id}: failed requests is {failed}, expected zero")
                    if summary.get("details_sha256") != entry.get("details_sha256"):
                        errors.append(f"{evidence_id}: summary details hash is not inventory-bound")
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    errors.append(f"{evidence_id}: quality artifact parse failed: {exc}")

        if "active-semantic-canary" in evidence_id and isinstance(entry.get("path"), str):
            path = resolve_path(entry["path"], worktree)
            if path.is_file():
                canary = load_json(path)
                if canary.get("answer_contains_key") is not True:
                    errors.append(f"{evidence_id}: answer key was not observed")
                if canary.get("input_tokens") != 32768:
                    errors.append(f"{evidence_id}: input token ruler is not 32768")

        if "native-profile" in evidence_id and isinstance(entry.get("manifest_path"), str):
            path = resolve_path(entry["manifest_path"], worktree)
            if path.is_file():
                manifest = load_json(path)
                if manifest.get("profiler_exit_code") != 0:
                    errors.append(f"{evidence_id}: profiler_exit_code is not zero")
                workload_exit = manifest.get("workload_exit_code")
                if workload_exit != 0:
                    capture = manifest.get("profile_capture_stimulus")
                    observed = (
                        capture.get("observed")
                        if isinstance(capture, dict)
                        else None
                    )
                    capture_ok = (
                        manifest.get("phase") == "pdc-hypic"
                        and workload_exit == 1
                        and isinstance(capture, dict)
                        and capture.get("verified") is True
                        and capture.get("algorithm_acceptance_derived_from_this_gate")
                        is False
                        and isinstance(observed, dict)
                        and observed.get("configured_requests") == 4
                        and observed.get("summary_requests") == 4
                        and observed.get("successful") == 4
                        and observed.get("failed") == 0
                        and observed.get("fixed_output_verified") is True
                        and observed.get("result_count") == 4
                        and observed.get("all_measured_results_ok") is True
                    )
                    if not capture_ok:
                        errors.append(
                            f"{evidence_id}: nonzero workload exit lacks a "
                            "strictly verified capture-only stimulus"
                        )
                if manifest.get("cpuset_cpus") != "112-191":
                    errors.append(f"{evidence_id}: unexpected CPU set")
                if manifest.get("host_accelerator_devices") != [
                    "/dev/davinci0",
                    "/dev/davinci1",
                    "/dev/davinci2",
                    "/dev/davinci3",
                ]:
                    errors.append(f"{evidence_id}: unexpected host accelerator devices")
                files = manifest.get("profile_files")
                if not isinstance(files, list) or not files:
                    errors.append(f"{evidence_id}: profile_files is not a non-empty list")
                else:
                    total_bytes = 0
                    valid_files = 0
                    for file_entry in files:
                        if not isinstance(file_entry, dict):
                            errors.append(f"{evidence_id}: invalid profile file record")
                            continue
                        file_path_raw = file_entry.get("path")
                        expected_file_hash = file_entry.get("sha256")
                        expected_size = file_entry.get("size_bytes")
                        if (
                            not isinstance(file_path_raw, str)
                            or not isinstance(expected_file_hash, str)
                            or not isinstance(expected_size, int)
                            or expected_size <= 0
                        ):
                            errors.append(f"{evidence_id}: incomplete profile file record")
                            continue
                        file_path = resolve_path(file_path_raw, worktree)
                        if not file_path.is_file():
                            errors.append(f"{evidence_id}: missing profile payload {file_path}")
                            continue
                        actual_size = file_path.stat().st_size
                        if actual_size != expected_size:
                            errors.append(
                                f"{evidence_id}: profile payload size mismatch for {file_path}"
                            )
                            continue
                        if sha256_file(file_path) != expected_file_hash:
                            errors.append(
                                f"{evidence_id}: profile payload hash mismatch for {file_path}"
                            )
                            continue
                        total_bytes += actual_size
                        valid_files += 1
                    profile_payloads[evidence_id] = {
                        "files_checked": valid_files,
                        "total_bytes": total_bytes,
                    }

    report = {
        "schema": "hypic-evidence-audit/v1",
        "evidence_path": str(evidence_path),
        "evidence_sha256": sha256_file(evidence_path),
        "worktree_root": str(worktree),
        "ok": not errors,
        "checked_file_count": len(checked),
        "checked_files": checked,
        "profile_payloads": profile_payloads,
        "allowed_volatile_evidence": allowed_volatile,
        "skipped_external_sources": skipped_external,
        "errors": errors,
    }
    if args.output:
        write_json_atomic(args.output.resolve(), report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
