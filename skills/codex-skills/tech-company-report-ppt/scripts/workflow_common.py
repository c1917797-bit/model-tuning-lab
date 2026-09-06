#!/usr/bin/env python3
"""Shared helpers for the unified Huawei presentation workflow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_CATALOG = SKILL_ROOT / "assets" / "huawei-template" / "template-catalog.json"
DEFAULT_TEMPLATE = SKILL_ROOT / "assets" / "huawei-template" / "PPT模板.pptx"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit("Missing JSON file: %s" % path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit("Invalid JSON in %s: %s" % (path, exc)) from exc


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_project(value: str) -> Path:
    project = Path(value).expanduser().resolve()
    if not project.exists() or not project.is_dir():
        raise SystemExit("Project directory does not exist: %s" % project)
    return project


def normalize_slide(slide: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(slide)
    template = normalized.get("template") if isinstance(normalized.get("template"), dict) else {}
    normalized["slide_number"] = normalized.get("slide_number", normalized.get("page_number"))
    normalized["page_role"] = normalized.get("page_role", normalized.get("role"))
    normalized["layout_type"] = normalized.get("layout_type", template.get("layout_type"))
    normalized["core_judgment"] = normalized.get("core_judgment", normalized.get("core_message"))
    normalized["supports"] = normalized.get("supports", normalized.get("support_groups", []))
    normalized["main_visual"] = normalized.get("main_visual", normalized.get("primary_case", {}))
    normalized["required_assets"] = normalized.get("required_assets", [])
    return normalized


def normalize_deck_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(spec)
    slides = normalized.get("slides")
    if isinstance(slides, list):
        normalized["slides"] = [normalize_slide(slide) for slide in slides]
    return normalized


def validate_deck_spec(spec: Dict[str, Any]) -> None:
    slides = spec.get("slides")
    if not isinstance(slides, list) or not slides:
        raise SystemExit("deck_spec.json must contain a non-empty slides array")
    seen = set()
    required = ("slide_number", "page_role", "layout_type", "title", "core_judgment")
    for index, slide in enumerate(slides, 1):
        missing = [key for key in required if not slide.get(key)]
        if missing:
            raise SystemExit("Slide %s is missing required fields: %s" % (index, ", ".join(missing)))
        number = int(slide["slide_number"])
        if number in seen:
            raise SystemExit("Duplicate slide_number: %s" % number)
        seen.add(number)


def emphasis_contract(slide: Dict[str, Any]) -> Dict[str, Any]:
    value = slide.get("emphasis", {"targets": [], "reason": "", "meaning": "none"})
    if not isinstance(value, dict):
        raise SystemExit("emphasis must be an object")
    targets = value.get("targets")
    if (not isinstance(targets, list) or
            any(not isinstance(x, str) or not x.strip() for x in targets) or
            len(set(targets)) != len(targets)):
        raise SystemExit("emphasis.targets must be unique nonempty strings")
    if targets and (value.get("meaning") not in {"difference", "change", "recommendation"}
                    or not isinstance(value.get("reason"), str) or not value["reason"].strip()):
        raise SystemExit("Color emphasis needs a content-based reason and meaning")
    return {"targets": targets, "reason": value.get("reason", ""),
            "meaning": value.get("meaning", "none") if targets else "none"}
