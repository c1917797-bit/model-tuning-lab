#!/usr/bin/env python3
"""Record a selected Image2 design result for one slide."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

from workflow_common import read_json, resolve_project, sha256, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--slide", required=True, type=int)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    project = resolve_project(args.project)
    source = Path(args.image).expanduser().resolve()
    if not source.exists():
        raise SystemExit("Design image does not exist: %s" % source)
    state_path = project / "design-run-state.json"
    state = read_json(state_path)
    entry = next((item for item in state.get("slides", []) if int(item["slide_number"]) == args.slide), None)
    if entry is None:
        raise SystemExit("Slide %s is not registered in design-run-state.json" % args.slide)
    if int(entry.get("attempt") or 0) >= 3:
        raise SystemExit("Slide %s already used the maximum of three design candidates" % args.slide)
    attempt = int(entry.get("attempt") or 0) + 1
    archive = project / "design-drafts" / "candidates" / ("slide-%02d-attempt-%02d.png" % (args.slide, attempt))
    archive.parent.mkdir(parents=True, exist_ok=True)
    if source != archive:
        shutil.copy2(source, archive)
    destination = project / "design-drafts" / ("slide-%02d.png" % args.slide)
    shutil.copy2(archive, destination)
    recorded_at = datetime.now(timezone.utc).isoformat()
    candidate = {
        "attempt": attempt,
        "design_path": str(archive.relative_to(project)),
        "sha256": sha256(archive),
        "recorded_at": recorded_at,
    }
    entry.setdefault("candidates", []).append(candidate)
    entry.update({
        "status": "designed",
        "attempt": candidate["attempt"],
        "design_path": str(destination.relative_to(project)),
        "sha256": sha256(destination),
        "recorded_at": recorded_at,
    })
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    if all(item.get("status") == "designed" for item in state["slides"]):
        state["status"] = "ready_for_review"
    write_json(state_path, state)
    print("Recorded slide %s design: %s" % (args.slide, destination))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
