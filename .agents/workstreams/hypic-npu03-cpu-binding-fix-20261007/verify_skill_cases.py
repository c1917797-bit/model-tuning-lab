#!/usr/bin/env python3
"""Verify retained per-Skill case provenance; never infer behavioral success."""

from __future__ import annotations

import collections
import hashlib
import json
import subprocess
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CASES = HERE / "skill-cases"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=REPO, text=True).strip()


def evidence_path(value: str) -> Path:
    path = (REPO / value).resolve()
    try:
        path.relative_to(REPO.resolve())
    except ValueError as exc:
        raise RuntimeError(f"evidence path escapes repository: {value}") from exc
    require(path.is_file(), f"evidence file absent: {value}")
    return path


def check_case(path: Path, main: str, known: set[str]) -> tuple[str, str]:
    case = json.loads(path.read_text(encoding="utf-8"))
    skill = case["skill"]
    require(case["schema"] == "mst-real-task-skill-case/v1"
            and skill in known and path.stem == skill,
            f"case identity invalid: {path}")
    require(case["reviewed_current_main_commit"] == main,
            f"{skill}: main moved; case needs new review")
    tested = case["tested_main_commit"]
    require(git("rev-parse", f"{tested}:.agents/skills/{skill}/SKILL.md")
            == case["tested_skill_git_blob_oid"],
            f"{skill}: tested Skill blob drift")
    require(git("rev-parse", f"{tested}:.agents/skills.registry.yaml")
            == case["tested_registry_git_blob_oid"],
            f"{skill}: tested registry blob drift")
    if case["current_skill_and_registry_blobs_unchanged"]:
        require(git("rev-parse", f"{main}:.agents/skills/{skill}/SKILL.md")
                == case["tested_skill_git_blob_oid"]
                and git("rev-parse", f"{main}:.agents/skills.registry.yaml")
                == case["tested_registry_git_blob_oid"],
                f"{skill}: current main blob changed")
    require(case["evidence"], f"{skill}: evidence list empty")
    for item in case["evidence"]:
        actual = hashlib.sha256(evidence_path(item["path"]).read_bytes()).hexdigest()
        require(actual == item["sha256"], f"{skill}: evidence SHA256 drift")
    state = case["long_term_acceptance"]
    require(state in {"verified", "partial-evidence", "not-run"},
            f"{skill}: unknown acceptance state")
    if state == "verified":
        require(case["replayable_regression_recorded"] is True
                and case.get("behavioral_evidence_verified") is True,
                f"{skill}: cannot assert verified without replayable behavior proof")
    return skill, state


def main() -> int:
    main_commit = git("rev-parse", "origin/main")
    registry = yaml.safe_load(git("show", f"{main_commit}:.agents/skills.registry.yaml"))
    names = [item["id"] for item in registry["skills"]]
    require(len(names) == len(set(names)), "main registry has duplicate IDs")
    reviewed: dict[str, str] = {}
    for path in sorted(CASES.glob("*.json")):
        skill, state = check_case(path, main_commit, set(names))
        require(skill not in reviewed, f"duplicate case: {skill}")
        reviewed[skill] = state
    missing = sorted(set(names) - reviewed.keys())
    print(json.dumps({
        "main_commit": main_commit,
        "registered_skills": len(names),
        "cases_with_verified_provenance": len(reviewed),
        "case_acceptance": dict(collections.Counter(reviewed.values())),
        "skills_without_case": len(missing),
        "missing_skill_ids": missing,
        "behavioral_acceptance_not_inferred_from_structure": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
