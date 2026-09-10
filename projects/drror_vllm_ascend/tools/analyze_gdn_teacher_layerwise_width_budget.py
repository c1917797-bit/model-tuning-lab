#!/usr/bin/env python3
"""Solve the frozen equal-cost Dk48/Dk64/Dk80 DRRQR layer allocation."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics


REPORT_SCHEMA = "drrqr-captured-teacher-width-curve-merge/v1"
WIDTHS = (48, 64, 80)
WINDOWS = {
    "all": range(136),
    "prefill_late": range(64, 128),
    "decode_late": range(132, 136),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def checksum(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def analyze(rows, layers, *, regression_limit=1.05, improvement_minimum=0.10):
    require(
        math.isfinite(regression_limit)
        and regression_limit >= 1.0
        and math.isfinite(improvement_minimum)
        and 0.0 < improvement_minimum < 1.0,
        "invalid frozen allocation thresholds",
    )
    expected = {
        (f"teacher-{sequence}", rank, layer, position)
        for sequence in range(2)
        for rank in range(4)
        for layer in layers
        for position in range(136)
    }
    lookup = {}
    fields = tuple(f"energy{width}_relative_l2" for width in WIDTHS)
    for row in rows:
        key = (
            row["sequence_id"],
            row["rank"],
            row["layer"],
            row["position"],
        )
        require(key in expected and key not in lookup, "row outside/duplicate")
        require(
            all(
                type(row[field]) in (float, int)
                and math.isfinite(row[field])
                and row[field] >= 0
                for field in fields
            ),
            "invalid fidelity value",
        )
        lookup[key] = row
    require(set(lookup) == expected, "complete token fidelity matrix required")

    layer_evidence = {}
    for layer in layers:
        means = {}
        worst = {}
        violations = {}
        for width in WIDTHS:
            field = f"energy{width}_relative_l2"
            means[width] = statistics.fmean(
                lookup[sequence, rank, layer, position][field]
                for sequence in ("teacher-0", "teacher-1")
                for rank in range(4)
                for position in range(136)
            )
            ratios = []
            for sequence in ("teacher-0", "teacher-1"):
                for rank in range(4):
                    for window, positions in WINDOWS.items():
                        candidate = statistics.fmean(
                            lookup[sequence, rank, layer, position][field]
                            for position in positions
                        )
                        baseline = statistics.fmean(
                            lookup[sequence, rank, layer, position][
                                "energy64_relative_l2"
                            ]
                            for position in positions
                        )
                        ratios.append(
                            {
                                "sequence_id": sequence,
                                "rank": rank,
                                "window": window,
                                "ratio": candidate / max(baseline, 1e-6),
                            }
                        )
            worst[width] = max(item["ratio"] for item in ratios)
            violations[width] = sum(
                item["ratio"] > regression_limit for item in ratios
            )
        layer_evidence[layer] = {
            "means": means,
            "worst_window_ratio": worst,
            "violating_window_count": violations,
            "feasible_widths": [
                width for width in WIDTHS if worst[width] <= regression_limit
            ],
        }

    budget_limit = 64 * len(layers)
    states = {0: (0.0, ())}
    for layer in layers:
        next_states = {}
        for used, (error, assignment) in states.items():
            for width in layer_evidence[layer]["feasible_widths"]:
                new_used = used + width
                if new_used > budget_limit:
                    continue
                candidate = (
                    error + layer_evidence[layer]["means"][width],
                    assignment + ((layer, width),),
                )
                current = next_states.get(new_used)
                if current is None or candidate[0] < current[0] - 1e-15:
                    next_states[new_used] = candidate
        states = next_states
    require(states, "no allocation satisfies budget and local regression gates")
    used, (selected_error, assignment) = min(
        states.items(), key=lambda item: (item[1][0], item[0])
    )
    baseline_error = sum(layer_evidence[layer]["means"][64] for layer in layers)
    improvement = 1.0 - selected_error / max(baseline_error, 1e-12)
    selected_worst = max(
        layer_evidence[layer]["worst_window_ratio"][width]
        for layer, width in assignment
    )
    passed = (
        used <= budget_limit
        and improvement >= improvement_minimum
        and selected_worst <= regression_limit
    )
    return {
        "schema": "drrqr-layerwise-width-budget/v1",
        "decision": (
            "accept_equal_cost_layerwise_width_plan"
            if passed
            else "reject_equal_cost_layerwise_width_plan"
        ),
        "passed": passed,
        "claim_boundary": (
            "Captured-teacher local trajectory fidelity only; not endpoint "
            "performance, task accuracy, exact StrongRRQR, or portability proof."
        ),
        "layer_count": len(layers),
        "widths": list(WIDTHS),
        "budget_limit": budget_limit,
        "selected_budget": used,
        "regression_ratio_limit": regression_limit,
        "improvement_minimum": improvement_minimum,
        "uniform64_mean_relative_l2": baseline_error / len(layers),
        "selected_mean_relative_l2": selected_error / len(layers),
        "selected_improvement_fraction": improvement,
        "selected_worst_window_ratio": selected_worst,
        "assignment_counts": {
            str(width): Counter(width for _, width in assignment)[width]
            for width in WIDTHS
        },
        "assignment": [
            {"layer": layer, "head_k_dim": width}
            for layer, width in assignment
        ],
        "safe_layer_counts": {
            str(width): sum(
                width in layer_evidence[layer]["feasible_widths"]
                for layer in layers
            )
            for width in WIDTHS
        },
        "layers": {
            str(layer): {
                "mean_relative_l2": {
                    str(width): layer_evidence[layer]["means"][width]
                    for width in WIDTHS
                },
                "worst_window_ratio": {
                    str(width): layer_evidence[layer]["worst_window_ratio"][width]
                    for width in WIDTHS
                },
                "violating_window_count": {
                    str(width): layer_evidence[layer]["violating_window_count"][width]
                    for width in WIDTHS
                },
                "feasible_widths": layer_evidence[layer]["feasible_widths"],
            }
            for layer in layers
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width-report", type=Path, required=True)
    parser.add_argument("--width-report-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        args.width_report.is_file()
        and checksum(args.width_report) == args.width_report_sha256,
        "width report hash mismatch",
    )
    source = json.loads(args.width_report.read_text(encoding="utf-8"))
    require(
        source.get("schema") == REPORT_SCHEMA
        and source.get("status") == "width_curve_pass"
        and source.get("candidate_numerical_gate_passed") is True,
        "width report did not pass its complete numerical gate",
    )
    rows_path = Path(source["token_fidelity"]["path"])
    require(
        rows_path.is_file()
        and checksum(rows_path) == source["token_fidelity"]["sha256"],
        "token fidelity hash mismatch",
    )
    rows = json.loads(rows_path.read_text(encoding="utf-8"))
    layers = sorted({row["layer"] for row in rows})
    require(len(layers) == 48, "exactly 48 linear-attention layers required")
    report = analyze(rows, layers)
    report["source"] = {
        "width_report": str(args.width_report),
        "width_report_sha256": args.width_report_sha256,
        "token_fidelity": source["token_fidelity"],
    }
    require(not args.output.exists(), "fresh output path required")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": report["decision"],
        "output": str(args.output),
        "output_sha256": checksum(args.output),
        "selected_improvement_fraction": report["selected_improvement_fraction"],
        "assignment_counts": report["assignment_counts"],
        "safe_layer_counts": report["safe_layer_counts"],
    }))


if __name__ == "__main__":
    main()
