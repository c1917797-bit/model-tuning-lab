#!/usr/bin/env python3
"""Exercise the unified workflow through editppt record/finalize with three slides."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CATALOG = ROOT / "assets" / "huawei-template" / "template-catalog.json"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_source(path: Path, label: str) -> None:
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((55, 55, 1545, 845), outline="#D5D9DE", width=2)
    draw.rectangle((55, 720, 1545, 845), fill="#F4F5F6")
    draw.text((80, 80), label, fill="#222222")
    image.save(path)


def base_manifest(page_id: str, request: Dict[str, Any], title: str) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "page_id": page_id,
        "strategy": "native-editable-reconstruction",
        "slide": request["slide"],
        "content_box": request["content_box"],
        "source": {
            "path": "source.png",
            "width_px": request["source_size_px"]["width"],
            "height_px": request["source_size_px"]["height"],
        },
        "text_inventory": [{"id": "title", "required_text": [title]}],
        "visual_inventory": [{"id": "structure", "description": "Native structural shapes and editable text."}],
        "background_strategy": {
            "mode": "native-or-script",
            "source_consistency_contract": "Preserve the white canvas, Huawei red accents, grid, and object positions with native objects.",
            "removed_foreground": [],
            "comparison_note": "The page uses a native white background and editable structural objects.",
        },
        "quality_checks": {
            "font_size_calibrated": True,
            "visual_inventory_matched": True,
            "background_strategy_checked": True,
            "shape_corner_geometry_checked": True,
        },
        "text_boxes": [{
            "id": "title",
            "text": title,
            "box_px": [70, 55, 1460, 75],
            "font": "Arial",
            "font_size": 27,
            "bold": True,
            "color": "#222222",
            "fit_text": True,
            "z_index": 50,
        }],
        "shapes": [{
            "id": "title_rule",
            "type": "line",
            "points_px": [70, 140, 1530, 140],
            "stroke": "#C7000B",
            "stroke_width": 2,
            "z_index": 5,
        }],
        "images": [],
        "asset_provenance": [],
    }


def architecture_manifest(page_id: str, request: Dict[str, Any], title: str) -> Dict[str, Any]:
    manifest = base_manifest(page_id, request, title)
    stages = ["Prepare", "Compress", "Deliver", "First Run", "Diagnose"]
    for index, stage in enumerate(stages):
        x = 80 + index * 300
        manifest["shapes"].append({
            "id": "stage_%s" % index,
            "type": "rect",
            "box_px": [x, 280, 240, 210],
            "fill": "#FFFFFF",
            "stroke": "#9AA1A9",
            "stroke_width": 1.2,
            "z_index": 10,
        })
        manifest["text_boxes"].append({
            "id": "stage_text_%s" % index,
            "text": stage,
            "box_px": [x + 20, 330, 200, 60],
            "font": "Arial",
            "font_size": 18,
            "bold": True,
            "align": "center",
            "color": "#C7000B" if index in (1, 3) else "#222222",
            "z_index": 30,
        })
        if index < len(stages) - 1:
            manifest["shapes"].append({
                "id": "link_%s" % index,
                "type": "line",
                "points_px": [x + 240, 385, x + 300, 385],
                "stroke": "#C7000B",
                "stroke_width": 2,
                "z_index": 12,
            })
    manifest["text_inventory"].append({"id": "stages", "required_text": stages})
    return manifest


def screenshot_manifest(page_id: str, request: Dict[str, Any], title: str, page_dir: Path) -> Dict[str, Any]:
    manifest = base_manifest(page_id, request, title)
    assets = page_dir / "assets"
    assets.mkdir(exist_ok=True)
    screenshot = Image.new("RGB", (900, 540), "#EEF2F7")
    draw = ImageDraw.Draw(screenshot)
    draw.rectangle((35, 35, 865, 505), outline="#496C9E", width=5)
    draw.rectangle((70, 95, 530, 180), fill="#FFFFFF", outline="#BBC3CD")
    draw.rectangle((70, 220, 800, 440), fill="#FFFFFF", outline="#BBC3CD")
    screenshot.save(assets / "official-ui.png")
    manifest["images"] = [{
        "id": "official_ui",
        "path": "assets/official-ui.png",
        "box_px": [80, 190, 880, 530],
        "alt": "Replaceable official product screenshot",
        "z_index": 20,
    }]
    manifest["asset_provenance"] = [{
        "path": "assets/official-ui.png",
        "source": "assets/official-ui.png",
        "source_type": "user-provided",
        "original_asset": True,
        "asset_id": "official-ui.png",
        "provenance_note": "Original replaceable product UI asset supplied through the slide content contract.",
    }]
    labels = ["Evidence source", "What it shows", "Platform meaning"]
    for index, label in enumerate(labels):
        y = 220 + index * 150
        manifest["shapes"].append({
            "id": "insight_%s" % index,
            "type": "rect",
            "box_px": [1030, y, 470, 105],
            "fill": "#FFFFFF",
            "stroke": "#C8CDD3",
            "stroke_width": 1,
            "z_index": 10,
        })
        manifest["text_boxes"].append({
            "id": "insight_text_%s" % index,
            "text": label,
            "box_px": [1055, y + 25, 420, 50],
            "font": "Arial",
            "font_size": 17,
            "bold": True,
            "color": "#C7000B" if index == 1 else "#222222",
            "z_index": 30,
        })
    manifest["text_inventory"].append({"id": "labels", "required_text": labels})
    manifest["visual_inventory"].append({"id": "official_ui", "path": "assets/official-ui.png", "description": "Original product UI asset supplied through the slide content contract as a separate replaceable image object."})
    return manifest


def table_manifest(page_id: str, request: Dict[str, Any], title: str) -> Dict[str, Any]:
    manifest = base_manifest(page_id, request, title)
    headers = ["Mechanism", "Engineering value", "Current scope"]
    rows = [
        ["Model protocol", "Common call surface", "App runtime"],
        ["Structured output", "Inspectable handoff", "Typed result"],
        ["Evaluation", "Repeatable regression", "Known dataset"],
        ["Observability", "Failure localization", "Tool trajectory"],
    ]
    x_positions = [90, 540, 1040]
    widths = [450, 500, 470]
    for col, header in enumerate(headers):
        manifest["shapes"].append({
            "id": "header_cell_%s" % col,
            "type": "rect",
            "box_px": [x_positions[col], 200, widths[col], 85],
            "fill": "#F2F3F5",
            "stroke": "#AEB4BB",
            "stroke_width": 1,
            "z_index": 10,
        })
        manifest["text_boxes"].append({
            "id": "header_text_%s" % col,
            "text": header,
            "box_px": [x_positions[col] + 18, 222, widths[col] - 36, 42],
            "font": "Arial",
            "font_size": 16,
            "bold": True,
            "color": "#C7000B",
            "z_index": 30,
        })
    for row_index, row in enumerate(rows):
        y = 285 + row_index * 105
        for col, value in enumerate(row):
            manifest["shapes"].append({
                "id": "cell_%s_%s" % (row_index, col),
                "type": "rect",
                "box_px": [x_positions[col], y, widths[col], 105],
                "fill": "#FFFFFF",
                "stroke": "#D5D9DE",
                "stroke_width": 1,
                "z_index": 10,
            })
            manifest["text_boxes"].append({
                "id": "cell_text_%s_%s" % (row_index, col),
                "text": value,
                "box_px": [x_positions[col] + 18, y + 30, widths[col] - 36, 45],
                "font": "Arial",
                "font_size": 15,
                "bold": col == 0,
                "color": "#222222",
                "z_index": 30,
            })
    required = headers + [value for row in rows for value in row]
    manifest["text_inventory"].append({"id": "table", "required_text": required})
    return manifest


def build_page(page_dir: Path, manifest: Dict[str, Any], agent_id: str, run_dir: Path) -> None:
    write_json(page_dir / "manifest.json", manifest)
    run("editppt", "page", "build", str(page_dir))
    run("editppt", "page", "contact-sheet", str(page_dir))
    run("editppt", "page", "validate", str(page_dir), "--report", str(page_dir / "validation.json"))
    write_json(page_dir / "page_result.json", {
        "page_manifest": "manifest.json",
        "imagegen_jobs": "imagegen-jobs.json",
        "page_pptx": "page.pptx",
        "preview": "preview.png",
        "contact_sheet": "split_assets_contact.png",
        "validation": "validation.json",
        "page_result": "page_result.json",
    })
    write_json(page_dir / "visual-fidelity.json", {
        "passed": True,
        "checks": {
            "visual_semantics_preserved": True,
            "region_geometry_preserved": True,
            "density_preserved": True,
            "distinct_views_and_states_preserved": True,
            "complex_assets_not_approximated": True,
            "icon_language_consistent": True,
            "typography_hierarchy_preserved": True,
        },
        "regions": [],
        "blocking_issues": [],
    })
    prompt = page_dir / "worker-prompt.md"
    prompt.write_text("Smoke worker prompt\n", encoding="utf-8")
    page_id = page_dir.name
    run("editppt", "run", "dispatch", str(run_dir), "--page", page_id, "--agent-id", agent_id, "--prompt-file", str(prompt))
    run("editppt", "run", "record", str(run_dir), "--page", page_id, "--agent-id", agent_id)


def main() -> int:
    out = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path("/private/tmp/ppt-skills-unified-e2e")
    if out.exists():
        shutil.rmtree(out)
    wrapper_dir = out.parent / "ppt-skills-unified-e2e-bin"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    editppt_python = Path("/Users/rain/.local/share/uv/tools/image-to-editable-ppt-cli/bin/python")
    wrapper = wrapper_dir / "editppt"
    wrapper.write_text(
        "#!/bin/zsh\nPYTHONPATH=%s exec %s -m editppt.cli \"$@\"\n" % (
            str(ROOT / "cli" / "editppt"),
            str(editppt_python),
        ),
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    os.environ["PATH"] = str(wrapper_dir) + os.pathsep + os.environ.get("PATH", "")
    brief = out.parent / "ppt-skills-unified-e2e-brief.md"
    brief.write_text("Three-slide unified workflow smoke deck.", encoding="utf-8")
    run("python3", str(SCRIPTS / "huawei_ppt.py"), "init", "--brief", str(brief), "--out", str(out))
    spec = {
        "schema_version": 1,
        "deck_name": "unified-huawei-ppt-smoke",
        "slides": [
            {"slide_number": 1, "page_role": "architecture", "layout_type": "layered-architecture", "title": "On-device AI becomes a managed product capability", "core_judgment": "The platform manages delivery and runtime behavior.", "supports": ["Prepare", "Deliver", "Diagnose"], "bottom_conclusion": "Model engineering spans the product lifecycle.", "required_assets": []},
            {"slide_number": 2, "page_role": "evidence", "layout_type": "left-image-right-insights", "title": "Product evidence remains separate from interpretation", "core_judgment": "Official UI stays replaceable while explanations stay editable.", "supports": ["Source", "Meaning", "Boundary"], "bottom_conclusion": "Evidence and analysis remain traceable.", "required_assets": ["official-ui.png"]},
            {"slide_number": 3, "page_role": "table", "layout_type": "table", "title": "Dense comparisons remain editable and readable", "core_judgment": "Each cell can be revised without redrawing the page.", "supports": ["Mechanism", "Value", "Scope"], "bottom_conclusion": "High density does not require a flattened slide.", "required_assets": []},
        ],
    }
    write_json(out / "deck_spec.json", spec)
    run("python3", str(SCRIPTS / "prepare_design_jobs.py"), str(out), "--catalog", str(CATALOG))
    for slide in spec["slides"]:
        number = slide["slide_number"]
        candidate = out / ("candidate-%02d.png" % number)
        make_source(candidate, slide["title"])
        run("python3", str(SCRIPTS / "record_design_result.py"), str(out), "--slide", str(number), "--image", str(candidate))
    semantic_checks = {
        "contract_match": True,
        "no_pseudo_text": True,
        "required_assets_present": True,
        "information_density": True,
        "red_discipline": True,
                "structural_color_clarity": True,
        "no_dashboard_wall": True,
        "no_crop_overlap_or_drift": True,
        "template_match": True,
        "no_simulated_official_ui": True,
        "no_redundant_copy": True,
        "visual_semantics_explicit": True,
        "distinct_views_and_states": True,
        "asset_decomposition_feasible": True,
    }
    write_json(out / "design-review-input.json", {
        "slides": [
            {"slide_number": slide["slide_number"], "checks": semantic_checks, "observed_emphasis_targets": [], "notes": []}
            for slide in spec["slides"]
        ]
    })
    run("python3", str(SCRIPTS / "review_designs.py"), str(out))
    run("python3", str(SCRIPTS / "huawei_ppt.py"), "prepare-editable", str(out))
    run_dir = out / "editable-run"
    builders = [architecture_manifest, screenshot_manifest, table_manifest]
    for index, builder in enumerate(builders, 1):
        page_dir = run_dir / "pages" / ("page_%03d" % index)
        request = json.loads((page_dir / "page_request.json").read_text(encoding="utf-8"))
        title = spec["slides"][index - 1]["title"]
        manifest = builder(page_dir.name, request, title, page_dir) if builder is screenshot_manifest else builder(page_dir.name, request, title)
        build_page(page_dir, manifest, "smoke-%s" % index, run_dir)
    run("python3", str(SCRIPTS / "huawei_ppt.py"), "finalize", str(out))
    final = out / "final" / "unified-huawei-ppt-smoke.pptx"
    if not final.exists():
        raise SystemExit("Missing final PPTX")
    if sorted(path.name for path in out.iterdir()) != ["final"]:
        raise SystemExit("Successful finalize did not clean production workfiles")
    print(final)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
