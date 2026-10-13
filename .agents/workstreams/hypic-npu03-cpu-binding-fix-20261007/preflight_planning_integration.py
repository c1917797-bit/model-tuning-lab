#!/usr/bin/env python3
"""Read-only selective-patch admission check; never applies, commits or pushes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BUNDLE=HERE/"integration/planning-schema"
TARGET="ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
SOURCE="4a95c87b8bf6a59557ad0e45c42e7b0616593caa"
PATH=".agents/skills/mst-practice-iteration-planning/SKILL.md"
BEFORE="171e1f401b18dc6aaa4d38a2c3b6b260fca46123"
AFTER="9be62a7adfec954b2b08d8d3d30e496e676d9ac8"

def need(ok,reason):
    if not ok:
        raise ValueError(reason)

def admit(doc,target,before,after,patch,canonical_patch):
    need(doc["schema"]=="mst-selective-integration-candidate/v1","schema")
    need(doc["target_commit"]==target==TARGET,"target drift")
    need(doc["source_commit"]==SOURCE,"source drift")
    need(doc["paths"]==[PATH],"allowlist changed")
    need(doc["before_blob"]==before==BEFORE and doc["after_blob"]==after==AFTER,"blob mismatch")
    need(patch==canonical_patch,"patch differs from exact source/path")
    need(doc["state"]=="offline-preflight-only" and
         doc["remote_authentication_verified"] is False and doc["primary_changed"] is False,
         "offline result overclaims readiness")
    return True

def git(cwd,*args):
    return subprocess.check_output(["git",*args],cwd=cwd,stderr=subprocess.DEVNULL)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--target",type=Path,required=True)
    target=parser.parse_args().target.resolve()
    doc=json.loads((BUNDLE/"manifest.json").read_text())
    envelope=json.loads((BUNDLE/"planning-schema.diff.json").read_text())
    need(envelope["schema"]=="git-unified-diff/v1","patch envelope schema")
    patch=envelope["diff"].encode()
    head=git(target,"rev-parse","HEAD").decode().strip()
    need(not git(target,"status","--porcelain").strip(),"target checkout not clean")
    old=git(target,"rev-parse","HEAD:"+PATH).decode().strip()
    new=git(REPO,"rev-parse",SOURCE+":"+PATH).decode().strip()
    canonical=git(REPO,"diff","--full-index",TARGET,SOURCE,"--",PATH)
    admit(doc,head,old,new,patch,canonical)
    before_status=git(target,"status","--porcelain")
    subprocess.run(["git","apply","--check","--whitespace=error-all"],
                   input=patch,cwd=target,check=True,capture_output=True)
    need(git(target,"rev-parse","HEAD").decode().strip()==head and
         git(target,"status","--porcelain")==before_status and
         git(target,"rev-parse","HEAD:"+PATH).decode().strip()==old,"read-only preflight mutated target")
    print(json.dumps({"schema":"mst-selective-integration-preflight/v1","valid":True,
                      "target_commit":head,"source_commit":SOURCE,"paths":[PATH],
                      "patch_sha256":hashlib.sha256(patch).hexdigest(),
                      "main_changed":False,"remote_authenticated":False,
                      "integration_ready":False,
                      "boundary":"Applies cleanly to pinned local main; live remote and final-tree gates remain."},
                     sort_keys=True))

if __name__=="__main__":
    main()
