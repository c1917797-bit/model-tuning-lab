#!/usr/bin/env python3
import csv
import importlib.util
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PATH = (
    ROOT
    / "qwen35-performance-optimization"
    / "scripts"
    / "analyze_qwen35_gdn_decode_chain.py"
)
SPEC = importlib.util.spec_from_file_location("gdn_chain", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def row(start, duration, name, shape, stream="7"):
    return {
        "Task Start Time(us)": str(start),
        "Task Duration(us)": str(duration),
        "Op Name": name,
        "Input Shapes": shape,
        "Stream ID": stream,
    }


rows = []
for offset in (0.0, 100.0):
    rows.extend(
        [
            row(offset + 0, 10, MODULE.TRANSPOSE, MODULE.TRANSPOSE_SHAPE),
            row(offset + 12, 8, MODULE.CAUSAL, MODULE.CAUSAL_SHAPE),
            row(offset + 22, 6, MODULE.CAT, MODULE.CAT_SHAPE),
            row(offset + 29, 2, MODULE.COPY, MODULE.COPY_SHAPE),
            row(offset + 32, 4, MODULE.GATING, MODULE.GATING_SHAPE),
            row(offset + 37, 2, MODULE.L2NORM, MODULE.L2NORM_SHAPE),
            row(offset + 40, 3, MODULE.L2NORM, MODULE.L2NORM_SHAPE),
            row(offset + 45, 15, MODULE.RECURRENT, MODULE.RECURRENT_SHAPE),
        ]
    )

result = MODULE.analyze_rows(
    [
        {
            "start": float(item["Task Start Time(us)"]),
            "end": float(item["Task Start Time(us)"])
            + float(item["Task Duration(us)"]),
            "duration": float(item["Task Duration(us)"]),
            "name": item["Op Name"],
            "shape": item["Input Shapes"],
            "stream": item["Stream ID"],
        }
        for item in rows
    ]
)
assert result["target_recurrent_calls"] == 2
assert result["paired_chains"] == 2
assert result["metrics"]["weight_transpose_duration_us"]["median_us"] == 10
assert (
    result["metrics"]["weight_transpose_start_to_recurrent_end_us"]["median_us"]
    == 60
)

with tempfile.TemporaryDirectory() as directory:
    path = pathlib.Path(directory) / "rank0" / "op_summary.csv"
    path.parent.mkdir()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    report = MODULE.analyze_files(
        [path], decode_steps=1, gdn_layers=2, required_saving_ms=1.0
    )
    assert report["opportunity"]["conv_prepack_zero_cost_upper_bound_ms_per_token"] == 0.02
    assert report["opportunity"]["full_chain_zero_cost_upper_bound_ms_per_token"] == 0.12

print("PASS: GDN decode-chain analyzer")
