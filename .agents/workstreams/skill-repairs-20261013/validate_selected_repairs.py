#!/usr/bin/env python3
"""Target-owned acceptance for six selected repairs; no device experiments."""
import hashlib,importlib.util,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
import yaml
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
EVALS=["skill-repairs-planning-20261013","skill-repairs-runtime-20261013"]
def need(ok,message):
    if not ok:raise ValueError(message)
def git(*args):
    return subprocess.check_output(["git",*args],cwd=REPO,text=True).strip()
def scope(task):
    selected={r["path"] for r in task["selected_files"]}
    changed=set(git("diff","--name-only",task["original_base"]).splitlines())
    changed|=set(git("ls-files","--others","--exclude-standard").splitlines())
    allowed=selected|{".agents/evals/practice-iterations/"+n+".yaml" for n in EVALS}
    allowed|={".agents/HANDOFF.md"} if task["integration_state"]=="merged" else set()
    need(all(p in allowed or p.startswith(".agents/workstreams/skill-repairs-20261013/") for p in changed),"unexpected changed path")
    for row in task["selected_files"]:
        p=REPO/row["path"]
        need(git("hash-object",str(p))==row["after"]["oid"],"source byte drift: "+row["path"])
        expected=task.get("mode_overrides",{}).get(row["path"],row["after"]["mode"])
        mode="100755" if p.stat().st_mode&0o111 else "100644"
        need(mode==expected,"mode drift: "+row["path"])
    for p,h in task["frozen_constraints"].items():
        actual=hashlib.sha256((REPO/p).read_bytes()).hexdigest() if (REPO/p).is_file() else None
        need(actual==h,"constraint drift: "+p)
    return len(changed)
def planning():
    text=(REPO/".agents/skills/mst-practice-iteration-planning/SKILL.md").read_text()
    example=yaml.safe_load(re.search(r"```yaml\n(.*?)\n```",text,re.S).group(1))
    need(example["schema"]=="mst-practice-iteration/v1" and "validated_commit" in example,"example contract")
    example.update(id="copied-skill-example",repository="model-tuning-lab",status="in_progress",
      date="2026-10-13",validated_commit=git("rev-parse","HEAD"),stage_goal="Validate the documented planning example.")
    example["changes"]=[dict(type="docs",description="Instantiate the exact Skill example",files=["example"])]
    example["validation_commands"]=["bash scripts/validate-mst.sh"]
    example["lessons_ingested"]=[dict(lesson="Align generated plans with maintained schema",destination=".agents/skills/mst-practice-iteration-planning/SKILL.md",severity="medium")]
    with tempfile.TemporaryDirectory(prefix="skill-plan-") as td:
        dest=Path(td)
        for n in [".agents","scripts","templates"]:
            if (REPO/n).is_dir():shutil.copytree(REPO/n,dest/n)
        shutil.copy2(REPO/"AGENTS.md",dest/"AGENTS.md")
        p=dest/".agents/evals/practice-iterations/copied-example.yaml";p.parent.mkdir(parents=True,exist_ok=True)
        for mutation,expected in [("valid",0),("old-schema",1),("missing-commit",1)]:
            candidate=dict(example)
            if mutation=="old-schema":candidate["schema"]="practice-iteration/v1"
            if mutation=="missing-commit":candidate.pop("validated_commit")
            p.write_text(yaml.safe_dump(candidate,sort_keys=False))
            r=subprocess.run(["bash","scripts/validate-mst.sh"],cwd=dest,capture_output=True,text=True)
            need((r.returncode==0)==(expected==0),"planning fixture "+mutation+": "+r.stderr)
    for n in EVALS:
        row=yaml.safe_load((REPO/(".agents/evals/practice-iterations/"+n+".yaml")).read_text())
        need(row["schema"]==example["schema"] and row["status"] in ["in_progress","done"],"iteration state")
        git("cat-file","-e",row["validated_commit"]+"^{commit}")
        need(bool(row["validation_commands"]) and all(x["destination"] and x["severity"] for x in row["lessons_ingested"]),"iteration evidence")
    return 3
def direct_cli():
    spec=importlib.util.spec_from_file_location("runtime_fixture",REPO/"tests/test_validate_monkeypatch_package.py")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    case=mod.PackageValidatorTests();case.setUp()
    try:
        case.valid_fixture()
        r=subprocess.run([str(REPO/"scripts/validate_monkeypatch_package.py"),str(case.package)],capture_output=True,text=True,cwd=REPO)
        need(r.returncode==0 and json.loads(r.stdout)["static_identity_valid"],"documented direct CLI")
        case.manifest_path.write_text("{}")
        r=subprocess.run([str(REPO/"scripts/validate_monkeypatch_package.py"),str(case.package)],capture_output=True,text=True,cwd=REPO)
        need(r.returncode==2,"direct CLI fail-closed")
    finally:case.doCleanups()
    return 2
def main():
    task=json.loads((HERE/"task.json").read_text())
    result=dict(changed_paths=scope(task),planning_controls=planning(),direct_cli_controls=direct_cli(),
        selected_repair_files=len(task["selected_files"]),device_acceptance=False,all_skill_acceptance=False)
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
