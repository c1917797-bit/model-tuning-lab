#!/usr/bin/env python3
"""Read-only HYPIC reproduction-case replay; never promotes paper success."""

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
SKILL_PATH = ".agents/skills/paper-to-ascend-reproduction/SKILL.md"
MAIN_SKILL_BLOB = "d0298d9fdf1ce7ba27f1bd711d26834b6bd7b6aa"
BRANCH_SKILL_BLOB = "90fd7d45e7b0630c81c2a0c3694c46e4995131dc"
BRANCH_SKILL_WORKTREE_SHA256 = (
    "c77a108f89367cb1987fcc3493d2f5ba22c573089ffa3f1a8e3a64c2e11aab34"
)
REFERENCE_BLOB = "582852d43b5550594da257b1a274a84103542411"
REGISTRY_BLOB = "2611864bbcf719d57920aae03ff9eb85521526b4"
ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
PERFORMANCE = ROOT / "performance-independent-audit.json"
PERFORMANCE_SHA = (
    "de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1"
)
NATURAL_QUALITY = (
    ROOT / "quality-context-41984-clean2/quality-natural-scope-audit.json"
)
NATURAL_QUALITY_SHA = (
    "61bcccd926459b8ee57cfc3860a5b30c581c7e7b525fe3b746b52146c2c0dbf0"
)
R12_SHA = "4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60"
R13_QUALITY = ROOT / "hotpath-quality-cache10r13-dual-audit.json"
R13_QUALITY_SHA = (
    "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b"
)
R13_MATCHED_PERFORMANCE = ROOT / "hotpath-cache10r13-matched-performance-audit.json"
R13_MATCHED_PERFORMANCE_SHA = (
    "d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062"
)
R13_PERF_RETRY3_ROOT = ROOT / (
    "performance-context-41984-hotpath-cache10perf-"
    "hypic-only-repeat3-retry3"
)
R13_PERF_RETRY3_RECEIPTS = {
    "contract.json": "4b5f052f3d593ae3f18809cc4abc536e5a8010f8dd651e059427a9db17fa6430",
    "arm-result.json": "b5dc3cbf3b5bdb2ef5339c38a176018e0f1c422b819c8ae96a96b3138a56e989",
    "hypic-only/lane-guard.json": "71ab16271c01749770fb34c4131b495a838dc24426d6bebb68db97d33e4909f2",
    "hypic-only/pre-health-release.json": "6243302a434aa93f614e977a539278d0a4782676c1c198d7a3ba36ffaf07664a",
}
R13_PERF_RETRY4_ROOT = ROOT / (
    "performance-context-41984-hotpath-cache10perf-"
    "hypic-only-repeat3-retry4"
)
R13_PERF_RETRY4_RECEIPTS = {
    "contract.json": "ea583f6e41ed38f76766def75d2592c1812e2220338115c89677211b6e3f22e9",
    "arm-result.json": "5a93ce9402e9ae20c6370cae16f32c1674e57867bd477b33241f7190cd6bc88d",
    "performance.json": "323ced3b25c2e0ac1bfaed2f69e3dbfe369a9617f0d0d6488b9fe5fb2a4e13a5",
    "benchmark-command.json": "f0b54998e4077f3c7a56f90ffad629279d91ff74cd3d411e975a547cbbd2e8ae",
    "hypic-only/lane-guard.json": "0551cda9bcdf0a9394a55ed777241610b75a0e89924fd2df26c818b9bb177480",
    "hypic-only/service-stop.json": "0d8c3b4bf4be2d3761df618e66fdc4edc3f291f58ef4d64f2748dd5a1b8bfec3",
    "hypic-only/source-attestation.json": "6a1bd87df57ee2665f578a80291fd388232ef6cd1a5fa975295382474baba2a2",
    "hypic-only/hypic-evidence.jsonl": "1bac011528b752a4d8a804caca20c9725c933827e68b857e5e0220dc39a70155",
}
R13_PERF_RETRY5_ROOT = ROOT / (
    "performance-context-41984-hotpath-cache10perf-"
    "hypic-only-repeat3-retry5"
)
R13_PERF_RETRY5_RECEIPTS = {
    "contract.json": "8a1020814dad5ea91520fb44c161137a2b7212d36e65a1c294f100c096a96057",
    "hypic-only/lane-guard.json": "24d9e1f91596214903a95d9fe8b7ff91562a8fc5411eedd63a3e7845c9e8ce87",
    "hypic-only/hypic-evidence.jsonl": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}
