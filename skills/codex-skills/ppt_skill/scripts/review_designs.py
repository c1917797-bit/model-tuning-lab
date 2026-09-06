#!/usr/bin/env python3
"""Run deterministic preflight checks before editable slide reconstruction."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

from workflow_common import emphasis_contract, normalize_deck_spec, read_json, resolve_project, write_json


REQUIRED_SEMANTIC_CHECKS = (
    "contract_match",
    "no_pseudo_text",
    "required_assets_present",
    "information_density",
    "red_discipline",
    "structural_color_clarity",
    "no_dashboard_wall",
    "no_crop_overlap_or_drift",
    "template_match",
    "no_simulated_official_ui",
    "no_redundant_copy",
    "visual_semantics_explicit",
    "distinct_views_and_states",
    "asset_decomposition_feasible",
)


def review_slide(
    project: Path,
    slide: Dict[str, Any],
    state_entry: Dict[str, Any],
    semantic_entry: Dict[str, Any],
) -> Dict[str, Any]:
    issues: List[str] = []
    design_path_value = state_entry.get("design_path")
    if not design_path_value:
        issues.append("No selected design image was recorded")
        return {"slide_number": slide["slide_number"], "passed": False, "issues": issues}
    design_path = project / design_path_value
    if not design_path.exists():
        issues.append("Recorded design image is missing: %s" % design_path_value)
        return {"slide_number": slide["slide_number"], "passed": False, "issues": issues}
    try:
        with Image.open(design_path) as image:
            width, height = image.size
    except Exception as exc:
        issues.append("Design image cannot be opened: %s" % exc)
        return {"slide_number": slide["slide_number"], "passed": False, "issues": issues}
    aspect = width / float(height)
    if abs(aspect - (16.0 / 9.0)) > 0.02:
        issues.append("Design must use a 16:9 canvas; found %sx%s" % (width, height))
    if width < 1280 or height < 720:
        issues.append("Design resolution is below 1280x720")
    if not slide.get("title") or not slide.get("core_judgment"):
        issues.append("Canonical title or core judgment is missing from deck_spec.json")
    semantic_checks = semantic_entry.get("checks") if isinstance(semantic_entry, dict) else None
    if not isinstance(semantic_checks, dict):
        issues.append("Agent semantic review is missing for this slide")
    else:
        for key in REQUIRED_SEMANTIC_CHECKS:
            if semantic_checks.get(key) is not True:
                issues.append("Agent semantic review failed: %s" % key)
    contract = emphasis_contract(slide)
    # Inventory attention-grabbing emphasis only, not ordinary structural colors.
    # Structural mapping and visual weight are checked by the visual reviewer.
    observed = semantic_entry.get("observed_emphasis_targets")
    if (not isinstance(observed, list) or
            any(not isinstance(x, str) for x in observed)):
        issues.append("Missing observed_emphasis_targets inventory from visual review")
    elif sorted(observed) != sorted(contract["targets"]):
        issues.append("Observed emphasis does not match the declared content targets")
    return {
        "observed_emphasis_targets": observed,
        "slide_number": slide["slide_number"],
        "passed": not issues,
        "issues": issues,
        "image": str(design_path.relative_to(project)),
        "dimensions": [width, height],
        "semantic_checks": semantic_checks or {},
        "notes": semantic_entry.get("notes", []) if isinstance(semantic_entry, dict) else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    args = parser.parse_args()
    project = resolve_project(args.project)
    spec = normalize_deck_spec(read_json(project / "deck_spec.json"))
    state = read_json(project / "design-run-state.json")
    states = {int(item["slide_number"]): item for item in state.get("slides", [])}
    semantic_path = project / "design-review-input.json"
    semantic_payload = read_json(semantic_path) if semantic_path.exists() else {"slides": []}
    semantic_by_slide = {
        int(item["slide_number"]): item
        for item in semantic_payload.get("slides", [])
        if isinstance(item, dict) and item.get("slide_number") is not None
    }
    reviews = []
    for slide in sorted(spec.get("slides", []), key=lambda item: int(item["slide_number"])):
        number = int(slide["slide_number"])
        entry = states.get(number, {"slide_number": number})
        reviews.append(review_slide(project, slide, entry, semantic_by_slide.get(number, {})))
    passed = bool(reviews) and all(item["passed"] for item in reviews)
    payload = {
        "schema_version": 1,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed else "blocked",
        "slides": reviews,
        "note": "Structural image checks and agent semantic checks must both pass before reconstruction.",
    }
    write_json(project / "design-review.json", payload)
    state["status"] = "review_passed" if passed else "review_blocked"
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(project / "design-run-state.json", state)
    print("Design review: %s" % payload["status"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
