import unittest
from independent_c1_execution_mode import validate_c1_mode
class ExecutionModeTests(unittest.TestCase):
    def base(self):
        return dict(packed=True,native=True,completion=True,shadow=True,probe=False,performance=False)
    def test_canary_unchanged(self):
        validate_c1_mode(**self.base())
        x=self.base();x["shadow"]=False
        with self.assertRaises(ValueError):validate_c1_mode(**x)
    def test_explicit_performance(self):
        x=self.base();x.update(performance=True,shadow=False)
        validate_c1_mode(**x)
        for field,value in (("probe",True),("shadow",True),("native",False),
                            ("completion",False),("packed",False)):
            y=dict(x);y[field]=value
            with self.assertRaises(ValueError):validate_c1_mode(**y)
    def test_wrong_types(self):
        for field in self.base():
            x=self.base();x[field]=1
            with self.assertRaises(ValueError):validate_c1_mode(**x)
    def test_source_wiring(self):
        from pathlib import Path
        hook=Path("independent_compact_gdn_hook.py").read_text()
        self.assertIn("validate_shadow=not performance_mode",hook)
        self.assertIn("check_packed_shadow=layer_shadow and bool(packed)",hook)
        self.assertIn("finite_guard.validate()",hook)
        self.assertIn("state_cache[slot].copy_",hook)
