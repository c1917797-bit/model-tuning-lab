#!/usr/bin/env python3
"""Replay the isolated real-task transformation acceptance fixture."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
DEFAULT_FIXTURE = HERE / "skill-fixtures" / "repository-transformation" / "target"
EXPECTED_CORE = {
    "mst-repo-onboarding",
    "mst-repo-transformation",
    "mst-agentsmd-authoring",
    "mst-skill-tree-design",
    "mst-transformation-verification",
    "mst-skill-governor",
}


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    root = args.fixture.resolve()
    snapshot = json.loads((root.parent / "input-snapshot.json").read_text())
    require(snapshot["misplaced_runtime_skill"].startswith(".agents/skills/"),
            "input does not exercise runtime separation")

    agents = (root / "AGENTS.md").read_text()
    require(len(agents.splitlines()) <= 60, "AGENTS.md exceeds 60 lines")
    for needle in ("repository maintainer", ".agents/skills.registry.yaml",
                   ".agents/skills/**/SKILL.md", "runtime-skills/**"):
        require(needle in agents, f"AGENTS.md missing {needle}")
    require((root / "CLAUDE.md").read_text() == "@AGENTS.md\n",
            "CLAUDE.md is not an exact thin shim")

    registry = yaml.safe_load((root / ".agents/skills.registry.yaml").read_text())
    require(registry["authority"] == "AGENTS.md", "wrong authority")
    require(registry["selection"]["strategy"] == "smallest-relevant-set",
            "wrong selection strategy")
    entries = registry["skills"]
    ids = [item["id"] for item in entries]
    require(len(ids) == len(set(ids)), "duplicate Skill IDs")
    require(EXPECTED_CORE <= set(ids), "default transformation tree incomplete")
    require("mst-runtime-skill-boundary" in ids,
            "runtime boundary Skill not added for observed need")
    for item in entries:
        require(all(item.get(key) for key in
                    ("id", "path", "status", "purpose", "triggers", "scope")),
                f"incomplete registry entry: {item.get('id')}")
        skill_path = root / item["path"] / "SKILL.md"
        require(skill_path.is_file(), f"missing {skill_path}")
        text = skill_path.read_text()
        require(len(text.splitlines()) <= 120, f"{item['id']} exceeds 120 lines")
        require(text.startswith("---\n"), f"{item['id']} lacks frontmatter")
        require(f"name: {item['id']}" in text, f"{item['id']} name mismatch")
        require("description:" in text and "## Purpose" in text
                and "## Workflow" in text,
                f"{item['id']} lacks required behavioral sections")

    misplaced = root / ".agents/skills/customer-helper"
    require(not misplaced.exists(), "runtime Skill remains under maintainer tree")
    runtime_registry = yaml.safe_load(
        (root / "runtime-skills/registry.yaml").read_text())
    runtime = runtime_registry["skills"][0]
    runtime_skill = root / runtime["path"] / "SKILL.md"
    require(runtime_skill.is_file(), "runtime Skill missing")
    require(runtime["visibility"] == "tenant"
            and runtime["permissions"] == ["catalog.read"],
            "runtime visibility/permissions not explicit")
    runtime_text = runtime_skill.read_text()
    require(".agents/" not in runtime_text and "govern maintainers" in runtime_text,
            "runtime Skill claims or references maintainer governance")
    policy = yaml.safe_load(
        (root / "runtime-skills/publish-policy.yaml").read_text())
    require(policy["default"] == "deny"
            and policy["allowed"][0]["safety_review"] == "required",
            "publish policy is not deny-by-default with review")

    governance = json.loads(
        (root / ".agents/governance-record.json").read_text())
    require(governance["reusable"] is True
            and governance["registry_updated"] is True
            and governance["replayable_verification_added"] is True,
            "Skill governance decision is not evidenced")

    app = root / "src/app.py"
    subprocess.run(("python3", "-m", "py_compile", str(app)), check=True)
    output = subprocess.check_output(("python3", str(app)), text=True).strip()
    require(output == "ok", "retained product behavior failed")
    print(json.dumps({
        "schema": "mst-transformation-suite-result/v1",
        "fixture": str(root),
        "maintainer_skills": len(ids),
        "agents_lines": len(agents.splitlines()),
        "thin_adapter": True,
        "runtime_boundary": True,
        "governance_record": True,
        "product_health": output,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
