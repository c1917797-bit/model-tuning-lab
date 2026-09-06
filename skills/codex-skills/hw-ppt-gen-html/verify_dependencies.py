#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def pass_check(name: str, detail: str = "") -> None:
    print(f"通过 {name}{'：' + detail if detail else ''}")


def check_python() -> bool:
    version = sys.version_info
    pass_check("Python", f"{version.major}.{version.minor}.{version.micro}")
    return True


def main() -> int:
    ok = True
    ok = check_python() and ok
    root = Path(__file__).resolve().parent
    agent_path = root / ".codex" / "agents" / "html_ppt_visual_qa_checker.toml"
    if agent_path.exists():
        text = agent_path.read_text(encoding="utf-8")
        if 'name = "html_ppt_visual_qa_checker"' in text:
            pass_check("Codex visual QA checker agent", str(agent_path.relative_to(root)))
        else:
            print("失败 Codex visual QA checker agent：name 不匹配")
            ok = False
    else:
        print("失败 Codex visual QA checker agent：文件不存在")
        ok = False

    if ok:
        print("通过 依赖检查完成")
        return 0

    print("失败 依赖检查未通过")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
