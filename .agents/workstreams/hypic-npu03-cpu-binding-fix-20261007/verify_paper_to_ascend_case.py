#!/usr/bin/env python3
"""Read-only bounded replay for the main Paper-to-Ascend HYPIC case."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
SKILL_BLOB = "ad455c2d22d64eaff61384c23c39bd4693d15636"
REFERENCE_BLOB = "744b6daa280b14a90930b7be0c7a1055e9170935"
REGISTRY_BLOB = "2611864bbcf719d57920aae03ff9eb85521526b4"
PERFORMANCE = Path(
    "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/"
    "performance-independent-audit.json"
)
PERFORMANCE_SHA = (
    "de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1"
)
R12_SHA = "4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60"


def expect(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def command(*args: str, env: dict[str, str] | None = None,
            cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                          text=True, check=False)


def git(*args: str) -> str:
    result = command("git", *args)
    expect(result.returncode == 0, f"git {args!r}: {result.stderr}")
    return result.stdout.strip()


def main() -> int:
    expect(git("rev-parse", "origin/main") == MAIN,
           "locally tracked main moved; review the case again")
    for path, blob in (
        (".agents/skills/paper-to-ascend/SKILL.md", SKILL_BLOB),
        (".agents/skills/paper-to-ascend/references/"
         "qwen36-linear-hybrid-lessons.md", REFERENCE_BLOB),
        (".agents/skills.registry.yaml", REGISTRY_BLOB),
    ):
        expect(git("rev-parse", f"{MAIN}:{path}") == blob,
               f"main source changed: {path}")

    raw_performance = PERFORMANCE.read_bytes()
    expect(hashlib.sha256(raw_performance).hexdigest() == PERFORMANCE_SHA,
           "historical performance audit hash drifted")
    performance = json.loads(raw_performance)
    effect = performance["paper_effect"]
    expect(performance["all_six_units_valid"] is True and
           performance["normalized_serving_command_identical"] is True and
           performance["preregistered_paper_effect_gate_pass"] is True and
           performance["quality_decision"] == "not-measured" and
           abs(effect["tpot_saved_pct"] - 22.35616395806199) < 1e-8 and
           abs(effect["throughput_ratio"] - 1.4222905939342232) < 1e-9,
           "bounded historical performance state drifted")

    env = os.environ.copy()
    env["HYPIC_STRESS_AUDIT_CAMPAIGN"] = "cache10r12"
    audited = command(sys.executable, "-B",
                      str(HERE / "audit_cache10r11_stress.py"),
                      env=env, cwd=HERE)
    expect(audited.returncode == 2 and bool(audited.stdout.strip()),
           f"r12 strict audit did not retain its negative: {audited.stderr}")
    stress = json.loads(audited.stdout)
    expect(stress.get("reason") == "scored-request-hot-path-proof-missing"
           and stress.get("evidence_sha256") == R12_SHA
           and stress.get("samples") == 19
           and stress.get("scored_rows") == 57
           and stress.get("guard_samples") == 279
           and stress["diagnostic"]["four_worker_verified_requests"] == 52,
           "r12 raw stress evidence drifted")
    replay = command(sys.executable, "-B",
                     str(HERE / "analyze_cache10r12_fallbacks.py"),
                     cwd=HERE)
    expect(replay.returncode == 0, f"cold-path replay failed: {replay.stderr}")
    cold = json.loads(replay.stdout)
    expect(cold["four_worker_hot"] == 52
           and cold["scored"] == 57
           and cold["repeated_producer_segments"] == 4
           and list(cold["cold_reasons"].values()).count(
               "ready_cache_partial_chunk") == 1
           and cold["exact_cache_eviction_causality_proven"] is False,
           "cold-path cause boundary drifted")
    terminal_run = command(
        sys.executable, "-B",
        str(HERE / "verify_paper_to_ascend_reproduction_case.py"),
        cwd=HERE,
    )
    expect(terminal_run.returncode == 0 and bool(terminal_run.stdout.strip()),
           f"r13 terminal cross-skill replay failed: {terminal_run.stderr}")
    terminal = json.loads(terminal_run.stdout)
    expect(
        terminal["r13_quality_pair_complete"] is True
        and terminal["r13_correct"] == [230, 219]
        and terminal["r13_deployment_quality"] == "REJECT_OR_QUALIFY"
        and terminal["r13_strict_hot"] == [368, 381]
        and terminal["r13_performance_all_six_phases_valid"] is True
        and terminal["r13_performance_strict_hot"] == [120, 120]
        and abs(terminal["r13_performance_weighted_tpot_saved_pct"]
                - 21.524278158508903) < 1e-12
        and terminal["reproduction_skill_completion_gate_passed"] is False,
        "r13 paired quality/performance or adoption boundary drifted",
    )
    print(json.dumps({
        "schema": "paper-to-ascend-real-task-case/v1",
        "main": MAIN,
        "historical_performance_six_units_valid": True,
        "historical_tpot_reduction_percent": effect["tpot_saved_pct"],
        "r12_explicit_scored": 57,
        "r12_four_worker_hot": 52,
        "full_explicit_2048_quality_pair_complete": True,
        "current_matched_085_control_complete": True,
        "current_three_round_matched_performance_complete": True,
        "r13_deployment_quality": "REJECT_OR_QUALIFY",
        "r13_strict_quality_hot": [368, 381],
        "r13_performance_strict_hot": [120, 120],
        "r13_weighted_tpot_saved_pct":
            terminal["r13_performance_weighted_tpot_saved_pct"],
        "r13_terminal_mixed_experiment": True,
        "paper_c3_complete": False,
        "whole_paper_adoption_accepted": False,
        "long_term_acceptance": "partial-evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
