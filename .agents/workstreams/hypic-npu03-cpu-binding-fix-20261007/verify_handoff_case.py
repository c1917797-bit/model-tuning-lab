#!/usr/bin/env python3
"""Replay the pinned branch-local maintainer handoff acceptance snapshot."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parent.parents[2]
CHECKPOINT = "622d68af221d76cf9098db8ef4ce9141da2cf047"
PREFIX = ".agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/"
PINNED_SHA = {
    "HANDOFF.md": "6f850f99cc4d2390e590ef9336f5045b9e042d3e3a8928f044612f950d0674b7",
    "HANDOFF_HISTORY.md": "0e3acab34a83a78c03b398c7055db561ae66c3021c5ffe56a1f68025f1d127fc",
    "test_handoff_current.py": "15093b0b5a6135f80aad07b726553e0116ef4c7b2fe50d5feb736f02f599e827",
}


def git(*args: str) -> bytes:
    return subprocess.check_output(("git", *args), cwd=REPO)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    require(git("rev-parse", "origin/main:.agents/skills/"
                "mst-maintainer-handoff/SKILL.md").decode().strip()
            == "f9eba56e3048643163342b1bab024632929b382c",
            "main handoff Skill blob changed")
    snapshots = {}
    for name, expected in PINNED_SHA.items():
        content = git("show", f"{CHECKPOINT}:{PREFIX}{name}")
        require(hashlib.sha256(content).hexdigest() == expected,
                f"historical {name} bytes changed")
        snapshots[name] = content.decode("utf-8")
    handoff = snapshots["HANDOFF.md"]
    history = snapshots["HANDOFF_HISTORY.md"]
    require(re.findall(r"^## ([0-8])\. ", handoff, re.M)
            == list("012345678"), "required section order drift")
    require(len(handoff.splitlines()) <= 150
            and len(history.splitlines()) >= 380,
            "current/history size boundary drift")
    for marker in ("cache10r3", "NPU4–7", "HANDOFF_HISTORY.md",
                   "Validation Commands", "Do Not Do", "Recovery / Resume"):
        require(marker in handoff, f"handoff missing {marker}")
    require("cache10r3 terminal decision" in history,
            "historical evidence lost")
    subprocess.run(("git", "diff", "--quiet", f"{CHECKPOINT}^", CHECKPOINT,
                    "--", ".agents/HANDOFF.md"), cwd=REPO, check=True)
    subprocess.run(("git", "merge-base", "--is-ancestor", CHECKPOINT, "HEAD"),
                   cwd=REPO, check=True)
    print(json.dumps({
        "skill": "mst-maintainer-handoff",
        "checkpoint": CHECKPOINT,
        "branch_local_sections": 9,
        "current_lines": len(handoff.splitlines()),
        "history_lines": len(history.splitlines()),
        "global_handoff_unchanged": True,
        "scope": "branch-local current handoff and preserved history",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
