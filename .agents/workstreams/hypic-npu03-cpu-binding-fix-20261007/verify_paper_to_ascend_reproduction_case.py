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
    print(json.dumps({
        "schema": "paper-to-ascend-reproduction-real-task-case/v1",
        "main": MAIN,
        "branch_skill_differs_from_main": True,
        "historical_performance_units": 6,
        "natural_quality_units": 12,
        "natural_quality_worker_hot_pids": 0,
        "r12_scored": 57,
        "r12_four_worker_hot": 52,
        "reproduction_skill_completion_gate_passed": False,
        "long_term_acceptance": "partial-evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
