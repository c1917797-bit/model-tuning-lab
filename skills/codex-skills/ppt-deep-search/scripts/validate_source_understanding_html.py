#!/usr/bin/env python3
"""Windows/Playwright port of html-ppt-skill/scripts/render.sh."""

from __future__ import annotations

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
MIN_IMAGE_SCALE = 0.8


class SlideSourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.slides: list[dict[str, str]] = []
        self.non_section_slide_classes: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        class_attr = attr_map.get("class", "")
        class_tokens = class_attr.split()
        has_slide_class = "slide" in class_tokens
        if tag.lower() == "section" and has_slide_class:
            self.slides.append(
                {
                    "index": str(len(self.slides) + 1),
                    "tag": tag,
                    "class": class_attr,
                    "id": attr_map.get("id", ""),
                    "title": attr_map.get("data-title", "") or attr_map.get("aria-label", ""),
                }
            )
        elif has_slide_class:
            self.non_section_slide_classes.append(
                {
                    "tag": tag,
                    "class": class_attr,
                    "id": attr_map.get("id", ""),
                }
            )


def import_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Python Playwright is required. Install it with "
            "`python -m pip install playwright` and `python -m playwright install chromium`."
        ) from exc
    return sync_playwright


def inspect_slide_source(html_file: Path) -> dict[str, object]:
    parser = SlideSourceParser()
    parser.feed(html_file.read_text(encoding="utf-8"))
    return {
        "slides": parser.slides,
        "non_section_slide_classes": parser.non_section_slide_classes,
    }


def count_slides(html_file: Path) -> int:
    source = inspect_slide_source(html_file)
    count = len(source["slides"])
    return count if count > 0 else 1


def file_url(html_file: Path, index: int | None = None) -> str:
    url = html_file.resolve().as_uri()
    if index is not None:
        url += f"#/{index}"
    return url


def visible_image_scale_issues(page, slide_index: int) -> list[dict[str, object]]:
    return page.evaluate(
        """([slideIndex, minScale]) => {
          function visible(el) {
            const style = getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            return style.display !== 'none' &&
              style.visibility !== 'hidden' &&
              Number(style.opacity || 1) > 0.01 &&
              rect.width > 0 &&
              rect.height > 0;
          }
          const slides = [...document.querySelectorAll('.deck .slide, section.slide')].filter(visible);
          const active =
            slides.find((slide) => slide.classList.contains('is-active')) ||
            slides[0] ||
            document.body;
          return [...active.querySelectorAll('img')]
            .map((img, index) => {
              const rect = img.getBoundingClientRect();
              const naturalWidth = img.naturalWidth || 0;
              const naturalHeight = img.naturalHeight || 0;
              const renderedWidth = rect.width;
              const renderedHeight = rect.height;
              const scale = naturalWidth && naturalHeight
                ? Math.min(renderedWidth / naturalWidth, renderedHeight / naturalHeight)
                : 0;
              const broken = !img.complete || naturalWidth <= 0 || naturalHeight <= 0;
              const invisible = !visible(img);
              const tinySource = naturalWidth < 160 || naturalHeight < 120;
              return {
                slide: slideIndex,
                image: index + 1,
                src: img.getAttribute('src') || '',
                alt: img.getAttribute('alt') || '',
                naturalWidth: Math.round(naturalWidth),
                naturalHeight: Math.round(naturalHeight),
                renderedWidth: Math.round(renderedWidth),
                renderedHeight: Math.round(renderedHeight),
                scale: Math.round(scale * 100) / 100,
                broken,
                invisible,
                tinySource,
                fail: !tinySource && !broken && !invisible && scale < minScale
              };
            })
            .filter((item) => item.fail);
        }""",
        [slide_index, MIN_IMAGE_SCALE],
    )


def current_slide_state(page) -> dict[str, object]:
    return page.evaluate(
        """() => {
          function visible(el) {
            const style = getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            return style.display !== 'none' &&
              style.visibility !== 'hidden' &&
              Number(style.opacity || 1) > 0.01 &&
              rect.width > 0 &&
              rect.height > 0;
          }
          const slides = [...document.querySelectorAll('section.slide')];
          const activeIndex = slides.findIndex((slide) =>
            slide.classList.contains('is-active') ||
            slide.classList.contains('active') ||
            slide.getAttribute('aria-hidden') === 'false' ||
            visible(slide)
          );
          const hashMatch = location.hash.match(/#\\/(\\d+)/);
          return {
            hash: location.hash,
            hashIndex: hashMatch ? Number(hashMatch[1]) : null,
            activeIndex: activeIndex >= 0 ? activeIndex + 1 : null,
            slideCount: slides.length
          };
        }"""
    )


