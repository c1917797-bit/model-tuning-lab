#!/usr/bin/env python3
"""Verify that every process observed on physical NPU4-7 belongs to one container."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
import subprocess
from pathlib import Path


PROCESS_RE = re.compile(r"Process id:\s*(\d+)")


def parse_container_pids(text: str) -> set[int]:
    pids = set()
    for line in text.splitlines():
        value = line.strip()
        if value.isdigit():
            pids.add(int(value))
    return pids


def parse_device_pids(snapshots: dict[int, str]) -> set[int]:
    return {
        int(match)
        for text in snapshots.values()
        for match in PROCESS_RE.findall(text)
    }


def verify(owned: set[int], observed: set[int]) -> dict:
    foreign = sorted(observed - owned)
    return {
        "owned_pids": sorted(owned),
        "observed_device_pids": sorted(observed),
        "foreign_pids": foreign,
        "ok": bool(owned) and not foreign,
    }


def run(container: str, cards: list[int]) -> dict:
    top = subprocess.run(
        # The Docker/ps combination on chicaihong01 rejects the GNU-style
        # header suppression token "pid=".  "pid" is accepted by both the
        # host daemon and newer daemons; parse_container_pids already ignores
        # the non-numeric header.
        ["docker", "top", container, "-eo", "pid"],
        check=True,
        capture_output=True,
        text=True,
    )
    snapshots = {}
    for card in cards:
        result = subprocess.run(
            ["npu-smi", "info", "-t", "proc-mem", "-i", str(card), "-c", "0"],
            check=True,
            capture_output=True,
            text=True,
        )
        snapshots[card] = result.stdout + result.stderr
    result = verify(parse_container_pids(top.stdout), parse_device_pids(snapshots))
    result.update(
        {
            "container": container,
            "physical_npus": cards,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        }
    )
    return result


def append_history(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (json.dumps(result, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        written = os.write(descriptor, line)
        if written != len(line):
            raise OSError(f"short ownership-history write: {written}/{len(line)}")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--container", required=True)
    parser.add_argument("--cards", nargs="+", type=int, required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--history", type=Path)
    args = parser.parse_args()
    result = run(args.container, args.cards)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(args.output)
    if args.history:
        append_history(args.history, result)
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
