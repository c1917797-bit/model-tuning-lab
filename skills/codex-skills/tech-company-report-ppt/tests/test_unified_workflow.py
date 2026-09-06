from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TEMPLATE = ROOT / "assets" / "huawei-template" / "PPT模板.pptx"


def run_script(name: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPTS / name), *args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


class TemplateCatalogTests(unittest.TestCase):
    def test_catalog_covers_all_42_template_slides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "catalog.json"
            run_script("index_template.py", "--template", str(TEMPLATE), "--out", str(out))
            catalog = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(catalog["slide_count"], 42)
        self.assertEqual(len(catalog["slides"]), 42)
        self.assertEqual({slide["source_slide"] for slide in catalog["slides"]}, set(range(1, 43)))
        for slide in catalog["slides"]:
            self.assertTrue(slide["template_id"])
            self.assertTrue(slide["page_roles"])
            self.assertIn(slide["density"], {"low", "medium", "high"})

    def test_template_selection_matches_representative_page_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "deck"
            project.mkdir()
            catalog = Path(tmp) / "catalog.json"
            run_script("index_template.py", "--template", str(TEMPLATE), "--out", str(catalog))
            spec = {
                "deck_name": "selection-test",
                "slides": [
                    {"slide_number": 1, "page_role": "architecture", "layout_type": "layered-architecture", "title": "Architecture", "core_judgment": "A", "supports": []},
                    {"slide_number": 2, "page_role": "evidence", "layout_type": "left-image-right-insights", "title": "Evidence", "core_judgment": "B", "supports": []},
                    {"slide_number": 3, "page_role": "comparison", "layout_type": "three-column", "title": "Comparison", "core_judgment": "C", "supports": []},
                    {"slide_number": 4, "page_role": "table", "layout_type": "table", "title": "Table", "core_judgment": "D", "supports": []},
                    {"slide_number": 5, "page_role": "summary", "layout_type": "summary", "title": "Summary", "core_judgment": "E", "supports": []},
                ],
            }
            (project / "deck_spec.json").write_text(json.dumps(spec), encoding="utf-8")
            run_script("prepare_design_jobs.py", str(project), "--catalog", str(catalog))
            mapping = json.loads((project / "template-map.json").read_text(encoding="utf-8"))

        selected = {item["slide_number"]: item for item in mapping["slides"]}
        self.assertIn(selected[1]["source_slide"], {39, 40, 41, 42})
        self.assertIn(selected[2]["source_slide"], {9, 19, 21, 23, 25})
        self.assertIn(selected[3]["source_slide"], {17, 19, 21, 23})
        self.assertIn(selected[4]["source_slide"], {26, 30})
        self.assertIn(selected[5]["source_slide"], {5, 7, 23})
        self.assertTrue(all(item["selection_reason"] for item in mapping["slides"]))
        self.assertEqual(selected[4]["insight_reference"]["reference_id"], "R05")

    def test_documented_deck_spec_field_names_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "deck"
            project.mkdir()
            catalog = Path(tmp) / "catalog.json"
            run_script("index_template.py", "--template", str(TEMPLATE), "--out", str(catalog))
            spec = {
                "deck_name": "documented-schema",
                "outline_approved": True,
                "slides": [{
                    "slide_id": "slide-01",
                    "page_number": 1,
                    "role": "evidence",
                    "title": "Official evidence anchors the interpretation",
                    "core_message": "The screenshot and explanation remain separate objects.",
                    "primary_case": {"name": "Product UI", "nature": "official_fact"},
                    "support_groups": [{"heading": "Meaning", "points": ["One fact"]}],
                    "template": {"layout_type": "left-image-right-insights"},
                }],
            }
            (project / "deck_spec.json").write_text(json.dumps(spec), encoding="utf-8")
            run_script("prepare_design_jobs.py", str(project), "--catalog", str(catalog))
            prompt = json.loads((project / "design-prompts" / "slide-01.json").read_text(encoding="utf-8"))

        self.assertEqual(prompt["canonical_text"]["title"], spec["slides"][0]["title"])
        self.assertEqual(prompt["content_contract"]["page_role"], "evidence")
        self.assertEqual(prompt["content_contract"]["layout_type"], "left-image-right-insights")


class DesignWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "deck"
        self.project.mkdir()
        self.catalog = Path(self.tmp.name) / "catalog.json"
        run_script("index_template.py", "--template", str(TEMPLATE), "--out", str(self.catalog))
        self.spec = {
            "deck_name": "three-slide-smoke",
            "slides": [
                {
                    "slide_number": 1,
                    "page_role": "architecture",
                    "layout_type": "layered-architecture",
                    "title": "On-device AI becomes a managed product capability",
                    "core_judgment": "Model delivery and runtime diagnostics are part of the platform.",
                    "main_visual": {"type": "architecture", "description": "A five-stage lifecycle"},
                    "supports": ["Prepare", "Deliver", "Diagnose"],
                    "bottom_conclusion": "The operating system manages more than inference.",
                    "content_nature": "report-analysis",
                    "required_assets": [],
                    "editable_priority": "high",
                },
                {
                    "slide_number": 2,
                    "page_role": "evidence",
                    "layout_type": "left-image-right-insights",
                    "title": "A real product image anchors the technical explanation",
                    "core_judgment": "Screenshots remain replaceable objects.",
                    "main_visual": {"type": "product-screenshot", "description": "Official product UI"},
                    "supports": ["Source", "Meaning"],
                    "bottom_conclusion": "Evidence and interpretation stay distinct.",
                    "content_nature": "official-fact",
                    "required_assets": ["official-ui.png"],
                    "editable_priority": "medium",
                },
                {
                    "slide_number": 3,
                    "page_role": "table",
                    "layout_type": "table",
                    "title": "Dense comparison remains readable and editable",
                    "core_judgment": "Rows compare mechanisms, value, and limits.",
                    "main_visual": {"type": "table", "description": "Three-column comparison"},
                    "supports": ["Mechanism", "Value", "Boundary"],
                    "bottom_conclusion": "The table is a native PowerPoint object.",
                    "content_nature": "report-analysis",
                    "required_assets": [],
                    "editable_priority": "high",
                },
            ],
        }
        (self.project / "deck_spec.json").write_text(json.dumps(self.spec), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_prepare_creates_authoritative_page_jobs_and_state(self) -> None:
        run_script("prepare_design_jobs.py", str(self.project), "--catalog", str(self.catalog))
        jobs = json.loads((self.project / "design-jobs.json").read_text(encoding="utf-8"))
        state = json.loads((self.project / "design-run-state.json").read_text(encoding="utf-8"))

        self.assertEqual(len(jobs["slides"]), 3)
        self.assertEqual(len(state["slides"]), 3)
        self.assertEqual(state["status"], "waiting_for_designs")
        prompt = json.loads((self.project / "design-prompts" / "slide-01.json").read_text(encoding="utf-8"))
        self.assertEqual(prompt["canonical_text"]["title"], self.spec["slides"][0]["title"])
        self.assertEqual(prompt["canvas"], {"width": 1600, "height": 900, "aspect_ratio": "16:9"})
        self.assertTrue(prompt["template_reference"]["source_slide"])

    def test_recording_a_design_updates_hash_and_status(self) -> None:
        run_script("prepare_design_jobs.py", str(self.project), "--catalog", str(self.catalog))
        draft = self.project / "candidate.png"
        Image.new("RGB", (1600, 900), "white").save(draft)
        run_script("record_design_result.py", str(self.project), "--slide", "1", "--image", str(draft))
        state = json.loads((self.project / "design-run-state.json").read_text(encoding="utf-8"))

        first = state["slides"][0]
        self.assertEqual(first["status"], "designed")
        self.assertRegex(first["sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue((self.project / first["design_path"]).exists())

    def test_recording_rejects_a_fourth_design_candidate(self) -> None:
        run_script("prepare_design_jobs.py", str(self.project), "--catalog", str(self.catalog))
        draft = self.project / "candidate.png"
        Image.new("RGB", (1600, 900), "white").save(draft)
        for _ in range(3):
            run_script("record_design_result.py", str(self.project), "--slide", "1", "--image", str(draft))
        fourth = run_script("record_design_result.py", str(self.project), "--slide", "1", "--image", str(draft), check=False)

        self.assertNotEqual(fourth.returncode, 0)
        self.assertIn("three", (fourth.stdout + fourth.stderr).lower())

    def test_review_blocks_missing_or_wrong_aspect_designs(self) -> None:
        run_script("prepare_design_jobs.py", str(self.project), "--catalog", str(self.catalog))
        bad = self.project / "bad.png"
        Image.new("RGB", (1000, 1000), "white").save(bad)
        run_script("record_design_result.py", str(self.project), "--slide", "1", "--image", str(bad))
        result = run_script("review_designs.py", str(self.project), check=False)
        review = json.loads((self.project / "design-review.json").read_text(encoding="utf-8"))

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(review["status"], "blocked")
        self.assertTrue(any("16:9" in issue for issue in review["slides"][0]["issues"]))

    def test_review_passes_three_structurally_valid_designs(self) -> None:
        run_script("prepare_design_jobs.py", str(self.project), "--catalog", str(self.catalog))
        for number in range(1, 4):
            draft = self.project / f"candidate-{number}.png"
            Image.new("RGB", (1600, 900), "white").save(draft)
            run_script("record_design_result.py", str(self.project), "--slide", str(number), "--image", str(draft))
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
        write_review = {"slides": [{"slide_number": number, "checks": checks, "observed_emphasis_targets": [], "notes": []} for number in range(1, 4)]}
        (self.project / "design-review-input.json").write_text(json.dumps(write_review), encoding="utf-8")
        result = run_script("review_designs.py", str(self.project))
        review = json.loads((self.project / "design-review.json").read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(review["status"], "passed")
        self.assertTrue(all(slide["passed"] for slide in review["slides"]))

    def test_review_blocks_when_agent_semantic_review_is_missing(self) -> None:
        run_script("prepare_design_jobs.py", str(self.project), "--catalog", str(self.catalog))
        for number in range(1, 4):
            draft = self.project / f"candidate-{number}.png"
            Image.new("RGB", (1600, 900), "white").save(draft)
            run_script("record_design_result.py", str(self.project), "--slide", str(number), "--image", str(draft))
        result = run_script("review_designs.py", str(self.project), check=False)
        review = json.loads((self.project / "design-review.json").read_text(encoding="utf-8"))

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(review["status"], "blocked")
        self.assertTrue(any("semantic review" in issue.lower() for issue in review["slides"][0]["issues"]))


class UnifiedCliTests(unittest.TestCase):
    def test_doctor_passes_with_bundled_template_catalog_and_editppt(self) -> None:
        result = run_script("huawei_ppt.py", "doctor", check=False)
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(payload["passed"])
        self.assertEqual(next(item for item in payload["checks"] if item["name"] == "template_catalog")["slide_count"], 42)

    def test_init_creates_the_documented_project_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "brief.md"
            brief.write_text("Create a three-slide technology insight deck.", encoding="utf-8")
            project = Path(tmp) / "project"
            run_script("huawei_ppt.py", "init", "--brief", str(brief), "--out", str(project))

            self.assertTrue((project / "brief.md").exists())
            self.assertTrue((project / "outline.md").exists())
            self.assertTrue((project / "deck_spec.json").exists())
            for folder in ["design-prompts", "design-drafts", "editable-run", "qa", "final"]:
                self.assertTrue((project / folder).is_dir(), folder)

    def test_cleanup_keeps_only_final_deliverables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            (project / "final").mkdir(parents=True)
            (project / "final" / "deck.pptx").write_bytes(b"final")
            (project / "final" / "result.md").write_text("temporary")
            (project / "final" / "state.json").write_text("{}")
            (project / "final" / "build.py").write_text("temporary")
            (project / "qa").mkdir()
            (project / "qa" / "contact-sheet.png").write_bytes(b"qa")
            (project / "design-drafts").mkdir()
            (project / "design-drafts" / "slide-01.png").write_bytes(b"draft")
            (project / "project.json").write_text(json.dumps({"stage": "finalized"}), encoding="utf-8")
            result = run_script("huawei_ppt.py", "cleanup", str(project))

            self.assertEqual(result.returncode, 0)
            self.assertEqual(sorted(path.name for path in project.iterdir()), ["final"])
            self.assertEqual(sorted(path.name for path in (project / "final").iterdir()), ["deck.pptx"])

    def test_cleanup_preserves_only_explicit_extra_and_original_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            (project / "final").mkdir(parents=True)
            for name in ["deck.pptx", "requested.pdf", "extra.md", "~$deck.pptx"]:
                (project / "final" / name).write_bytes(b"content")
            (project / "original.pdf").write_bytes(b"original")
            (project / "shared").mkdir()
            (project / "shared" / "input.json").write_text("{}")
            (project / "project.json").write_text(json.dumps({"stage": "finalized"}))
            run_script("huawei_ppt.py", "cleanup", str(project), "--keep-deliverable", "requested.pdf")
            self.assertEqual(sorted(p.name for p in (project / "final").iterdir()), ["deck.pptx", "requested.pdf"])
            self.assertEqual((project / "original.pdf").read_bytes(), b"original")
            self.assertTrue((project / "shared" / "input.json").exists())

    def test_cleanup_rejects_unfinalized_and_symlink_final_without_deletion(self) -> None:
        for stage, symlink in [("editable_prepared", False), ("finalized", True)]:
            with self.subTest(stage=stage, symlink=symlink), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp) / "project"
                project.mkdir()
                final = Path(tmp) / "external" if symlink else project / "final"
                final.mkdir()
                (final / "deck.pptx").write_bytes(b"deck")
                if symlink:
                    (project / "final").symlink_to(final, target_is_directory=True)
                (project / "project.json").write_text(json.dumps({"stage": stage}))
                (project / "qa").mkdir()
                result = run_script("huawei_ppt.py", "cleanup", str(project), check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue((project / "qa").exists())
                self.assertTrue((final / "deck.pptx").exists())

    def test_cleanup_rejects_invalid_whitelist_before_deleting(self) -> None:
        for name in ["../outside.pdf", "missing.pdf", "nested", "linked.pdf"]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp) / "project"
                (project / "final" / "nested").mkdir(parents=True)
                (project / "final" / "deck.pptx").write_bytes(b"deck")
                (project / "final" / "linked.pdf").symlink_to(project / "final" / "deck.pptx")
                (project / "project.json").write_text(json.dumps({"stage": "finalized"}))
                result = run_script("huawei_ppt.py", "cleanup", str(project), "--keep-deliverable", name, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue((project / "project.json").exists())

    def test_cleanup_refuses_when_final_pptx_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            (project / "final").mkdir(parents=True)
            (project / "qa").mkdir()
            blocked = run_script("huawei_ppt.py", "cleanup", str(project), check=False)

            self.assertNotEqual(blocked.returncode, 0)
            self.assertTrue((project / "qa").exists())

    def test_status_reports_missing_outline_approval_without_claiming_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "brief.md"
            brief.write_text("Deck brief", encoding="utf-8")
            project = Path(tmp) / "project"
            run_script("huawei_ppt.py", "init", "--brief", str(brief), "--out", str(project))
            result = run_script("huawei_ppt.py", "status", str(project))
            payload = json.loads(result.stdout)

        self.assertFalse(payload["outline_approved"])
        self.assertEqual(payload["stage"], "outline")

    def test_status_does_not_treat_a_stray_final_pptx_as_finalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "brief.md"
            brief.write_text("Deck brief", encoding="utf-8")
            project = Path(tmp) / "project"
            run_script("huawei_ppt.py", "init", "--brief", str(brief), "--out", str(project))
            metadata = json.loads((project / "project.json").read_text(encoding="utf-8"))
            metadata["stage"] = "editable_prepared"
            (project / "project.json").write_text(json.dumps(metadata), encoding="utf-8")
            (project / "final" / "manual-bypass.pptx").write_bytes(b"not-a-finalized-editppt-deck")
            result = run_script("huawei_ppt.py", "status", str(project))
            payload = json.loads(result.stdout)

        self.assertEqual(payload["stage"], "editable_prepared")
        self.assertIsNone(payload["editable_validation"])

    def test_status_reads_editppt_validation_from_final_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "brief.md"
            brief.write_text("Deck brief", encoding="utf-8")
            project = Path(tmp) / "project"
            run_script("huawei_ppt.py", "init", "--brief", str(brief), "--out", str(project))
            metadata = json.loads((project / "project.json").read_text(encoding="utf-8"))
            metadata["stage"] = "finalized"
            (project / "project.json").write_text(json.dumps(metadata), encoding="utf-8")
            (project / "final" / "editppt-output.pptx").write_bytes(b"validated-editppt-deck")
            validation_dir = project / "editable-run" / "final"
            validation_dir.mkdir(parents=True, exist_ok=True)
            (validation_dir / "validation.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
            result = run_script("huawei_ppt.py", "status", str(project))
            payload = json.loads(result.stdout)

        self.assertEqual(payload["stage"], "finalized")
        self.assertTrue(payload["editable_validation"])

    def test_status_ignores_powerpoint_owner_lock_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "brief.md"
            brief.write_text("Deck brief", encoding="utf-8")
            project = Path(tmp) / "project"
            run_script("huawei_ppt.py", "init", "--brief", str(brief), "--out", str(project))
            (project / "final" / "~$temporary.pptx").write_bytes(b"owner-lock")
            result = run_script("huawei_ppt.py", "status", str(project))
            payload = json.loads(result.stdout)

        self.assertEqual(payload["final_files"], [])

    def test_prepare_design_requires_the_one_time_outline_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "brief.md"
            brief.write_text("Deck brief", encoding="utf-8")
            project = Path(tmp) / "project"
            run_script("huawei_ppt.py", "init", "--brief", str(brief), "--out", str(project))
            spec = {
                "schema_version": 1,
                "deck_name": "approval-gate",
                "outline_approved": False,
                "slides": [{"page_number": 1, "role": "summary", "title": "A title", "core_message": "A judgment", "template": {"layout_type": "summary"}}],
            }
            (project / "deck_spec.json").write_text(json.dumps(spec), encoding="utf-8")
            blocked = run_script("huawei_ppt.py", "prepare-design", str(project), check=False)
            spec["outline_approved"] = True
            (project / "deck_spec.json").write_text(json.dumps(spec), encoding="utf-8")
            passed = run_script("huawei_ppt.py", "prepare-design", str(project), check=False)

        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("approval", (blocked.stdout + blocked.stderr).lower())
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)


if __name__ == "__main__":
    unittest.main()
