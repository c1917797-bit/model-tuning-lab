import copy,unittest
from native_lifecycle_audit import activation
class TestActivation(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(event="plugin_build_active",pid=p,version="0.8.5",
            module="/opt/hypic/hypic_vllm_ascend/__init__.py") for p in [10,11,12,13,14]]
        self.rows += [dict(event="runtime_scheduler_active",pid=10)]
        self.rows += [dict(event="worker_hot_request_verified",pid=p,request_id="chatcmpl-test-abcdef01",
            skipped_prefix_tokens=16376,complete_hybrid_repair_validated=True,
            expected_full_layers=16,expected_gdn_layers=48) for p in [11,12,13,14]]
    def check(self,rows): return activation(rows,"enabled",{11,12,13,14},{10},"chatcmpl-test")
    def test_valid(self): self.assertEqual(len(self.check(self.rows)["target_hot_worker_pids"]),4)
    def test_marker_only_fails(self):
        with self.assertRaises(ValueError): self.check(self.rows[:6])
    def test_missing_rank_fails(self):
        with self.assertRaises(ValueError): self.check(self.rows[:-1])
    def test_wrong_request_fails(self):
        rows=copy.deepcopy(self.rows);rows[-1]["request_id"]="chatcmpl-other-abcdef01"
        with self.assertRaises(ValueError): self.check(rows)
    def test_invalid_repair_fails(self):
        rows=copy.deepcopy(self.rows);rows[-1]["complete_hybrid_repair_validated"]=False
        with self.assertRaises(ValueError): self.check(rows)
    def test_missing_engine_fails(self):
        with self.assertRaises(ValueError): self.check([r for r in self.rows if r["pid"]!=10])
    def test_disabled_clean(self):
        self.assertTrue(activation([],"disabled",{11,12,13,14},{10},"x")["disabled_marker_absent"])
    def test_disabled_polluted_fails(self):
        with self.assertRaises(ValueError): activation(self.rows[:1],"disabled",{11,12,13,14},{10},"x")
    def test_uninstalled_polluted_fails(self):
        with self.assertRaises(ValueError): activation(self.rows[:1],"uninstalled",{11,12,13,14},{10},"x")
if __name__=="__main__":unittest.main()
