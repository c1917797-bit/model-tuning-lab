#!/usr/bin/env python3
"""Capture the small Prometheus metric subset used by DASC acceptance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.request


NEEDLES = (
    "prefix_cache_queries_total",
    "prefix_cache_hits_total",
    "prompt_tokens_cached_total",
    "request_success_total",
)


def parse_metrics(text: str) -> dict[str, float]:
    selected: dict[str, float] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or not any(x in line for x in NEEDLES):
            continue
        try:
            name, raw_value = line.rsplit(None, 1)
            value = float(raw_value)
        except (ValueError, TypeError) as error:
            raise ValueError(f"invalid Prometheus row {number}: {raw!r}") from error
        if name in selected:
            raise ValueError(f"duplicate Prometheus series at row {number}: {name}")
        selected[name] = value
    if not any("prefix_cache_hits_total" in name for name in selected):
        raise ValueError("prefix_cache_hits_total metric is absent")
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with urllib.request.urlopen(args.url, timeout=30) as response:
        result = parse_metrics(response.read().decode("utf-8"))
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
