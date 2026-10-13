"""Protect real historical failure classes and missing evidence."""
import copy,json,unittest
from verify_hypic_profiler_history import FILE,validate_manifest

class HistoryTests(unittest.TestCase):
    def setUp(self):self.m=json.loads(FILE.read_text())
    def test_retained_inventory(self):self.assertTrue(validate_manifest(self.m))
    def test_missing_r3(self):
        self.m["attempts"].pop(3)
        with self.assertRaises(RuntimeError):validate_manifest(self.m)
    def test_missing_release_not_true(self):
        self.m["attempts"][3]["release"]={"container_removed":True}
        with self.assertRaises(RuntimeError):validate_manifest(self.m)
    def test_plugin_commit_not_controller_proof(self):
        self.m["source_provenance"]["prefill_r2_executed_controller_bytes"]="proven"
        with self.assertRaises(RuntimeError):validate_manifest(self.m)
    def test_environment_not_algorithm(self):
        self.m["attempts"][0]["outcome"]="algorithm-failure"
        with self.assertRaises(RuntimeError):validate_manifest(self.m)
    def test_no_new_device_authority(self):
        self.m["new_device_work"]=True
        with self.assertRaises(RuntimeError):validate_manifest(self.m)

if __name__=="__main__":unittest.main()
