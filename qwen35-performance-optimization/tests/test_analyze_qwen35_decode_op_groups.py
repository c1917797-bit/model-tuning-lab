#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import pathlib
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_qwen35_decode_op_groups.py"
spec = importlib.util.spec_from_file_location("decode_op_groups", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def write_rank(root: pathlib.Path, rank: int) -> None:
    output = root / f"rank{rank}" / "PROF" / "mindstudio_profiler_output"
    output.mkdir(parents=True)
    path = output / "op_summary_test.csv"
    fields = ["Op Name", "Input Shapes", "Task Type", "Task Duration(us)"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for _ in range(6):
            writer.writerow(
                {
                    "Op Name": "DecodeMatmul",
                    "Input Shapes": "1,4;4,8",
                    "Task Type": "AI_CORE",
                    "Task Duration(us)": 2 + rank,
                }
            )
        for _ in range(3):
            writer.writerow(
                {
                    "Op Name": "DecodeVector",
                    "Input Shapes": "1,8",
                    "Task Type": "AI_VECTOR_CORE",
                    "Task Duration(us)": 5,
                }
            )
        for _ in range(3):
            writer.writerow(
                {
                    "Op Name": "MatmulAllReduceMc2AicpuKernel",
                    "Input Shapes": "N/A",
                    "Task Type": "AI_CPU",
                    "Task Duration(us)": 20,
                }
            )
        for _ in range(4):
            writer.writerow(
                {
                    "Op Name": "MixedPrefill",
                    "Input Shapes": "7,8",
                    "Task Type": "AI_CORE",
                    "Task Duration(us)": 99,
                }
            )


with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    for rank in range(4):
        write_rank(root, rank)
    result = module.analyze(str(root), decode_steps=3, top=10)
    assert result["decode_steps"] == 3
    assert len(result["ranks"]) == 4
    names = [item["op"] for item in result["common_top_groups"]]
    assert "MixedPrefill" not in names
    assert "DecodeMatmul" in names
    matmul = next(item for item in result["common_top_groups"] if item["op"] == "DecodeMatmul")
    assert matmul["max_us_per_step"] == 10
    aicpu = next(
        item
        for item in result["common_top_groups"]
        if item["op"] == "MatmulAllReduceMc2AicpuKernel"
    )
    assert aicpu["overlap_warning"] is not None

print("PASS: decode op-group analyzer")

