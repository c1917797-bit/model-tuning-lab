"""Build and audit a retained exact-main + five-file CPU integration fixture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
PLAN = BASE / "RUNTIME_SELECTIVE_INTEGRATION_PLAN_20261013.json"
PYTHON = "/cache/cch/python-envs/model-tuning-lab-py311/bin/python"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def invoke(cwd, args, env=None, check=True):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"{args}: {result.returncode}: {result.stderr.decode()}")
    return result

def git(cwd, *args):
    return invoke(cwd, ["git", *args]).stdout

def status(cwd):
    return git(cwd, "status", "--porcelain=v1", "--untracked-files=all").decode()

def inventory(cwd, revision):
    records = git(cwd, "ls-tree", "-r", "-z", revision).split(b"\0")
    output = {}
    for record in records:
        if not record:
            continue
        identity, path = record.split(b"\t")
        mode, kind, oid = identity.decode().split()
        output[path.decode()] = {"mode": mode, "type": kind, "oid": oid}
    return output

def load_plan():
    plan = json.loads(PLAN.read_text())
    paths = [f["path"] for f in plan["files"]]
    assert len(paths) == len(set(paths)) == 5
    assert plan["status"] == "frozen-before-execution"
    return plan

def expected_tree(repo, plan):
    expected = inventory(repo, plan["target_commit"])
    for item in plan["files"]:
        expected[item["path"]] = inventory(repo, item["source_commit"])[item["path"]]
    return expected

def audit(root):
    root = Path(root).resolve()
    result = json.loads((root / "result.json").read_text())
    plan = load_plan()
    assert result["plan_sha256"] == sha(PLAN.read_bytes()), "plan changed"
    assert result["runner_sha256"] == sha(Path(__file__).read_bytes()), "runner changed"
    candidate = root / "candidate"
    assert git(candidate, "rev-parse", "HEAD").decode().strip() == plan["target_commit"]
    assert inventory(candidate, result["candidate_tree"]) == expected_tree(REPO, plan), "tree mismatch"
    assert git(candidate, "write-tree").decode().strip() == result["candidate_tree"], "index drift"
    assert not git(candidate, "diff", "--name-only"), "unstaged drift"
    assert not git(candidate, "ls-files", "--others", "--exclude-standard"), "extra files"
    assert result["changed_paths"] == sorted(f["path"] for f in plan["files"])
    patch = git(candidate, "diff", "--cached", "--binary", "--full-index", plan["target_commit"])
    assert sha(patch) == result["patch_sha256"]
    assert json.loads((root / "repair.diff.json").read_text()) == patch.decode()
    for receipt in result["checks"]:
        for field in ("stdout", "stderr"):
            assert sha((root / receipt[field]).read_bytes()) == receipt[field + "_sha256"]
        assert receipt["exit_code"] == 0, receipt["name"]
    tests = next(r for r in result["checks"] if r["name"] == "legacy-tests")
    log = (root / tests["stderr"]).read_text()
    assert "Ran 9 tests" in log and log.rstrip().endswith("OK")
    structure = next(r for r in result["checks"] if r["name"] == "skill-tree")
    assert "PASS: Maintainer Skill Tree structure is valid (29 skills)" in (root / structure["stdout"]).read_text()
    assert result["source_before"] == result["source_after"]
    assert result["main_changed"] is False and result["device_acceptance"] is False
    return {"audit": "PASS", "fixture": str(root), "candidate_tree": result["candidate_tree"],
            "changed_paths": result["changed_paths"], "cpu_tests": 9,
            "main_changed": False, "full_skill_acceptance": False}

def run():
    plan = load_plan()
    before = {"head": git(REPO, "rev-parse", "HEAD").decode().strip(), "status": status(REPO)}
    assert before["head"] == plan["source_checkpoint"], "source drift"
    root = Path(tempfile.mkdtemp(prefix="mst-runtime-selective-", dir="/cache/cch"))
    print(json.dumps({"fixture_created": str(root)}), flush=True)
    candidate = root / "candidate"
    invoke(root, ["git", "clone", "--shared", "--no-checkout", str(REPO), str(candidate)])
    git(candidate, "checkout", "-b", "work/runtime-selective-acceptance", plan["target_commit"])
    for item in plan["files"]:
        path = candidate / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        data = git(REPO, "show", item["source_commit"] + ":" + item["path"])
        path.write_bytes(data)
        mode = inventory(REPO, item["source_commit"])[item["path"]]["mode"]
        path.chmod(0o755 if mode == "100755" else 0o644)
    git(candidate, "add", "--", *(f["path"] for f in plan["files"]))
    tree = git(candidate, "write-tree").decode().strip()
    assert inventory(candidate, tree) == expected_tree(REPO, plan)
    patch = git(candidate, "diff", "--cached", "--binary", "--full-index", plan["target_commit"])
    (root / "repair.diff.json").write_text(json.dumps(patch.decode()) + "\n")
    env = os.environ.copy()
    env.update({"TMPDIR": str(root), "PYTHONDONTWRITEBYTECODE": "1"})
    env.pop("PYTHONPATH", None)
    env.pop("MODEL_TUNING_RUNTIME_PATCH_ENABLE", None)
    env.pop("MTL_TEST_ACTIVATION_FAIL", None)
    checks = []
    commands = [
        ("legacy-tests", [PYTHON, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_validate_monkeypatch_package.py", "-v"]),
        ("skill-tree", ["bash", "scripts/validate-mst.sh"]),
        ("diff-check", ["git", "diff", "--cached", "--check"]),
    ]
    for name, command in commands:
        completed = invoke(candidate, command, env=env, check=False)
        row = {"name": name, "command": command, "exit_code": completed.returncode}
        for field, content in (("stdout", completed.stdout), ("stderr", completed.stderr)):
            filename = name + "." + field + ".txt"
            (root / filename).write_bytes(content)
            row[field] = filename
            row[field + "_sha256"] = sha(content)
        checks.append(row)
        print(json.dumps({"check": name, "exit_code": completed.returncode}), flush=True)
    result = {
        "schema": "mst-selective-runtime-repair-result/v1",
        "plan_sha256": sha(PLAN.read_bytes()), "runner_sha256": sha(Path(__file__).read_bytes()),
        "candidate_tree": tree, "target_commit": plan["target_commit"],
        "changed_paths": sorted(f["path"] for f in plan["files"]),
        "patch_sha256": sha(patch), "checks": checks, "source_before": before,
        "source_after": {"head": git(REPO, "rev-parse", "HEAD").decode().strip(), "status": status(REPO)},
        "main_changed": False, "device_acceptance": False,
        "source_object_store_dependency": str(REPO), "fixture": str(root),
    }
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(audit(root), sort_keys=True))
    return root

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true")
    group.add_argument("--audit", type=Path)
    args = parser.parse_args()
    if args.run:
        run()
    else:
        print(json.dumps(audit(args.audit), sort_keys=True))
