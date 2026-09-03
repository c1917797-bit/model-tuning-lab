import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from paper_to_ascend.dynamic_moe import dynamic_top_p_select, fixed_top_k_select  # noqa: E402


class DynamicMoERoutingTests(unittest.TestCase):
    def test_minimal_prefix_reaches_threshold(self):
        selection = dynamic_top_p_select([0.50, 0.20, 0.15, 0.10, 0.05], threshold=0.60)
        self.assertEqual(selection.expert_ids, (0, 1))
        self.assertEqual(selection.weights, (0.50, 0.20))

    def test_one_confident_expert_is_enough(self):
        selection = dynamic_top_p_select([0.70, 0.10, 0.10, 0.10], threshold=0.40)
        self.assertEqual(selection.expert_ids, (0,))
        self.assertEqual(selection.count, 1)

    def test_harder_distribution_activates_more_experts(self):
        easy = dynamic_top_p_select([0.80, 0.10, 0.05, 0.05], threshold=0.60)
        hard = dynamic_top_p_select([0.26, 0.25, 0.25, 0.24], threshold=0.60)
        self.assertLess(easy.count, hard.count)
        self.assertEqual(hard.count, 3)

    def test_fixed_top2_baseline(self):
        selection = fixed_top_k_select([0.10, 0.40, 0.20, 0.30], k=2)
        self.assertEqual(selection.expert_ids, (1, 3))

    def test_invalid_probability_mass(self):
        with self.assertRaises(ValueError):
            dynamic_top_p_select([0.0, 0.0], threshold=0.4)


if __name__ == "__main__":
    unittest.main()
