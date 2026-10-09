#!/usr/bin/env python3
"""Verify the bounded Cannbot routing/readiness case without inventing a capture."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def main() -> int:
    report = (HERE / "ASCEND_CANNBOT_PROFILER_BOUNDARY_CASE_20261009.md").read_text()
    source_map = (HERE / "ASCEND_SOURCE_MAP_CASE_20261009.md").read_text()
    final_report = (HERE / "REPORT.md").read_text()
    for value in (
        "d5e0d44b7a1d2e90c5f0b9fb62970fb3bac89ec3",
        "222677fc719c7014879b161ed1dd3ed3276d7a5d",
        "0684247214bae5abb5cb6dc7d90b34a6ad401cdd",
        "3ed968171bd42d57874bd96bc242c5868b0e6d59",
        "Level1 + PipeUtilization",
    ):
        require(value in report, f"case report missing boundary or identity: {value}")
    require("does not validate" in report
            and "actual NPU profiler capture" in report,
            "case report lost the no-capture boundary")
    require("not an HCCL or CANN kernel change" in source_map,
            "source-map routing boundary disappeared")
    require("without a profile showing that seam" in source_map,
            "source-map profiler admission rule disappeared")
    require("no profiler" in final_report,
            "final campaign no-profiler fact disappeared")
    result = {
        "schema": "ascend-cannbot-profiler-case-result/v1",
        "fresh_workspace_root": "/cache/cch",
        "historical_workspace_root_valid": False,
        "expert_contract_consulted": True,
        "low_level_widening_admitted": False,
        "npu_profiler_capture_completed": False,
        "acceptance": "partial-evidence",
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
