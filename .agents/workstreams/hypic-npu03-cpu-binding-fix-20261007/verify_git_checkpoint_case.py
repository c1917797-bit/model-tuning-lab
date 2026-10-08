#!/usr/bin/env python3
"""Replay the bounded commit-implies-push workstream acceptance check."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parent.parents[2]
BRANCH = "work/hypic-npu03-cpu-binding-fix-20261007"
CHECKPOINT = "57771f36d194098883119aeb28692017399cac15"
SKILL_BLOB = "10da1ba69cb54c46dc6bdbdbbe7c434bc1b423f8"
EXPECTED_FILES = {
    ".agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/"
    "MAIN_SKILL_ACCEPTANCE_GAP_AUDIT_20261008.md",
    ".agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/"
    "skill-cases/chicaihong01-host-maintenance.json",
    ".agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/"
    "test_verify_skill_cases.py",
}


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=REPO, text=True,
                                   timeout=15).strip()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-current-sync", action="store_true",
                        help="also fail when current HEAD is not pushed")
    args = parser.parse_args()
    policy = yaml.safe_load(git("show", "origin/main:.agents/git-policy.yaml"))
    require(policy["repository_policy"] == "commit_implies_push"
            and policy["status"] == "maintainer-confirmed",
            "maintainer-confirmed policy absent")
    require(git("rev-parse", "origin/main:.agents/skills/"
                "mst-git-checkpoint-policy/SKILL.md") == SKILL_BLOB,
            "main Skill blob changed")
    require(git("branch", "--show-current") == BRANCH, "wrong work branch")
    require(git("rev-parse", "--symbolic-full-name", "@{upstream}")
            == "refs/remotes/origin/" + BRANCH, "wrong branch upstream")
    worktree_clean = git("status", "--porcelain=v1") == ""
    require(git("show", "-s", "--format=%P", CHECKPOINT)
            == "98443fe4b9ad5e5b6b7878662f81f8b91b710787",
            "checkpoint parent drift")
    files = set(git("diff-tree", "--no-commit-id", "--name-only", "-r",
                    CHECKPOINT).splitlines())
    require(files == EXPECTED_FILES, "checkpoint mixed unrelated files")
    head = git("rev-parse", "HEAD")
    upstream = git("rev-parse", "@{upstream}")
    # This is a cached remote-tracking ref. The separate live receipt in the
    # acceptance report proves the historical push at checkpoint time.
    subprocess.run(("git", "merge-base", "--is-ancestor", CHECKPOINT, head),
                   cwd=REPO, check=True, timeout=15)
    subprocess.run(("git", "merge-base", "--is-ancestor", CHECKPOINT, upstream),
                   cwd=REPO, check=True, timeout=15)
    current_synced = worktree_clean and head == upstream
    if args.require_current_sync:
        remote = git("ls-remote", "--heads", "origin", BRANCH).split()
        require(len(remote) == 2 and remote[1] == "refs/heads/" + BRANCH,
                "exact live remote work branch absent")
        current_synced = current_synced and remote[0] == head
        require(current_synced, "current HEAD/upstream/remote is not clean and synced")
    print(json.dumps({
        "policy": "commit_implies_push",
        "branch": BRANCH,
        "checkpoint": CHECKPOINT,
        "historical_checkpoint_in_tracking_ref": True,
        "live_remote_checked": args.require_current_sync,
        "local_head": head,
        "remote_tracking_head": upstream,
        "current_branch_synced": current_synced,
        "worktree_clean": worktree_clean,
        "scope": "one named-branch validated checkpoint, not every policy option",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
