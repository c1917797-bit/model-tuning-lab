#!/usr/bin/env python3
"""Verify that every process observed on physical NPU4-7 belongs to one container."""

from __future__ import annotations

import argparse
import json
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
        ["docker", "top", container, "-eo", "pid="],
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
    return verify(parse_container_pids(top.stdout), parse_device_pids(snapshots))


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--container", required=True)
    parser.add_argument("--cards", nargs="+", type=int, required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.container, args.cards)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(args.output)
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
