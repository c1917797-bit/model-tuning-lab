#!/usr/bin/env python3
"""Build an editable-page worker prompt with canonical text from deck_spec.json."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from workflow_common import SKILL_ROOT, normalize_deck_spec, read_json, resolve_project


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--page", required=True, type=int)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    project = resolve_project(args.project)
    run_dir = project / "editable-run"
    jobs = read_json(run_dir / "page_jobs.json")
    page_id = "page_%03d" % args.page
    job = next((item for item in jobs.get("pages", []) if item.get("page_id") == page_id), None)
    if job is None:
        raise SystemExit("Page %s not found in editable run" % page_id)
    page_dir_value = Path(str(job.get("page_dir") or ("pages/" + page_id)))
    page_dir = page_dir_value if page_dir_value.is_absolute() else (run_dir / page_dir_value).resolve()
    temp_prompt = page_dir / "upstream-worker-prompt.md"
    subprocess.run([
        sys.executable,
        str(SKILL_ROOT / "scripts" / "upstream_build_page_worker_prompt.py"),
        str(run_dir),
        "--page", str(args.page),
        "--out", str(temp_prompt),
    ], check=True, capture_output=True, text=True)
    spec = normalize_deck_spec(read_json(project / "deck_spec.json"))
    slide = next((item for item in spec["slides"] if int(item["slide_number"]) == args.page), None)
    if slide is None:
        raise SystemExit("Slide %s not found in deck_spec.json" % args.page)
    canonical = json.dumps(slide, ensure_ascii=False, indent=2)
    base = temp_prompt.read_text(encoding="utf-8")
    addition = (SKILL_ROOT / "prompts" / "editable-page-worker.md").read_text(encoding="utf-8")
    replacements = {
        "{{SLIDE_CONTRACT_PATH}}": str(project / "deck_spec.json"),
        "{{TEMPLATE_MAPPING_PATH}}": str(project / "template-map.json"),
        "{{DESIGN_DRAFT_PATH}}": str(project / "design-drafts" / ("slide-%02d.png" % args.page)),
        "{{ASSET_PATHS}}": json.dumps(slide.get("required_assets", []), ensure_ascii=False),
        "{{PAGE_WORKSPACE}}": str(page_dir),
        "{{SLIDE_ID}}": page_id,
        "{{CANONICAL_SLIDE_SPEC}}": canonical,
        "{{PROJECT_DIR}}": str(project),
    }
    for placeholder, value in replacements.items():
        addition = addition.replace(placeholder, value)
    output = Path(args.out).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep upstream mechanics first and the unified Huawei constraints last so
    # local model-vision and fidelity rules cannot be overridden by upstream
    # OCR/text-hint guidance.
    combined = base + "\n\n" + addition + "\n\n## Canonical slide specification\n\n```json\n" + canonical + "\n```\n"
    if "{{" in combined:
        raise SystemExit("Unfilled placeholder remains in worker prompt")
    output.write_text(combined, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
