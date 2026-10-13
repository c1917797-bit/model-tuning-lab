import unittest
from analyze_hypic_profile_timeline import intersection, length, merge, ns


class TimelineTests(unittest.TestCase):
    def test_overlapping_not_sum(self):
        self.assertEqual(length([(0, 10), (5, 15)]), 15)

    def test_nested_duplicate(self):
        self.assertEqual(merge([(0, 20), (2, 3), (0, 20)]), [(0, 20)])

    def test_compute_communication_overlap(self):
        self.assertEqual(intersection([(0, 10), (20, 30)], [(5, 25)]), 10)

    def test_empty_and_touching(self):
        self.assertEqual(length([]), 0)
        self.assertEqual(intersection([(0, 10)], [(10, 20)]), 0)

    def test_reversed_invalid(self):
        with self.assertRaises(ValueError):
            merge([(2, 1)])

    def test_epoch_precision(self):
        self.assertEqual(ns("1791571479499537.295"), 1791571479499537295)

    def test_invalid_times(self):
        for value in ("-1", "NaN", "Infinity"):
            with self.assertRaises(ValueError):
                ns(value)


if __name__ == "__main__":
    unittest.main()
