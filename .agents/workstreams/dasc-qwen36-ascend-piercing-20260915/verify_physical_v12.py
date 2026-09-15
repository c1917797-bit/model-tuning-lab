#!/usr/bin/env python3
"""Independently recompute the DASC v12 mechanism verdict from raw artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess


SHA_LINE = re.compile(r"^([0-9a-f]{64}) [ *](.+)$")
EXPECTED_MODEL_CONFIG = Path("/cache/efim/Qwen3.6-27B/config.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_manifest(path: Path) -> list[tuple[str, Path]]:
    records: list[tuple[str, Path]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = SHA_LINE.fullmatch(line)
        if match is None:
            raise ValueError(f"{path}:{line_number}: invalid sha256sum record")
        records.append((match.group(1), Path(match.group(2))))
    if not records:
        raise ValueError(f"{path}: empty manifest")
    return records


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def verify_manifest(path: Path, allowed_root: Path) -> dict:
    failures: list[str] = []
    records = parse_manifest(path)
    for expected, target in records:
        if not target.is_absolute():
            target = path.parent / target
        if not is_within(target, allowed_root):
            failures.append(f"outside allowed root: {target}")
        elif not target.is_file():
            failures.append(f"missing: {target}")
        else:
            actual = sha256_file(target)
            if actual != expected:
                failures.append(f"sha256 mismatch: {target}")
    return {"records": len(records), "failures": failures, "ok": not failures}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected object")
        rows.append(value)
    return rows


def evidence_verdict(rows: list[dict]) -> dict:
    counts = Counter(row.get("event") for row in rows)

    def pids(event: str) -> list[int]:
        return sorted(
            {
                row["pid"]
                for row in rows
                if row.get("event") == event and isinstance(row.get("pid"), int)
            }
        )

    physical = [row for row in rows if row.get("event") == "physical_cache_bound"]
    physical_pids = pids("physical_cache_bound")
    geometry_pids = pids("tp_geometry_aligned")
    dispatch_pids = pids("worker_dispatch_verified")
    cohort_ok = (
        len(physical_pids) == 4
        and physical_pids == geometry_pids
        and physical_pids == dispatch_pids
    )
    compact_ok = bool(physical) and all(
        isinstance(row.get("compact_page_bytes"), int)
        and isinstance(row.get("dense_page_bytes"), int)
        and row["compact_page_bytes"] < row["dense_page_bytes"]
        for row in physical
    )
    blocks_ok = bool(physical) and all(
        isinstance(row.get("num_blocks"), int) and row["num_blocks"] > 0
        for row in physical
    )
    result = {
        "row_count": len(rows),
        "event_counts": dict(sorted(counts.items(), key=lambda item: str(item[0]))),
        "physical_cache_pids": physical_pids,
        "tp_geometry_pids": geometry_pids,
        "worker_dispatch_pids": dispatch_pids,
        "worker_cohort_aligned": cohort_ok,
        "compact_lt_dense": compact_ok,
        "positive_blocks": blocks_ok,
        "heterogeneous_cache_grouped": counts["heterogeneous_cache_grouped"] >= 1,
    }
    result["ok"] = all(
        result[key]
        for key in (
            "worker_cohort_aligned",
            "compact_lt_dense",
            "positive_blocks",
            "heterogeneous_cache_grouped",
        )
    )
    return result


def metric_sum(snapshot: dict[str, float], needle: str) -> float:
    return sum(float(value) for name, value in snapshot.items() if needle in name)


def exact_stopped(record: dict, expected: str) -> bool:
    return (
        record.get("content") == expected
        and record.get("finish_reason") == "stop"
        and not record.get("reasoning_content")
    )


def canary_verdict(canary: dict, evidence: list[dict]) -> dict:
    runs = canary.get("runs", [])
    hit_delta = metric_sum(
        canary.get("metrics_after", {}), "prefix_cache_hits_total"
    ) - metric_sum(canary.get("metrics_before", {}), "prefix_cache_hits_total")
    raw_evidence = evidence_verdict(evidence)
    checks = {
        "schema": canary.get("schema") == "mst.dasc.physical-canary/v1",
        "short_exact": exact_stopped(canary.get("short", {}), "OK"),
        "three_replays": len(runs) == 3,
        "replays_exact": len(runs) == 3
        and all(exact_stopped(run, "VERIFIED") for run in runs),
        "variant_exact": exact_stopped(canary.get("variant", {}), "ASCEND"),
        "cache_hit_positive": hit_delta > 0,
        "raw_activation": raw_evidence["ok"],
    }
    return {
        "checks": checks,
        "prefix_cache_hit_delta": hit_delta,
        "raw_activation": raw_evidence,
        "reported_ok": canary.get("ok"),
        "ok": all(checks.values()),
    }


def verify_source_commit(repo: Path, value: str) -> bool:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        return False
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{value}^{{commit}}"],
        cwd=repo,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def verify(root: Path, repo: Path) -> dict:
    required = (
        "SUCCESS",
        "controller-exit-code.txt",
        "source-commit.txt",
        "source-status.txt",
        "model-config.sha256",
        "image-inspect.json",
        "plugin-files.sha256",
        "canary.sha256",
        "evidence.jsonl",
        "physical-canary.json",
        "service.log",
        "artifacts.sha256",
    )
    missing = [name for name in required if not (root / name).is_file()]
    result: dict = {"root": str(root), "missing": missing}
    if missing:
        result["ok"] = False
        return result

    result["artifacts_manifest"] = verify_manifest(root / "artifacts.sha256", root)
    result["plugin_manifest"] = verify_manifest(root / "plugin-files.sha256", root)
    result["canary_manifest"] = verify_manifest(root / "canary.sha256", root)

    model_records = parse_manifest(root / "model-config.sha256")
    model_ok = len(model_records) == 1
    if model_ok:
        expected, target = model_records[0]
        model_ok = (
            target.resolve() == EXPECTED_MODEL_CONFIG.resolve()
            and target.is_file()
            and sha256_file(target) == expected
        )
    result["model_config_ok"] = model_ok

    source_commit = (root / "source-commit.txt").read_text(encoding="utf-8").strip()
    source_lines = (root / "source-status.txt").read_text(encoding="utf-8").splitlines()
    result["source_commit"] = source_commit
    result["source_commit_exists"] = verify_source_commit(repo, source_commit)
    result["source_status_clean"] = bool(source_lines) and not any(
        line and not line.startswith("## ") for line in source_lines
    )
    result["controller_exit_zero"] = (
        root.joinpath("controller-exit-code.txt").read_text(encoding="utf-8").strip()
        == "0"
    )
    canary = json.loads(
        root.joinpath("physical-canary.json").read_text(encoding="utf-8")
    )
    result["canary"] = canary_verdict(canary, load_jsonl(root / "evidence.jsonl"))
    result["ok"] = (
        not missing
        and result["artifacts_manifest"]["ok"]
        and result["plugin_manifest"]["ok"]
        and result["canary_manifest"]["ok"]
        and result["model_config_ok"]
        and result["source_commit_exists"]
        and result["source_status_clean"]
        and result["controller_exit_zero"]
        and result["canary"]["ok"]
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.root.resolve(), args.repo.resolve())
    encoded = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