def slide_state_matches(state: dict[str, object], expected_index: int) -> bool:
    return state.get("hashIndex") == expected_index or state.get("activeIndex") == expected_index


def check_keyboard_navigation(page, html_file: Path, count: int, timeout_ms: int) -> list[str]:
    if count <= 1:
        return []
    page.goto(file_url(html_file, 1), wait_until="load", timeout=timeout_ms)
    page.wait_for_timeout(500)
    page.locator("body").click(position={"x": 10, "y": 10})
    start = current_slide_state(page)
    issues: list[str] = []
    if not slide_state_matches(start, 1):
        issues.append(
            "Initial route `#/1` did not activate slide 1 "
            f"(hash={start.get('hash')}, active={start.get('activeIndex')})."
        )

    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(500)
    after_right = current_slide_state(page)
    if not slide_state_matches(after_right, 2):
        issues.append(
            "ArrowRight did not navigate from slide 1 to slide 2 "
            f"(hash={after_right.get('hash')}, active={after_right.get('activeIndex')})."
        )

    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(500)
    after_left = current_slide_state(page)
    if not slide_state_matches(after_left, 1):
        issues.append(
            "ArrowLeft did not navigate back from slide 2 to slide 1 "
            f"(hash={after_left.get('hash')}, active={after_left.get('activeIndex')})."
        )

    if issues:
        print("[ERROR] html-ppt keyboard navigation QA failed.")
        for issue in issues:
            print(f"  - {issue}")
        print(
            "    React: Keep the html-ppt runtime keyboard handler intact. "
            "ArrowRight must advance one slide and ArrowLeft must return one slide in the file:// review experience."
        )
    else:
        print("[OK] keyboard navigation: ArrowRight advances and ArrowLeft returns.")
    return issues


def render_one(page, url: str, target: Path, timeout_ms: int, slide_index: int) -> list[dict[str, object]]:
    page.goto(url, wait_until="load", timeout=timeout_ms)
    page.wait_for_timeout(500)
    issues = visible_image_scale_issues(page, slide_index)
    page.screenshot(path=str(target), full_page=False)
    print(f"  OK {target}")
    return issues


def print_image_scale_errors(issues: list[dict[str, object]]) -> None:
    print("[ERROR] html-ppt render QA failed: evidence images are scaled below 80%.")
    for issue in issues:
        label = str(issue.get("alt") or issue.get("src") or "image")[:80]
        print(
            "  - Slide "
            + str(issue["slide"])
            + ", image "
            + str(issue["image"])
            + ": scale="
            + str(issue["scale"])
            + " rendered="
            + str(issue["renderedWidth"])
            + "x"
            + str(issue["renderedHeight"])
            + " natural="
            + str(issue["naturalWidth"])
            + "x"
            + str(issue["naturalHeight"])
            + " "
            + label
        )
    print(
        "    React: Keep the source image near its original size, split dense figures across pages, "
        "crop or enlarge the relevant subfigure, rebuild small tables as HTML, or reduce competing content."
    )
    print(
        "    Note: This gate checks rendered image scale only; visual QA must still inspect readability, "
        "cropping, layout overlap, and broken visual context."
    )


def print_slide_diagnostics(source: dict[str, object], count: int, count_arg: str) -> None:
    slides = source["slides"]
    non_section = source["non_section_slide_classes"]
    if count_arg == "all":
        print(f"[INFO] detected {len(slides)} section.slide node(s); rendering {count} slide(s).")
    else:
        print(f"[INFO] rendering explicit slide count: {count}. Source has {len(slides)} section.slide node(s).")
    for slide in slides:
        title = slide["title"] or slide["id"] or "(untitled)"
        print(f"  - slide {slide['index']}: <{slide['tag']} class=\"{slide['class']}\"> {title}")
    if non_section:
        print("[WARN] found non-section elements with class token `slide`; they are not counted as pages.")
        for item in non_section[:10]:
            label = item["id"] or "(no id)"
            print(f"  - <{item['tag']} class=\"{item['class']}\"> {label}")
        if len(non_section) > 10:
            print(f"  - ... {len(non_section) - 10} more")


def clean_png_outputs(out_path: Path, count: int) -> int:
    if count <= 1 or not out_path.exists():
        return 0
    removed = 0
    for png in out_path.glob("*.png"):
        png.unlink()
        removed += 1
    if removed:
        print(f"[INFO] cleaned {removed} stale PNG file(s) from {out_path}")
    return removed


