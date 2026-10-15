import unittest
from copy import deepcopy
from audit_c2_barrier_activation import audit_barrier_activation
class Activation(unittest.TestCase):
    def fixture(self):
        return [{"event":"compact_hypic_hooks_installed","pid":pid,"manifest_sha256":"abc",
            "c2_layer_completion_barrier":True,"default_disabled":True} for pid in (58,59,60,61)]
    def run_audit(self,rows):
        return audit_barrier_activation(rows,{0:58,1:59,2:60,3:61},manifest_sha256="abc")
    def test_exact_four(self):self.assertTrue(self.run_audit(self.fixture())["barrier_activation_verified"])
    def test_missing(self):
        with self.assertRaises(ValueError):self.run_audit(self.fixture()[:3])
    def test_duplicate(self):
        rows=self.fixture();rows[-1]=deepcopy(rows[0])
        with self.assertRaises(ValueError):self.run_audit(rows)
    def test_wrong_mode(self):
        rows=self.fixture();rows[0]["c2_layer_completion_barrier"]=False
        with self.assertRaises(ValueError):self.run_audit(rows)
    def test_wrong_pid(self):
        rows=self.fixture();rows[0]["pid"]=999
        with self.assertRaises(ValueError):self.run_audit(rows)
    def test_source_drift(self):
        rows=self.fixture();rows[0]["manifest_sha256"]="other"
        with self.assertRaises(ValueError):self.run_audit(rows)
if __name__=="__main__":unittest.main()
