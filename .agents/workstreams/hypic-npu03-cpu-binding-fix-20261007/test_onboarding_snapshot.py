import unittest
from verify_onboarding_snapshot import inventory

class InventoryTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(inventory([{"id":"a","path":".agents/skills/a"}], ["a"], ["a"]), ["a"])
    def test_duplicate_id(self):
        with self.assertRaises(ValueError):
            inventory([{"id":"a","path":".agents/skills/a"}] * 2, ["a"], ["a"])
    def test_missing_directory(self):
        with self.assertRaises(ValueError):
            inventory([{"id":"a","path":".agents/skills/a"}], [], [])
    def test_orphan_directory(self):
        with self.assertRaises(ValueError):
            inventory([{"id":"a","path":".agents/skills/a"}], ["a","b"], ["a","b"])
    def test_missing_entrypoint(self):
        with self.assertRaises(ValueError):
            inventory([{"id":"a","path":".agents/skills/a"}], ["a"], [])
    def test_wrong_path(self):
        with self.assertRaises(ValueError):
            inventory([{"id":"a","path":"../a"}], ["a"], ["a"])
if __name__ == "__main__":
    unittest.main()
