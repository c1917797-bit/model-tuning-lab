#!/usr/bin/env python3
"""Verify that each pinned main Skill has exactly one current-campaign status."""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
from pathlib import Path

import yaml

DEFAULT_MATRIX = Path(__file__).with_name("SKILL_VERIFICATION.md")
REGISTRY_PATH = ".agents/skills.registry.yaml"


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--registry-ref", default="origin/main")
    args = parser.parse_args()
    document = args.matrix.read_text(encoding="utf-8")
    pinned = re.search(r"origin/main at ([0-9a-f]{40})", document)
    if pinned is None or git("rev-parse", args.registry_ref) != pinned.group(1):
        raise RuntimeError("matrix main-commit pin is absent or stale; refresh main and re-audit")
    registry = yaml.safe_load(git("show", f"{args.registry_ref}:{REGISTRY_PATH}"))
    ids = [entry["id"] for entry in registry["skills"]]
    if len(ids) != len(set(ids)):
        raise RuntimeError("main registry has duplicate Skill IDs")
    rows = []
    for line in document.splitlines():
        if not line.startswith("| "):
            continue
        fields = [field.strip() for field in line.strip().strip("|").split("|")]
        if len(fields) >= 4 and fields[2] in ("V", "P", "N"):
            rows.append((fields[0], fields[2]))
    names = [name for name, _ in rows]
    if len(names) != len(set(names)) or set(names) != set(ids):
        raise RuntimeError("current Skill matrix has missing, duplicate or extra IDs")
    counts = collections.Counter(code for _, code in rows)
    stated = re.search(r"Current bounded-workflow status: (\d+) V, (\d+) P, (\d+) N = (\d+)", document)
    if stated is None:
        raise RuntimeError("current Skill count declaration is absent")
    declared = tuple(int(value) for value in stated.groups())
    actual = (counts["V"], counts["P"], counts["N"], len(rows))
    if actual != declared:
        raise RuntimeError(f"declared current status count {declared} != actual {actual}")
    changed_bodies = sorted(
        name for name in ids
        if git("rev-parse", f"{args.registry_ref}:.agents/skills/{name}/SKILL.md")
        != git("rev-parse", f"HEAD:.agents/skills/{name}/SKILL.md")
    )
    current_v = {name for name, code in rows if code == "V"}
    changed_v = sorted(current_v.intersection(changed_bodies))
    main_registry_blob = git("rev-parse", f"{args.registry_ref}:{REGISTRY_PATH}")
    branch_registry_blob = git("rev-parse", f"HEAD:{REGISTRY_PATH}")
    print(json.dumps({"main_commit": pinned.group(1), "skills": len(ids),
                      "current_status": dict(counts), "names_match": True,
                      "branch_modified_main_skill_bodies": changed_bodies,
                      "branch_modified_bounded_v": changed_v,
                      "branch_registry_differs_from_main":
                          branch_registry_blob != main_registry_blob},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
