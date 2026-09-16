"""CPU-only evidence-validator tests; no accelerator or service launch."""
import unittest
from run_v12r9_once import validate_layer_cohorts


def rows():
    return [
        {"event": event, "pid": pid, "layer": f"layers.{layer}"}
        for event in ("physical_cache_bound", "request_active_state_initialized", "request_active_state_continued")
        for pid in range(100, 104)
        for layer in range(48)
    ]


class CoverageTests(unittest.TestCase):
    def test_complete(self):
        self.assertTrue(validate_layer_cohorts(rows())["ok"])

    def test_first_layer_only_fails(self):
        with self.assertRaisesRegex(ValueError, "linear-layer"):
            validate_layer_cohorts([r for r in rows() if r["layer"] == "layers.0"])

    def test_missing_continuity_fails(self):
        with self.assertRaisesRegex(ValueError, "lifecycle coverage"):
            validate_layer_cohorts(rows()[:-1])

    def test_duplicate_fails(self):
        evidence = rows()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_layer_cohorts(evidence + [evidence[0]])

    def test_missing_rank_fails(self):
        with self.assertRaisesRegex(ValueError, "rank coverage"):
            validate_layer_cohorts([r for r in rows() if r["pid"] != 100])

    def test_different_layer_identity_fails(self):
        evidence = rows()
        evidence[0]["layer"] = "wrong.layer"
        with self.assertRaisesRegex(ValueError, "layer identities"):
            validate_layer_cohorts(evidence)


if __name__ == "__main__":
    unittest.main()
