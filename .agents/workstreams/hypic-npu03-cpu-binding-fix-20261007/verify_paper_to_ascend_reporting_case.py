#!/usr/bin/env python3
"""Read-only replay of the HYPIC reporting case; never infers a final report."""

from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def git(*args: str) -> str:
    result = subprocess.run(("git", *args), cwd=REPO, text=True,
                            capture_output=True, check=False)
    require(result.returncode == 0, result.stderr)
    return result.stdout.strip()


def checked_bytes(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected,
            f"SHA256 drift: {path}")
    return raw


def audit_report_receipt_hashes(report: str, receipts: dict[str, str]) -> None:
    """Bind each labelled report digest to its raw file, not just any substring."""
    for label, expected in receipts.items():
        matches = re.findall(r"\b" + re.escape(label) + r"\s+`([0-9a-f]+)`", report)
        require(len(matches) == 1 and matches[0] == expected
                and re.fullmatch(r"[0-9a-f]{64}", matches[0]) is not None,
                f"report receipt hash mismatch: {label}")


def audit_decode_report_receipts() -> None:
    raw = ROOT / "profiler-hypic-hotcold-20261009-r6"
    files = {
        "contract": raw / "decode/contract.json",
        "capture": raw / "decode/capture.json",
        "artifact inventory": raw / "decode/artifact-audit.json",
        "guard": raw / "hypic-only-decode/lane-guard.json",
        "release": raw / "decode/release.json",
        "result": raw / "decode/result.json",
    }
    audit_report_receipt_hashes(
        (HERE / "HYPIC_PROFILER_DECODE_AUDIT_20261009.md").read_text(),
        {label: hashlib.sha256(path.read_bytes()).hexdigest()
         for label, path in files.items()})


def audit_terminal_report(quality: dict, performance: dict) -> None:
    audit_decode_report_receipts()
    report = (HERE / "HYPIC_R13_TERMINAL_NEGATIVE_REPORT_20261009.md").read_text()
    for required in (
        "final negative result for the frozen r13 C1/C2 experiment",
        "Step 0. 环境准备", "Step 1–3. 分组", "实测结果",
        "与论文及同事历史结果分开比较", "Decision 与结论",
        "报错、失败尝试与排除", "证据索引与精确交接",
        "REJECT_OR_QUALIFY", "NOT_ACCEPTED_HOT_COVERAGE",
        "EFFECT_SCREEN_PASS", "C3", "GSM8K",
        "16/40", "46/47", "retry6", "逐字节可重建性仍有边界",
        "不重新拉起服务",
    ):
        require(required in report, f"terminal report section/limit absent: {required}")
    for placeholder in ("TBD", "TODO", "待补充", "<measured>", "<hash>"):
        require(placeholder not in report, f"terminal report placeholder: {placeholder}")
    require(quality["evidence_valid"] is True
            and quality["deployed_quality_decision"] == "REJECT_OR_QUALIFY"
            and quality["strict_c1_c2_hot_coverage"]["four_worker_verified_scored_requests"] == 368
            and quality["strict_c1_c2_hot_coverage"]["expected_scored_requests"] == 381
            and quality["all_request_quality"]["baseline_run_correct"] == [77, 74, 79]
            and quality["all_request_quality"]["candidate_run_correct"] == [69, 73, 77],
            "terminal report quality source drift")
    q = quality["all_request_quality"]
    require(f"G1 {q['baseline_correct']}/381" in report
            and f"G2 {q['candidate_correct']}/381" in report
            and f"{q['delta_pp']:.4f}" in report
            and f"G1 `{','.join(map(str, q['baseline_run_correct']))}`" in report
            and f"G2 `{','.join(map(str, q['candidate_run_correct']))}`" in report,
            "terminal report quality arithmetic mismatch")
    require(performance["all_six_phases_valid"] is True
            and performance["strict_c1_c2_hot_coverage"]
                ["four_worker_verified_measured_requests"] == 120
            and performance["deployed_quality_decision"] == "REJECT_OR_QUALIFY",
            "terminal report performance source drift")
    phase_rows = [
        ("screen", "G1", "no-cache", 0, 160),
        ("screen", "G2", "hypic-only", 0, 150),
        ("repeat2", "G2", "hypic-only", 1, 150),
        ("repeat2", "G1", "no-cache", 1, 162),
        ("repeat3", "G1", "no-cache", 2, 164),
        ("repeat3/retry21", "G2", "hypic-only", 2, 164),
    ]
    for phase, group, arm, index, guard in phase_rows:
        row = performance["per_arm"][arm][index]
        expected = (
            f"| {phase} | {group} | {row['tpot_weighted_ms']:.6f}"
            f" | {row['tpot_p95_ms']:.6f} | {row['ttft_p95_ms']:.6f}"
            f" | {row['output_tokens_per_second']:.6f}"
            f" | {row['benchmark_duration_s']:.6f} | {guard} |"
        )
        require(expected in report, f"terminal report phase row mismatch: {arm}/{phase}")
    for arm, group in (("no-cache", "G1"), ("hypic-only", "G2")):
        tpot = [row["tpot_weighted_ms"] for row in performance["per_arm"][arm]]
        require(f"{statistics.mean(tpot):.6f} ± {statistics.stdev(tpot):.6f}"
                in report, f"terminal report {group} TPOT dispersion mismatch")
    effect = performance["effect"]
    require(f"{effect['weighted_tpot_saved_pct']:.4f}%" in report
            and f"{effect['weighted_tpot_saved_ms']:.6f}" in report
            and f"{effect['ttft_p95_saved_s']:.6f}" in report
            and f"{effect['throughput_ratio']:.6f}" in report,
            "terminal report effect arithmetic mismatch")
    for digest in (
        "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b",
        "d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062",
        "d2169d9b36561aa59c1fdcded08df9c98f7fee6a145e7aca1290986c1a92a687",
    ):
        require(digest in report, f"terminal report evidence index missing: {digest}")


