import unittest

from drror_vllm_ascend.plan import (
    OFFICIAL_COMMIT,
    OFFICIAL_RRQR_SHA256,
    validate_selection_provenance,
)
from drror_vllm_ascend.prepare import selection_method


class SelectionProvenanceTests(unittest.TestCase):
    def energy_plan(self):
        return {
            "selection_objective": "energy-kernel",
            "provenance": {
                "method": "Experimental joint normalized Q/K energy top-k selector",
                "paper_exact_selection": False,
                "official_commit": OFFICIAL_COMMIT,
                "official_rrqr_sha256": OFFICIAL_RRQR_SHA256,
                "calibration_sha256": "a" * 64,
                "selection": {
                    "schema": "drrqr-selection/v1",
                    "method": "Top shared coordinates by joint normalized Q/K energy",
                    "selection_objective": "energy-kernel",
                    "l2norm_eps": 1e-6,
                    "official_commit": OFFICIAL_COMMIT,
                    "official_rrqr_sha256": OFFICIAL_RRQR_SHA256,
                    "f_param": 1.5,
                    "max_swaps": 20,
                    "subsample_threshold": 5000,
                    "seed": 42,
                    "capture_file_count": 3072,
                    "capture_manifest_sha256": "b" * 64,
                    "layers": {"0": {}},
                },
            },
        }

    def test_official_raw_is_the_only_paper_exact_selector(self):
        method, paper_exact = selection_method("official-raw")
        self.assertEqual(method, "DRRQR (paper-faithful Strong RRQR selector)")
        self.assertTrue(paper_exact)

        for objective in ("cosine-kernel", "energy-kernel"):
            method, paper_exact = selection_method(objective)
            self.assertIn("Experimental", method)
            self.assertFalse(paper_exact)

    def test_unknown_selector_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown selection objective"):
            selection_method("not-a-selector")

    def test_energy_plan_provenance_is_accepted_without_paper_exact_claim(self):
        selection = validate_selection_provenance(self.energy_plan())
        self.assertEqual(selection["selection_objective"], "energy-kernel")

    def test_plan_provenance_rejects_label_or_identity_drift(self):
        mutations = (
            ("objective", "selection_objective", "not-a-selector"),
            ("method", "method", "DRRQR"),
            ("paper exact", "paper_exact_selection", True),
            ("calibration", "calibration_sha256", "not-a-hash"),
        )
        for label, field, value in mutations:
            with self.subTest(label=label):
                plan = self.energy_plan()
                target = plan if field == "selection_objective" else plan["provenance"]
                target[field] = value
                with self.assertRaisesRegex(ValueError, "pinned algorithm/calibration"):
                    validate_selection_provenance(plan)

        plan = self.energy_plan()
        plan["provenance"]["selection"]["selection_objective"] = "official-raw"
        with self.assertRaisesRegex(ValueError, "pinned algorithm/calibration"):
            validate_selection_provenance(plan)


if __name__ == "__main__":
    unittest.main()
