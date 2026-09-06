#!/usr/bin/env python3
"""Run the offline summarize -> quality -> decision pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(command: list[str], allowed: tuple[int, ...] = (0,)) -> int:
    result = subprocess.run(command, check=False)
    if result.returncode not in allowed:
        raise RuntimeError(
            f"command returned {result.returncode}, expected one of {allowed}: "
            + " ".join(command)
        )
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--performance-results", required=True, type=Path)
    parser.add_argument("--quality-results", required=True, type=Path)
    parser.add_argument(
        "--profile-evidence",
        type=Path,
        help="Production G1-versus-winning-candidate profile evidence manifest.",
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--noise-threshold-pp", type=float)
    parser.add_argument("--noise-evidence", type=Path)
    parser.add_argument(
        "--build-noise-evidence",
        action="store_true",
        help="Build production G1 noise evidence in output-dir from quality results.",
    )
    parser.add_argument("--minimum-improvement-percent", required=True, type=float)
    parser.add_argument("--expected-repetitions", type=int, default=3)
    parser.add_argument("--expected-models", type=int, default=2)
    parser.add_argument("--minimum-quality-models", type=int, default=2)
    parser.add_argument("--expected-dataset", action="append")
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    args.output_dir.mkdir(parents=True, exist_ok=True)
    performance = args.output_dir / "performance-summary.json"
    quality = args.output_dir / "quality-gate.json"
    decision_json = args.output_dir / "decision.json"
    decision_md = args.output_dir / "DECISION.md"
    profile_verification = args.output_dir / "profile-verification.json"
    python = sys.executable
    if args.fixture_mode and args.profile_evidence is not None:
        raise RuntimeError("--profile-evidence is production-only")
    if not args.fixture_mode and args.profile_evidence is None:
        raise RuntimeError("--profile-evidence is required outside fixture mode")
    if args.build_noise_evidence:
        if args.fixture_mode:
            raise RuntimeError(
                "--build-noise-evidence is production-only, not fixture mode"
            )
        if args.noise_evidence is not None:
            raise RuntimeError(
                "omit --noise-evidence when --build-noise-evidence is used"
            )
        if args.noise_threshold_pp is not None:
            raise RuntimeError(
                "omit --noise-threshold-pp when --build-noise-evidence is used"
            )
        noise_evidence = args.output_dir / "repeated-g1-noise-evidence.json"
        run(
            [
                python,
                str(here / "build_g1_noise_evidence.py"),
                "--quality-results",
                str(args.quality_results),
                "--output",
                str(noise_evidence),
                "--expected-repetitions",
                str(args.expected_repetitions),
                "--minimum-models",
                str(args.minimum_quality_models),
            ]
        )
    else:
        if args.noise_evidence is None:
            raise RuntimeError(
                "--noise-evidence is required unless --build-noise-evidence is used"
            )
        noise_evidence = args.noise_evidence
    try:
        noise_document = json.loads(noise_evidence.read_text(encoding="utf-8"))
        evidence_noise_threshold = float(noise_document["noise_threshold_pp"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read noise threshold from evidence: {exc}") from exc
    noise_threshold = (
        evidence_noise_threshold
        if args.noise_threshold_pp is None
        else args.noise_threshold_pp
    )

    run(
        [
            python,
            str(here / "summarize_ablation.py"),
            "--results",
            str(args.performance_results),
            "--output",
            str(performance),
            "--expected-repetitions",
            str(args.expected_repetitions),
            "--expected-models",
            str(args.expected_models),
            *(
                ["--fixture-mode"]
                if args.fixture_mode
                else []
            ),
        ]
    )
    run(
        [
            python,
            str(here / "evaluate_quality_gate.py"),
            "--results",
            str(args.quality_results),
            "--output",
            str(quality),
            "--noise-threshold-pp",
            str(noise_threshold),
            "--noise-evidence",
            str(noise_evidence),
            "--expected-repetitions",
            str(args.expected_repetitions),
            "--minimum-models",
            str(args.minimum_quality_models),
            *sum(
                (["--expected-dataset", value] for value in (args.expected_dataset or [])),
                [],
            ),
            *(["--fixture-mode"] if args.fixture_mode else []),
        ],
        allowed=(0, 2),
    )
    if args.profile_evidence is not None:
        run(
            [
                python,
                str(here / "verify_profile_evidence.py"),
                "--manifest",
                str(args.profile_evidence),
                "--output",
                str(profile_verification),
                "--minimum-models",
                str(args.expected_models),
            ]
        )
    decision_status = run(
        [
            python,
            str(here / "render_decision.py"),
            "--performance-summary",
            str(performance),
            "--quality-gate",
            str(quality),
            *(
                ["--profile-verification", str(profile_verification)]
                if args.profile_evidence is not None
                else []
            ),
            "--output-json",
            str(decision_json),
            "--output-md",
            str(decision_md),
            "--minimum-improvement-percent",
            str(args.minimum_improvement_percent),
        ],
        allowed=(0, 2),
    )
    decision = json.loads(decision_json.read_text(encoding="utf-8"))
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return decision_status


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
