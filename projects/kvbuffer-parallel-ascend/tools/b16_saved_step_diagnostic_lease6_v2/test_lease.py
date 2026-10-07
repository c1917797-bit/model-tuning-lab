#!/usr/bin/env python3
"""Source-scope stdlib tests; no Torch/Docker/NPU authority."""
import ast,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent/"host.py"
s=importlib.util.spec_from_file_location("_lease6_test",P);h=importlib.util.module_from_spec(s);sys.modules[s.name]=h;s.loader.exec_module(h)
class Tests(unittest.TestCase):
    def test_no_other_card_idle_predicate(self):
        tree=ast.parse(P.read_text())
        f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="observe_child")
        source=ast.unparse(f)
        self.assertNotIn("idle_one(",source)
        self.assertIn("n == 6",source)
        self.assertIn("validate_pid",source)
        self.assertIn("protected",source)
        self.assertIn("RESERVE",source)
    def test_exact_pre_post_selected_idle(self):
        tree=ast.parse(P.read_text())
        f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="execute")
        calls=[x for x in ast.walk(f) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=="idle_one"]
        self.assertEqual(len(calls),2)
        self.assertTrue(all(isinstance(x.args[-1],ast.Constant) and x.args[-1].value==6 for x in calls))
        self.assertNotIn(".idle(",ast.unparse(f))
    def test_other_compute_does_not_hide_selected_compute(self):
        # Invoke the actual unchanged original helper: selected6 PID/AICore/HBM still rejects.
        f=h.frozen()
        text="| 6     910B4 | OK | 0 | 0 |\n| 0 | bus | 0 0 / 0 2861 / 32768 |\nNo running processes found in NPU 6\n| 4 0 123 python |"
        f.idle_one(text,6)
        for bad in (text.replace("No running processes found in NPU 6","| 6 0 456 python |"),text.replace("2861 / 32768","8000 / 32768"),text.replace("| 0 | bus | 0 ","| 0 | bus | 10 ")):
            with self.assertRaises(ValueError):f.idle_one(bad,6)
    def test_budget_unchanged_and_no_timing(self):
        self.assertEqual((h.MEM,h.RESERVE,h.CAP,h.CLEANUP),(8*1024**3,8*1024**3,600,90))
        self.assertEqual(h.floor(16*1024**3,3,13*1024**3)["full_model_floor_unchanged"],72*1024**3)
        self.assertIn('"timing_authorized":False',P.read_text())
        self.assertEqual(h.devices()["/dev/davinci6"],"/dev/davinci0")
    def test_off_importless(self):
        with patch.object(h,"frozen",side_effect=AssertionError("OFF import")):
            h.main([])
    def test_unknown_selected_pid_still_fails(self):
        dummy=type("D",(),{"gate_process":staticmethod(lambda pid:{"cgroup":"foreignCID","argv":["x"]})})
        with patch.object(h,"frozen",return_value=dummy):
            with self.assertRaises(ValueError):h.validate_pid(6,0,123,"a"*64,"x","123 x",["x"])
    def test_original_files_never_overwritten(self):
        self.assertNotEqual(h.OUT.name,"b16-saved-step-diagnostic-v1-20261007")
        self.assertNotEqual(h.NAME,"kvbuffer_b16_saved_step_diagnostic_v1_20261007")
        self.assertEqual(h.REPLAY.name,"replay.py")
        self.assertEqual(h.REPLAY_SHA,"86cd69ee8c3de19ffeea91e753cc8056320e192c208741775d97bb0938530a00")
        self.assertIn("original real child failure",P.read_text())
if __name__=="__main__":unittest.main()
