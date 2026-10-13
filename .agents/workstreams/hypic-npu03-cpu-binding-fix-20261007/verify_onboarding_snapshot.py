"""Read-only exact-main onboarding replay; no device or service actions."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
SKILL = ".agents/skills/mst-repo-onboarding/SKILL.md"
SKILL_BLOB = "a1eb74cee760653f63181f8e4e775a7cf29ee75c"
REGISTRY_BLOB = "2611864bbcf719d57920aae03ff9eb85521526b4"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def inventory(entries, directories, entrypoints):
    ids = [entry["id"] for entry in entries]
    require(len(ids) == len(set(ids)), "duplicate registry ID")
    for entry in entries:
        require(entry["path"] == ".agents/skills/" + entry["id"], "unexpected Skill path")
    expected = set(ids)
    require(expected == set(directories), "missing or orphan Skill directory")
    require(expected == set(entrypoints), "missing or orphan SKILL.md")
    return sorted(ids)

def replay(root):
    root = Path(root).resolve(strict=True)
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    require(git("rev-parse", "HEAD") == MAIN, "wrong main checkpoint")
    require(not git("status", "--porcelain"), "acceptance checkout is dirty")
    require(git("hash-object", SKILL) == SKILL_BLOB, "onboarding Skill drift")
    require(git("hash-object", ".agents/skills.registry.yaml") == REGISTRY_BLOB,
            "registry drift")
    registry = yaml.safe_load((root / ".agents/skills.registry.yaml").read_text())
    dirs = [p for p in (root / ".agents/skills").iterdir() if p.is_dir()]
    require(all(not p.is_symlink() for p in dirs), "symlink Skill directory")
    ids = inventory(registry["skills"], [p.name for p in dirs],
                    [p.name for p in dirs if (p / "SKILL.md").is_file()])
    backlogs = list(root.glob("agents/*/work/backlog.yaml"))
    require(not backlogs, "new backlog needs task-schema review; do not report zero")
    docs = {name: (root / name).is_file()
            for name in ("docs/ARCHITECTURE.md", "CLAUDE.md", "AGENTS.md")}
    require(docs["AGENTS.md"], "missing maintainer entrypoint")
    result = subprocess.run(["bash", "scripts/validate-mst.sh"], cwd=root,
                            capture_output=True, text=True, check=True)
    require("PASS:" in result.stdout, "validator did not report PASS")
    workstreams = sorted(str(p.relative_to(root))
                         for p in root.glob(".agents/workstreams/*/task.json"))
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
              for name in ("AGENTS.md", ".agents/skills.registry.yaml", SKILL, "CLAUDE.md")
              if (root / name).is_file()}
    return {
        "schema": "exact-main-onboarding-replay/v1", "repository": str(root),
        "commit": MAIN, "skill_blob": SKILL_BLOB, "registry_blob": REGISTRY_BLOB,
        "skills": ids, "skill_count": len(ids), "agent_backlog_directories": 0,
        "non_done_tasks_across_legacy_backlogs": 0,
        "task_count_scope": "agents/*/work/backlog.yaml only; not live task/host inventory",
        "other_task_records": workstreams, "docs_present": docs,
        "validator_stdout": result.stdout.strip(), "input_sha256": hashes,
        "last_significant_change": git("log", "-1", "--oneline"),
        "structural_changes_since_last_session": "first session in this isolated checkpoint; no prior snapshot",
        "clone_is_local_shared_object_fixture": True, "github_authentication_tested": False,
        "new_device_work": False,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    print(json.dumps(replay(parser.parse_args().root), sort_keys=True, indent=2))