def main() -> int:
    require(git("rev-parse", "origin/main") == MAIN, "main moved")
    for path, blob in (
        (".agents/skills/paper-to-ascend-reporting/SKILL.md",
         "7902b3f9c96ebd6b77a35b328333ad3834fe4a9f"),
        (".agents/skills/paper-to-ascend-reporting/references/report-template.md",
         "40582e499b5589893524df3b74aabfeebe040f8c"),
        (".agents/skills.registry.yaml",
         "2611864bbcf719d57920aae03ff9eb85521526b4"),
    ):
        require(git("rev-parse", f"{MAIN}:{path}") == blob,
                f"main reporting contract drift: {path}")

    performance = json.loads(checked_bytes(
        ROOT / "performance-independent-audit.json",
        "de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1"))
    require(performance["all_six_units_valid"] is True
            and performance["quality_decision"] == "not-measured"
            and abs(performance["paper_effect"]["tpot_saved_pct"]
                    - 22.35616395806199) < 1e-8,
            "historical performance attribution drift")
    natural = json.loads(checked_bytes(
        ROOT / "quality-context-41984-clean2/quality-natural-scope-audit.json",
        "61bcccd926459b8ee57cfc3860a5b30c581c7e7b525fe3b746b52146c2c0dbf0"))
    require(natural["all_twelve_rows_and_receipts_valid"] is True
            and natural["formal_acceptance_claim"] is False
            and natural["activation"]["distinct_worker_hot_pids"] == [],
            "natural quality scope drift")

    env = os.environ.copy()
    env["HYPIC_STRESS_AUDIT_CAMPAIGN"] = "cache10r12"
    result = subprocess.run(
        (sys.executable, "-B", str(HERE / "audit_cache10r11_stress.py")),
        cwd=HERE, env=env, text=True, capture_output=True, check=False)
    require(result.returncode == 2 and bool(result.stdout.strip()),
            f"r12 independent audit did not reach expected negative gate: {result.stderr}")
    r12 = json.loads(result.stdout)
    require(r12["reason"] == "scored-request-hot-path-proof-missing"
            and r12["evidence_sha256"] ==
            "4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60"
            and r12["scored_rows"] == 57
            and r12["diagnostic"]["four_worker_verified_requests"] == 52
            and r12["guard_samples"] == 279,
            "r12 strict activation/isolation boundary drift")

    terminal_run = subprocess.run(
        (sys.executable, "-B", str(HERE / "verify_paper_to_ascend_reproduction_case.py")),
        cwd=HERE, text=True, capture_output=True, check=False)
    require(terminal_run.returncode == 0 and bool(terminal_run.stdout.strip()),
            f"r13 terminal replay failed: {terminal_run.stderr}")
    terminal = json.loads(terminal_run.stdout)
    require(terminal["r13_quality_pair_complete"] is True
            and terminal["r13_correct"] == [230, 219]
            and terminal["r13_deployment_quality"] == "REJECT_OR_QUALIFY"
            and terminal["r13_strict_hot"] == [368, 381]
            and terminal["r13_performance_all_six_phases_valid"] is True
            and terminal["r13_performance_strict_hot"] == [120, 120]
            and abs(terminal["r13_performance_weighted_tpot_saved_pct"]
                    - 21.524278158508903) < 1e-12
            and terminal["reproduction_skill_completion_gate_passed"] is False,
            "r13 quality/performance reporting boundary drift")
    current_quality = json.loads(checked_bytes(
        ROOT / "hotpath-quality-cache10r13-dual-audit.json",
        "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b"))
    current_performance = json.loads(checked_bytes(
        ROOT / "hotpath-cache10r13-matched-performance-audit.json",
        "d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062"))
    audit_terminal_report(current_quality, current_performance)
    for name in ("verify_hypic_profiler_prefill.py",
                 "verify_hypic_profiler_decode.py"):
        profile = subprocess.run(
            (sys.executable, "-B", str(HERE / name)), cwd=HERE,
            text=True, capture_output=True, check=False)
        require(profile.returncode == 0,
                f"{name} independent replay failed: {profile.stderr}")

    report = (HERE / "PAPER_TO_ASCEND_REPORTING_CASE_20261009.md").read_text()
    for required in ("Status: **progress / partial-evidence**",
                     "Historical measured r12", "Current r13 addendum",
                     "Historical same-lane reference",
                     "Historical natural-task reference", "Paper claim",
                     "not measured", "no no-cache arm",
                     "final-report completion gate", "REJECT_OR_QUALIFY",
                     "120/120", "Forbidden:"):
        require(required in report, f"report boundary absent: {required}")
    print(json.dumps({
        "schema": "paper-to-ascend-reporting-real-task-case/v1",
        "historical_performance_units": 6,
        "historical_natural_quality_units": 12,
        "r12_scored": 57,
        "r12_four_worker_hot": 52,
        "current_matched_quality_pair": True,
        "current_matched_performance_six_phases": True,
        "current_matched_baseline_treatment_profile": False,
        "bounded_terminal_negative_report_replay_valid": True,
        "final_report_ready": False,
        "long_term_acceptance": "partial-evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
