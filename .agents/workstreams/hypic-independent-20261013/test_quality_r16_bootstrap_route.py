import ast,unittest
from pathlib import Path
from independent_quality_bootstrap_route import select_bootstrap
class Tests(unittest.TestCase):
    def test_canary_no_treatment_rejected_before_admission(self):
        from independent_quality_bootstrap_route import quality_mode
        for diagnostic in (None,{}, {"x":1}, {"compact_manifest":False}):
            with self.assertRaises(ValueError):quality_mode({"formal_quality_canary":True,"cache_diagnostic":diagnostic})
    def test_canary_catalog(self):
        self.assertEqual(select_bootstrap({"formal_quality_canary":True,"cache_diagnostic":{"compact_manifest":"q.json"}}),"quality_bootstrap")
    def test_canary_conflict(self):
        for key in ("formal_quality","formal_performance"):
            with self.assertRaises(ValueError):select_bootstrap({"formal_quality_canary":True,key:True})
    def test_canary_strict(self):
        for value in (0,1,None,"false"):
            with self.assertRaises(ValueError):select_bootstrap({"formal_quality_canary":value})
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
        changes=[["    quality_spec=contract.get(\"quality_workload\")\n    if contract.get(\"formal_quality\"):","    quality_spec=contract.get(\"quality_workload\")\n    from independent_quality_bootstrap_route import quality_mode\n    quality_kind=quality_mode(contract)\n    if quality_kind:"],["        if contract.get(\"formal_quality\"):\n            from independent_quality_workload import run_quality_workload","        if quality_kind:\n            from independent_quality_workload import run_quality_workload"],["            result_unit=run_quality_workload(quality_spec,\n                send=lambda p:http_quality(port,p,guard=require_guard,timeout=2400),\n                guard=require_guard,record=journal.append,\n                require_material_ready=quality_ready)\n            responses=result_unit[\"results\"]\n            write(raw,\"quality-unit.json\",result_unit)\n            if result_unit[\"successful\"]!=381:\n                raise RuntimeError(\"full quality request failures retained\")","            if quality_kind==\"canary\":\n                if not diagnostic:raise ValueError(\"catalog eviction Canary requires treatment\")\n                from independent_catalog_quality_canary import run_catalog_canary\n                from independent_catalog_rebuild_selection import choose_evicted_rebuild\n                def choose_rebuild(candidates):\n                    require_guard();worker_events=[]\n                    for path in (raw/\"diagnostics\").glob(\"compact-worker-*.jsonl\"):\n                        if path.is_symlink() or path.stat().st_size>128*1024**2:\n                            raise ValueError(\"bounded regular worker evidence required\")\n                        data=path.read_text();complete=data[:data.rfind(\"\\n\")+1]\n                        worker_events.extend(json.loads(line) for line in complete.splitlines())\n                    manifest_hash=hashlib.sha256((HERE/diagnostic[\"compact_manifest\"]).read_bytes()).hexdigest()\n                    return choose_evicted_rebuild(worker_events,manifest_hash,candidates)\n                result_unit=run_catalog_canary(quality_spec,\n                    send=lambda p:http_quality(port,p,guard=require_guard,timeout=2400),\n                    guard=require_guard,record=journal.append,\n                    require_material_ready=quality_ready,choose_rebuild=choose_rebuild)\n            else:\n                result_unit=run_quality_workload(quality_spec,\n                    send=lambda p:http_quality(port,p,guard=require_guard,timeout=2400),\n                    guard=require_guard,record=journal.append,\n                    require_material_ready=quality_ready)\n            responses=result_unit[\"results\"]\n            write(raw,\"catalog-canary-unit.json\" if quality_kind==\"canary\" else \"quality-unit.json\",result_unit)\n            if result_unit[\"successful\"]!=(17 if quality_kind==\"canary\" else 381):\n                raise RuntimeError(\"quality request failures retained\")"]]
        for before,after in changes:
            self.assertEqual(new.count(after),1)
            new=new.replace(after,before)
        new=new.replace('from independent_quality_bootstrap_route import select_bootstrap\n            bootstrap=select_bootstrap(contract)',
            'bootstrap="compact_bootstrap" if diagnostic.get("compact_manifest") else "diagnostic_bootstrap"')
        new=new.replace('CONTRACT = HERE / "QUALITY_R16_CONTRACT.json"','CONTRACT = HERE / "NATIVE_SMOKE_CONTRACT.json"')
        a=ast.parse(old);b=ast.parse(new)
        self.assertEqual(ast.dump(ast.Module(body=a.body[1:],type_ignores=[])),ast.dump(ast.Module(body=b.body[1:],type_ignores=[])))
if __name__=="__main__":unittest.main()
