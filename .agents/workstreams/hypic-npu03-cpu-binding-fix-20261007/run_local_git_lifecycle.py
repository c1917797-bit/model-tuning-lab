#!/usr/bin/env python3
"""Actual Git lifecycle exercise in a new retained, fixture-owned directory."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BRANCH = "work/bounded-lifecycle"
TASK = ".agents/workstreams/bounded-lifecycle"
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
BLOB = "c47b989bc006561d347e0fbfe5d59026fb8e91e0"
ENV = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1",
           GIT_TERMINAL_PROMPT="0", GIT_AUTHOR_NAME="Skill lifecycle fixture",
           GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_NAME="Skill lifecycle fixture",
           GIT_COMMITTER_EMAIL="fixture@example.invalid", PYTHONDONTWRITEBYTECODE="1")
EVENTS = []

def require(ok, text):
    if not ok:
        raise RuntimeError(text)

def cmd(root, *args):
    result = subprocess.run(args, cwd=root, env=ENV, capture_output=True, text=True, timeout=30)
    EVENTS.append(dict(cwd=str(root), args=list(args), exit_code=result.returncode,
                       stdout=result.stdout, stderr=result.stderr))
    require(result.returncode == 0, repr(args) + ": " + result.stderr)
    return result.stdout.strip()

def git(root, *args):
    return cmd(root, "git", "-c", "protocol.file.allow=always", *args)

def write(root, name, content):
    path = root / name
    require(path.resolve().is_relative_to(root.resolve()), "fixture write escaped")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

def write_json(root, name, data):
    write(root, name, json.dumps(data, indent=2, sort_keys=True) + "\n")

def named(root):
    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    require(branch.startswith("work/"), "not a named workstream")
    return branch

def clean(root):
    require(not git(root, "status", "--porcelain"), "dirty worktree")

def synced(root, ref):
    require(git(root, "rev-list", "--left-right", "--count", "HEAD..." + ref) == "0\t0",
            "upstream mismatch")

def contains(root, base, tip="HEAD"):
    result = subprocess.run(["git", "merge-base", "--is-ancestor", base, tip],
                            cwd=root, env=ENV, capture_output=True, timeout=30)
    return result.returncode == 0

def ready(root, target):
    named(root)
    clean(root)
    synced(root, "origin/" + BRANCH)
    require(contains(root, target), "target drift")
    state = json.loads((root / TASK / "task.json").read_text())
    require(state["execution_state"] == "completed" and state["integration_state"] == "ready",
            "state is not ready")
    require(not state["dependencies"], "unmet dependencies")

def attest(parent, source, record):
    require(record["target_parent"] == parent and record["source"] == source,
            "attestation mismatch")

def reclaim(primary, worker, source):
    clean(worker)
    require(contains(primary, source, "origin/main"), "unmerged source")
    require(git(worker, "rev-parse", "HEAD") == source, "worker tip changed")
    require(git(primary, "rev-parse", "origin/" + BRANCH) == source, "source not pushed")
    state = json.loads((primary / TASK / "task.json").read_text())
    require(state["integration_state"] == "merged" and state["claims_released"],
            "claims/state not released")

def expected_failure(label, function):
    try:
        function()
    except RuntimeError as exc:
        EVENTS.append({"negative_control": label, "rejected": True, "reason": str(exc)})
        return
    raise RuntimeError("negative control accepted: " + label)

def validate(root, value):
    cmd(root, "bash", "scripts/validate-mst.sh", value)

def checkpoint(root, message, value):
    validate(root, value)
    git(root, "add", "--all")
    git(root, "diff", "--cached", "--check")
    tree = git(root, "write-tree")
    git(root, "commit", "-m", message)
    require(git(root, "rev-parse", "HEAD^{tree}") == tree, "committed unvalidated tree")
    return git(root, "rev-parse", "HEAD")

def exercise(root):
    origin, primary, worker = root/"origin.git", root/"primary", root/"worker"
    git(root, "init", "--bare", "--initial-branch=main", str(origin))
    git(root, "clone", str(origin), str(primary))
    require(git(REPO, "rev-parse", MAIN + ":.agents/skills/mst-parallel-workstreams/SKILL.md") == BLOB,
            "exact-main Skill changed")
    skill = git(REPO, "show", MAIN + ":.agents/skills/mst-parallel-workstreams/SKILL.md") + "\n"
    write(primary, ".agents/skills/mst-parallel-workstreams/SKILL.md", skill)
    policy = {"repository_policy": "commit_implies_push", "remote": "origin",
              "primary": "main", "prefix": "work/", "integration": "serialized-no-ff",
              "worktree_budget": 4, "remote_branch_retention": "retain"}
    write_json(primary, ".agents/git-policy.json", policy)
    write(primary, "AGENTS.md", "You are the repository maintainer.\nUse .agents/skills/mst-parallel-workstreams/SKILL.md.\n")
    write(primary, ".agents/HANDOFF.md", "Bootstrap; no product workstream integrated.\n")
    write(primary, "app.py", "print('baseline')\n")
    write(primary, "scripts/validate-mst.sh",
          "#!/bin/sh\nset -eu\npython3 -B scripts/validate.py \"$1\"\n")
    write(primary, "scripts/validate.py",
          "import json,pathlib,subprocess,sys\n"
          "p=pathlib.Path('.')\n"
          "assert 'repository maintainer' in (p/'AGENTS.md').read_text()\n"
          "assert json.loads((p/'.agents/git-policy.json').read_text())['repository_policy']=='commit_implies_push'\n"
          "assert (p/'.agents/skills/mst-parallel-workstreams/SKILL.md').is_file()\n"
          "assert subprocess.check_output([sys.executable,'-B','app.py'],text=True).strip()==sys.argv[1]\n"
          "print('PASS: fixture policy and product '+sys.argv[1])\n")
    base = checkpoint(primary, "fixture: bootstrap confirmed workstream policy", "baseline")
    git(primary, "push", "-u", "origin", "main")
    git(primary, "fetch", "origin")
    clean(primary); synced(primary, "origin/main")
    require(git(primary, "worktree", "list", "--porcelain").count("worktree ") == 1, "initial inventory")
    git(primary, "worktree", "add", "-b", BRANCH, str(worker), "origin/main")
    frozen = hashlib.sha256((worker/".agents/git-policy.json").read_bytes()).hexdigest()
    created_at = datetime.now(timezone.utc)
    state = {"task_id": "bounded-lifecycle", "branch": BRANCH, "target": "main", "remote": "origin",
             "created_at": created_at.isoformat(), "owner": "fixture-only",
             "original_base": base, "frozen_policy_sha256": frozen,
             "objective": "Change fixture response from baseline to feature-v1",
             "boundaries": ["local bare origin", "no NPU", "no real main mutation"],
             "dependencies": [], "resource_leases": [], "retention": "retain remote branch",
             "validation_commands": ["bash scripts/validate-mst.sh feature-v1"],
             "claims": [{"kind": k, "mode": mode, "target": target} for k,mode,target in [
                 ("file","exclusive","app.py"),("semantic","exclusive","fixture response"),
                 ("resource","exclusive",str(worker)),("strategy","read",".agents/git-policy.json"),
                 ("knowledge","shared","knowledge-proposals.json")]],
             "execution_state": "started", "integration_state": "not-ready"}
    write_json(worker, TASK+"/task.json", state)
    write(worker, TASK+"/HANDOFF.md", "Start from "+base+"; validate before product edits.\n")
    write_json(worker, TASK+"/knowledge-proposals.json", {"proposals": []})
    write_json(worker, TASK+"/integration-evidence.json", {"state": "not-ready"})
    start = checkpoint(worker, "fixture: start named workstream", "baseline")
    git(worker, "push", "-u", "origin", BRANCH)
    clean(worker); synced(worker, "origin/"+BRANCH)
    require(git(worker,"show",start+":app.py")==git(worker,"show",base+":app.py"),"product edited before start")
    # Competing exclusive claims choose the earlier tuple, not a running foreign job.
    claims = [(state["created_at"],"bounded-lifecycle"),((created_at+timedelta(seconds=60)).isoformat(),"later")]
    require(min(claims) == claims[0], "exclusive claim arbitration")
    EVENTS.append({"negative_control":"later exclusive claimant waits","rejected":True})
    write(worker, "app.py", "print('feature-v1')\n")
    state["execution_state"] = "in-progress"
    write_json(worker, TASK+"/task.json", state)
    write_json(worker, TASK+"/knowledge-proposals.json",
               {"proposals":[{"lesson":"Check original base before integration",
                              "decision":"proposed","destination":"target-owned handoff"}]})
    implemented = checkpoint(worker,"fixture: bounded product implementation","feature-v1")
    git(worker,"push","origin",BRANCH); synced(worker,"origin/"+BRANCH)
    detached = root/"detached-inspection"
    git(primary,"worktree","add","--detach",str(detached),implemented)
    expected_failure("detached authoring",lambda:named(detached))
    git(primary,"worktree","remove",str(detached))
    expected_failure("unmerged reclamation",lambda:reclaim(primary,worker,implemented))
    write(primary,"target-note.txt","Independent target change in isolated fixture.\n")
    target = checkpoint(primary,"fixture: advance target","baseline")
    git(primary,"push","origin","main")
    git(worker,"fetch","origin")
    expected_failure("stale target",lambda:require(contains(worker,target),"target drift"))
    state["integration_state"] = "needs-revalidation"
    git(worker,"merge","--no-ff","--no-commit","origin/main")
    write_json(worker,TASK+"/task.json",state)
    revalidated = checkpoint(worker,"fixture: merge target and revalidate","feature-v1")
    git(worker,"push","origin",BRANCH)
    state.update(execution_state="completed",integration_state="ready",
                 validated_content_commit=revalidated)
    write_json(worker,TASK+"/task.json",state)
    write(worker,TASK+"/HANDOFF.md",
          "Validated content checkpoint: "+revalidated+"\nReady envelope is the exact fetched remote tip; not self-referential.\n")
    source = checkpoint(worker,"fixture: publish ready evidence envelope","feature-v1")
    git(worker,"push","origin",BRANCH); git(worker,"fetch","origin")
    write(worker,"dirty-probe.txt","fixture negative control\n")
    expected_failure("dirty readiness",lambda:ready(worker,target))
    (worker/"dirty-probe.txt").unlink()
    ready(worker,target)
    require(state["original_base"] == base and
            hashlib.sha256((worker/".agents/git-policy.json").read_bytes()).hexdigest()==frozen,
            "original base or strategy changed")
    git(primary,"fetch","origin"); clean(primary); synced(primary,"origin/main")
    require(git(primary,"rev-parse","origin/"+BRANCH)==source,"fetched source mismatch")
    evidence={"target_parent":target,"source":source,"original_base":base,"validated_content":revalidated}
    expected_failure("wrong source attestation",lambda:attest(target,base,evidence))
    attest(target,source,evidence)
    lock=root/"integration.lock"
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        try:
            os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        except FileExistsError:
            EVENTS.append({"negative_control":"competing integrator","rejected":True})
        else:
            raise RuntimeError("second integrator admitted")
        git(primary,"merge","--no-ff","--no-commit","origin/"+BRANCH)
        state.update(integration_state="merged",claims_released=True)
        write_json(primary,TASK+"/task.json",state)
        write_json(primary,TASK+"/integration-evidence.json",evidence)
        write_json(primary,TASK+"/knowledge-proposals.json",{"proposals":[
            {"lesson":"Check original base before integration","decision":"accepted",
             "destination":".agents/HANDOFF.md"}]})
        write(primary,".agents/HANDOFF.md","Integrated source "+source+" onto "+target+
              "; original base preserved; check drift before integration.\n")
        merged=checkpoint(primary,"fixture: serialized validated integration","feature-v1")
        require(git(primary,"rev-list","--parents","-n","1",merged).split()[1:]==[target,source],
                "not exact no-ff integration")
        git(primary,"push","origin","main")
        git(primary,"fetch","origin"); synced(primary,"origin/main")
        reclaim(primary,worker,source)
        git(primary,"worktree","remove",str(worker))
        git(primary,"branch","-d",BRANCH)
        git(primary,"worktree","prune")
        require(git(primary,"worktree","list","--porcelain").count("worktree ")==1,"reclamation incomplete")
        clean(primary)
    finally:
        os.close(fd)
        lock.unlink()
    return dict(schema="mst-local-git-lifecycle-result/v1",root=str(root),base=base,start=start,
                implemented=implemented,target_parent=target,revalidated=revalidated,
                source=source,merged=merged,frozen_policy_sha256=frozen,
                skill_blob=BLOB,negative_controls=7,transport="local bare Git origin",
                real_github_authentication=False,real_model_tuning_main_changed=False)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",action="store_true",required=True)
    parser.parse_args()
    root=Path(tempfile.mkdtemp(prefix="mst-workstream-lifecycle-",dir="/cache/cch"))
    try:
        result=exercise(root)
        write_json(root,"result.json",result)
        print(json.dumps(result,sort_keys=True))
    except Exception:
        print(json.dumps({"failed_fixture_root":str(root)}),flush=True)
        raise
    finally:
        write_json(root,"execution-journal.json",EVENTS)

if __name__ == "__main__":
    main()
