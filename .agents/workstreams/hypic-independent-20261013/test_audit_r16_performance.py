import copy,unittest
from audit_r16_performance import validate_timed_mode
class Tests(unittest.TestCase):
    def config(self):return dict(prefill_prompt_snapshot=True,prompt_snapshot_probe_batches=0,c1_performance_mode=True,c1_layer_shadow_validation=False)
    def contract(self,g="G3"):return dict(performance_group=g,formal_performance=True,cache_diagnostic={"x":1} if g=="G3" else None,independent_acceptance={"require_hypic_markers_absent":True},protocol_notes={"timed_diagnostics":False})
    def test_candidate(self):self.assertEqual(validate_timed_mode(self.contract(),self.config()),"G3")
    def test_baseline(self):self.assertEqual(validate_timed_mode(self.contract("G1"),self.config()),"G1")
    def test_probe_enabled(self):
        c=self.config();c["prompt_snapshot_probe_batches"]=2
        with self.assertRaises(ValueError):validate_timed_mode(self.contract(),c)
    def test_boolean_probe(self):
        c=self.config();c["prompt_snapshot_probe_batches"]=False
        with self.assertRaises(ValueError):validate_timed_mode(self.contract(),c)
    def test_shadow_enabled(self):
        c=self.config();c["c1_layer_shadow_validation"]=True
        with self.assertRaises(ValueError):validate_timed_mode(self.contract(),c)
    def test_active_baseline(self):
        c=self.contract("G1");c["cache_diagnostic"]={"x":1}
        with self.assertRaises(ValueError):validate_timed_mode(c,self.config())
    def test_no_timed_diagnostic(self):
        c=self.contract();c["protocol_notes"]["timed_diagnostics"]=True
        with self.assertRaises(ValueError):validate_timed_mode(c,self.config())
    def test_no_undeclared_group(self):
        with self.assertRaises(ValueError):validate_timed_mode(self.contract("G4"),self.config())
if __name__=="__main__":unittest.main()
