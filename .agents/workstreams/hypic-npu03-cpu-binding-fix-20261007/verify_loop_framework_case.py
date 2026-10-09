#!/usr/bin/env python3
"""Replay the pinned task-manifest non-drift counterexample and repair."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PIN = "494771a8157624d659f562837f380f166f499d8d"
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
ROOT = ".agents/workstreams/hypic-npu03-cpu-binding-fix-20261007"


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=REPO, text=True).strip()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    skill = git("show", f"{MAIN}:.agents/skills/mst-loop-engineering-framework/SKILL.md")
    require("## Non-Drift Loop Contract" in skill
            and "current state is recorded outside chat" in skill
            and "handoff/backlog says exactly what comes next" in skill,
            "exact-main loop contract drift")
    before = json.loads(git("show", f"{PIN}^:{ROOT}/task.json"))
    after = json.loads(git("show", f"{PIN}:{ROOT}/task.json"))
    require(before["active_attempt"] is None
            and before["state"].startswith("r12_terminal")
            and "Resolve prospective full-pair" in before["next_action"],
            "stale-state counterexample is not pinned")
    active = after["active_attempt"]
    require(after["state"] == "r13_full_baseline_running_no_paired_verdict"
            and active["campaign"] == "cache10r13"
            and active["arm"] == "no-cache"
            and active["controller_operation"] == "exec-0000000000001a76"
            and active["root"].endswith(
                "/quality-context-41984-hotpath-cache10r13-full-baseline")
            and after["resource_claim"]["physical_npus"] == [0, 1, 2, 3]
            and after["resource_claim"]["forbidden_npus"] == [4, 5, 6, 7],
            "active-r13 repair identity drift")
    goals = after["goal_horizons"]
    require(all(goals.get(key) for key in ("long_term", "medium_term", "short_term"))
            and "all 29" in goals["long_term"]
            and "127x3" in goals["short_term"]
            and "exec-0000000000001a76" in after["next_action"]
            and "actual" in after["next_action"],
            "goal horizons or next action drift")
    handoff = git("show", f"{PIN}:{ROOT}/HANDOFF.md")
    headings = re.findall(r"^## ([0-8])\. ", handoff, re.M)
    require(headings == list("012345678")
            and "exec-0000000000001a76" in handoff
            and "NPU4–7" in handoff,
            "pinned handoff cannot orient a successor")
    test = git("show", f"{PIN}:{ROOT}/test_handoff_current.py")
    require('self.assertEqual(task["active_attempt"]["campaign"], "cache10r13")'
            in test and 'self.assertIsNone(task["active_attempt"])' not in test,
            "focused handoff regression did not reject stale null")
    print(json.dumps({
        "skill": "mst-loop-engineering-framework",
        "snapshot": PIN,
        "stale_active_null_rejected": True,
        "active_r13_handle_recorded": True,
        "goal_horizons_recorded": True,
        "long_term_acceptance": "partial-evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
