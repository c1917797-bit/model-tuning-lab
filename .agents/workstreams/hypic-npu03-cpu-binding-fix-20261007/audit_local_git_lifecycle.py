#!/usr/bin/env python3
"""Independently inspect retained Git objects, refs, final state and ordered receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def audit(root, claimed_result=None):
    root=root.resolve()
    need(root.parent==Path("/cache/cch") and root.name.startswith("mst-workstream-lifecycle-"),
         "not a retained lifecycle fixture")
    result=json.loads((root/"result.json").read_text()) if claimed_result is None else claimed_result
    primary=root/"primary"; remote=root/"origin.git"
    def git(*args):
        return subprocess.check_output(["git",*args],cwd=primary,text=True,
                                       stderr=subprocess.DEVNULL,timeout=15).strip()
    def remote_ref(ref):
        return git("--git-dir",str(remote),"rev-parse",ref)
    need(git("rev-parse","HEAD")==result["merged"]==remote_ref("refs/heads/main"),"primary equality")
    need(remote_ref("refs/heads/work/bounded-lifecycle")==result["source"],"retained remote source")
    need(git("status","--porcelain")=="","primary dirty")
    need(git("rev-list","--parents","-n","1",result["merged"]).split()[1:]==
         [result["target_parent"],result["source"]],"wrong merge parents")
    for parent,child in [(result["base"],result["start"]),(result["start"],result["implemented"]),
                         (result["implemented"],result["revalidated"]),
                         (result["target_parent"],result["revalidated"]),
                         (result["revalidated"],result["source"]),
                         (result["source"],result["merged"])]:
        ancestry=subprocess.run(["git","merge-base","--is-ancestor",parent,child],cwd=primary,
                                capture_output=True,timeout=15)
        need(ancestry.returncode==0,"claimed ancestry invalid")
    path=".agents/workstreams/bounded-lifecycle/"
    state=json.loads(git("show",result["source"]+":"+path+"task.json"))
    target=json.loads((primary/path/"task.json").read_text())
    need(state["execution_state"]=="completed" and state["integration_state"]=="ready","source state")
    need(target["execution_state"]=="completed" and target["integration_state"]=="merged"
         and target["claims_released"],"target-owned release state")
    need(state["original_base"]==target["original_base"]==result["base"],"original base overwritten")
    need(state["validated_content_commit"]==result["revalidated"],"content checkpoint")
    for ref in [result["base"],result["source"],result["merged"]]:
        data=subprocess.check_output(["git","show",ref+":.agents/git-policy.json"],cwd=primary)
        need(hashlib.sha256(data).hexdigest()==result["frozen_policy_sha256"],"strategy drift")
    evidence=json.loads((primary/path/"integration-evidence.json").read_text())
    need(evidence["source"]==result["source"] and
         evidence["target_parent"]==result["target_parent"],"attestation mismatch")
    need(git("rev-parse",result["merged"]+":.agents/skills/mst-parallel-workstreams/SKILL.md")==
         result["skill_blob"]=="c47b989bc006561d347e0fbfe5d59026fb8e91e0","not exact-main Skill")
    need(git("show",result["base"]+":app.py")==git("show",result["start"]+":app.py"),
         "product changed before remote start")
    need(git("show",result["source"]+":app.py")==git("show",result["merged"]+":app.py"),
         "source product not retained")
    need(not (root/"worker").exists() and not (root/"detached-inspection").exists(),"worktree remains")
    need(git("worktree","list","--porcelain").count("worktree ")==1,"worktree inventory")
    need(not (root/"integration.lock").exists(),"integration lock retained")
    need("refs/heads/work/bounded-lifecycle" not in git("for-each-ref","--format=%(refname)","refs/heads"),
         "merged local branch not reclaimed")
    journal=json.loads((root/"execution-journal.json").read_text())
    negative={x["negative_control"] for x in journal if x.get("rejected")}
    expected={"later exclusive claimant waits","detached authoring","unmerged reclamation",
              "stale target","dirty readiness","wrong source attestation","competing integrator"}
    need(negative==expected,"negative controls incomplete")
    commits=[]
    for i,entry in enumerate(journal):
        args=entry.get("args",[])
        if args[:1]==["git"] and "commit" in args and "-m" in args:
            need(entry["exit_code"]==0,"failed commit")
            before=journal[i-4:i]
            need(len(before)==4 and before[0]["args"][:2]==["bash","scripts/validate-mst.sh"]
                 and all(x["exit_code"]==0 for x in before),"validation not before commit")
            need(before[-1]["args"][-1]=="write-tree","validated tree not captured")
            after=journal[i+1]
            need(after["args"][-1]=="HEAD^{tree}" and
                 after["stdout"].strip()==before[-1]["stdout"].strip(),"tree changed at commit")
            commit=journal[i+2]["stdout"].strip()
            need(git("rev-parse",commit+"^{tree}")==before[-1]["stdout"].strip(),"object tree mismatch")
            commits.append(commit)
    expected_commits={result[k] for k in ["base","start","implemented","target_parent",
                                         "revalidated","source","merged"]}
    need(set(commits)==expected_commits and len(commits)==7,"checkpoint journal incomplete")
    pushes=[x for x in journal if x.get("args",[])[:1]==["git"] and "push" in x["args"]]
    need(len(pushes)==7 and all(x["exit_code"]==0 for x in pushes),"push lifecycle incomplete")
    need(all("--force" not in x["args"] and "-f" not in x["args"] for x in pushes),"force push used")
    need(all("origin" in x["args"] for x in pushes),"unknown push remote")
    output=subprocess.check_output(["python3","-B","app.py"],cwd=primary,text=True).strip()
    need(output=="feature-v1","merged product failed")
    return {"schema":"mst-local-git-lifecycle-audit/v1","root":str(root),"valid":True,
            "actual_commits":7,"actual_pushes":7,"negative_controls":7,"merged":result["merged"],
            "source":result["source"],"worktrees_remaining":1,"remote_branch_retained":True,
            "scope":"local bare Git transport; not GitHub authentication or actual model-tuning-lab main"}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("root",type=Path)
    print(json.dumps(audit(parser.parse_args().root),sort_keys=True))
