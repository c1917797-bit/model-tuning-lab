#!/usr/bin/env python3
"""Combine performance statistics and quality gates into a scoped decision."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


TREATMENTS = ("G2", "G3", "G4")
EXPECTED_METRICS = {
    "ttft_ms",
    "tpot_ms",
    "ott_ms",
    "throughput_tps",
    "batch_delay_ms",
}


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8") as stream:
        stream.write(content)
    os.replace(temp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--performance-summary", required=True, type=Path)
    parser.add_argument("--quality-gate", required=True, type=Path)
    parser.add_argument("--profile-verification", type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument(
        "--minimum-improvement-percent",
        type=float,
        default=0.0,
        help="Required average improvement for every reported performance metric.",
    )
    args = parser.parse_args()
    if (
        not math.isfinite(args.minimum_improvement_percent)
        or args.minimum_improvement_percent < 0
    ):
        raise ValueError(
            "--minimum-improvement-percent must be finite and non-negative"
        )

    performance = load(args.performance_summary)
    quality = load(args.quality_gate)
    profile = (
        load(args.profile_verification)
        if args.profile_verification is not None
        else None
    )
    blockers = []
    if not performance.get("valid"):
        blockers.append("performance summary is invalid")
    if not quality.get("passed"):
        blockers.append("quality gate did not pass")
    performance_fixture = bool(performance.get("fixture_mode"))
    quality_fixture = bool(quality.get("fixture_mode"))
    if performance_fixture != quality_fixture:
        blockers.append("performance and quality fixture modes differ")
    elif not performance_fixture:
        performance_bindings = performance.get("global_bindings")
        quality_bindings = quality.get("global_bindings")
        if (
            not isinstance(performance_bindings, dict)
            or not isinstance(quality_bindings, dict)
            or performance_bindings != quality_bindings
        ):
            blockers.append(
                "performance and quality frozen/config/treatment bindings differ"
            )
        if (
            performance.get("service_config_bindings")
            != quality.get("service_config_bindings")
        ):
            blockers.append(
                "performance and quality service-config bindings differ"
            )
        if (
            performance.get("checkpoint_manifest_bindings")
            != quality.get("checkpoint_manifest_bindings")
        ):
            blockers.append(
                "performance and quality checkpoint-manifest bindings differ"
            )
        if profile is None:
            blockers.append("production decision requires profile verification")
        else:
            if not profile.get("valid"):
                blockers.append("profile verification is invalid")
            if profile.get("global_bindings") != performance_bindings:
                blockers.append(
                    "profile and performance frozen/config/treatment bindings differ"
                )
    elif profile is not None:
        blockers.append("fixture decisions must not consume production profile evidence")

    improvements: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for cell in performance.get("cells", []):
        group = cell.get("group")
        if group not in TREATMENTS:
            continue
        for metric, value in cell.get(
            "relative_improvement_percent_vs_G1", {}
        ).items():
            improvements[group][metric].append(float(value))

    averages = {}
    for group in TREATMENTS:
        averages[group] = {
            metric: sum(values) / len(values)
            for metric, values in sorted(improvements[group].items())
            if values
        }
        if not averages[group]:
            blockers.append(f"{group} has no comparable performance metrics")

    metric_names = sorted(
        set().union(*(set(metrics) for metrics in averages.values()))
    )
    worst_case_improvements = {
        group: {
            metric: min(values)
            for metric, values in sorted(improvements[group].items())
            if values
        }
        for group in TREATMENTS
    }
    if set(performance.get("required_metrics", [])) != EXPECTED_METRICS:
        blockers.append("performance summary required-metric contract is invalid")
    if set(metric_names) != EXPECTED_METRICS:
        blockers.append(
            "performance evidence does not contain the exact TTFT/TPOT/OTT/"
            "throughput/batch-delay metric set"
        )
    for group in TREATMENTS:
        missing = sorted(set(metric_names) - set(averages[group]))
        if missing:
            blockers.append(f"{group} missing metrics: {', '.join(missing)}")

    non_dominated = []
    local_threshold_failures = []
    if not blockers and metric_names:
        for candidate in TREATMENTS:
            dominates_all = True
            for other in TREATMENTS:
                if other == candidate:
                    continue
                if not all(
                    averages[candidate][metric] >= averages[other][metric]
                    for metric in metric_names
                ):
                    dominates_all = False
                    break
            average_threshold_passed = all(
                averages[candidate][metric]
                >= args.minimum_improvement_percent
                for metric in metric_names
            )
            local_threshold_passed = all(
                value >= args.minimum_improvement_percent
                for metric in metric_names
                for value in improvements[candidate][metric]
            )
            if dominates_all and average_threshold_passed and local_threshold_passed:
                non_dominated.append(candidate)
            elif dominates_all and average_threshold_passed:
                failed = {
                    metric: worst_case_improvements[candidate][metric]
                    for metric in metric_names
                    if worst_case_improvements[candidate][metric]
                    < args.minimum_improvement_percent
                }
                local_threshold_failures.append(
                    f"{candidate} has local cell improvements below threshold: "
                    + ", ".join(
                        f"{metric}={value:.4f}%"
                        for metric, value in failed.items()
                    )
                )
    blockers.extend(local_threshold_failures)
    if len(non_dominated) != 1:
        blockers.append(
            "no unique all-metric winner"
            if not non_dominated
            else "multiple tied all-metric winners"
        )

    recommended = non_dominated[0] if len(non_dominated) == 1 else None
    decision = "adopt" if recommended and not blockers else "iterate"
    model_count = len(
        {cell.get("model") for cell in performance.get("cells", [])}
    )
    dataset_count = len(
        {cell.get("dataset") for cell in performance.get("cells", [])}
    )
    performance_scope = {
        (str(cell.get("model")), str(cell.get("dataset")))
        for cell in performance.get("cells", [])
    }
    quality_scope = {
        (str(item.get("model")), str(item.get("dataset")))
        for item in quality.get("decisions", [])
    }
    if performance_scope != quality_scope:
        blockers.append("performance and quality model/dataset scopes differ")
    if performance.get("expected_models", 0) < 2 or model_count < 2:
        blockers.append("fewer than two models in the generalization evidence")
    performance_models = {
        str(cell.get("model")) for cell in performance.get("cells", [])
    }
    if not performance_fixture and profile is not None:
        if set(map(str, profile.get("models", []))) != performance_models:
            blockers.append("profile and performance model scopes differ")
        if recommended is not None and profile.get("candidate_group") != recommended:
            blockers.append(
                "profile candidate does not match the unique performance winner"
            )
    if blockers:
        recommended = None
        decision = "iterate"
    if decision == "adopt":
        metric_text = ", ".join(
            f"{metric} {value:+.2f}%"
            for metric, value in averages[recommended].items()
        )
        conclusion = (
            f"{recommended} is the unique all-metric winner versus G1 "
            f"({metric_text}); {quality['allowed_claim']} "
            f"({dataset_count} datasets, {model_count} models)."
        )
    else:
        conclusion = (
            "No adoption recommendation. Resolve: " + "; ".join(blockers)
        )

    report = {
        "schema": "paper-to-ascend-decision-render/v1",
        "decision": decision,
        "recommended_group": recommended if decision == "adopt" else None,
        "average_improvement_percent_vs_G1": averages,
        "worst_case_improvement_percent_vs_G1": worst_case_improvements,
        "minimum_improvement_percent": args.minimum_improvement_percent,
        "model_count": model_count,
        "dataset_count": dataset_count,
        "quality_claim": quality.get("allowed_claim"),
        "fixture_mode": performance_fixture and quality_fixture,
        "global_bindings": (
            performance.get("global_bindings")
            if not performance_fixture and not quality_fixture
            else None
        ),
        "profile_verification": (
            {
                "candidate_group": profile.get("candidate_group"),
                "manifest_sha256": profile.get("manifest_sha256"),
                "target_region_improvement_percent": profile.get(
                    "target_region_improvement_percent"
                ),
            }
            if profile is not None
            else None
        ),
        "blockers": blockers,
        "conclusion": conclusion,
    }
    atomic_write(
        args.output_json,
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    )
    markdown = (
        "# Paper-to-Ascend Decision\n\n"
        f"- Decision: {decision}\n"
        f"- Recommended group: {report['recommended_group']}\n"
        f"- Models: {model_count}\n"
        f"- Datasets: {dataset_count}\n\n"
        f"{conclusion}\n"
    )
    atomic_write(args.output_md, markdown)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if decision == "adopt" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
