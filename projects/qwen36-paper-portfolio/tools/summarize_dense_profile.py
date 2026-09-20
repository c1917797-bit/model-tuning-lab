#!/usr/bin/env python3
"""Validate and summarize a frozen Qwen3.6 dense Ascend profile.

Kernel sums and operator ratios are diagnostic aggregates.  They are not an
end-to-end critical path and must not be converted directly into throughput.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from statistics import mean


REQUIRED = (
    "kernel_details.csv",
    "op_statistic.csv",
    "api_statistic.csv",
    "trace_view.json",
)

PREFILL_EXPECTED = {
    "FusedInferAttentionScore": 16,
    "CausalConv1d": 48,
    "ChunkGatedDeltaRuleFwdH": 48,
    "RecurrentGatedDeltaRule": 0,
    "_compute_slot_mapping_kernel": 1,
}

DECODE_EXPECTED = {
    "FusedInferAttentionScore": 16 * 30,
    "CausalConv1d": 48 * 30,
    "ChunkGatedDeltaRuleFwdH": 0,
    "RecurrentGatedDeltaRule": 48 * 30,
    "_compute_slot_mapping_kernel": 30,
}

SCOPES = {
    "prefill_direct_triangular_inversion": {
        "phases": {"prefill"},
        "operators": {
            "merge_16x16_to_64x64_inverse_kernel",
            "solve_tril_16x16_kernel",
        },
    },
    "prefill_megagdn_six_stage": {
        "phases": {"prefill"},
        "operators": {
            "ChunkGatedDeltaRuleFwdH",
            "recompute_w_u_fwd_kernel",
            "merge_16x16_to_64x64_inverse_kernel",
            "solve_tril_16x16_kernel",
            "chunk_scaled_dot_kkt_fwd_kernel",
            "ChunkFwdO",
        },
    },
    "decode_recurrent_only": {
        "phases": {"decode"},
        "operators": {"RecurrentGatedDeltaRule"},
    },
    "decode_linear_attention_broad": {
        "phases": {"decode"},
        "operators": {
            "RecurrentGatedDeltaRule",
            "FusedGdnGating",
            "l2norm_fwd_kernel2",
            "CausalConv1d",
            "Slice",
            "ConcatD",
        },
    },
    "attention": {
        "phases": {"prefill", "decode"},
        "operators": {"FusedInferAttentionScore"},
    },
    "matmul": {
        "phases": {"prefill", "decode"},
        "operators": {"MatMulV2", "MatMulV3"},
    },
}

# These shapes map to the single GDN call chain in v0.23: concatenate local
# Q/K/V projections, transpose convolution weights, run causal-conv, split
# mixed QKV and gating tensors, normalize Q/K, and update the recurrent state.
# Shape filtering prevents unrelated Slice/Transpose kernels from inflating the
# plugin fusion seam.
DECODE_GDN_SHAPE_FILTERS = {
    "ConcatD": None,
    "Transpose": {"2560,4;2"},
    "CausalConv1d": None,
    "Slice": {"16,24;2;2", "16,2560;2;2", "16,32,128;3;3"},
    "FusedGdnGating": None,
    "l2norm_fwd_kernel2": None,
    "RecurrentGatedDeltaRule": None,
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ns(value: str) -> int:
    return int(Decimal(value.strip()) * 1000)


def union_ns(intervals: list[tuple[int, int]]) -> int:
    total = 0
    left = right = None
    for start, end in sorted(intervals):
        if end < start:
            raise ValueError("negative interval")
        if left is None:
            left, right = start, end
        elif start <= right:
            right = max(right, end)
        else:
            total += right - left
            left, right = start, end
    return total + (right - left if left is not None else 0)


def required_local_speedup(scope_fraction: float, target: float = 1.10) -> float | None:
    residual = (1 / target) - (1 - scope_fraction)
    if residual <= 0:
        return None
    return scope_fraction / residual


def read_operator_statistics(output: Path) -> tuple[list[dict], dict[str, int]]:
    with (output / "op_statistic.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("empty operator statistics")
    counts = {row["OP Type"]: int(row["Count"]) for row in rows}
    operators = [
        {
            "name": row["OP Type"],
            "core": row["Core Type"],
            "count": int(row["Count"]),
            "total_time_ms": float(row["Total Time(us)"]) / 1000,
            "ratio_pct": float(row["Ratio(%)"]),
        }
        for row in rows
    ]
    return operators, counts


def summarize_trace(directory: Path, phase: str) -> dict:
    output = directory / "ASCEND_PROFILER_OUTPUT"
    missing = [name for name in REQUIRED if not (output / name).is_file()]
    if missing:
        raise ValueError(f"{directory.name}: missing {missing}")

    operators, counts = read_operator_statistics(output)
    expected = PREFILL_EXPECTED if phase == "prefill" else DECODE_EXPECTED
    coverage = {
        name: {
            "expected": expected_count,
            "observed": counts.get(name, 0),
            "passed": counts.get(name, 0) == expected_count,
        }
        for name, expected_count in expected.items()
    }
    if not all(item["passed"] for item in coverage.values()):
        raise ValueError(f"{directory.name}: unexpected phase/step coverage {coverage}")

    with (output / "kernel_details.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        kernel_rows = list(reader)
    if len(fields) < 40 or not kernel_rows:
        raise ValueError("expected populated Level1 + PipeUtilization kernel details")

    groups: dict[tuple[str, str, str], list[tuple[dict, tuple[int, int]]]] = defaultdict(list)
    streams: dict[str, list[tuple[int, int]]] = defaultdict(list)
    device_intervals: list[tuple[int, int]] = []
    compute_intervals: list[tuple[int, int]] = []
    communication_intervals: list[tuple[int, int]] = []
    for row in kernel_rows:
        duration = ns(row["Duration(us)"])
        start = ns(row["Start Time(us)"])
        interval = (start, start + duration)
        core = row["Accelerator Core"]
        groups[(row["Name"], row["Type"], core)].append((row, interval))
        streams[row["Stream ID"]].append(interval)
        if core not in ("AI_CPU", "AICPU"):
            device_intervals.append(interval)
            if core == "COMMUNICATION":
                communication_intervals.append(interval)
            else:
                compute_intervals.append(interval)

    full_start = min(start for start, _ in device_intervals)
    full_end = max(end for _, end in device_intervals)
    wall = full_end - full_start
    active = union_ns(device_intervals)
    compute = union_ns(compute_intervals)
    communication = union_ns(communication_intervals)

    scopes = {}
    operator_by_name = {item["name"]: item for item in operators}
    for name, definition in SCOPES.items():
        if phase not in definition["phases"]:
            continue
        selected = [operator_by_name[op] for op in definition["operators"] if op in operator_by_name]
        ratio_fraction = sum(item["ratio_pct"] for item in selected) / 100
        scopes[name] = {
            "operators": sorted(item["name"] for item in selected),
            "operator_sum_ms": sum(item["total_time_ms"] for item in selected),
            "operator_ratio_pct": ratio_fraction * 100,
            "perfect_elimination_phase_speedup": 1 / (1 - ratio_fraction),
            "local_speedup_needed_for_10pct_phase_gain": required_local_speedup(ratio_fraction),
        }

    if phase == "decode":
        selected_rows = []
        for row in kernel_rows:
            allowed_shapes = DECODE_GDN_SHAPE_FILTERS.get(row["Type"], set())
            if row["Type"] not in DECODE_GDN_SHAPE_FILTERS:
                continue
            shape = row["Input Shapes"].strip('"')
            if allowed_shapes is None or shape in allowed_shapes:
                selected_rows.append(row)
        selected_ms = sum(float(row["Duration(us)"]) for row in selected_rows) / 1000
        total_operator_ms = sum(item["total_time_ms"] for item in operators)
        ratio_fraction = selected_ms / total_operator_ms
        scopes["decode_gdn_shape_filtered_fusion_seam"] = {
            "operators": sorted(DECODE_GDN_SHAPE_FILTERS),
            "selected_kernel_rows": len(selected_rows),
            "operator_sum_ms": selected_ms,
            "operator_ratio_pct": ratio_fraction * 100,
            "perfect_elimination_phase_speedup": 1 / (1 - ratio_fraction),
            "local_speedup_needed_for_10pct_phase_gain": required_local_speedup(ratio_fraction),
            "boundary": "Shape-filtered upper bound for one exact-semantics GDN decode mega-op; not an achieved fusion or speedup.",
        }

    top_kernels = []
    for (name, kind, core), entries in groups.items():
        intervals = [interval for _, interval in entries]
        duration = sum(end - start for start, end in intervals)
        pipeline = {}
        for field in (
            "aic_mac_ratio",
            "aic_mte2_ratio",
            "aiv_vec_ratio",
            "aiv_mte2_ratio",
            "aiv_mte3_ratio",
        ):
            weighted = []
            for row, (start, end) in entries:
                try:
                    weighted.append((float(row[field]), end - start))
                except (KeyError, ValueError):
                    pass
            denominator = sum(weight for _, weight in weighted)
            pipeline[field] = (
                sum(value * weight for value, weight in weighted) / denominator
                if denominator
                else None
            )
        top_kernels.append(
            {
                "name": name,
                "type": kind,
                "core": core,
                "count": len(entries),
                "kernel_sum_ms": duration / 1e6,
                "kernel_union_ms": union_ns(intervals) / 1e6,
                "pipeline_duration_weighted_means": pipeline,
            }
        )

    trace = json.loads((output / "trace_view.json").read_text())
    events = trace.get("traceEvents") if isinstance(trace, dict) else trace
    if not isinstance(events, list) or not events:
        raise ValueError("empty or invalid trace event list")

    return {
        "trace_dir": str(directory),
        "phase": phase,
        "rank": int(re.match(r"rank(\d+)_", directory.name)[1]),
        "kernel_columns": len(fields),
        "kernel_rows": len(kernel_rows),
        "trace_events": len(events),
        "coverage": coverage,
        "sha256": {name: file_sha256(output / name) for name in REQUIRED},
        "kernel_envelope_ms": wall / 1e6,
        "npu_interval_union_ms": active / 1e6,
        "no_listed_npu_kernel_ms": (wall - active) / 1e6,
        "compute_interval_union_ms": compute / 1e6,
        "communication_interval_union_ms": communication / 1e6,
        "compute_communication_overlap_ms": (compute + communication - active) / 1e6,
        "communication_without_compute_ms": (active - compute) / 1e6,
        "streams": {
            stream: {"events": len(items), "union_ms": union_ns(items) / 1e6}
            for stream, items in streams.items()
        },
        "mechanism_scopes": scopes,
        "top_operators": operators[:25],
        "top_kernels": sorted(top_kernels, key=lambda item: item["kernel_sum_ms"], reverse=True)[:25],
    }


def aggregate(records: list[dict]) -> dict:
    result = {}
    for phase in ("prefill", "decode"):
        phase_records = [item for item in records if item["phase"] == phase]
        scope_names = sorted({name for item in phase_records for name in item["mechanism_scopes"]})
        result[phase] = {
            "ranks": [item["rank"] for item in phase_records],
            "mean_kernel_envelope_ms": mean(item["kernel_envelope_ms"] for item in phase_records),
            "mean_npu_interval_union_ms": mean(item["npu_interval_union_ms"] for item in phase_records),
            "mechanism_scope_rank_means": {
                name: {
                    "operator_ratio_pct": mean(
                        item["mechanism_scopes"][name]["operator_ratio_pct"] for item in phase_records
                    ),
                    "operator_sum_ms": mean(
                        item["mechanism_scopes"][name]["operator_sum_ms"] for item in phase_records
                    ),
                    "perfect_elimination_phase_speedup": mean(
                        item["mechanism_scopes"][name]["perfect_elimination_phase_speedup"]
                        for item in phase_records
                    ),
                    "local_speedup_needed_for_10pct_phase_gain": mean(
                        item["mechanism_scopes"][name]["local_speedup_needed_for_10pct_phase_gain"]
                        for item in phase_records
                        if item["mechanism_scopes"][name]["local_speedup_needed_for_10pct_phase_gain"]
                        is not None
                    )
                    if all(
                        item["mechanism_scopes"][name]["local_speedup_needed_for_10pct_phase_gain"]
                        is not None
                        for item in phase_records
                    )
                    else None,
                }
                for name in scope_names
            },
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing reports; choose a new output")

    manifest_path = args.service_dir / "service-manifest.json"
    client_path = args.service_dir / "profile-client.json"
    export_path = args.service_dir / "profile-export.json"
    service = json.loads(manifest_path.read_text())
    client = json.loads(client_path.read_text())
    exported = json.loads(export_path.read_text())
    if client.get("status") != "requests_complete":
        raise ValueError("profile client is incomplete")
    if client.get("service_manifest_sha256") != file_sha256(manifest_path):
        raise ValueError("client is not bound to service manifest")
    if exported.get("profile_client_sha256") != file_sha256(client_path):
        raise ValueError("export receipt is not bound to profile client")
    if exported.get("service_manifest_sha256") != file_sha256(manifest_path):
        raise ValueError("export receipt is not bound to service manifest")

    records = []
    for phase in ("prefill", "decode"):
        paths = client["results"][phase]["trace_dirs"]
        phase_records = [summarize_trace(args.service_dir / path, phase) for path in paths]
        if {record["rank"] for record in phase_records} != {0, 1, 2, 3}:
            raise ValueError(f"{phase} rank coverage differs")
        records.extend(phase_records)

    report = {
        "schema": "qwen36-dense-profile-summary/v1",
        "status": "eight_traces_validated",
        "summary_script_sha256": file_sha256(Path(__file__)),
        "client_sha256": file_sha256(client_path),
        "service_manifest_sha256": file_sha256(manifest_path),
        "profile_export_sha256": file_sha256(export_path),
        "variant": service["variant"],
        "claim": "Single-arm diagnostic profile; not a dense/candidate benchmark or critical-path proof.",
        "interpretation": (
            "Operator sums identify optimization scopes. Interval unions preserve overlap, but neither "
            "metric alone proves an end-to-end speedup. Profiler-disabled paired runs remain mandatory."
        ),
        "aggregate": aggregate(records),
        "records": records,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "aggregate": report["aggregate"]}, indent=2))


if __name__ == "__main__":
    main()
