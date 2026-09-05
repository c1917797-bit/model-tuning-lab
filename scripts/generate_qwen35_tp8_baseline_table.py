#!/usr/bin/env python3
"""Create the frozen TP8 MTP OFF/ON baseline comparison artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

CONCURRENCIES = ("1", "5", "8", "16")
METRICS = (
    "ttft_p50_ms",
    "tpot_p50_ms",
    "e2e_p50_ms",
    "request_throughput_rps",
    "output_token_throughput_tps",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_summary(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cells = payload.get("cells")
    if not isinstance(cells, dict) or set(cells) != set(CONCURRENCIES):
        raise ValueError(f"{path}: expected cells {CONCURRENCIES}")
    for concurrency in CONCURRENCIES:
        missing = [metric for metric in METRICS if metric not in cells[concurrency]]
        if missing:
            raise ValueError(f"{path}: c{concurrency} missing {missing}")
    return payload


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mtp-off-summary", type=Path, required=True)
    parser.add_argument("--mtp-on-summary", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    parser.add_argument("--mtp-on-source", required=True)
    args = parser.parse_args()

    off = load_summary(args.mtp_off_summary)
    on = load_summary(args.mtp_on_summary)
    rows: list[dict[str, object]] = []
    for concurrency in CONCURRENCIES:
        for label, enabled, summary in (("MTP OFF", False, off), ("MTP ON", True, on)):
            cell = summary["cells"][concurrency]
            rows.append({
                "baseline": label,
                "mtp_enabled": str(enabled).lower(),
                "concurrency": int(concurrency),
                **{metric: cell[metric] for metric in METRICS},
                "ttft_speedup_vs_off": 1.0 if not enabled else off["cells"][concurrency]["ttft_p50_ms"] / cell["ttft_p50_ms"],
                "tpot_speedup_vs_off": 1.0 if not enabled else off["cells"][concurrency]["tpot_p50_ms"] / cell["tpot_p50_ms"],
            })

    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Qwen3.5-27B TP8 dual baseline comparison",
        "",
        "Both groups use physical NPU0-7, TP8/DP1, BF16 without quantization, the same first 32 query_rewrite records, c1/c5/c8/c16, three repetitions, and the median of the three request-level p50 values.",
        "",
        "| Concurrency | MTP OFF TTFT ms | MTP ON TTFT ms | TTFT speedup | MTP OFF TPOT ms | MTP ON TPOT ms | TPOT speedup | OFF/ON output tok/s |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for concurrency in CONCURRENCIES:
        off_cell = off["cells"][concurrency]
        on_cell = on["cells"][concurrency]
        lines.append(
            f"| {concurrency} | {fmt(off_cell['ttft_p50_ms'])} | {fmt(on_cell['ttft_p50_ms'])} | "
            f"{fmt(off_cell['ttft_p50_ms'] / on_cell['ttft_p50_ms'])}x | "
            f"{fmt(off_cell['tpot_p50_ms'])} | {fmt(on_cell['tpot_p50_ms'])} | "
            f"{fmt(off_cell['tpot_p50_ms'] / on_cell['tpot_p50_ms'])}x | "
            f"{fmt(off_cell['output_token_throughput_tps'])} / {fmt(on_cell['output_token_throughput_tps'])} |"
        )
    lines.extend([
        "",
        "A speedup above 1.0x is better. The final target is at least 2.0x for both TTFT and TPOT at every concurrency.",
        "",
        "## Evidence",
        "",
        f"- MTP OFF summary: `{args.mtp_off_summary}` (SHA256 `{sha256(args.mtp_off_summary)}`)",
        f"- MTP ON summary: `{args.mtp_on_summary}` (SHA256 `{sha256(args.mtp_on_summary)}`)",
        f"- MTP ON source: `{args.mtp_on_source}`",
        f"- Machine-readable table: `{args.csv_output}` (SHA256 `{sha256(args.csv_output)}`)",
        "",
        "## Protocol audit",
        "",
        "- These frozen v1 results include EOS-only requests in the legacy TPOT summary and reuse identical prompts with prefix caching enabled. Treat them as cache-policy-specific.",
        "- Natural EOS and zero request errors prove runtime validity. Task correctness is reported separately; string hashes and character similarity are diagnostic.",
        "- MTP acceptance metrics and the full per-repeat results remain in the external evidence root.",
        "",
    ])
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

