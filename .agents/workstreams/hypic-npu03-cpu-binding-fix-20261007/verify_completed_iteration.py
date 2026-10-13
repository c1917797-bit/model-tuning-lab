#!/usr/bin/env python3
"""Read-only completed-plan checkpoint audit; does not execute plan commands."""
import hashlib
import json
import subprocess
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[3]
WS = Path(__file__).resolve().parent
PLAN = ".agents/evals/practice-iterations/hypic-remaining-skills-onboarding-20261013.yaml"
START = "d7b1738495f53ebac59bad3f2e0969eebf036284"
PUBLISHED = "c142c93f3849d9de4a4620ebdacfae572259193e"
RECEIPT = "85181563682334fe9f1d7379400d12ff6844b78ce42ab242aba7286aebb626eb"

def require(value, message):
    if not value:
        raise ValueError(message)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, stderr=subprocess.DEVNULL)

def audit_plan(plan, is_ancestor, checkpoint_file, current_file):
    require(plan.get("schema") == "mst-practice-iteration/v1", "schema")
    require(plan.get("status") == "done", "not a completed iteration")
    checkpoint = plan.get("validated_commit", "")
    require(is_ancestor(checkpoint), "checkpoint is not an existing ancestor")
    require(plan.get("validation_commands") and
            all(isinstance(x, str) and x.strip() for x in plan["validation_commands"]),
            "validation commands absent")
    files = [p for change in plan.get("changes", []) for p in change.get("files", [])]
    require(files and len(files) == len(set(files)), "empty or duplicate file scope")
    for path in files:
        require(not Path(path).is_absolute() and ".." not in Path(path).parts,
                "unsafe file scope")
        require(checkpoint_file(checkpoint, path) == current_file(path),
                "declared file differs from validated checkpoint: " + path)
    for lesson in plan.get("lessons_ingested", []):
        require(lesson.get("destination") in files and
                lesson.get("severity") in {"high", "medium", "low"} and
                lesson.get("classification") and lesson.get("verification"),
                "lesson routing incomplete")
    return {"checkpoint": checkpoint, "files_checked": len(files)}

def ancestor(ref):
    if not ref:
        return False
    try:
        return (git("cat-file", "-t", ref).strip() == b"commit" and
                subprocess.run(["git", "merge-base", "--is-ancestor", ref, "HEAD"],
                               cwd=REPO, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL).returncode == 0)
    except subprocess.CalledProcessError:
        return False

def main():
    read_commit = lambda ref, path: git("show", ref + ":" + path)
    read_current = lambda path: (REPO / path).read_bytes()
    before = yaml.safe_load(read_commit(START, PLAN))
    require(before["status"] == "in_progress" and ancestor(before["validated_commit"]),
            "initial plan missing or unvalidated input")
    plan = yaml.safe_load(read_current(PLAN))
    result = audit_plan(plan, ancestor, read_commit, read_current)
    # Preserve and reproduce the publication defect instead of rewriting its history.
    old = yaml.safe_load(read_commit(PUBLISHED, PLAN))
    try:
        audit_plan(old, ancestor, read_commit, read_current)
    except ValueError as exc:
        require("differs from validated checkpoint" in str(exc), "unexpected old-plan failure")
    else:
        raise ValueError("historical stale-file negative control unexpectedly passed")
    raw = (WS / "ONBOARDING_EXACT_MAIN_RECEIPT_20261013.json").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == RECEIPT, "receipt changed")
    receipt = json.loads(raw)
    require(receipt["exit_code"] == 0 and "Ran 6 tests" in receipt["stderr"]
            and "OK" in receipt["stderr"], "execution/test receipt incomplete")
    for name in ["verify_onboarding_snapshot.py", "test_onboarding_snapshot.py"]:
        digest = hashlib.sha256((WS / name).read_bytes()).hexdigest()
        require(digest + "  " + str((WS / name).relative_to(REPO)) in receipt["stdout"],
                "executed source digest absent: " + name)
    require("PASS: Maintainer Skill Tree structure is valid (29 skills)" in receipt["stdout"],
            "exact-main structure result absent")
    result.update(initial_plan_commit=START, publication_commit=PUBLISHED,
                  historical_stale_file_rejected=True, execution_receipt=receipt["operation_id"],
                  no_new_npu_work=True, main_planning_skill_integrated=False,
                  boundary="Checkpoint and retained execution evidence; not remote integration.")
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
