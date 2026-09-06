#!/usr/bin/env python3
"""Validate compact web-article-capture source packages."""

from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
SCREENSHOT_NAME_RE = re.compile(r"(screenshot|snapshot|full[-_ ]?page|viewport|rendered[-_ ]?page)", re.IGNORECASE)


def markdown_image_paths(source_md: Path) -> list[str]:
    text = source_md.read_text(encoding="utf-8")
    paths: list[str] = []
    for match in MARKDOWN_IMAGE_RE.finditer(text):
        target = match.group(1).strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        target = target.split()[0].strip()
        if target.startswith(("http://", "https://", "#")):
            continue
        paths.append(target)
    return paths


def image_files(images_dir: Path) -> list[Path]:
    if not images_dir.exists():
        return []
    return [
        path for path in images_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def is_screenshot_name(path: Path) -> bool:
    return bool(SCREENSHOT_NAME_RE.search(path.name))


def package_dirs(root: Path) -> list[Path]:
    if (root / "source.md").exists():
        return [root]
    return sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith("."))


def validate(root: Path, require_images: str) -> list[str]:
    errors: list[str] = []
    packages = package_dirs(root)
    if not packages:
        return [f"no source package directories found under {root}"]

    for package in packages:
        label = package.name
        source_md = package / "source.md"
        images_dir = package / "images"

        if not source_md.exists():
            errors.append(f"{label}: missing source.md")
            continue

        allowed_root_entries = {"source.md", "images"}
        for entry in package.iterdir():
            if entry.name not in allowed_root_entries:
                errors.append(f"{label}: unexpected root entry {entry.name}; packages should contain source.md and images/")

        if not images_dir.exists() or not images_dir.is_dir():
            errors.append(f"{label}: missing images/")
            continue

        for path in images_dir.rglob("*"):
            if path.is_dir():
                continue
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                errors.append(f"{label}: non-image file in images/: {path.relative_to(package).as_posix()}")
            if is_screenshot_name(path):
                errors.append(f"{label}: screenshot-like file in images/: {path.relative_to(package).as_posix()}")

        local_images = image_files(images_dir)
        referenced_images = markdown_image_paths(source_md)

        if require_images == "always" and not local_images:
            errors.append(f"{label}: images/ has no image files")
        if require_images == "when-referenced" and referenced_images and not local_images:
            errors.append(f"{label}: source.md references images but images/ is empty")

        for ref in referenced_images:
            ref_path = (package / ref).resolve()
            try:
                ref_path.relative_to(package.resolve())
            except ValueError:
                errors.append(f"{label}: image reference points outside package: {ref}")
                continue
            if not ref_path.exists():
                errors.append(f"{label}: missing referenced image {ref}")
            elif ref_path.suffix.lower() not in IMAGE_EXTENSIONS:
                errors.append(f"{label}: referenced image has unsupported extension {ref}")

    return errors


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        good = root / "good"
        (good / "images").mkdir(parents=True)
        (good / "images" / "hero.jpg").write_bytes(b"jpg")
        (good / "source.md").write_text(
            "# Example\n\nSource: https://example.com\n\n![Hero](images/hero.jpg)\n",
            encoding="utf-8",
        )

        bad = root / "bad"
        (bad / "images").mkdir(parents=True)
        (bad / "images" / "fallback-page-snapshot.png").write_bytes(b"png")
        (bad / "extra.txt").write_text("extra", encoding="utf-8")
        (bad / "source.md").write_text(
            "# Example\n\n![Missing](images/missing.jpg)\n",
            encoding="utf-8",
        )

        good_errors = validate(good, "always")
        bad_errors = validate(bad, "always")
        if good_errors:
            print("[ERROR] valid package failed:")
            print("\n".join(good_errors))
            return 1
        if not any("unexpected root entry" in error for error in bad_errors):
            print("[ERROR] extra root files were not rejected:")
            print("\n".join(bad_errors))
            return 1
        if not any("missing referenced image" in error for error in bad_errors):
            print("[ERROR] missing markdown image was not rejected:")
            print("\n".join(bad_errors))
            return 1
        if not any("screenshot-like file" in error for error in bad_errors):
            print("[ERROR] screenshot-like image was not rejected:")
            print("\n".join(bad_errors))
            return 1
    print("[OK] web-article-capture validator self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate compact web-article-capture source packages.")
    parser.add_argument("root", nargs="?", type=Path)
    parser.add_argument("--require-images", choices=("never", "when-referenced", "always"), default="when-referenced")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.root is None:
        parser.error("root is required unless --self-test is used")

    errors = validate(args.root, args.require_images)
    if errors:
        print("[ERROR] web-article-capture validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("[OK] web-article-capture validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
