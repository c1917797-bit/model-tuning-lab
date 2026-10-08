#!/usr/bin/env python3
"""Replay the bounded shared-NPU experience-ingestion case on its raw host artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[3]
CASE = REPO / ".agents/evals/transformation-cases/hypic-shared-npu-reentry-ingestion.yaml"
FOREIGN_CONTAINER = "efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    case = yaml.safe_load(CASE.read_text(encoding="utf-8"))
    require(case["schema"] == "mst-transformation-case/v1"
            and case["id"] == CASE.stem, "eval identity drift")
    lesson = case["lesson"]
    require(lesson["classification"] == 1
            and lesson["destination"] == ".agents/skills/chicaihong01-host-maintenance/SKILL.md",
            "ingestion destination drift")
    require(all(lesson.get(k) for k in ("trigger", "different_action", "verification")),
            "ingestion four-question gate incomplete")
    require(len(case["facts"]) in range(3, 8), "practice fact count out of range")
    main_skill = subprocess.check_output(("git", "show", "origin/main:.agents/skills/chicaihong01-host-maintenance/SKILL.md"), cwd=REPO, text=True)
    branch_skill = (REPO / lesson["destination"]).read_text(encoding="utf-8")
    require("Container-local" in main_skill
            and "physical-device process guard" not in main_skill,
            "main coverage needs fresh review")
    require("continuous" in branch_skill
            and "physical-device process guard" in branch_skill
            and "capture its cgroup/container identity" in branch_skill,
            "branch Skill update absent or incomplete")
    observed = []
    for item in case["raw_evidence"]:
        root = Path(item["root"])
        require(root.is_dir(), f"raw root absent: {root}")
        guard_path = root / "hypic-only/lane-guard.json"
        stop_path = root / "hypic-only/service-stop.json"
        require(sha256(guard_path) == item["lane_guard_sha256"],
                f"{item['attempt']}: guard hash drift")
        require(sha256(stop_path) == item["service_stop_sha256"],
                f"{item['attempt']}: cleanup hash drift")
        guard = json.loads(guard_path.read_text(encoding="utf-8"))
        stop = json.loads(stop_path.read_text(encoding="utf-8"))
        progress = json.loads((root / "progress.json").read_text(encoding="utf-8"))
        foreign = [p for observation in guard["foreign"]
                   for p in observation["processes"]]
        require(any(p["container_id"] == FOREIGN_CONTAINER
                    and p["physical_npu"] == item["physical_npu"]
                    and p["pid"] == item["foreign_pid"] for p in foreign),
                f"{item['attempt']}: foreign physical PID absent")
        require(not guard["probe_errors"] and guard["owned_container_id"] == stop["container_id"],
                f"{item['attempt']}: guard/owned identity mismatch")
        require(stop["container_removed"] and stop["owned_npus_released"]
                and stop["port_released"] and not stop["service_reached_health"],
                f"{item['attempt']}: cleanup or pre-health boundary failed")
        require(progress["stage"] == "arm-failed" and progress["completed"] == 0
                and progress["expected"] == 127,
                f"{item['attempt']}: outcome is not 0/127 isolation-invalid")
        observed.append({"attempt": item["attempt"], "physical_npu": item["physical_npu"],
                         "foreign_pid": item["foreign_pid"], "completed": 0})
    require([x["attempt"] for x in observed] == ["cache10r6", "cache10r7"],
            "attempt coverage drift")
    print(json.dumps({"case": case["id"], "classification": 1,
                      "observed": observed, "scope": "target-host startup isolation only"},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
