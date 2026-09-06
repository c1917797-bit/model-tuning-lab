from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_required_copyright_notices_and_commits_are_present(self) -> None:
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("f2ed80372f65bb05fe62dd07979b239a17ac065d", notice)
        self.assertIn("fb869763127fd31ba7288d905671ffc4ea542f60", notice)
        for name in ["codex-ppt-MIT.txt", "image-to-editable-ppt-MIT.txt"]:
            text = (ROOT / "LICENSES" / name).read_text(encoding="utf-8")
            self.assertIn("MIT License", text)
            self.assertIn("Copyright (c) 2026 ningzimu", text)
            self.assertIn("Permission is hereby granted", text)

    def test_skill_links_resolve_and_legacy_three_zone_files_are_absent(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for relative in re.findall(r"\]\(([^)]+)\)", skill):
            if relative.startswith("http"):
                continue
            self.assertTrue((ROOT / relative).exists(), relative)
        for relative in [
            "scripts/build_three_zone_deck.js",
            "scripts/init_three_zone_project.js",
            "scripts/smoke_test_v1.js",
            "references/image2-middle-canvas.md",
        ]:
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_template_assets_cover_all_slides(self) -> None:
        previews = sorted((ROOT / "assets" / "huawei-template" / "previews").glob("slide-*.png"))
        self.assertEqual(len(previews), 42)
        self.assertTrue((ROOT / "assets" / "huawei-template" / "PPT模板.pptx").exists())

    def test_editppt_runtime_emits_powerpoint_compatibility_parts(self) -> None:
        builder = (ROOT / "cli" / "editppt" / "editppt" / "runtime" / "build_pptx_from_manifest.py").read_text(encoding="utf-8")
        for part in ["ppt/presProps.xml", "ppt/viewProps.xml", "ppt/tableStyles.xml"]:
            self.assertIn(part, builder)
        self.assertNotIn("<a:p/></p:txBody>", builder)


if __name__ == "__main__":
    unittest.main()
