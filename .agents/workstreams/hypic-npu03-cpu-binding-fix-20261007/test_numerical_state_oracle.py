import copy
import unittest
from numerical_state_oracle import compare, COMPONENTS


def snapshot(component="gdn_state"):
    return dict(request_id="diagnostic-fixture", rank=0, layer="layer0", step=1,
                component=component, segment_hash="fixture-only", generation=1,
                coordinates=[[0, 0], [0, 1], [1, 0], [1, 1]],
                shape=[2, 2], dtype="float32", comparison="fixture",
                values=[1, 2, 3, 4])


class OracleTests(unittest.TestCase):
    def test_identical_is_not_device_or_quality_acceptance(self):
        a = snapshot()
        result = compare(a, copy.deepcopy(a))
        self.assertEqual(result["max_abs_error"], 0)
        self.assertTrue(result["full_tensor_coverage"])
        self.assertFalse(result["device_execution_proven"])
        self.assertFalse(result["quality_or_causality_proven"])

    def test_each_component_detects_local_perturbation(self):
        for component in COMPONENTS:
            with self.subTest(component=component):
                a = snapshot(component)
                b = copy.deepcopy(a)
                b["values"][2] += 2
                r = compare(a, b)
                self.assertEqual(r["different_coordinates"], 1)
                self.assertEqual(r["max_abs_error"], 2)
                self.assertEqual(r["rms_error"], 1)

    def test_different_request_generation_or_position_map_rejected(self):
        for key, value in (("request_id", "other"), ("generation", 2),
                           ("rank", 3), ("step", 2),
                           ("coordinates", [[0, 1], [0, 0], [1, 0], [1, 1]])):
            a, b = snapshot(), snapshot()
            b[key] = value
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                compare(a, b)

    def test_sparse_sample_not_full_equivalence(self):
        a = snapshot()
        a["coordinates"], a["values"] = [[0, 0]], [1]
        self.assertFalse(compare(a, copy.deepcopy(a))["full_tensor_coverage"])

    def test_nonfinite_empty_and_duplicate_are_invalid(self):
        for values, coordinates in (([float("nan")], [[0, 0]]),
                                    ([], []), ([1, 2], [[0, 0], [0, 0]])):
            a = snapshot()
            a["values"], a["coordinates"] = values, coordinates
            with self.assertRaises(ValueError):
                compare(a, copy.deepcopy(a))

    def test_zero_reference_no_infinite_relative_error(self):
        a = snapshot()
        a["values"] = [0, 0, 0, 0]
        b = copy.deepcopy(a)
        b["values"][0] = 1
        self.assertIsNone(compare(a, b)["relative_rms_error"])

    def test_positions_cannot_be_fractional(self):
        a = snapshot("positions")
        a["values"][0] = 1.5
        with self.assertRaises(ValueError):
            compare(a, copy.deepcopy(a))


if __name__ == "__main__":
    unittest.main()
