import unittest
from audit_c1_http_identity import resolve_http_ids

class IdentityTests(unittest.TestCase):
    def test_exact_delimited_bijection(self):
        self.assertEqual(resolve_http_ids(["a", "b"], ["warm-0", "a-0-x", "b-0-y"], expected_count=2),
                         {"a": "a-0-x", "b": "b-0-y"})
    def test_negative_controls(self):
        cases = [
            (["a"], ["ab-0"], 1),
            (["a"], ["a-"], 1),
            (["a"], [], 1),
            (["a"], ["a-0", "a-1"], 1),
            (["a", "a"], ["a-0"], 2),
            (["a", "a-b"], ["a-b-c"], 2),
            (["a"], ["a-0", "a-0"], 1),
            ([""], ["-0"], 1), ([" "], [" -0"], 1),
            ([1], ["1-0"], 1), (["a"], [None], 1),
            (["a"], ["a-0"], 2), (["a"], ["a-0"], True),
            ("a", ["a-0"], 1), (["a "], ["a -0"], 1)]
        for apis, runtimes, count in cases:
            with self.subTest(apis=apis, runtimes=runtimes, count=count):
                with self.assertRaises(ValueError):
                    resolve_http_ids(apis, runtimes, expected_count=count)
