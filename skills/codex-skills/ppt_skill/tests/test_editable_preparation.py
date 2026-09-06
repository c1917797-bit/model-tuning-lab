from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CATALOG = ROOT / "assets" / "huawei-template" / "template-catalog.json"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=True)


class EditablePreparationTests(unittest.TestCase):
    def test_worker_prompt_contains_canonical_text_and_no_unfilled_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "deck"
            brief = Path(tmp) / "brief.md"
            brief.write_text("One-slide deck", encoding="utf-8")
            run("python3", str(SCRIPTS / "huawei_ppt.py"), "init", "--brief", str(brief), "--out", str(project))
            spec = {
                "schema_version": 1,
                "deck_name": "prompt-smoke",
                "slides": [{
                    "slide_number": 1,
                    "page_role": "architecture",
                    "layout_type": "layered-architecture",
                    "title": "Canonical title must survive reconstruction",
                    "core_judgment": "The draft is a visual blueprint, not a text source.",
                    "main_visual": {"type": "architecture", "description": "Five stages"},
                    "supports": ["Editable text", "Editable shapes"],
                    "bottom_conclusion": "No full-slide bitmap is allowed.",
                    "content_nature": "report-analysis",
                    "required_assets": [],
                    "editable_priority": "high",
                }],
            }
            (project / "deck_spec.json").write_text(json.dumps(spec), encoding="utf-8")
            run("python3", str(SCRIPTS / "prepare_design_jobs.py"), str(project), "--catalog", str(CATALOG))
            candidate = project / "candidate.png"
            Image.new("RGB", (1600, 900), "white").save(candidate)
            run("python3", str(SCRIPTS / "record_design_result.py"), str(project), "--slide", "1", "--image", str(candidate))
            checks = {
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
            (project / "design-review-input.json").write_text(json.dumps({"slides": [{"slide_number": 1, "checks": checks, "observed_emphasis_targets": [], "notes": []}]}), encoding="utf-8")
            run("python3", str(SCRIPTS / "review_designs.py"), str(project))
            run("python3", str(SCRIPTS / "huawei_ppt.py"), "prepare-editable", str(project))
            page_dir = project / "editable-run" / "pages" / "page_001"
            self.assertFalse((page_dir / "text_hints.json").exists())
            self.assertFalse((page_dir / "text_hints.png").exists())
            prompt = project / "editable-run" / "pages" / "page_001" / "worker-prompt.md"
            run("python3", str(SCRIPTS / "build_worker_prompt.py"), str(project), "--page", "1", "--out", str(prompt))
            text = prompt.read_text(encoding="utf-8")

        self.assertIn("Canonical title must survive reconstruction", text)
        self.assertIn("No full-slide bitmap is allowed.", text)
        self.assertIn("model vision", text)
        self.assertIn("Do not call PaddleOCR", text)
        self.assertNotIn("{{", text)


if __name__ == "__main__":
    unittest.main()
