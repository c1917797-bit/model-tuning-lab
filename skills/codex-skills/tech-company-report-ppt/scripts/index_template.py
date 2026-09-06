#!/usr/bin/env python3
"""Index the 42-page Huawei template library into a deterministic catalog."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from workflow_common import write_json


GROUPS = {
    "T01": {
        "slides": [1, 2, 3, 4, 8, 24],
        "name": "agenda-and-section",
        "roles": ["cover", "agenda", "section"],
        "layouts": ["agenda", "section-divider"],
        "density": "low",
        "columns": 1,
        "image_slots": 0,
        "recommended": "Agenda, section divider, restrained chapter navigation",
        "unsuitable": "Dense evidence, architecture, or multi-row comparisons",
    },
    "T02": {
        "slides": [5],
        "name": "executive-overview-grid",
        "roles": ["overview", "summary"],
        "layouts": ["summary", "overview-grid"],
        "density": "high",
        "columns": 4,
        "image_slots": 0,
        "recommended": "Executive overview with multiple concise findings",
        "unsuitable": "Single-case explanation or large product screenshot",
    },
    "T03": {
        "slides": [6],
        "name": "logic-pyramid-and-timeline",
        "roles": ["framework", "summary"],
        "layouts": ["summary", "pyramid-timeline"],
        "density": "high",
        "columns": 2,
        "image_slots": 0,
        "recommended": "Causal structure with a companion implementation path",
        "unsuitable": "Screenshot-led evidence page",
    },
    "T04": {
        "slides": [7],
        "name": "capability-framework",
        "roles": ["framework", "summary", "architecture"],
        "layouts": ["summary", "capability-map"],
        "density": "high",
        "columns": 3,
        "image_slots": 0,
        "recommended": "Platform capability landscape and executive synthesis",
        "unsuitable": "Detailed code or long-form narrative",
    },
    "T05": {
        "slides": [9, 25],
        "name": "text-image-explanation",
        "roles": ["evidence", "explanation"],
        "layouts": ["left-image-right-insights", "right-image-left-insights", "narrative"],
        "density": "medium",
        "columns": 2,
        "image_slots": 1,
        "recommended": "One primary screenshot or visual with focused interpretation",
        "unsuitable": "Five-way comparison or deep architecture",
    },
    "T06": {
        "slides": [10, 28, 31, 32, 33, 34, 35],
        "name": "charts-and-kpis",
        "roles": ["metrics", "evidence", "comparison"],
        "layouts": ["chart", "kpi", "quantitative-comparison"],
        "density": "high",
        "columns": 2,
        "image_slots": 0,
        "recommended": "Performance, KPI, benchmark, and quantitative evidence",
        "unsuitable": "Pure conceptual architecture without metrics",
    },
    "T07": {
        "slides": [14, 15, 16],
        "name": "strategy-map",
        "roles": ["strategy", "comparison"],
        "layouts": ["strategy-map", "portfolio"],
        "density": "high",
        "columns": 3,
        "image_slots": 0,
        "recommended": "Ecosystem positioning, option maps, risk-opportunity views",
        "unsuitable": "Precise technical execution flow",
    },
    "T08": {
        "slides": [17, 19, 21, 23],
        "name": "cards-and-columns",
        "roles": ["evidence", "comparison", "summary", "explanation"],
        "layouts": ["two-column", "three-column", "left-image-right-insights", "summary"],
        "density": "high",
        "columns": 3,
        "image_slots": 1,
        "recommended": "Dense technology insight pages with two or three content groups",
        "unsuitable": "Full-width architecture requiring many connected nodes",
    },
    "T09": {
        "slides": [26, 30],
        "name": "table-and-comparison",
        "roles": ["table", "comparison"],
        "layouts": ["table", "comparison-table"],
        "density": "high",
        "columns": 3,
        "image_slots": 0,
        "recommended": "Competitive matrix, capability comparison, evidence-boundary table",
        "unsuitable": "Hero image or narrative case study",
    },
    "T10": {
        "slides": [27],
        "name": "map-and-regions",
        "roles": ["map", "ecosystem"],
        "layouts": ["map", "regional-network"],
        "density": "medium",
        "columns": 1,
        "image_slots": 1,
        "recommended": "Regional distribution, ecosystem reach, geographic network",
        "unsuitable": "Non-geographic technical mechanisms",
    },
    "T11": {
        "slides": [36, 37],
        "name": "process-and-loop",
        "roles": ["process", "architecture"],
        "layouts": ["process", "pipeline", "loop"],
        "density": "high",
        "columns": 4,
        "image_slots": 0,
        "recommended": "Agent loops, runtime pipelines, controlled execution sequences",
        "unsuitable": "Text-heavy legal or source index pages",
    },
    "T12": {
        "slides": [38],
        "name": "timeline",
        "roles": ["timeline", "roadmap"],
        "layouts": ["timeline", "roadmap"],
        "density": "medium",
        "columns": 4,
        "image_slots": 0,
        "recommended": "Evolution timeline or staged delivery sequence",
        "unsuitable": "Static comparison without sequence",
    },
    "T13": {
        "slides": [39, 40, 41, 42],
        "name": "layered-architecture",
        "roles": ["architecture", "framework"],
        "layouts": ["layered-architecture", "architecture", "system-stack"],
        "density": "high",
        "columns": 5,
        "image_slots": 0,
        "recommended": "System stack, distributed OS architecture, AI platform layers",
        "unsuitable": "Simple single-case screenshot page",
    },
    "T14": {
        "slides": [11, 12, 13, 18, 20, 22, 29],
        "name": "mixed-analysis",
        "roles": ["comparison", "explanation", "metrics"],
        "layouts": ["two-column", "three-column", "mixed-analysis"],
        "density": "high",
        "columns": 3,
        "image_slots": 1,
        "recommended": "Mixed qualitative and quantitative analysis with compact sections",
        "unsuitable": "Minimal cover or full-bleed visual",
    },
}


def pptx_slide_count(template: Path) -> int:
    if not template.exists():
        raise SystemExit("Template not found: %s" % template)
    with zipfile.ZipFile(template) as archive:
        names = archive.namelist()
    return len([name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)])


def build_catalog(template: Path) -> Dict[str, Any]:
    count = pptx_slide_count(template)
    by_slide: Dict[int, Dict[str, Any]] = {}
    for template_id, group in GROUPS.items():
        for source_slide in group["slides"]:
            by_slide[source_slide] = {
                "source_slide": source_slide,
                "template_id": template_id,
                "template_name": group["name"],
                "page_roles": group["roles"],
                "layout_types": group["layouts"],
                "density": group["density"],
                "columns": group["columns"],
                "image_slots": group["image_slots"],
                "supports_table": "table" in group["roles"],
                "supports_chart": "metrics" in group["roles"],
                "recommended_content": group["recommended"],
                "unsuitable_content": group["unsuitable"],
                "preview": "previews/slide-%02d.png" % source_slide,
                "content_bounds": {"left": 0.45, "top": 0.75, "right": 12.88, "bottom": 7.05},
            }
    missing = [number for number in range(1, count + 1) if number not in by_slide]
    if missing:
        raise SystemExit("Template catalog mapping missing slides: %s" % missing)
    return {
        "schema_version": 1,
        "template_file": template.name,
        "slide_count": count,
        "slides": [by_slide[number] for number in range(1, count + 1)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    payload = build_catalog(Path(args.template).expanduser().resolve())
    write_json(Path(args.out).expanduser().resolve(), payload)
    print("Indexed %s template slides" % payload["slide_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
