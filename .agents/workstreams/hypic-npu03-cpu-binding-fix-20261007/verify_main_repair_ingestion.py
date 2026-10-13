#!/usr/bin/env python3
"""Review structured ingestion of actual main repairs; no device work."""
import copy
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAIN = "23ec33d7d692bb77d17fb5b81aabacf57adad5c7"
ROOT = ".agents/workstreams/skill-repairs-20261013"
PROPOSALS = ROOT + "/knowledge-proposals.json"
BLOB = "24a66ce8c986dc44266f0f56948c637e958afabf"
FIELDS = ("trigger", "different_action", "destination", "verification")
EXPECTED = {"planning-schema": 1, "runtime-template": 1, "documented-direct-cli": 5}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()

def missing_explicit(records):
    return {r["id"]: [f for f in ("classification", *FIELDS) if not r.get(f)]
            for r in records if any(not r.get(f) for f in ("classification", *FIELDS))}

def validate(review, source, selected):
    need(review["main_commit"] == MAIN and review["source_proposal_blob"] == BLOB, "source binding")
    need(review["status"] == "branch-supplement-not-main-integrated", "supplement state")
    need(3 <= len(review["facts"]) <= 7, "practice facts")
    lessons = review["lessons"]
    need({r["id"] for r in lessons} == set(EXPECTED) and len(lessons) == 3, "lesson coverage")
    need(not missing_explicit(lessons), "four-question gate")
    original = {r["id"]: r for r in source["proposals"]}
    need(set(original) == set(EXPECTED), "main proposal identity")
    for row in lessons:
        need(row["classification"] == EXPECTED[row["id"]], "classification")
        need(row["destination"] == original[row["id"]]["destination"], "destination drift")
        need(original[row["id"]]["decision"] == "accepted", "not accepted in source")
        need(row["scope"] in {"general", "repository-specific", "tool-specific"}, "lesson scope")
        need(row["checkpoint"] == "f9af6d162b34ceaf96179ecbd963d8b90172693c", "validated checkpoint")
        need(row["validation_command"] and row["files_changed"]
             and set(row["files_changed"]) <= selected, "validation/files association")
        # Do not overwrite complete historical four-question records.
        for key in ("classification", *FIELDS):
            if original[row["id"]].get(key):
                need(row[key] == original[row["id"]][key], "original field changed")
    boundary = review["claim_boundary"]
    need(not any(boundary[k] for k in ("new_npu_work", "historical_host_guard_integrated",
              "full_skill_acceptance", "proposed_metadata_integrated")), "scope overclaim")
    need(boundary["original_hypic_verdict_unchanged"], "historical verdict")
    need(not review["registry_decision"]["changed"], "unexpected registry edit")
    return missing_explicit(source["proposals"])

def load_and_check():
    need(git("rev-parse", "origin/main") == MAIN, "main drift; re-review")
    need(git("rev-parse", MAIN + ":" + PROPOSALS) == BLOB, "proposal bytes")
    source = json.loads(git("show", MAIN + ":" + PROPOSALS))
    task = json.loads(git("show", MAIN + ":" + ROOT + "/task.json"))
    need(task["integration_state"] == "merged", "not integrated")
    selected = {r["path"] for r in task["selected_files"]}
    direct = json.loads(git("show", MAIN + ":" + ROOT + "/DIRECT_CLI_FAILURE.json"))
    failure = json.loads(direct["stdout"])
    need(failure["direct_skill_command_failed"] and failure["error_type"] == "PermissionError", "real failure evidence")
    review = json.loads((HERE / "EXPERIENCE_MAIN_REPAIR_REVIEW_20261013.json").read_text())
    missing = validate(review, source, selected)
    return review, source, selected, missing

def main():
    review, source, selected, missing = load_and_check()
    print(json.dumps(dict(source_main=MAIN, source_missing_explicit_fields=missing,
        structured_lessons=len(review["lessons"]), supplemented_four_question_gates=3,
        scope="retrospective explicit classification of already integrated repairs",
        main_metadata_updated=False, skill_acceptance_promoted=False), sort_keys=True))

if __name__ == "__main__":
    main()
