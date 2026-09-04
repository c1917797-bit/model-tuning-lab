#!/usr/bin/env python3
"""Aggregate Ascend torch-profiler kernel_details.csv into optimization hotspots."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

SCHEMA = "qwen35-ascend-profile-hotspots/v1"
DURATION_COLUMN = "Duration(us)"
CATEGORY_RULES = (
    ("collective", re.compile(r"hcom_|allreduce|all_reduce|reduce_scatter|allgather|all_gather", re.I)),
    ("gdn_prefill", re.compile(r"chunkgateddeltarule|chunk_gated|recompute_w_u|merge_16x16|chunkfwdo|solve_tril", re.I)),
    ("gdn_decode", re.compile(r"recurrent_gated_delta|recurrentgateddelta", re.I)),
    ("attention", re.compile(r"attention|flash", re.I)),
    ("causal_conv1d", re.compile(r"causalconv|causal_conv", re.I)),
    ("matmul", re.compile(r"matmul|gemm|mm_", re.I)),
    ("normalization", re.compile(r"rmsnorm|layernorm|l2norm", re.I)),
    ("activation", re.compile(r"swiglu|silu|gelu", re.I)),
    ("copy_transpose", re.compile(r"transpose|tensorMove|inplacecopy|memcpy", re.I)),
    ("sampling", re.compile(r"topk|softmax|sampling|multinomial", re.I)),
    ("elementwise", re.compile(r"add|mul|cast|fill|where|exp|sigmoid", re.I)),
)


def categorize(name: str) -> str:
    for category, pattern in CATEGORY_RULES:
        if pattern.search(name):
            return category
    return "other"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover(inputs: Iterable[str]) -> list[Path]:
    found: set[Path] = set()
    for raw in inputs:
        path = Path(raw)
        if path.is_file() and path.name == "kernel_details.csv":
            found.add(path.resolve())
        elif path.is_dir():
            found.update(p.resolve() for p in path.rglob("kernel_details.csv"))
    return sorted(found)


def parse_file(path: Path) -> dict:
    kernels: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    categories: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    total_us = 0.0
    skipped_rows = 0
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"Name", DURATION_COLUMN}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: missing columns {sorted(required)}")
        for row in reader:
            try:
                duration = float(row[DURATION_COLUMN])
            except (TypeError, ValueError):
                skipped_rows += 1
                continue
            name = row["Name"].strip() or "<unnamed>"
            category = categorize(name)
            kernels[name][0] += 1
            kernels[name][1] += duration
            categories[category][0] += 1
            categories[category][1] += duration
            total_us += duration
    return {
        "path": str(path),
        "sha256": sha256(path),
        "total_kernel_duration_us": total_us,
        "kernel_calls": sum(int(v[0]) for v in kernels.values()),
        "unique_kernels": len(kernels),
        "skipped_rows": skipped_rows,
        "_kernels": kernels,
        "_categories": categories,
    }


def ranked(entries: dict[str, list[float]], total_us: float, limit: int | None = None) -> list[dict]:
    rows = [
        {
            "name": name,
            "calls": int(values[0]),
            "duration_us": round(values[1], 3),
            "share_pct": round(100.0 * values[1] / total_us, 4) if total_us else 0.0,
        }
        for name, values in entries.items()
    ]
    rows.sort(key=lambda row: (-row["duration_us"], row["name"]))
    return rows[:limit] if limit is not None else rows


def analyze(inputs: Iterable[str], top: int) -> dict:
    paths = discover(inputs)
    if not paths:
        raise FileNotFoundError("no kernel_details.csv found")
    combined_kernels: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    combined_categories: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    parsed = []
    for path in paths:
        item = parse_file(path)
        for name, values in item.pop("_kernels").items():
            combined_kernels[name][0] += values[0]
            combined_kernels[name][1] += values[1]
        for name, values in item.pop("_categories").items():
            combined_categories[name][0] += values[0]
            combined_categories[name][1] += values[1]
        parsed.append(item)
    total_us = sum(item["total_kernel_duration_us"] for item in parsed)
    return {
        "schema": SCHEMA,
        "measurement_semantics": {
            "total_kernel_duration_us": "sum of kernel durations across rows and files",
            "not_wall_time": True,
            "warning": "Do not use summed kernel duration as E2E latency or add it to TTFT/TPOT; streams may overlap.",
        },
        "files": parsed,
        "summary": {
            "file_count": len(parsed),
            "total_kernel_duration_us": round(total_us, 3),
            "kernel_calls": sum(item["kernel_calls"] for item in parsed),
            "categories": ranked(combined_categories, total_us),
            "top_kernels": ranked(combined_kernels, total_us, top),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="profile directories or kernel_details.csv files")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be positive")
    payload = analyze(args.inputs, args.top)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
