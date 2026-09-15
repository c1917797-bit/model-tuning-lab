#!/usr/bin/env python3
"""Reconcile live vLLM cache capacity with DASC per-worker allocation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


TOKEN_RE = re.compile(r"GPU KV cache size:\s*([0-9,]+) tokens")
BLOCK_SIZE = 128
EXPECTED_DENSE_BLOCKS = 445


def service_tokens(text: str) -> int:
    values = {int(x.replace(",", "")) for x in TOKEN_RE.findall(text)}
    if len(values) != 1:
        raise ValueError(f"expected one live cache token capacity, observed {sorted(values)}")
    return values.pop()


def evidence_blocks(path: Path) -> tuple[int, int]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    physical = [row for row in rows if row.get("event") == "physical_cache_bound"]
    pids = {row.get("pid") for row in physical if isinstance(row.get("pid"), int)}
    blocks = {row.get("num_blocks") for row in physical if isinstance(row.get("num_blocks"), int)}
    if len(pids) != 4 or len(blocks) != 1:
        raise ValueError(f"candidate allocation evidence is inconsistent: pids={pids}, blocks={blocks}")
    return blocks.pop(), len(pids)


def verify(dense_log: Path, candidate_log: Path, candidate_evidence: Path) -> dict:
    dense_tokens = service_tokens(dense_log.read_text(encoding="utf-8", errors="replace"))
    candidate_tokens = service_tokens(candidate_log.read_text(encoding="utf-8", errors="replace"))
    if dense_tokens % BLOCK_SIZE or candidate_tokens % BLOCK_SIZE:
        raise ValueError("live token capacity is not divisible by block size")
    evidence_count, workers = evidence_blocks(candidate_evidence)
    dense_aggregate_blocks = dense_tokens // BLOCK_SIZE
    candidate_aggregate_blocks = candidate_tokens // BLOCK_SIZE
    dense_groups, dense_remainder = divmod(dense_aggregate_blocks, EXPECTED_DENSE_BLOCKS)
    candidate_groups, candidate_remainder = divmod(candidate_aggregate_blocks, evidence_count)
    checks = {
        "dense_matches_static_budget": dense_groups > 0 and dense_remainder == 0,
        "candidate_admits_more_blocks": evidence_count > EXPECTED_DENSE_BLOCKS,
        "candidate_log_matches_evidence": candidate_groups > 0
        and candidate_remainder == 0,
        "same_cache_group_multiplier": candidate_groups == dense_groups,
        "total_token_capacity_grows": candidate_tokens > dense_tokens,
        "four_candidate_workers": workers == 4,
    }
    return {
        "block_size": BLOCK_SIZE,
        "dense_tokens": dense_tokens,
        "dense_blocks_per_group": EXPECTED_DENSE_BLOCKS,
        "dense_cache_groups": dense_groups,
        "candidate_tokens": candidate_tokens,
        "candidate_blocks_per_group": evidence_count,
        "candidate_cache_groups": candidate_groups,
        "candidate_evidence_blocks": evidence_count,
        "checks": checks,
        "ok": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--dense-log", required=True, type=Path)
    parser.add_argument("--candidate-log", required=True, type=Path)
    parser.add_argument("--candidate-evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.dense_log, args.candidate_log, args.candidate_evidence)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
