import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from independent_pic_scheduler_loader import enable_scheduler

class Loader(unittest.TestCase):
    def test_default_disabled_no_sideeffects(self):
        before=list(sys.meta_path)
        stop=enable_scheduler("/missing",{},Path("/missing"))
        stop();self.assertEqual(sys.meta_path,before)
    def test_pending_install_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);manifest=root/"manifest.json";manifest.write_text("{}")
            before=list(sys.meta_path)
            stop=enable_scheduler(manifest,{"public_tokens":[9,8]},root,enabled=True)
            self.assertEqual(len(sys.meta_path),len(before)+1)
            self.assertEqual(list(root.glob("compact-scheduler-*.jsonl")),[])
            stop();self.assertEqual(sys.meta_path,before)
    def test_late_install_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);manifest=root/"manifest.json";manifest.write_text("{}")
            with patch.dict(sys.modules,{"vllm.v1.core.sched.scheduler":object()}):
                with self.assertRaises(ValueError):
                    enable_scheduler(manifest,{"public_tokens":[9,8]},root,enabled=True)
if __name__=="__main__":unittest.main()
