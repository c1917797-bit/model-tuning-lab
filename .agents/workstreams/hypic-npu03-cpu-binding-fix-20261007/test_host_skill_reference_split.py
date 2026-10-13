"""Negative controls for instruction loss and missing required routes."""
import unittest
from verify_host_skill_reference_split import inputs, validate

class HostReferenceSplitTests(unittest.TestCase):
    def setUp(self):
        self.base, self.core, self.refs = inputs()

    def test_actual_relocation_is_lossless(self):
        self.assertEqual(validate(self.base, self.core, self.refs)["moved_sections_preserved"], 3)

    def test_instruction_loss_fails(self):
        refs = dict(self.refs)
        refs["machine-experiment-safety.md"] = refs["machine-experiment-safety.md"].replace(
            "release only owned resources", "release resources")
        with self.assertRaisesRegex(ValueError, "moved instructions"):
            validate(self.base, self.core, refs)

    def test_optional_read_route_fails(self):
        core = self.core.replace("Before inspecting or changing", "Optionally when inspecting or changing")
        with self.assertRaisesRegex(ValueError, "required read routing"):
            validate(self.base, core, self.refs)

    def test_missing_reference_fails(self):
        refs = dict(self.refs)
        del refs["session-orientation.md"]
        with self.assertRaisesRegex(ValueError, "required reference missing"):
            validate(self.base, self.core, refs)

    def test_core_credential_rule_loss_fails(self):
        core = self.core.replace("Never commit, print, log, echo, cache, or embed", "You may embed")
        with self.assertRaisesRegex(ValueError, "unmoved instructions"):
            validate(self.base, core, self.refs)

    def test_wrong_relocated_link_fails(self):
        refs = dict(self.refs)
        refs["machine-experiment-safety.md"] = refs["machine-experiment-safety.md"].replace(
            "qwen35-v023-runtime-lessons.md", "references/qwen35-v023-runtime-lessons.md")
        with self.assertRaisesRegex(ValueError, "moved instructions"):
            validate(self.base, self.core, refs)

    def test_missing_nested_reference_fails(self):
        with self.assertRaisesRegex(ValueError, "nested Qwen reference"):
            validate(self.base, self.core, self.refs, False)

    def test_overlong_core_fails(self):
        with self.assertRaisesRegex(ValueError, "120 lines"):
            validate(self.base, self.core + "\n" * 121, self.refs)

if __name__ == "__main__":
    unittest.main()
