#!/usr/bin/env python3
"""Replay the bounded real-repository tool-adapter boundary audit."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ADAPTER_FILES = ("CLAUDE.md", ".cursorrules")
ADAPTER_DIRS = (".codex", ".opencode", ".cursor")


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=REPO, text=True)


def adapter_inventory(root: Path) -> list[str]:
    """Include untracked adapters; do not silently follow external symlinks."""
    found = []
    for name in ADAPTER_FILES + ADAPTER_DIRS:
        path = root / name
        if path.is_symlink():
            raise RuntimeError(f"adapter symlink needs review: {name}")
        candidates = [path] if path.is_file() else path.rglob("*")
        for candidate in candidates:
            if candidate.is_symlink():
                raise RuntimeError("adapter symlink needs review")
            if candidate.is_file():
                found.append(candidate.relative_to(root).as_posix())
    return sorted(found)


def audit_boundary(root: Path, main_shim: str) -> dict:
    adapters = adapter_inventory(root)
    if adapters != ["CLAUDE.md"]:
        raise RuntimeError(f"adapter inventory changed: {adapters}")
    shim = (root / "CLAUDE.md").read_text(encoding="utf-8")
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    if shim != "@AGENTS.md\n" or main_shim != shim:
        raise RuntimeError("Claude adapter is not the exact main one-line shim")
    for phrase in ("repository maintainer", ".agents/skills.registry.yaml",
                   ".agents/skills/**/SKILL.md", "Tool-specific files are adapters"):
        if phrase not in agents:
            raise RuntimeError(f"canonical bootstrap pointer missing: {phrase}")
    return {
        "existing_adapters": adapters,
        "claude_sha256": hashlib.sha256(shim.encode()).hexdigest(),
        "agents_sha256": hashlib.sha256(agents.encode()).hexdigest(),
        "duplicate_governance_rules": False,
        "scope": "actual current repository root adapters, including untracked files",
    }


def main() -> int:
    tracked = git("ls-files").splitlines()
    adapter_names = sorted(name for name in tracked if
        name in ADAPTER_FILES or name.startswith(tuple(x + "/" for x in ADAPTER_DIRS)))
    if adapter_names != ["CLAUDE.md"]:
        raise RuntimeError(f"tracked adapter inventory changed: {adapter_names}")
    result = audit_boundary(REPO, git("show", "origin/main:CLAUDE.md"))
    result["tracked_adapters"] = adapter_names
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