R13_PERF_RETRY14_ROOT = ROOT / (
    "performance-context-41984-hotpath-cache10perf-"
    "hypic-only-repeat3-retry14"
)
R13_PERF_RETRY14_RECEIPTS = {
    "contract.json": "b260e81ab4f766ee1b5ee3c485d5d3f993dfdbb4ba8733dff339700616dd2c2a",
    "arm-result.json": "8438fbd58b4be0c06412667c57442e7340e5dc08d1d7889a059f736113eaae0a",
    "hypic-only/lane-guard.json": "71f8ece8c31869544653661b26c9f520ed6a7a8210b93c2c4b79dfa8ad89b0ed",
    "hypic-only/pre-health-release.json": "7afb397349d54ce1c19725bcd5e22523d84ac3e9d3d44cb8ed8222439e7ffc09",
    "hypic-only/hypic-evidence.jsonl": "fb3f7f0f342b3738e637ecb517d90dc5b2f603ddc3ce0978dbb6a8cc6c9389be",
}
R13_PERF_RETRY19_ROOT = ROOT / (
    "performance-context-41984-hotpath-cache10perf-"
    "hypic-only-repeat3-retry19"
)
R13_PERF_RETRY19_RECEIPTS = {
    "contract.json": "fe59917a8ddf62cb538e7a5e9ef30d63d2eae8d14fd5f3798a495211d303b8f9",
    "arm-result.json": "25cce108c805d785d4ac01b092990bafced2a3409667cdf1fa2813d572d78506",
    "hypic-only/lane-guard.json": "f4d59b8e9553aa1b526af1e3d6b9e03d5e9a6b90cb9175c9f14f1958eeee91e5",
    "hypic-only/pre-health-release.json": "e938b1a0e99c76d281bf781909bc4392b853f3af424c3a33f925f54125ae59e7",
    "hypic-only/hypic-evidence.jsonl": "9df31bb84fa849c581e7815390e9e120b8fcb2ff2152050463b1c9db9ad15ffd",
}
R13_PERF_RETRY20_ROOT = ROOT / (
    "performance-context-41984-hotpath-cache10perf-"
    "hypic-only-repeat3-retry20"
)
R13_PERF_RETRY20_RECEIPTS = {
    "contract.json": "58ab99d5742582a6e66b256844324742480dc882bff77edf91910711796c750f",
    "arm-result.json": "8a5c6cdbda2344615dae10f14e10bfcc36924c6b567004311aebcdb4a58f9046",
    "hypic-only/lane-guard.json": "4efe09fe5750e112356e6029fad68e712358f993f9474bd58035720492b72690",
    "hypic-only/pre-health-release.json": "c184f1d0af692b0b93b3deaef12cc4a49c3269f0dae66141d522ef11a6135576",
    "hypic-only/hypic-evidence.jsonl": "7c94c68175fa496a766ca9c5670787c0680a81bcc1798b29f0ed01ab9f51ba59",
}


