#!/usr/bin/env python3
"""Replay the bounded real-repository tool-adapter boundary audit."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=REPO, text=True)


def main() -> int:
    tracked = git("ls-files").splitlines()
    adapter_names = sorted(name for name in tracked if
        name in {"CLAUDE.md", ".cursorrules"} or
        name.startswith((".codex/", ".opencode/", ".cursor/")))
    if adapter_names != ["CLAUDE.md"]:
        raise RuntimeError(f"tracked adapter inventory changed: {adapter_names}")
    shim = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    if shim != "@AGENTS.md\n" or git("show", "origin/main:CLAUDE.md") != shim:
        raise RuntimeError("Claude adapter is not the exact main one-line shim")
    for phrase in ("repository maintainer", ".agents/skills.registry.yaml",
                   ".agents/skills/**/SKILL.md", "Tool-specific files are adapters"):
        if phrase not in agents:
            raise RuntimeError(f"canonical bootstrap pointer missing: {phrase}")
    print(json.dumps({
        "tracked_adapters": adapter_names,
        "claude_sha256": hashlib.sha256(shim.encode()).hexdigest(),
        "agents_sha256": hashlib.sha256(agents.encode()).hexdigest(),
        "duplicate_governance_rules": False,
        "scope": "current tracked repository adapters only",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
