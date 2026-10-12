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


ALLOWED_STATUSES = {"stable", "experimental", "deprecated", "retired"}


def verify_registry_contract(root: Path) -> int:
    """Check every maintainer registry, including unexpected component trees."""
    registries = sorted(root.rglob(".agents/skills.registry.yaml"))
    require(root / ".agents/skills.registry.yaml" in registries,
            "root registry missing")
    root_registry = yaml.safe_load((root / ".agents/skills.registry.yaml").read_text())
    if len(registries) > 1:
        precedence = root_registry.get("selection", {}).get("precedence", [])
        require("crate_scoped" in precedence and "workspace_scoped" in precedence
                and precedence.index("crate_scoped") < precedence.index("workspace_scoped"),
                "component registry lacks narrower selection precedence")
    count = 0
    for registry_path in registries:
        owner = registry_path.parent.parent.resolve()
        registry = yaml.safe_load(registry_path.read_text())
        entries = registry.get("skills", [])
        ids = [entry["id"] for entry in entries]
        require(len(ids) == len(set(ids)), "duplicate Skill IDs")
        declared = set()
        for entry in entries:
            require(entry.get("status") in ALLOWED_STATUSES,
                    f"invalid Skill status: {entry['id']}={entry.get('status')}")
            require(bool(entry.get("triggers")), f"missing triggers: {entry['id']}")
            skill_dir = (owner / entry["path"]).resolve()
            require(skill_dir.is_relative_to(owner / ".agents/skills"),
                    f"maintainer path escapes tree: {entry['id']}")
            require(skill_dir not in declared, "duplicate Skill path")
            declared.add(skill_dir)
            skill_file = skill_dir / "SKILL.md"
            require(skill_file.is_file(), f"missing Skill file: {entry['id']}")
            text = skill_file.read_text()
            parts = text.split("---", 2)
            require(len(parts) == 3 and not parts[0].strip(),
                    f"frontmatter absent: {entry['id']}")
            frontmatter = yaml.safe_load(parts[1])
            require(isinstance(frontmatter, dict) and
                    frontmatter.get("name") == entry["id"] and
                    bool(frontmatter.get("description")),
                    f"frontmatter mismatch: {entry['id']}")
            require("## Purpose" in text and "## Workflow" in text,
                    f"behavioral sections absent: {entry['id']}")
            count += 1
        actual = {p.resolve() for p in (owner / ".agents/skills").iterdir() if p.is_dir()}
        require(actual == declared, "orphan or missing Skill directory")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    root = args.fixture.resolve()
    registry_skill_count = verify_registry_contract(root)
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
    require(registry_skill_count == len(ids), "this fixture expects a single package")
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
    runtime_ids = {item["id"] for item in runtime_registry["skills"]}
    require(all(item.get("skill") in runtime_ids
                for item in policy.get("allowed", [])),
            "maintainer or unknown Skill exposed as runtime asset")
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
