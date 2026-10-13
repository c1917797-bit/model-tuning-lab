import unittest
from unittest.mock import patch
import current_source_performance_20261013 as c

class ProspectiveContractTests(unittest.TestCase):
    def test_all_six_roots_are_new_and_unique(self):
        roots=[c.root_for(*pair) for pair in c.ORDER]
        self.assertEqual(len(set(roots)),6)
        self.assertTrue(all("current4429-performance-20261013" in p.name for p in roots))
        self.assertTrue(all(not p.exists() for p in roots))
    def test_invalid_phase_is_rejected(self):
        with self.assertRaises(RuntimeError): c.root_for("other","screen")
    def test_quality_hash_drift_is_rejected(self):
        with patch.object(c,"sha",return_value="wrong"):
            with self.assertRaises(RuntimeError): c.validate_inputs()
    def test_live_source_pins_and_pair_configuration(self):
        for arm,phase in c.ORDER:
            q,s,p,a=c.setup(arm,phase)
            self.assertEqual(q.preflight()["source_commit"],c.COMMIT)
            self.assertTrue(p.pair_seam(q)["enablement_only"])
            self.assertEqual(p.EXPECTED_CONFIG["output_tokens"],1024)
            self.assertEqual(q.QROOT,c.root_for(arm,phase))
            self.assertEqual(a.root_for(arm,phase),q.QROOT)
    def test_independent_predecessor_audit_is_required(self):
        q,s,p,a=c.setup("hypic-only","screen")
        with self.assertRaises(RuntimeError): p.earlier_phases(q,"hypic-only","screen")
    def test_source_and_primitives_are_pinned(self):
        c.validate_inputs()
        self.assertEqual(c.COMMIT,"4429e35177979c874bf053ab29789e4773f39b22")
        self.assertEqual(len(c.PINS),5)

if __name__ == "__main__": unittest.main()

