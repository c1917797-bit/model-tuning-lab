#!/usr/bin/env python3
"""Verify local dependencies for web-article-capture."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "scripts" / "validate_capture_package.py"
FORWARD_TESTS = ROOT / "forward-tests"


def main() -> int:
    checks: list[dict[str, object]] = []

    try:
        py_compile.compile(str(VALIDATOR), doraise=True)
        checks.append({"name": "validator compiles", "ok": True})
    except Exception as exc:  # pragma: no cover - defensive reporting path
        checks.append({"name": "validator compiles", "ok": False, "detail": str(exc)})

    self_test = subprocess.run(
        [sys.executable, str(VALIDATOR), "--self-test"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    checks.append(
        {
            "name": "validator self-test",
            "ok": self_test.returncode == 0,
            "stdout": self_test.stdout.strip(),
            "stderr": self_test.stderr.strip(),
        }
    )

    required_forward_files = [
        FORWARD_TESTS / "README.md",
        FORWARD_TESTS / "main-agent-prompt.md",
    ]
    for case_dir in sorted(path for path in FORWARD_TESTS.iterdir() if path.is_dir()):
        required_forward_files.extend(
            [
                case_dir / "main-agent-prompt.md",
                case_dir / "candidate" / "prompt.md",
                case_dir / "candidate" / "input",
                case_dir / "judge" / "rubric.md",
            ]
        )
    missing_forward_files = [
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in required_forward_files
        if not path.exists()
    ]
    checks.append(
        {
            "name": "forward-test protocol files",
            "ok": not missing_forward_files,
            "missing": missing_forward_files,
        }
    )

    result = {
        "ok": all(bool(check["ok"]) for check in checks),
        "checks": checks,
        "python_packages": [],
        "external": ["Codex in-app Browser for real webpage capture"],
        "optional": ["network access to target webpages and image assets during capture"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
