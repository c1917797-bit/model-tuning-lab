#!/usr/bin/env python3
"""Validate Markdown file size budgets for skill repositories.

This gate is intentionally generic: it checks only file size, not domain
semantics. Editorial quality, rule ownership, and duplication still require
human or AI review.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MAX_LINES = 300
DEFAULT_MAX_CHARS = 15000
DEFAULT_MAX_LINE_CHARS = 300
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".tmp",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


PRINCIPLES = [
    "Treat the context window as a shared budget; every paragraph must earn its token cost.",
    "Keep entry files concise: core workflow, routing, and hard boundaries only.",
    "Move detailed guidance, schemas, long examples, and reusable material into focused references, scripts, or assets.",
    "Review the document architecture as a whole before editing; do not satisfy this gate by shaving one line in one place.",
    "Prefer smaller single-purpose Markdown files over one large file that mixes workflow, examples, policy, and templates.",
    "Do not pass the line-length gate by adding unnatural hard wraps; rewrite, split, or use Markdown/YAML structures that remain readable.",
]


@dataclass(frozen=True)
class MarkdownStats:
    path: Path
    lines: int
    chars: int
    max_line_chars: int
    max_line_number: int


@dataclass(frozen=True)
class Violation:
    stats: MarkdownStats
    metric: str
    actual: int
    limit: int


def safe_print(text: str) -> None:
    print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))


def iter_markdown_files(root: Path, exclude_dirs: set[str]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        rel_parts = path.relative_to(root).parts
        if any(part in exclude_dirs for part in rel_parts):
            continue
        if is_inside_git_submodule(path, root):
            continue
        files.append(path)
    return sorted(files)


def is_inside_git_submodule(path: Path, root: Path) -> bool:
    """Skip vendored submodules; parent repo gates should not police them."""
    for parent in path.parents:
        if parent == root:
            return False
        git_marker = parent / ".git"
        if git_marker.is_file():
            return True
    return False


def collect_stats(path: Path) -> MarkdownStats:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    lengths = [len(line) for line in lines]
    max_line_chars = max(lengths, default=0)
    max_line_number = lengths.index(max_line_chars) + 1 if lengths else 0
    return MarkdownStats(
        path=path,
        lines=len(lines),
        chars=len(text),
        max_line_chars=max_line_chars,
        max_line_number=max_line_number,
    )


def validate_stats(
    stats: MarkdownStats,
    *,
    max_lines: int,
    max_chars: int,
    max_line_chars: int,
) -> list[Violation]:
    violations: list[Violation] = []
    checks = [
        ("lines", stats.lines, max_lines),
        ("chars", stats.chars, max_chars),
        ("max_line_chars", stats.max_line_chars, max_line_chars),
    ]
    for metric, actual, limit in checks:
        if actual > limit:
            violations.append(Violation(stats=stats, metric=metric, actual=actual, limit=limit))
    return violations


def format_violation(root: Path, violation: Violation) -> str:
    rel = violation.stats.path.relative_to(root)
    category = classify_markdown(rel)
    return (
        f"  - {rel} [{category}]: {violation.metric} {violation.actual} > {violation.limit} "
        f"(lines={violation.stats.lines}, chars={violation.stats.chars}, "
        f"max_line_chars={violation.stats.max_line_chars} at line {violation.stats.max_line_number})"
    )


def classify_markdown(path: Path) -> str:
    parts = path.parts
    if path.name == "SKILL.md":
        return "skill-entry"
    if parts and parts[0] == "references":
        return "reference"
    if parts and parts[0] == "forward-tests":
        return "forward-test"
    if len(parts) >= 2 and parts[0] == "docs" and parts[1] == "showcase":
        return "showcase"
    if parts and parts[0] == "docs":
        return "docs"
    if path.name == "AGENTS.md":
        return "agent-instructions"
    return "markdown"


def run_self_test() -> int:
    ok = MarkdownStats(path=Path("ok.md"), lines=3, chars=42, max_line_chars=20, max_line_number=2)
    too_large = MarkdownStats(path=Path("large.md"), lines=301, chars=15001, max_line_chars=301, max_line_number=7)
    ok_errors = validate_stats(ok, max_lines=300, max_chars=15000, max_line_chars=300)
    large_errors = validate_stats(too_large, max_lines=300, max_chars=15000, max_line_chars=300)
    if ok_errors:
        print("[ERROR] Self-test valid fixture failed.")
        return 1
    expected = {"lines", "chars", "max_line_chars"}
    actual = {error.metric for error in large_errors}
    if actual != expected:
        print("[ERROR] Self-test invalid fixture did not trigger expected failures.")
        print(f"Expected: {sorted(expected)}")
        print(f"Actual: {sorted(actual)}")
        return 1
    print("[OK] Markdown size validator self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown size budgets.")
    parser.add_argument("root", nargs="?", default=".", type=Path, help="Root directory to scan. Defaults to current directory.")
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES, help="Maximum lines allowed per Markdown file.")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="Maximum characters allowed per Markdown file.")
    parser.add_argument("--max-line-chars", type=int, default=DEFAULT_MAX_LINE_CHARS, help="Maximum characters allowed in a single line.")
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude. May be passed multiple times.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in validator regression tests.")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    root = args.root.resolve()
    if not root.exists():
        print(f"[ERROR] Root directory not found: {root}")
        return 1
    if not root.is_dir():
        print(f"[ERROR] Root path is not a directory: {root}")
        return 1

    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude_dir)
    markdown_files = iter_markdown_files(root, exclude_dirs)
    violations: list[Violation] = []
    for path in markdown_files:
        violations.extend(
            validate_stats(
                collect_stats(path),
                max_lines=args.max_lines,
                max_chars=args.max_chars,
                max_line_chars=args.max_line_chars,
            )
        )

    if violations:
        print("[ERROR] Markdown size gate failed.")
        print()
        print("Revision principles:")
        for principle in PRINCIPLES:
            print(f"  - {principle}")
        print()
        print("Size budgets:")
        print(f"  - max_lines: {args.max_lines}")
        print(f"  - max_chars: {args.max_chars}")
        print(f"  - max_line_chars: {args.max_line_chars}")
        print()
        print("Violations:")
        for violation in violations:
            safe_print(format_violation(root, violation))
        print()
        print("Repair hints:")
        print("  - skill-entry: keep routing and hard boundaries; move examples, schemas, and long guidance out.")
        print("  - reference: split by ownership or add focused assets/scripts when text is boilerplate.")
        print("  - forward-test/showcase: preserve meaning, but wrap readable prose or split large artifacts.")
        return 1

    print(f"[OK] Markdown size gate passed for {len(markdown_files)} file(s).")
    print(f"[OK] Budgets: max_lines={args.max_lines}, max_chars={args.max_chars}, max_line_chars={args.max_line_chars}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
