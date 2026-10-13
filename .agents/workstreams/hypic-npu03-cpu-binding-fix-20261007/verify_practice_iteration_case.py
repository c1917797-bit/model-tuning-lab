#!/usr/bin/env python3
"""Check that a real HYPIC stage plan follows the repaired iteration contract."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / ".agents/skills/mst-practice-iteration-planning/SKILL.md"
PLAN = REPO / ".agents/evals/practice-iterations/hypic-npu03-quality-preflight-20261008.yaml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=REPO, text=True).strip()


def main() -> int:
    main_skill = git("show", "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2:.agents/skills/mst-practice-iteration-planning/SKILL.md")
    repaired_skill = SKILL.read_text(encoding="utf-8")
    require("schema: practice-iteration/v1" in main_skill
            and "validated_commit:" not in main_skill,
            "historical main Skill identity mismatch")
    require("schema: mst-practice-iteration/v1" in repaired_skill
            and "validated_commit: <last validated Git checkpoint" in repaired_skill,
            "branch Skill output contract not repaired")
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    require(plan["schema"] == "mst-practice-iteration/v1"
            and plan["id"] == PLAN.stem, "plan identity/schema drift")
    require(plan["repository"] == "model-tuning-lab"
            and plan["status"] == "in_progress", "plan scope/status drift")
    require(plan["stage_goal"].count(".") == 1
            and "physical NPU0-3" in plan["stage_goal"],
            "stage goal not one bounded sentence")
    checkpoint = plan["validated_commit"]
    require(git("cat-file", "-t", checkpoint) == "commit",
            "validated_commit is not a commit")
    subprocess.run(("git", "merge-base", "--is-ancestor", checkpoint, "HEAD"),
                   cwd=REPO, check=True)
    require(len(plan["next_iterations"]) in {2, 3}
            and all(x.get("pass_criteria") for x in plan["next_iterations"]),
            "next iterations lack bounded pass criteria")
    require(plan["validation_commands"]
            and all(x.get("destination") and x.get("severity") in {"high", "medium", "low"}
                    for x in plan["lessons_ingested"]),
            "validation or lesson routing absent")
    require("127" in str(plan["next_iterations"])
            and "2048-token" in str(plan["next_iterations"]),
            "original full-quality ruler missing")
    print(json.dumps({"skill": "mst-practice-iteration-planning",
                      "plan": plan["id"], "status": plan["status"],
                      "validated_input_commit": checkpoint,
                      "next_iterations": len(plan["next_iterations"]),
                      "historical_main_output_example_rejected": True},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
