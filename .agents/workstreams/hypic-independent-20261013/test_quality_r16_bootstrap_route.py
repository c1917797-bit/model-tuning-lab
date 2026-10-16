import ast,unittest
from pathlib import Path
from independent_quality_bootstrap_route import select_bootstrap
class Tests(unittest.TestCase):
    def test_quality_catalog(self):
        self.assertEqual(select_bootstrap({"formal_quality":True,"cache_diagnostic":{"compact_manifest":"q.json"}}),"quality_bootstrap")
    def test_ordinary_compact(self):
        self.assertEqual(select_bootstrap({"cache_diagnostic":{"compact_manifest":"c.json"}}),"compact_bootstrap")
    def test_diagnostic(self):self.assertEqual(select_bootstrap({"cache_diagnostic":{"x":1}}),"diagnostic_bootstrap")
    def test_baseline(self):self.assertIsNone(select_bootstrap({"formal_quality":True}))
    def test_conflicting_modes(self):
        with self.assertRaises(ValueError):select_bootstrap({"formal_quality":True,"formal_performance":True})
    def test_strict_modes(self):
        for x in (0,1,None,"false"):
            with self.assertRaises(ValueError):select_bootstrap({"formal_quality":x})
    def test_quality_rejects_diagnostic_fallback(self):
        with self.assertRaises(ValueError):select_bootstrap({"formal_quality":True,"cache_diagnostic":{"x":1}})
    def test_bad_manifest(self):
        for x in ("",False,3):
            with self.assertRaises(ValueError):select_bootstrap({"cache_diagnostic":{"compact_manifest":x}})
    def test_only_declared_controller_changes(self):
        old=Path("formal_r15_tp4.py").read_text();new=Path("formal_quality_r16_tp4.py").read_text()
        new=new.replace('from independent_quality_bootstrap_route import select_bootstrap\n            bootstrap=select_bootstrap(contract)',
            'bootstrap="compact_bootstrap" if diagnostic.get("compact_manifest") else "diagnostic_bootstrap"')
        new=new.replace('CONTRACT = HERE / "QUALITY_R16_CONTRACT.json"','CONTRACT = HERE / "NATIVE_SMOKE_CONTRACT.json"')
        a=ast.parse(old);b=ast.parse(new)
        self.assertEqual(ast.dump(ast.Module(body=a.body[1:],type_ignores=[])),ast.dump(ast.Module(body=b.body[1:],type_ignores=[])))
if __name__=="__main__":unittest.main()
