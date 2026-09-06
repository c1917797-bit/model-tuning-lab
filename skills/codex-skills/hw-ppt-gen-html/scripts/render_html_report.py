#!/usr/bin/env python3
"""Render and sanity-check a scrolling HTML report at desktop width."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
MIN_BODY_HEIGHT = 900


def import_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Python Playwright is required. Install it with "
            "`python -m pip install playwright` and `python -m playwright install chromium`."
        ) from exc
    return sync_playwright


def file_url(html_file: Path) -> str:
    return html_file.resolve().as_uri()


def inspect_report(page, width: int) -> dict[str, object]:
    return page.evaluate(
        """(viewportWidth) => {
          function visible(el) {
            const style = getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            return style.display !== 'none' &&
              style.visibility !== 'hidden' &&
              Number(style.opacity || 1) > 0.01 &&
              rect.width > 0 &&
              rect.height > 0;
          }
          const body = document.body;
          const doc = document.documentElement;
          const all = [...document.querySelectorAll('body *')].filter(visible);
          function hasClippingAncestor(el) {
            let parent = el.parentElement;
            while (parent && parent !== document.body && parent !== document.documentElement) {
              const style = getComputedStyle(parent);
              const overflowX = style.overflowX;
              const rect = parent.getBoundingClientRect();
              if (['auto', 'scroll', 'hidden', 'clip'].includes(overflowX) &&
                  rect.left >= -2 && rect.right <= viewportWidth + 2) {
                return true;
              }
              parent = parent.parentElement;
            }
            return false;
          }
          const overflowing = all
            .map((el) => {
              const rect = el.getBoundingClientRect();
              const tag = el.tagName.toLowerCase();
              const label =
                el.getAttribute('id') ||
                el.getAttribute('class') ||
                (el.textContent || '').trim().slice(0, 80);
              return {
                tag,
                label,
                left: Math.round(rect.left),
                right: Math.round(rect.right),
                width: Math.round(rect.width),
                clippedByAncestor: hasClippingAncestor(el)
              };
            })
            .filter((item) => (item.left < -2 || item.right > viewportWidth + 2) && !item.clippedByAncestor)
            .slice(0, 20);
          const images = [...document.querySelectorAll('img')]
            .map((img, index) => {
              const rect = img.getBoundingClientRect();
              return {
                index: index + 1,
                src: img.getAttribute('src') || '',
                alt: img.getAttribute('alt') || '',
                complete: img.complete,
                naturalWidth: img.naturalWidth || 0,
                naturalHeight: img.naturalHeight || 0,
                renderedWidth: Math.round(rect.width),
                renderedHeight: Math.round(rect.height),
                visible: visible(img)
              };
            });
          const brokenImages = images.filter((img) =>
            img.visible && (!img.complete || img.naturalWidth <= 0 || img.naturalHeight <= 0)
          );
          const emptyAltImages = images.filter((img) => img.visible && img.alt.trim() === '');
          const slideCount = document.querySelectorAll('section.slide').length;
          return {
            title: document.title || '',
            bodyTextLength: (body.innerText || '').trim().length,
            bodyHeight: Math.max(body.scrollHeight, doc.scrollHeight),
            bodyWidth: Math.max(body.scrollWidth, doc.scrollWidth),
            viewportWidth,
            slideCount,
            overflowing,
            imageCount: images.length,
            brokenImages,
            emptyAltImages: emptyAltImages.slice(0, 20)
          };
        }""",
        width,
    )


def issues_from_inspection(info: dict[str, object], strict_alt: bool) -> list[str]:
    issues: list[str] = []
    if int(info.get("slideCount") or 0) > 0:
        issues.append(
            "Report mode found `section.slide` nodes. Use render_html_ppt.py for a deck, "
            "or remove slide runtime structure for a scrolling report."
        )
    if int(info.get("bodyTextLength") or 0) < 500:
        issues.append("Report body text is too short to be a substantive analysis report.")
    if int(info.get("bodyHeight") or 0) < MIN_BODY_HEIGHT:
        issues.append("Report body height is too small; screenshot may only capture a hero or sparse page.")
    if int(info.get("bodyWidth") or 0) > int(info.get("viewportWidth") or DEFAULT_WIDTH) + 2:
        issues.append(
            f"Document scrollWidth ({info.get('bodyWidth')}) exceeds viewport width "
            f"({info.get('viewportWidth')}); horizontal overflow is not allowed in report mode."
        )
    overflowing = info.get("overflowing") or []
    if overflowing:
        issues.append("Visible elements overflow the desktop viewport: " + json.dumps(overflowing, ensure_ascii=False))
    broken = info.get("brokenImages") or []
    if broken:
        issues.append("Visible broken images found: " + json.dumps(broken, ensure_ascii=False))
    empty_alt = info.get("emptyAltImages") or []
    if strict_alt and empty_alt:
        issues.append("Visible images with empty alt text found: " + json.dumps(empty_alt, ensure_ascii=False))
    return issues


def render_report(
    html_file: Path,
    out_dir: Path,
    width: int,
    height: int,
    timeout_ms: int,
    strict_alt: bool,
) -> int:
    if not html_file.exists():
        raise RuntimeError(f"{html_file} not found")
    if not html_file.is_file():
        raise RuntimeError(f"{html_file} is not a file")
    out_dir.mkdir(parents=True, exist_ok=True)

    screenshot = out_dir / "desktop-full.png"
    manifest = out_dir / "report-render-manifest.json"

    sync_playwright = import_playwright()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        try:
            page.goto(file_url(html_file), wait_until="load", timeout=timeout_ms)
            page.wait_for_timeout(700)
            info = inspect_report(page, width)
            page.screenshot(path=str(screenshot), full_page=True)
        finally:
            browser.close()

    issues = issues_from_inspection(info, strict_alt)
    status = "failed" if issues else "succeeded"
    manifest.write_text(
        json.dumps(
            {
                "status": status,
                "mode": "html-report",
                "html": str(html_file.resolve()),
                "screenshot": str(screenshot.resolve()),
                "viewport": {"width": width, "height": height},
                "inspection": info,
                "issues": issues,
                "note": (
                    "Render succeeded. Independent visual QA is still required."
                    if not issues
                    else "Render screenshot was produced, but report-mode QA checks failed."
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[INFO] wrote screenshot {screenshot}")
    print(f"[INFO] wrote manifest {manifest}")
    if issues:
        print("[ERROR] html-report render QA failed:")
        for issue in issues:
            print(f"  - {issue}")
        print(
            "    React: Fix the scrolling report layout for a 1920px desktop viewport. "
            "Do not switch to slide mode to satisfy this report gate."
        )
        return 1
    print("done: rendered desktop HTML report screenshot")
    print("note: render success only means the desktop screenshot and hard checks passed; independent visual QA is still required.")
    return 0


def run_self_test() -> list[str]:
    errors: list[str] = []
    if not file_url(Path("/tmp/example.html")).endswith("example.html"):
        errors.append("file URL generation failed")
    ok_info = {
        "slideCount": 0,
        "bodyTextLength": 800,
        "bodyHeight": 1400,
        "bodyWidth": 1920,
        "viewportWidth": 1920,
        "overflowing": [],
        "brokenImages": [],
        "emptyAltImages": [],
    }
    if issues_from_inspection(ok_info, strict_alt=True):
        errors.append("valid report inspection should pass")
    bad_info = dict(ok_info)
    bad_info["slideCount"] = 1
    bad_info["bodyWidth"] = 2100
    if len(issues_from_inspection(bad_info, strict_alt=True)) < 2:
        errors.append("invalid report inspection should report slide misuse and overflow")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a scrolling HTML analysis report to a full-page desktop PNG and run report-mode QA."
    )
    parser.add_argument("html", nargs="?", help="Scrolling HTML report file to render.")
    parser.add_argument("out_dir", nargs="?", help="Output directory for desktop-full.png and report-render-manifest.json.")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help=f"Desktop viewport width. Default: {DEFAULT_WIDTH}.")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help=f"Desktop viewport height. Default: {DEFAULT_HEIGHT}.")
    parser.add_argument("--timeout-ms", type=int, default=30000, help="Page load timeout. Default: 30000.")
    parser.add_argument("--allow-empty-alt", action="store_true", help="Do not fail on visible images with empty alt text.")
    parser.add_argument("--self-test", action="store_true", help="Run embedded self-test.")
    args = parser.parse_args()

    if args.self_test:
        errors = run_self_test()
        if errors:
            print("[ERROR] html-report render self-test failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
        print("[OK] html-report render self-test passed.")
        return 0

    if not args.html or not args.out_dir:
        parser.error("html and out_dir are required unless --self-test is used")
    if args.width < 1280:
        parser.error("--width must be >= 1280 for desktop report mode")
    if args.height < 720:
        parser.error("--height must be >= 720")
    if args.timeout_ms < 1000:
        parser.error("--timeout-ms must be >= 1000")

    try:
        return render_report(
            Path(args.html),
            Path(args.out_dir),
            args.width,
            args.height,
            args.timeout_ms,
            strict_alt=not args.allow_empty_alt,
        )
    except Exception as exc:
        print("[ERROR] html-report render failed:")
        print(f"  - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
