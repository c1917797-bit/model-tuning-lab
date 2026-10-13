"""Source-bound additive lesson metadata verification; no device execution."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess

BASE = "23ec33d7d692bb77d17fb5b81aabacf57adad5c7"
SOURCE = "b9386cd8b98ceca4be89d2a090db071f21842388"
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TARGET = ".agents/workstreams/skill-repairs-20261013/knowledge-proposals.json"
FIELDS = ("classification", "trigger", "different_action", "verification")
SELECTED = {"planning-schema", "runtime-template"}
REVIEW_SHA = "583f5c6baa693d7244bd0a87697197cd02f7d8003aa6c082660b2faae7a825fa"

def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()

def inputs():
    raw = (HERE / "source-review.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == REVIEW_SHA, "review digest drift"
    review = json.loads(raw)
    assert review["main_commit"] == BASE
    assert review["source_proposal_blob"] == git("rev-parse", BASE + ":" + TARGET)
    old = json.loads(git("show", BASE + ":" + TARGET))
    current = json.loads((ROOT / TARGET).read_text())
    return old, current, review

def check(old, current, review):
    expected = copy.deepcopy(old)
    lessons = {x["id"]: x for x in review["lessons"]}
    for item in expected["proposals"]:
        if item["id"] in SELECTED:
            for field in FIELDS:
                assert field not in item, "not an additive supplement"
                value = lessons[item["id"]][field]
                assert value == 1 if field == "classification" else bool(value.strip())
                item[field] = value
    assert current == expected, "unexpected omission, rewrite or unrelated metadata"
    assert review["claim_boundary"]["full_skill_acceptance"] is False
    assert review["claim_boundary"]["new_npu_work"] is False
    return {"supplemented_records": 2, "complete_records": 3,
            "historical_decisions_preserved": True, "acceptance_promoted": False}

def main():
    result = check(*inputs())
    task = json.loads((HERE / "task.json").read_text())
    assert task["original_base"] == BASE
    for path, oid in task["frozen_git_blobs"].items():
        assert git("hash-object", path) == oid, "constraint changed: " + path
    allowed = {TARGET, ".agents/HANDOFF.md"}
    prefix = ".agents/workstreams/lesson-records-20261013/"
    changed = git("diff", "--name-only", BASE).splitlines()
    assert all(p in allowed or p.startswith(prefix) for p in changed), changed
    assert task["resource_leases"] == {"physical_npus": [], "service_ports": []}
    result.update(base=BASE, review_source=SOURCE, runtime_changed=False)
    print(json.dumps(result, sort_keys=True))
    return result

if __name__ == "__main__":
    main()
