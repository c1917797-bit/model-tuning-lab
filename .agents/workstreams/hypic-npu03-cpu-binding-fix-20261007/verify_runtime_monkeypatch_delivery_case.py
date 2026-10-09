#!/usr/bin/env python3
"""Read-only bounded real-task replay; never promotes HYPIC delivery."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PLUGIN = Path("/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008")
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
PLUGIN_COMMIT = "c12060cd47e7575ead059983d7a8bb4704165c98"
SKILL_BLOB = "5ac9f8b07d8e092dcba7e1b0cfd5423469534666"
REFERENCE_BLOB = "302cf8cde20e7fda93b2972bbf1e5bab9fd81dde"
REGISTRY_BLOB = "2611864bbcf719d57920aae03ff9eb85521526b4"
SOURCE_BLOB = "53570af765c445b063d8ffe282032aee2de4ed45"
REGRESSION_BLOB = "f69a47ca8e5054bf7d3e4caa12d3a22c5a5750ac"
R12_EVIDENCE_SHA = "4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60"


def command(*args: str, cwd: Path = REPO,
            env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True,
                          capture_output=True, check=False)


def expect(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def git(*args: str, cwd: Path = REPO) -> str:
    result = command("git", *args, cwd=cwd)
    expect(result.returncode == 0, f"git {args!r}: {result.stderr}")
    return result.stdout.strip()


def main() -> int:
    expect(git("rev-parse", "origin/main") == MAIN,
           "locally tracked main changed; case needs re-review")
    for path, expected in (
        (".agents/skills/runtime-monkeypatch-delivery/SKILL.md", SKILL_BLOB),
        (".agents/skills/runtime-monkeypatch-delivery/references/delivery-contract.md",
         REFERENCE_BLOB),
        (".agents/skills.registry.yaml", REGISTRY_BLOB),
    ):
        expect(git("rev-parse", f"{MAIN}:{path}") == expected,
               f"main blob changed: {path}")
    missing_main_validator = not git(
        "ls-tree", "-r", "--name-only", MAIN,
        "scripts/validate_monkeypatch_package.py")
    expect(missing_main_validator, "main now has validator; update case")
    main_wrapper = git(
        "show", f"{MAIN}:.agents/skills/runtime-monkeypatch-delivery/"
                "assets/template/run_with_patch.sh")
    expect("export MODEL_TUNING_RUNTIME_PATCH_ENABLE=1" in main_wrapper,
           "main wrapper no longer forces treatment on; update case")
    expect((REPO / "scripts/validate_monkeypatch_package.py").is_file(),
           "branch validator absent")
    tests = command(
        sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
        "-p", "test_validate_monkeypatch_package.py")
    expect(tests.returncode == 0 and "Ran 7 tests" in tests.stderr,
           f"static validator regression failed: {tests.stderr}")

    expect(git("rev-parse", "HEAD", cwd=PLUGIN) == PLUGIN_COMMIT,
           "plugin source commit drift")
    expect(not git("status", "--porcelain", cwd=PLUGIN),
           "plugin worktree is dirty")
    for path, expected in (
        ("hypic_vllm_ascend/position_independent.py", SOURCE_BLOB),
        ("tests/test_evicted_directory_rebuild.py", REGRESSION_BLOB),
    ):
        expect(git("rev-parse", f"HEAD:{path}", cwd=PLUGIN) == expected,
               f"plugin source/test blob drift: {path}")
    expect(not git("ls-files", "*MANIFEST.json", cwd=PLUGIN),
           "plugin now contains a package manifest; update delivery case")

    env = os.environ.copy()
    env["HYPIC_STRESS_AUDIT_CAMPAIGN"] = "cache10r12"
    audited = command(sys.executable, "-B",
                      str(HERE / "audit_cache10r11_stress.py"),
                      cwd=HERE, env=env)
    expect(audited.returncode == 2 and bool(audited.stdout.strip()),
           f"r12 independent audit state drift: {audited.stderr}")
    result = json.loads(audited.stdout)
    expect(result.get("reason") == "scored-request-hot-path-proof-missing"
           and result.get("evidence_sha256") == R12_EVIDENCE_SHA
           and result.get("samples") == 19
           and result.get("scored_rows") == 57
           and result.get("guard_samples") == 279
           and result["diagnostic"]["four_worker_verified_requests"] == 52,
           "r12 bounded raw evidence drift")
    mapped = command(sys.executable, "-B",
                     str(HERE / "verify_ascend_source_map_case.py"))
    expect(mapped.returncode == 0, f"r13 live-source replay failed: {mapped.stderr}")
    source = json.loads(mapped.stdout.strip().splitlines()[-1])
    expect(source["plugin_commit"] == PLUGIN_COMMIT
           and source["r13_actual_bind_and_python_digest_verified"] is True,
           "r13 unpacked plugin source was not proven live")
    measured = command(sys.executable, "-B",
                       str(HERE / "verify_benchmark_evidence_r13_case.py"))
    expect(measured.returncode == 0,
           f"r13 matched quality/performance replay failed: {measured.stderr}")
    bounded = json.loads(measured.stdout.strip().splitlines()[-1])
    expect(bounded["quality_pair"] == "127x3 each arm, REJECT_OR_QUALIFY"
           and bounded["performance"] == "6/6 phases, EFFECT_SCREEN_PASS"
           and bounded["strict_quality_hot"] == "368/381 FAIL"
           and bounded["strict_performance_hot"] == "120/120 PASS"
           and bounded["full_skill_acceptance"] is False,
           "r13 unpacked A/B result or delivery boundary drift")
    case = json.loads((HERE / "skill-cases/runtime-monkeypatch-delivery.json").read_text())
    observed = case["observed"]
    expect(observed["r13_unpacked_plugin_same_identity_pair_complete"] is True
           and observed["r13_unpacked_plugin_performance_six_phases_complete"] is True
           and observed["r13_unpacked_plugin_quality_correct_baseline_candidate"] == [230, 219]
           and observed["r13_unpacked_plugin_quality_decision"] == "REJECT_OR_QUALIFY"
           and observed["plugin_manifest_package_present"] is False
           and observed["package_promotion_ready"] is False,
           "r13 bounded result was incorrectly promoted as a package")
    print(json.dumps({
        "schema": "runtime-monkeypatch-delivery-real-task-case/v1",
        "main": MAIN,
        "main_validator_missing": True,
        "main_wrapper_forces_treatment": True,
        "branch_static_validator_tests": 7,
        "plugin_source": PLUGIN_COMMIT,
        "r12_four_worker_hot": 52,
        "r12_scored": 57,
        "guard_samples": 279,
        "long_term_acceptance": "partial-evidence",
        "package_promotion_ready": False,
        "r13_unpacked_plugin_pair_measured": True,
        "r13_unpacked_plugin_quality": "REJECT_OR_QUALIFY",
        "r13_unpacked_plugin_performance": "EFFECT_SCREEN_PASS",
        "r13_not_hash_bound_manifest_package": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
