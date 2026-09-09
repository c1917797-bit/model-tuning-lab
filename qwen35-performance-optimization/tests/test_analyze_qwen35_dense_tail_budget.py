#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import pathlib
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_qwen35_dense_tail_budget.py"
spec = importlib.util.spec_from_file_location("dense_tail_budget", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def write_rank(root: pathlib.Path, rank: int, swiglu_us: float, mmar_us: float) -> None:
    out = root / f"rank{rank}" / "PROF" / "mindstudio_profiler_output"
    out.mkdir(parents=True)
    path = out / "op_summary_test.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Op Name", "Input Shapes", "Task Duration(us)"])
        writer.writeheader()
        for _ in range(128):
            writer.writerow({"Op Name": "SwiGlu", "Input Shapes": '"1,8704"', "Task Duration(us)": swiglu_us})
            writer.writerow({"Op Name": "MatmulAllReduce", "Input Shapes": '"1,4352;4352,5120;;;;;;;;"', "Task Duration(us)": mmar_us})
            writer.writerow({"Op Name": "MatmulAllReduceMc2AicpuKernel", "Input Shapes": "N/A", "Task Duration(us)": 9999})


with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    for rank in range(4):
        write_rank(root, rank, 4.0 + rank * 0.1, 90.0 + rank)
    result = module.analyze(str(root), layers=64, required_chain_speedup=1.15)
    assert result["decode_steps"] == 2
    assert result["slowest_rank"] == "rank3"
    assert result["decision"] == "requires-device-boundary-fusion"
    assert 1.0 < result["activation_only_speedup_ceiling"] < 1.15
    assert result["required_non_activation_savings_us_per_call"] > 0

print("PASS: dense-tail budget analysis")