def expect(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def command(*args: str, env: dict[str, str] | None = None,
            cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True,
                          capture_output=True, check=False)


def git(*args: str) -> str:
    result = command("git", *args)
    expect(result.returncode == 0, f"git {args!r}: {result.stderr}")
    return result.stdout.strip()


def hashed_json(path: Path, sha256: str) -> dict:
    raw = path.read_bytes()
    expect(hashlib.sha256(raw).hexdigest() == sha256,
           f"raw audit hash drifted: {path}")
    return json.loads(raw)


def classify_r13_quality(audit: dict) -> dict:
    baseline = audit["baseline"]
    candidate = audit["candidate"]
    quality = audit["all_request_quality"]
    hot = audit["strict_c1_c2_hot_coverage"]
    complete = (
        audit["evidence_valid"] is True
        and baseline["scored_rows"] == 381
        and candidate["scored_rows"] == 381
        and len(quality["baseline_run_correct"]) == 3
        and len(quality["candidate_run_correct"]) == 3
        and audit["scope"].startswith("LongBench-v2 127x3")
    )
    return {
        "quality_pair_complete": complete,
        "deployment_quality_decision": audit["deployed_quality_decision"],
        "baseline_correct": baseline["correct"],
        "candidate_correct": candidate["correct"],
        "quality_delta_pp": quality["delta_pp"],
        "strict_hot_proven": hot["four_worker_verified_scored_requests"],
        "strict_hot_expected": hot["expected_scored_requests"],
        "strict_hot_decision": audit["strict_quality_decision"],
        "performance_measured": audit["performance_decision"] != "not-measured",
    }


def main() -> int:
    expect(git("rev-parse", "origin/main") == MAIN,
           "locally tracked main changed; review case again")
    for path, blob in (
        (SKILL_PATH, MAIN_SKILL_BLOB),
        (".agents/skills/paper-to-ascend-reproduction/references/"
         "evidence-contract.md", REFERENCE_BLOB),
        (".agents/skills.registry.yaml", REGISTRY_BLOB),
    ):
        expect(git("rev-parse", f"{MAIN}:{path}") == blob,
               f"main Skill context changed: {path}")
    expect(git("rev-parse", f"HEAD:{SKILL_PATH}") == BRANCH_SKILL_BLOB
           and BRANCH_SKILL_BLOB != MAIN_SKILL_BLOB,
           "branch Skill version boundary changed")
    expect(hashlib.sha256((REPO / SKILL_PATH).read_bytes()).hexdigest()
           == BRANCH_SKILL_WORKTREE_SHA256,
           "branch Skill follow-up worktree revision changed")

    perf = hashed_json(PERFORMANCE, PERFORMANCE_SHA)
    expect(perf["all_six_units_valid"] is True
           and perf["normalized_serving_command_identical"] is True
           and perf["preregistered_paper_effect_gate_pass"] is True
           and perf["quality_decision"] == "not-measured"
           and abs(perf["paper_effect"]["tpot_saved_pct"]
                   - 22.35616395806199) < 1e-8,
           "historical six-unit performance scope drifted")
    quality = hashed_json(NATURAL_QUALITY, NATURAL_QUALITY_SHA)
    expect(quality["all_twelve_rows_and_receipts_valid"] is True
           and quality["paired_and_repeated_input_identity_valid"] is True
           and quality["only_arm_variable"] ==
           {"VLLM_ASCEND_HYPIC_ENABLE": ["0", "1"]}
           and quality["formal_acceptance_claim"] is False
           and quality["activation"]["formal_hotpath_gate_pass"] is False
           and quality["activation"]["distinct_worker_hot_pids"] == []
           and quality["service"]["hypic-only"]["release"]["port_released"]
           is True,
           "natural quality must remain a bounded activation negative")

    env = os.environ.copy()
    env["HYPIC_STRESS_AUDIT_CAMPAIGN"] = "cache10r12"
    audited = command(sys.executable, "-B",
                      str(HERE / "audit_cache10r11_stress.py"),
                      env=env, cwd=HERE)
    expect(audited.returncode == 2 and bool(audited.stdout.strip()),
           f"r12 strict audit drifted: {audited.stderr}")
    stress = json.loads(audited.stdout)
    expect(stress.get("reason") == "scored-request-hot-path-proof-missing"
           and stress.get("evidence_sha256") == R12_SHA
           and stress.get("samples") == 19
           and stress.get("scored_rows") == 57
           and stress.get("guard_samples") == 279
           and stress["diagnostic"]["four_worker_verified_requests"] == 52,
           "explicit-segment r12 boundary drifted")
    r13 = hashed_json(R13_QUALITY, R13_QUALITY_SHA)
    r13_result = classify_r13_quality(r13)
    expect(r13_result["quality_pair_complete"] is True
           and r13_result["deployment_quality_decision"] == "REJECT_OR_QUALIFY"
           and r13_result["baseline_correct"] == 230
           and r13_result["candidate_correct"] == 219
           and abs(r13_result["quality_delta_pp"] - (-2.8871391076115485))
           < 1e-12
           and r13_result["strict_hot_proven"] == 368
           and r13_result["strict_hot_expected"] == 381
           and r13_result["strict_hot_decision"] == "NOT_ACCEPTED_HOT_COVERAGE"
           and r13_result["performance_measured"] is False,
           "r13 must preserve completed negative deployment quality separately "
           "from incomplete strict mechanism coverage and unmeasured performance")
    r13_performance = hashed_json(
        R13_MATCHED_PERFORMANCE, R13_MATCHED_PERFORMANCE_SHA
    )
    expect(
        r13_performance["all_six_phases_valid"] is True
        and r13_performance["normalized_spec_identical"] is True
        and r13_performance["deployed_effect_screen_pass"] is True
        and r13_performance["strict_c1_c2_hot_coverage"]["decision"] == "PASS"
        and r13_performance["strict_c1_c2_hot_coverage"][
            "four_worker_verified_measured_requests"
        ] == 120
        and r13_performance["strict_c1_c2_performance_decision"]
        == "EFFECT_SCREEN_PASS"
        and r13_performance["deployed_quality_decision"] == "REJECT_OR_QUALIFY"
        and r13_performance["strict_quality_decision"]
        == "NOT_ACCEPTED_HOT_COVERAGE"
        and abs(
            r13_performance["effect"]["weighted_tpot_saved_pct"]
            - 21.524278158508903
        ) < 1e-12,
        "r13 six-phase performance or separate quality boundary drifted",
    )
    retry3_files = {
        name: hashed_json(R13_PERF_RETRY3_ROOT / name, digest)
        for name, digest in R13_PERF_RETRY3_RECEIPTS.items()
    }
    retry3_contract = retry3_files["contract.json"]
    retry3_result = retry3_files["arm-result.json"]
    retry3_guard = retry3_files["hypic-only/lane-guard.json"]
    retry3_release = retry3_files["hypic-only/pre-health-release.json"]
    expect(retry3_contract["arm"] == "hypic-only"
           and retry3_contract["phase"] == "repeat3"
           and retry3_contract["fingerprint"]["physical_npus"] == [0, 1, 2, 3]
           and retry3_contract["fingerprint"]["source_commit"] ==
           "c12060cd47e7575ead059983d7a8bb4704165c98",
           "retry3 frozen identity drifted")
    expect(retry3_result["valid"] is False
           and retry3_result["metrics"] is None
           and retry3_result["performance_sha256"] is None
           and retry3_result["phase"] == "repeat3",
           "retry3 must remain a pre-measurement environmental failure")
    expected_foreign = {
        "physical_npu": 3,
        "pid": 2731002,
        "container_id": "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6",
    }
    expect(retry3_guard["samples"] == 20
           and retry3_guard["probe_errors"] == []
           and len(retry3_guard["foreign"]) == 2
           and all(item["processes"] == [expected_foreign]
                   for item in retry3_guard["foreign"]),
           "retry3 physical-lane conflict evidence drifted")
    expect(retry3_release["container_removed"] is True
           and retry3_release["container_id"] == retry3_result["container_id"]
           and retry3_release["worker_release_proven"] is False
           and not (R13_PERF_RETRY3_ROOT / "hypic-only/service-start.json").exists()
           and not (R13_PERF_RETRY3_ROOT / "hypic-only/benchmark-command.json").exists()
           and not (R13_PERF_RETRY3_ROOT / "hypic-only/performance.json").exists(),
           "retry3 exact release or zero-measurement boundary drifted")
    retry4_files = {
        name: hashed_json(R13_PERF_RETRY4_ROOT / name, digest)
        for name, digest in R13_PERF_RETRY4_RECEIPTS.items()
        if name.endswith(".json")
    }
    retry4_evidence_path = R13_PERF_RETRY4_ROOT / "hypic-only/hypic-evidence.jsonl"
    expect(hashlib.sha256(retry4_evidence_path.read_bytes()).hexdigest()
           == R13_PERF_RETRY4_RECEIPTS["hypic-only/hypic-evidence.jsonl"],
           "retry4 HYPIC event evidence hash drifted")
    retry4_contract = retry4_files["contract.json"]
    retry4_result = retry4_files["arm-result.json"]
    retry4_perf = retry4_files["performance.json"]
    retry4_command = retry4_files["benchmark-command.json"]
    retry4_guard = retry4_files["hypic-only/lane-guard.json"]
    retry4_start = hashed_json(
        R13_PERF_RETRY4_ROOT / "hypic-only/service-start.json",
        "28c6e2acd3215c7ee0bf30a3e486860645244bed994d9e1fa01c87d5ae28376a",
    )
    retry4_release = retry4_files["hypic-only/service-stop.json"]
    retry4_attestation = retry4_files["hypic-only/source-attestation.json"]
    expect(retry4_contract["arm"] == "hypic-only"
           and retry4_contract["phase"] == "repeat3"
           and retry4_contract["order_index"] == 5
           and retry4_contract["quality_audit_sha256"] == R13_QUALITY_SHA
           and retry4_contract["fingerprint"]["source_commit"] ==
           "c12060cd47e7575ead059983d7a8bb4704165c98"
           and retry4_contract["fingerprint"]["physical_npus"] == [0, 1, 2, 3]
           and retry4_contract["benchmark_config"]["requests"] == 40
           and retry4_contract["benchmark_config"]["output_tokens"] == 1024,
           "retry4 frozen phase identity drifted")
    expect(retry4_start["fingerprint"] == retry4_contract["fingerprint"]
           and retry4_start["container_id"] == retry4_result["container_id"]
           and retry4_start["worker_pid_by_physical_npu"].keys() == {"0", "1", "2", "3"}
           and retry4_attestation["selected_source_commit"] ==
           "c12060cd47e7575ead059983d7a8bb4704165c98"
           and retry4_attestation["container_id"] == retry4_result["container_id"],
           "retry4 physical worker or source identity drifted")
    retry4_rows = retry4_perf["results"]
    retry4_ok = [row for row in retry4_rows if row.get("ok")]
    retry4_failed = [row for row in retry4_rows if not row.get("ok")]
    expect(retry4_result["valid"] is False
           and retry4_result["metrics"] is None
           and retry4_result["performance_sha256"] ==
           R13_PERF_RETRY4_RECEIPTS["performance.json"]
           and len(retry4_rows) == 40 and len(retry4_ok) == 16
           and len(retry4_failed) == 24
           and sum(row.get("output_tokens") == 1024 for row in retry4_ok) == 15
           and all("Connection refused" in str(row.get("error"))
                   for row in retry4_failed),
           "retry4 partial benchmark rows no longer match environmental stop")
    foreign4 = {
        "physical_npu": 1,
        "pid": 3079008,
        "container_id": "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6",
    }
    expect(retry4_guard["samples"] == 120
           and retry4_guard["probe_errors"] == []
           and len(retry4_guard["foreign"]) == 2
           and all(item["processes"] == [foreign4]
                   for item in retry4_guard["foreign"]),
           "retry4 actual foreign physical-NPU1 process evidence drifted")
    expect(retry4_release["container_removed"] is True
           and retry4_release["owned_npus_released"] is True
           and retry4_release["port_released"] is True
           and retry4_release["service_reached_health"] is True
           and retry4_release["container_id"] == retry4_result["container_id"],
           "retry4 exact owned-resource release evidence drifted")
    retry5_files = {
        name: hashed_json(R13_PERF_RETRY5_ROOT / name, digest)
        for name, digest in R13_PERF_RETRY5_RECEIPTS.items()
        if name.endswith(".json")
    }
    retry5_evidence_path = R13_PERF_RETRY5_ROOT / "hypic-only/hypic-evidence.jsonl"
    expect(hashlib.sha256(retry5_evidence_path.read_bytes()).hexdigest()
           == R13_PERF_RETRY5_RECEIPTS["hypic-only/hypic-evidence.jsonl"],
           "retry5 HYPIC event evidence hash drifted")
    retry5_contract = retry5_files["contract.json"]
    retry5_guard = retry5_files["hypic-only/lane-guard.json"]
    retry5_foreign = {
        "physical_npu": 0,
        "pid": 3539167,
        "container_id": "87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa",
    }
    expect(retry5_contract["arm"] == "hypic-only"
           and retry5_contract["phase"] == "repeat3"
           and retry5_contract["order_index"] == 5
           and retry5_contract["quality_audit_sha256"] == R13_QUALITY_SHA
           and retry5_contract["fingerprint"]["physical_npus"] == [0, 1, 2, 3]
           and retry5_contract["fingerprint"]["source_commit"] ==
           "c12060cd47e7575ead059983d7a8bb4704165c98"
           and retry5_contract["benchmark_config"]["requests"] == 40,
           "retry5 frozen phase identity drifted")
    expect(retry5_guard["attempt"] ==
           "hotpath-cache10perf-hypic-only-repeat3-retry5"
           and retry5_guard["samples"] == 2
           and retry5_guard["probe_errors"] == []
           and retry5_guard["foreign"] == [{
               "at_utc": "2026-10-09T10:36:02.322155+00:00",
               "processes": [retry5_foreign],
           }]
           and retry5_guard["owned_container_id"] ==
           "eec7c5ef562cd446364c6b021c1e0c70f1988362c8d5c108db3c4dab5091ca5f"
           and retry5_evidence_path.stat().st_size == 0
           and not (R13_PERF_RETRY5_ROOT / "performance.json").exists()
           and not (R13_PERF_RETRY5_ROOT / "arm-result.json").exists(),
           "retry5 must remain a two-sample foreign-lane pre-measurement failure")
    retry14_files = {
        name: hashed_json(R13_PERF_RETRY14_ROOT / name, digest)
        for name, digest in R13_PERF_RETRY14_RECEIPTS.items()
        if name.endswith(".json")
    }
    retry14_evidence_path = R13_PERF_RETRY14_ROOT / "hypic-only/hypic-evidence.jsonl"
    retry14_events = [json.loads(line) for line in retry14_evidence_path.read_text().splitlines()]
    expect(hashlib.sha256(retry14_evidence_path.read_bytes()).hexdigest()
           == R13_PERF_RETRY14_RECEIPTS["hypic-only/hypic-evidence.jsonl"],
           "retry14 HYPIC event evidence hash drifted")
    retry14_contract = retry14_files["contract.json"]
    retry14_result = retry14_files["arm-result.json"]
    retry14_guard = retry14_files["hypic-only/lane-guard.json"]
    retry14_release = retry14_files["hypic-only/pre-health-release.json"]
    retry14_foreign = {
        "physical_npu": 1,
        "pid": 242978,
        "container_id": "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6",
    }
    expect(retry14_contract["arm"] == "hypic-only"
           and retry14_contract["phase"] == "repeat3"
           and retry14_contract["order_index"] == 5
           and retry14_contract["quality_audit_sha256"] == R13_QUALITY_SHA
           and retry14_contract["fingerprint"]["physical_npus"] == [0, 1, 2, 3]
           and retry14_contract["fingerprint"]["source_commit"] ==
           "c12060cd47e7575ead059983d7a8bb4704165c98"
           and retry14_contract["benchmark_config"]["requests"] == 40
           and retry14_contract["benchmark_config"]["output_tokens"] == 1024,
           "retry14 frozen phase identity drifted")
    expect(retry14_result["valid"] is False
           and retry14_result["metrics"] is None
           and retry14_result["performance_sha256"] is None
           and retry14_result["container_id"] == retry14_guard["owned_container_id"]
           and retry14_result["container_id"] == retry14_release["container_id"]
           and retry14_guard["attempt"] ==
           "hotpath-cache10perf-hypic-only-repeat3-retry14"
           and retry14_guard["samples"] == 18
           and retry14_guard["probe_errors"] == []
           and len(retry14_guard["foreign"]) == 2
           and all(item["processes"] == [retry14_foreign]
                   for item in retry14_guard["foreign"])
           and [event["event"] for event in retry14_events] == [
               "plugin_build_active", "hypic_capability_contract",
               "hypic_upstream_parity_contract", "material_cache_configured",
           ]
           and retry14_events[1]["paper_complete"] is False
           and retry14_events[1]["paper_missing_ids"] == [
               "C3.1", "C3.2", "C3.3", "C3.4", "C3.5", "C3.6",
           ]
           and retry14_release["container_removed"] is True
           and retry14_release["worker_release_proven"] is False
           and not (R13_PERF_RETRY14_ROOT / "performance.json").exists()
           and not (R13_PERF_RETRY14_ROOT / "hypic-only/service-start.json").exists()
           and not (R13_PERF_RETRY14_ROOT / "hypic-only/benchmark-command.json").exists(),
            "retry14 must remain an 18-sample foreign-lane pre-health failure")
    retry19_files = {
        name: hashed_json(R13_PERF_RETRY19_ROOT / name, digest)
        for name, digest in R13_PERF_RETRY19_RECEIPTS.items()
        if name.endswith(".json")
    }
    retry20_files = {
        name: hashed_json(R13_PERF_RETRY20_ROOT / name, digest)
        for name, digest in R13_PERF_RETRY20_RECEIPTS.items()
        if name.endswith(".json")
    }
    retry19_result = retry19_files["arm-result.json"]
    retry19_guard = retry19_files["hypic-only/lane-guard.json"]
    retry19_release = retry19_files["hypic-only/pre-health-release.json"]
    retry20_result = retry20_files["arm-result.json"]
    retry20_guard = retry20_files["hypic-only/lane-guard.json"]
    retry20_release = retry20_files["hypic-only/pre-health-release.json"]
    retry19_foreign = {
        "physical_npu": 2,
        "pid": 1731309,
        "container_id": "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6",
    }
    retry20_foreign = {
        "physical_npu": 3,
        "pid": 1890601,
        "container_id": "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6",
    }
    for attempt_result, guard, release, expected, samples in (
        (retry19_result, retry19_guard, retry19_release, retry19_foreign, 46),
        (retry20_result, retry20_guard, retry20_release, retry20_foreign, 36),
    ):
        captured = [
            process
            for event in guard["foreign"]
            for process in event["processes"]
        ]
        expect(attempt_result["valid"] is False
               and attempt_result["metrics"] is None
               and attempt_result["performance_sha256"] is None
               and attempt_result["phase"] == "repeat3"
               and guard["samples"] == samples
               and guard["probe_errors"] == []
               and expected in captured
               and guard["owned_container_id"] == attempt_result["container_id"]
               and release["container_id"] == attempt_result["container_id"]
               and release["container_removed"] is True
               and release["worker_release_proven"] is False,
               "environmental retry must remain zero-metric with exact owned cleanup")
    for attempt_root in (R13_PERF_RETRY19_ROOT, R13_PERF_RETRY20_ROOT):
        expect(not (attempt_root / "hypic-only/service-start.json").exists()
               and not (attempt_root / "hypic-only/benchmark-command.json").exists()
               and not (attempt_root / "hypic-only/performance.json").exists(),
               "environmental retry unexpectedly contains scored performance artifacts")
    case = json.loads((HERE / "skill-cases/paper-to-ascend-reproduction.json").read_text())
    expect(case["r13_performance_retry4"]["classification"] ==
           "environmental mid-run isolation failure; not a HYPIC performance result"
           and case["r13_performance_retry4"]["successful_responses"] == 16
           and case["r13_performance_retry4"]["connection_refusals"] == 24
           and case["external_raw_receipts"]["r13_performance_retry4_arm_result_sha256"] ==
           R13_PERF_RETRY4_RECEIPTS["arm-result.json"],
           "retry4 Skill case diverges from the audited raw receipts")
    expect(case["r13_performance_retry5"]["classification"] ==
           "environmental pre-measurement isolation failure; not a HYPIC performance verdict"
           and case["r13_performance_retry5"]["benchmark_rows"] == 0
           and case["r13_performance_retry5"]["foreign_pid"] == retry5_foreign["pid"]
           and case["external_raw_receipts"]["r13_performance_retry5_guard_sha256"] ==
           R13_PERF_RETRY5_RECEIPTS["hypic-only/lane-guard.json"],
           "retry5 Skill case diverges from the audited raw receipts")
    expect(case["r13_performance_retry14"]["classification"] ==
           "environmental pre-health isolation failure; not a HYPIC performance result"
           and case["r13_performance_retry14"]["benchmark_rows"] == 0
           and case["r13_performance_retry14"]["foreign_pid"] == retry14_foreign["pid"]
           and case["external_raw_receipts"]["r13_performance_retry14_guard_sha256"] ==
           R13_PERF_RETRY14_RECEIPTS["hypic-only/lane-guard.json"]
            and case["external_raw_receipts"]["r13_performance_retry14_audit_sha256"] ==
            "362a8c5708584bd726003aa0825190b4b9c69eb2879d9673baf90f176e3394af",
            "retry14 Skill case diverges from the audited raw receipts")
    expect(case["retry19_followup"]["foreign_pid"] == retry19_foreign["pid"]
           and case["retry19_followup"]["guard_samples"] == 46
           and case["retry19_followup"]["scored_requests"] == 0
           and case["retry19_followup"]["exact_owned_container_removed"] is True
           and case["external_raw_receipts"]["retry19_arm_result_sha256"] ==
           R13_PERF_RETRY19_RECEIPTS["arm-result.json"]
           and case["retry20_followup"]["foreign_pid"] == retry20_foreign["pid"]
           and case["retry20_followup"]["foreign_physical_npu"] == 3
           and case["retry20_followup"]["guard_samples"] == 36
           and case["retry20_followup"]["scored_requests"] == 0
           and case["retry20_followup"]["exact_owned_container_removed"] is True
           and case["external_raw_receipts"]["retry20_arm_result_sha256"] ==
           R13_PERF_RETRY20_RECEIPTS["arm-result.json"],
           "retry19/retry20 environmental case diverges from immutable receipts")
    expect(
        case["observed"]["current_three_round_matched_performance_complete"] is True
        and case["r13_dual_lens_result"]["performance_decision"]
        == "EFFECT_SCREEN_PASS"
        and case["retry21_followup"]["scored_requests"] == 40
        and case["retry21_followup"]["four_worker_verified_scored_requests"] == 40
        and case["retry21_followup"]["guard_samples"] == 164
        and case["retry21_followup"]["exact_owned_container_removed"] is True
        and case["external_raw_receipts"][
            "r13_matched_performance_audit_sha256"
        ] == R13_MATCHED_PERFORMANCE_SHA,
        "retry21 or six-phase terminal Skill case diverges from immutable receipts",
    )
    print(json.dumps({
        "schema": "paper-to-ascend-reproduction-real-task-case/v1",
        "main": MAIN,
        "branch_skill_differs_from_main": True,
        "branch_skill_worktree_sha256": BRANCH_SKILL_WORKTREE_SHA256,
        "historical_performance_units": 6,
        "natural_quality_units": 12,
        "natural_quality_worker_hot_pids": 0,
        "r12_scored": 57,
        "r12_four_worker_hot": 52,
        "r13_quality_pair_complete": r13_result["quality_pair_complete"],
        "r13_deployment_quality": r13_result["deployment_quality_decision"],
        "r13_correct": [
            r13_result["baseline_correct"],
            r13_result["candidate_correct"],
        ],
        "r13_delta_pp": r13_result["quality_delta_pp"],
        "r13_strict_hot": [
            r13_result["strict_hot_proven"],
            r13_result["strict_hot_expected"],
        ],
        "r13_strict_hot_decision": r13_result["strict_hot_decision"],
        "r13_performance_measured": True,
        "r13_performance_all_six_phases_valid": True,
        "r13_performance_strict_hot": [120, 120],
        "r13_performance_weighted_tpot_saved_pct":
            r13_performance["effect"]["weighted_tpot_saved_pct"],
        "r13_performance_ttft_p95_saved_s":
            r13_performance["effect"]["ttft_p95_saved_s"],
        "r13_performance_retry3": "environmental-pre-health-failure",
        "r13_performance_retry3_foreign_device": expected_foreign["physical_npu"],
        "r13_performance_retry3_benchmark_rows": 0,
        "r13_performance_retry3_owned_container_removed": True,
        "r13_performance_retry4": "environmental-mid-run-invalid",
        "r13_performance_retry4_foreign_device": foreign4["physical_npu"],
        "r13_performance_retry4_foreign_pid": foreign4["pid"],
        "r13_performance_retry4_rows": [len(retry4_ok), len(retry4_failed)],
        "r13_performance_retry4_owned_container_removed": True,
        "r13_performance_retry5": "environmental-pre-measurement-failure",
        "r13_performance_retry5_foreign_device": retry5_foreign["physical_npu"],
        "r13_performance_retry5_foreign_pid": retry5_foreign["pid"],
        "r13_performance_retry5_guard_samples": retry5_guard["samples"],
        "r13_performance_retry5_benchmark_rows": 0,
        "r13_performance_retry5_owned_container_removed": True,
        "r13_performance_retry14": "environmental-pre-health-failure",
        "r13_performance_retry14_foreign_device": retry14_foreign["physical_npu"],
        "r13_performance_retry14_foreign_pid": retry14_foreign["pid"],
        "r13_performance_retry14_guard_samples": retry14_guard["samples"],
        "r13_performance_retry14_benchmark_rows": 0,
        "r13_performance_retry14_startup_events": len(retry14_events),
        "r13_performance_retry14_owned_container_removed": True,
        "r13_performance_retry19": "environmental-pre-health-failure",
        "r13_performance_retry19_foreign_device": retry19_foreign["physical_npu"],
        "r13_performance_retry19_foreign_pid": retry19_foreign["pid"],
        "r13_performance_retry19_guard_samples": retry19_guard["samples"],
        "r13_performance_retry19_benchmark_rows": 0,
        "r13_performance_retry19_owned_container_removed": True,
        "r13_performance_retry20": "environmental-pre-health-failure",
        "r13_performance_retry20_foreign_device": retry20_foreign["physical_npu"],
        "r13_performance_retry20_foreign_pid": retry20_foreign["pid"],
        "r13_performance_retry20_guard_samples": retry20_guard["samples"],
        "r13_performance_retry20_benchmark_rows": 0,
        "r13_performance_retry20_owned_container_removed": True,
        "reproduction_skill_completion_gate_passed": False,
        "long_term_acceptance": "partial-evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
