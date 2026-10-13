#!/usr/bin/env python3
"""Replay exact published main repairs; preserve historical case verdicts."""
import argparse
import json
import subprocess
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAIN = "23ec33d7d692bb77d17fb5b81aabacf57adad5c7"
BASE = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
SOURCE = "06365feb165898a86305296dc007b40ec4e09461"
SKILL = ".agents/skills/mst-practice-iteration-planning/SKILL.md"
BLOB = "9be62a7adfec954b2b08d8d3d30e496e676d9ac8"
TASK = ".agents/workstreams/skill-repairs-20261013"
CLONE = Path("/cache/cch/mst-main-repair-replay-wctz16xx/clone")

def need(ok, message):
    if not ok:
        raise ValueError(message)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()

def verify_receipt(row):
    need(row["main_commit"] == MAIN and row["target_parent"] == BASE
         and row["source_commit"] == SOURCE, "commit identity")
    need(row["fresh_clone_kind"] == "local-no-hardlinks-clone-of-published-main", "clone scope")
    rec = row["fresh_clone"]
    need(rec["state"] == "completed" and rec["exitCode"] == 0, "replay terminal")
    need(rec["route"] == "peer_direct" and rec["peer"] == "lgw_fba5a82fcb8b4c1eb9c2ae2d1b87d61d", "route identity")
    lines = rec["stdout"].splitlines()
    need(lines[0] == "FRESH_CLONE=" + str(CLONE) and
         lines[-1] == "FRESH_MAIN_REPLAY_PASS=" + MAIN, "clone result identity")
    checks = [json.loads(line) for line in lines[1:-1]]
    expected = [
        ["python3", "-B", TASK + "/validate_selected_repairs.py"],
        ["/cache/cch/python-envs/model-tuning-lab-py311/bin/python", "-B",
         "-m", "unittest", "discover", "-s", "tests", "-p", "test_validate_monkeypatch_package.py"],
        ["bash", "scripts/validate-mst.sh"],
    ]
    need([r["command"] for r in checks] == expected and all(r["exit"] == 0 for r in checks), "replay commands")
    out = json.loads(checks[0]["out"])
    need(out == dict(all_skill_acceptance=False, changed_paths=17, device_acceptance=False,
                    direct_cli_controls=2, planning_controls=3, registry_entries=29,
                    selected_repair_files=6), "replay scope")
    need("Ran 9 tests" in checks[1]["err"] and checks[1]["err"].rstrip().endswith("OK"), "runtime tests")
    need("valid (29 skills)" in checks[2]["out"], "structure result")
    integ = row["integration"]
    need(integ["state"] == "completed" and integ["exitCode"] == 0, "integration terminal")

def verify_git():
    need(git("rev-parse", "origin/main") == MAIN, "current main moved; re-review required")
    need(git("rev-parse", MAIN + "^1") == BASE and
         git("rev-parse", MAIN + "^2") == SOURCE, "merge parents")
    need(git("rev-parse", MAIN + ":" + SKILL) == BLOB, "planning Skill identity")
    task = json.loads(git("show", MAIN + ":" + TASK + "/task.json"))
    need(task["integration_state"] == "merged" and task["execution_state"] == "completed", "target-owned state")
    need(task["integration_source"] == SOURCE and task["integration_target_parent"] == BASE, "target source binding")
    for row in task["selected_files"]:
        entry = git("ls-tree", MAIN, "--", row["path"]).split()
        need(entry[2] == row["after"]["oid"], "selected source identity")
        need(entry[0] == task.get("mode_overrides", {}).get(row["path"], row["after"]["mode"]), "selected mode")
    plan = yaml.safe_load(git("show", MAIN + ":.agents/evals/practice-iterations/skill-repairs-planning-20261013.yaml"))
    checkpoint = plan["validated_commit"]
    need(checkpoint == task["validated_content_commit"] and plan["status"] == "done", "completed checkpoint")
    need(git("rev-parse", checkpoint + ":" + SKILL) == BLOB, "validated checkpoint content")
    subprocess.run(["git", "merge-base", "--is-ancestor", checkpoint, MAIN], cwd=REPO, check=True)
    need(len(plan["stage_goal"].split(".")) == 2 and len(plan["validation_commands"]) >= 1, "bounded plan")
    need(all(x["destination"] and x["severity"] in {"low", "medium", "high"}
             for x in plan["lessons_ingested"]), "lesson routing")
    need(plan["changes"][0]["files"] == [SKILL], "changed files")
    return task

def replay():
    need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=CLONE, text=True).strip() == MAIN, "clone HEAD")
    need(not subprocess.check_output(["git", "status", "--porcelain"], cwd=CLONE, text=True).strip(), "clone dirty")
    commands = [
        ["python3", "-B", TASK + "/validate_selected_repairs.py"],
        ["/cache/cch/python-envs/model-tuning-lab-py311/bin/python", "-B", "-m", "unittest",
         "discover", "-s", "tests", "-p", "test_validate_monkeypatch_package.py"],
        ["bash", "scripts/validate-mst.sh"],
    ]
    for cmd in commands:
        subprocess.run(cmd, cwd=CLONE, check=True)
    need(not subprocess.check_output(["git", "status", "--porcelain"], cwd=CLONE, text=True).strip(), "clone changed")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    verify_receipt(json.loads((HERE / "MAIN_REPAIR_REPLAY_RECEIPT_20261013.json").read_text()))
    verify_git()
    if args.replay:
        replay()
    print(json.dumps(dict(main=MAIN, planning_bounded_verified=True,
        runtime_cpu_verified=True, device_lifecycle_verified=False,
        all_skills_verified=False, replay_executed=args.replay), sort_keys=True))

if __name__ == "__main__":
    main()
