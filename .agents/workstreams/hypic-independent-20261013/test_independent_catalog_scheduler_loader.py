import json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import independent_catalog_scheduler_loader as target
from independent_catalog_scheduler_admission import CatalogPICAdmissionCallback
class LoaderTests(unittest.TestCase):
    def test_disabled_no_side_effect(self):
        before=list(sys.meta_path);target.enable_scheduler("/missing",{},Path("/missing"))()
        self.assertEqual(sys.meta_path,before)
    def prepare(self,root,*,limit=1024):
        manifest=root/"manifest.json";manifest.write_text("{}")
        stop=target.enable_scheduler(manifest,{"public_segments":[list(range(128))]},root,enabled=True,request_limit=limit)
        class Original:
            def exec_module(self,module):module.Scheduler=type("Scheduler",(),{})
        spec=types.SimpleNamespace(loader=Original())
        with patch.object(target.importlib.machinery.PathFinder,"find_spec",return_value=spec):
            wrapped=target._finder.find_spec("vllm.v1.core.sched.scheduler")
        return stop,wrapped
    def test_real_import_wrapper_selects_catalog_and_uninstalls(self):
        before=list(sys.meta_path);captured=[];removed=[]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def install(cls,**kwargs):captured.append(kwargs);return lambda:removed.append(True)
            with patch("independent_pic_scheduler_hook.install_pic_scheduler",install):
                stop,spec=self.prepare(root)
                spec.loader.exec_module(types.SimpleNamespace())
            self.assertIsInstance(captured[0]["cap"],CatalogPICAdmissionCallback)
            self.assertEqual(captured[0]["cap"].limit,1024)
            records=[json.loads(x) for x in next(root.glob("compact-scheduler-*.jsonl")).read_text().splitlines()]
            self.assertTrue(records[0]["catalog_enabled"]);self.assertEqual(records[0]["request_limit"],1024)
            stop();stop()
        self.assertEqual(removed,[True]);self.assertEqual(sys.meta_path,before)
    def test_evidence_failure_removes_owned_hook_and_finder(self):
        before=list(sys.meta_path);removed=[]
        with tempfile.TemporaryDirectory() as tmp:
            with patch("independent_pic_scheduler_hook.install_pic_scheduler",return_value=lambda:removed.append(True)),patch.object(target.os,"fsync",side_effect=OSError("sink failure")):
                stop,spec=self.prepare(Path(tmp))
                with self.assertRaises(OSError):spec.loader.exec_module(types.SimpleNamespace())
            stop()
        self.assertEqual(removed,[True]);self.assertEqual(sys.meta_path,before);self.assertIsNone(target._finder)
    def test_late_or_conflicting_install_rejected(self):
        with patch.dict(sys.modules,{"vllm.v1.core.sched.scheduler":object()}):
            with self.assertRaises(ValueError):target.enable_scheduler("/missing",{},Path("/missing"),enabled=True)
        fake=types.SimpleNamespace(_finder=object())
        with patch.dict(sys.modules,{"independent_pic_scheduler_loader":fake}):
            with self.assertRaises(ValueError):target.enable_scheduler("/missing",{},Path("/missing"),enabled=True)
    def test_explicit_bounds(self):
        for n in (True,0,4097):
            with self.assertRaises(ValueError):target.enable_scheduler("/missing",{},Path("/missing"),enabled=True,request_limit=n)
if __name__=="__main__":unittest.main()
