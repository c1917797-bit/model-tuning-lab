#!/usr/bin/env python3
"""Create template mappings and one full-slide Image2 design task per slide."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from workflow_common import DEFAULT_CATALOG, emphasis_contract, normalize_deck_spec, read_json, resolve_project, validate_deck_spec, write_json


LAYOUT_PREFERENCES = {
    "layered-architecture": [39, 40, 41, 42],
    "architecture": [39, 40, 41, 42, 7, 36, 37],
    "left-image-right-insights": [19, 21, 23, 9, 25],
    "right-image-left-insights": [9, 25, 19, 21, 23],
    "three-column": [17, 19, 21, 23, 18, 20, 22],
    "two-column": [19, 21, 23, 9, 25, 18, 20, 22],
    "table": [26, 30],
    "comparison-table": [26, 30],
    "summary": [5, 7, 23, 6],
    "overview-grid": [5, 7, 23],
    "process": [36, 37, 38],
    "pipeline": [36, 37, 39],
    "timeline": [38, 6],
    "chart": [31, 32, 33, 34, 35, 10, 28],
}


def choose_template(slide: Dict[str, Any], catalog: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    layout = str(slide.get("layout_type") or "").strip()
    role = str(slide.get("page_role") or "").strip()
    preferred = LAYOUT_PREFERENCES.get(layout, [])
    visual = slide.get("main_visual") if isinstance(slide.get("main_visual"), dict) else {}
    visual_type = str(visual.get("type") or visual.get("nature") or "").lower()
    density = str(slide.get("density") or "high").lower()
    ranked = []
    for item in catalog["slides"]:
        score = 0
        reasons = []
        if role in item["page_roles"]:
            score += 100
            reasons.append("page role")
        if layout in item["layout_types"]:
            score += 80
            reasons.append("content structure")
        if item["source_slide"] in preferred:
            score += max(1, 60 - preferred.index(item["source_slide"]) * 4)
            reasons.append("preferred layout page")
        if any(term in visual_type for term in ("screenshot", "photo", "image", "visual")) and item["image_slots"]:
            score += 40
            reasons.append("image slot")
        if "table" in visual_type and item["supports_table"]:
            score += 40
            reasons.append("table support")
        if "chart" in visual_type and item["supports_chart"]:
            score += 40
            reasons.append("chart support")
        if item["density"] == density:
            score += 20
            reasons.append("density")
        elif density in {"medium-high", "high"} and item["density"] == "high":
            score += 15
            reasons.append("high-density fit")
        ranked.append((score, -int(item["source_slide"]), item, reasons))
    score, _, selected, reasons = max(ranked, key=lambda entry: (entry[0], entry[1]))
    reason = "Selected %s slide %s by %s (score %s)" % (
        selected["template_id"],
        selected["source_slide"],
        ", ".join(reasons) if reasons else "nearest available page type",
        score,
    )
    return selected, reason


def insight_reference(slide: Dict[str, Any]) -> Dict[str, Any] | None:
    library = Path(__file__).resolve().parents[1] / "assets" / "insight-reference"
    catalog = read_json(library / "catalog.json")
    requested = slide.get("insight_reference_id")
    candidates = [item for item in catalog["slides"] if
                  (item["reference_id"] == requested if requested else
                   slide.get("page_role") in item["page_roles"])]
    if requested and not candidates:
        raise SystemExit("Unknown insight_reference_id: %s" % requested)
    if not candidates:
        return None
    item = dict(candidates[0])
    item["preview"] = str((library / item["preview"]).resolve())
    item["usage"] = "Reference evidence organization only; rebuild editable objects using current canonical text and assets."
    return item


def canonical_text(slide: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": slide["title"],
        "core_judgment": slide["core_judgment"],
        "supports": slide.get("supports", []),
        "bottom_conclusion": slide.get("bottom_conclusion", ""),
        "labels": slide.get("labels", []),
        "source_ids": slide.get("source_ids", []),
    }


def prepare(project: Path, catalog_path: Path) -> None:
    spec = normalize_deck_spec(read_json(project / "deck_spec.json"))
    validate_deck_spec(spec)
    catalog = read_json(catalog_path)
    prompt_dir = project / "design-prompts"
    draft_dir = project / "design-drafts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    draft_dir.mkdir(parents=True, exist_ok=True)
    mappings: List[Dict[str, Any]] = []
    jobs: List[Dict[str, Any]] = []
    states: List[Dict[str, Any]] = []
    for slide in sorted(spec["slides"], key=lambda item: int(item["slide_number"])):
        number = int(slide["slide_number"])
        selected, reason = choose_template(slide, catalog)
        preview = (catalog_path.parent / selected["preview"]).resolve()
        mapping = {
            "slide_number": number,
            "template_id": selected["template_id"],
            "source_slide": selected["source_slide"],
            "layout_type": slide["layout_type"],
            "page_role": slide["page_role"],
            "template_preview": str(preview),
            "selection_reason": reason,
            "content_bounds": selected["content_bounds"],
            "insight_reference": insight_reference(slide),
        }
        mappings.append(mapping)
        prompt_path = prompt_dir / ("slide-%02d.json" % number)
        design_path = draft_dir / ("slide-%02d.png" % number)
        prompt = {
            "schema_version": 1,
            "slide_number": number,
            "canvas": {"width": 1600, "height": 900, "aspect_ratio": "16:9"},
            "template_reference": mapping,
            "canonical_text": canonical_text(slide),
            "content_contract": slide,
            "color_system": spec.get("color_system") or {
                "structural_palette": ["#356A8A", "#438478", "#786493"],
                "role_colors": {},
                "usage": "Use coordinated muted colors for categories, components, stages and chart series. Establish role-to-color mapping once and reuse it across pages. Keep text dark and fills light; no color quota.",
            },
            "emphasis": emphasis_contract(slide),
            "global_style": {
                "background": "white",
                "body_color": "deep gray",
                "accent": "Use color_system for structural colors. Reserve muted red for explicit emphasis.targets; an empty emphasis list does not disable structural color.",
                "fonts": ["Microsoft YaHei", "Arial"],
                "density": "high but structured",
                "avoid": [
                    "dashboard card wall",
                    "meaningless pale red panels",
                    "decorative icons",
                    "large unused whitespace",
                    "invented official product UI",
                ],
            },
            "instructions": [
                "Keep body text dark on white. Use color_system to distinguish categories, components, stages and chart series through coordinated headings, icons, lines and light fills. Structural color is not emphasis and needs no per-object target. Keep peer colors equal in visual weight. Reserve red or other attention-grabbing treatment for emphasis.targets; do not color Analysis labels or invent a winning route. Preserve original evidence-image colors.",
                "Generate a complete 16:9 slide design draft using the rendered Huawei template page as the layout reference.",
                "Inspect the supplemental insight_reference preview when present; adapt its evidence organization without copying historical claims, branding, or full-page bitmap into the final deck.",
                "Use the canonical text exactly; this image is a visual blueprint and is not the source of final editable text.",
                "Use supplied official screenshots as-is and do not imitate or redraw official product UI.",
                "Keep one primary judgment, one main case or visual, and at most three support groups.",
            ],
            "output_path": str(design_path),
        }
        write_json(prompt_path, prompt)
        jobs.append({
            "slide_number": number,
            "prompt_file": str(prompt_path.relative_to(project)),
            "output_file": str(design_path.relative_to(project)),
            "status": "pending",
        })
        states.append({
            "slide_number": number,
            "status": "pending",
            "attempt": 0,
            "candidates": [],
            "design_path": None,
            "sha256": None,
        })
    now = datetime.now(timezone.utc).isoformat()
    write_json(project / "template-map.json", {"schema_version": 1, "slides": mappings})
    write_json(project / "design-jobs.json", {"schema_version": 1, "created_at": now, "slides": jobs})
    write_json(project / "design-run-state.json", {
        "schema_version": 1,
        "updated_at": now,
        "status": "waiting_for_designs",
        "slides": states,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    args = parser.parse_args()
    project = resolve_project(args.project)
    catalog = Path(args.catalog).expanduser().resolve()
    prepare(project, catalog)
    print("Prepared full-slide design tasks in %s" % project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
