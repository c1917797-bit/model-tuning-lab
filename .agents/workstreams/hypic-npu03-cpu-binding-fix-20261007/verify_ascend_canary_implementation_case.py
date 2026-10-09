#!/usr/bin/env python3
"""Read-only real-weight HYPIC canary replay, deliberately bounded."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RAW = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
SOURCE = "3ad0967589304cd8fc4e7cff02f48ecc6125c89f"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def git(*args: str) -> str:
    result = subprocess.run(("git", *args), cwd=REPO, text=True,
                            capture_output=True, check=False)
    require(result.returncode == 0, result.stderr)
    return result.stdout.strip()


def checked(path: Path, digest: str) -> bytes:
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == digest, f"SHA drift: {path}")
    return data


def replay(script: str) -> dict:
    result = subprocess.run((sys.executable, "-B", str(HERE / script)),
                            cwd=REPO, text=True, capture_output=True,
                            check=False)
    require(result.returncode == 0, f"{script}: {result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def main() -> int:
    skill = ".agents/skills/ascend-canary-implementation/SKILL.md"
    require(git("rev-parse", "origin/main") == MAIN, "main moved")
    require(git("rev-parse", f"{MAIN}:{skill}") ==
            "07dceac8c65c9d1696d8e2fa5543d9b8784a7628", "main Skill drift")
    require(git("rev-parse", f"HEAD:{skill}") ==
            "07dceac8c65c9d1696d8e2fa5543d9b8784a7628", "branch Skill drift")
    require(git("rev-parse", f"{MAIN}:.agents/skills.registry.yaml") ==
            "2611864bbcf719d57920aae03ff9eb85521526b4", "registry drift")
    disabled = json.loads(checked(
        RAW / "quality-context-41984-hotpath-baseline/canary-result.json",
        "6093ae3468e06ba47e125ee28838911d33846c655b49bfdf64bfd9023f748912"))
    enabled = json.loads(checked(
        RAW / "quality-context-41984-hotpath-canary/canary-result.json",
        "f206085cbfb41f6a5446eb92a8963df3b30dbab6d8a8cbb0c872488bbd11b2e1"))
    for arm in (disabled, enabled):
        require(arm["error"] is None and arm["scored"]["finish_reason"] == "stop",
                "canary request did not complete")
        require(arm["sample_id"] == "66ebed525a08c7b9b35e1cb4"
                and arm["prompt_sha256"] ==
                "1d1f65e33f8c94fcc7d55873d68434871b61df479a10fab43a663395d251a7c0"
                and arm["boundary_token_ends"] == [16384, 24616]
                and arm["scored_max_output_tokens"] == 2048
                and arm["warm_requests"] == 2
                and arm["warm_worker_hot_pids"] == [],
                "matched canary identity drift")
        require(arm["fingerprint"]["source_commit"] == SOURCE
                and arm["fingerprint"]["physical_npus"] == [0, 1, 2, 3]
                and arm["fingerprint"]["image"] ==
                "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1",
                "source/image/lane drift")
        require(arm["scored"]["prediction"] == "A"
                and arm["reference"] == "B"
                and arm["scored"]["correct"] is False,
                "single-sample accuracy boundary drift")
        require(not arm["lane_guard"]["foreign"]
                and not arm["lane_guard"]["probe_errors"]
                and arm["service_stop"]["container_removed"]
                and arm["service_stop"]["owned_npus_released"]
                and arm["service_stop"]["port_released"],
                "canary isolation or release drift")
    require(disabled["scored_worker_hot_pids"] == []
            and not disabled["scored_hot_path_valid"],
            "disabled control emitted worker hot proof")
    require(enabled["scored_hot_path_valid"]
            and enabled["scored_worker_hot_pids"] == [263, 264, 265, 266]
            and enabled["scored_skipped_prefix_tokens"] == [16376] * 4
            and enabled["scored_event_counts"]["worker_hot_path"] == 4,
            "four-worker scored activation drift")
    root = RAW / "quality-context-41984-hotpath-canary/hypic-only"
    start = json.loads(checked(root / "service-start.json",
        "c1a3fcda6be4789efa37071da897e6dc4131496b90fbd04b5db7dfdcfffd2be9"))
    require(start["fingerprint"]["source_commit"] == SOURCE
            and list(start["worker_pid_by_physical_npu"]) == ["0", "1", "2", "3"],
            "HYPIC service source/worker map drift")
    npu = checked(root / "npu-smi-at-health.txt",
        "b95949f8f10dc682cb517423d4622a300fe9cffc57e74907e22be019b1c9dab3").decode()
    require(all(str(pid) in npu for pid in start["worker_pid_by_physical_npu"].values()),
            "actual physical worker evidence drift")
    log = checked(root / "service.full.834d255046be.log",
        "f1478862efca1cf9973877e62d45b73a410bf3d5d0b3f0635ef5ab4988be6c9b").decode()
    require(log.count("module=/opt/hypic/hypic_vllm_ascend/__init__.py") >= 6
            and "paper_missing=C3.1,C3.2,C3.3,C3.4,C3.5,C3.6" in log,
            "runtime import/C3 boundary drift")
    case = (HERE / "ASCEND_CANARY_IMPLEMENTATION_CASE_20261009.md").read_text()
    for phrase in ("Status: **partial-evidence**", "both incorrect",
                   "not aggregate correctness", "no independently retained",
                   "current-source small deterministic canary",
                   "REJECT_OR_QUALIFY"):
        require(phrase in case, f"case boundary absent: {phrase}")
    source = replay("verify_ascend_source_map_case.py")
    benchmark = replay("verify_benchmark_evidence_r13_case.py")
    require(source["r13_actual_bind_and_python_digest_verified"] is True
            and source["r13_full_2048_pair_complete"] is True
            and source["plugin_commit"] ==
                "c12060cd47e7575ead059983d7a8bb4704165c98",
            "current-source attestation or pair drift")
    require(benchmark["quality_pair"] ==
                "127x3 each arm, REJECT_OR_QUALIFY"
            and benchmark["performance"] ==
                "6/6 phases, EFFECT_SCREEN_PASS"
            and benchmark["strict_quality_hot"] == "368/381 FAIL",
            "bounded r13 mixed verdict drift")
    record = json.loads((HERE / "skill-cases/ascend-canary-implementation.json")
                        .read_text(encoding="utf-8"))
    observed = record["observed"]
    require(observed["historical_canary_both_correct"] is False
            and observed["current_candidate_c12060c_same_identity_full_pair_complete"] is True
            and observed["current_candidate_c12060c_small_deterministic_canary_pass"] is False
            and observed["full_2048_token_quality_pair_complete"] is True
            and observed["r13_quality_correct_baseline_candidate"] == [230, 219]
            and observed["r13_deployed_quality_decision"] == "REJECT_OR_QUALIFY"
            and observed["r13_strict_four_worker_hot_requests"] == [368, 381]
            and observed["r13_six_phase_performance_screen_pass"] is True
            and observed["canary_acceptance_to_scale"] is False
            and record["long_term_acceptance"] == "partial-evidence",
            "canary case conflates completed measurement with acceptance")
    print(json.dumps({"schema": "ascend-canary-implementation-real-task-case/v1",
        "historical_scored_worker_hot_pids": 4, "disabled_worker_hot_pids": 0,
        "both_scored_correct": False, "r13_full_pair_complete": True,
        "r13_quality_decision": "REJECT_OR_QUALIFY",
        "r13_performance_screen": "EFFECT_SCREEN_PASS",
        "current_small_canary_pass": False, "full_quality_accepted": False,
        "long_term_acceptance": "partial-evidence"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