def write_manifest(out_path: Path, html_file: Path, count: int, width: int, height: int, png_paths: list[Path]) -> None:
    if count <= 1:
        return
    manifest = {
        "html": str(html_file.resolve()),
        "slide_count": count,
        "viewport": {"width": width, "height": height},
        "png_files": [str(path.resolve()) for path in png_paths],
        "note": "Render succeeded. Independent visual QA is still required.",
    }
    manifest_path = out_path / "render-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] wrote manifest {manifest_path}")


def render(html_file: Path, count_arg: str, out_arg: str | None, width: int, height: int, timeout_ms: int) -> int:
    if not html_file.exists():
        raise RuntimeError(f"{html_file} not found")
    if not html_file.is_file():
        raise RuntimeError(f"{html_file} is not a file")

    source = inspect_slide_source(html_file)
    if count_arg == "all":
        count = len(source["slides"]) or 1
    else:
        try:
            count = int(count_arg)
        except ValueError as exc:
            raise RuntimeError("count must be a positive integer or `all`") from exc
        if count < 1:
            raise RuntimeError("count must be >= 1")

    print_slide_diagnostics(source, count, count_arg)

    stem = html_file.stem
    if out_arg:
        out_path = Path(out_arg)
    elif count > 1:
        out_path = html_file.parent / f"{stem}-png"
    else:
        out_path = html_file.parent / f"{stem}.png"

    if count > 1:
        out_path.mkdir(parents=True, exist_ok=True)
        clean_png_outputs(out_path, count)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    sync_playwright = import_playwright()
    image_scale_issues: list[dict[str, object]] = []
    navigation_issues: list[str] = []
    png_paths: list[Path] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        try:
            navigation_issues.extend(check_keyboard_navigation(page, html_file, count, timeout_ms))
            if count == 1:
                target = out_path if out_path.suffix else out_path / f"{stem}.png"
                png_paths.append(target)
                image_scale_issues.extend(render_one(page, file_url(html_file), target, timeout_ms, 1))
            else:
                for index in range(1, count + 1):
                    target = out_path / f"{stem}_{index:02d}.png"
                    png_paths.append(target)
                    image_scale_issues.extend(render_one(page, file_url(html_file, index), target, timeout_ms, index))
        finally:
            browser.close()

    write_manifest(out_path, html_file, count, width, height, png_paths)
    print(f"done: rendered {count} slide(s) from {html_file}")
    print(
        "note: render success only means screenshots were produced and hard image-scale checks passed; "
        "independent visual QA is still required."
    )
    if image_scale_issues:
        print_image_scale_errors(image_scale_issues)
        return 1
    if navigation_issues:
        return 1
    return 0


def run_self_test() -> list[str]:
    errors: list[str] = []
    if DEFAULT_WIDTH != 1920 or DEFAULT_HEIGHT != 1080:
        errors.append("unexpected default viewport")
    if not file_url(Path("/tmp/example.html"), 3).endswith("#/3"):
        errors.append("hash URL generation failed")
    parser = SlideSourceParser()
    parser.feed(
        '<section class="slide is-active" data-title="A"></section>'
        '<div class="slide-number"></div>'
        '<section class="not-slide"></section>'
        '<section class="slide" id="b"></section>'
    )
    if len(parser.slides) != 2:
        errors.append("section.slide parser count failed")
    if parser.non_section_slide_classes:
        errors.append("slide-number should not be treated as a slide token")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render html-ppt slides to PNG on Windows using Playwright."
    )
    parser.add_argument("html", nargs="?", help="HTML file to render.")
    parser.add_argument("count", nargs="?", default="1", help="Slide count, or `all`. Default: 1.")
    parser.add_argument("out_dir", nargs="?", help="Output PNG file for one slide, or directory for multiple slides.")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help=f"Viewport width. Default: {DEFAULT_WIDTH}.")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help=f"Viewport height. Default: {DEFAULT_HEIGHT}.")
    parser.add_argument("--timeout-ms", type=int, default=30000, help="Page load timeout. Default: 30000.")
    parser.add_argument("--self-test", action="store_true", help="Run embedded self-test.")
    args = parser.parse_args()

    if args.self_test:
        errors = run_self_test()
        if errors:
            print("[ERROR] html-ppt render self-test failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
        print("[OK] html-ppt render self-test passed.")
        return 0

    if not args.html:
        parser.error("html is required unless --self-test is used")
    if args.width < 640:
        parser.error("--width must be >= 640")
    if args.height < 360:
        parser.error("--height must be >= 360")
    if args.timeout_ms < 1000:
        parser.error("--timeout-ms must be >= 1000")

    try:
        return render(Path(args.html), args.count, args.out_dir, args.width, args.height, args.timeout_ms)
    except Exception as exc:
        print("[ERROR] html-ppt render failed:")
        print(f"  - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
