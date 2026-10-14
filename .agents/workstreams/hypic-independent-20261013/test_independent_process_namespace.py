import unittest
from independent_process_namespace import namespace_pids
class NamespaceTests(unittest.TestCase):
    def test_explicit_chain(self):
        self.assertEqual(namespace_pids("Name: worker\nNSpid:\t123\t59\n",123),(123,59))
    def test_missing_mismatch_and_invalid_rejected(self):
        for value in ("Pid:123","NSpid:124 59","NSpid:123 0","NSpid:abc"):
            with self.assertRaises(ValueError):namespace_pids(value,123)
if __name__=="__main__":unittest.main()
