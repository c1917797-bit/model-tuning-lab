"""Bounded source controls; synthetic child reports, no Docker/Torch/NPU."""
import ast,copy,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_actual_bridge_owner',HERE/'owner.py');W=importlib.util.module_from_spec(s);s.loader.exec_module(W)
O=W.configured()
class Tests(unittest.TestCase):
    def test_seventeen_exact_inputs_and_missing_refusal(self):
        plan=json.loads(O.checked(W.PLAN).read_bytes());r=W.selected(plan)
        self.assertEqual(len(r),17);self.assertGreater(sum(x['bytes']for x in r),170*2**20)
        bad=copy.deepcopy(plan);bad['fixed_inputs']['arms'][1]=bad['fixed_inputs']['arms'][0]
        with self.assertRaises(ValueError):W.selected(bad)
        bad=copy.deepcopy(plan);bad['minimum_read_only_mount_keys'].pop()
        with self.assertRaises(ValueError):W.selected(bad)
    def test_complete_original_cpu_function_inverse(self):
        raw=O.checked(O.PARENT_HOST).read_bytes();body,pairs,original=O.derive_cpu(raw)
        back=body
        for a,b in reversed(pairs):back=back.replace(b,a,1)
        self.assertEqual(back,original);self.assertEqual(len(pairs),6)
        for text in ("co.observe(ctl,'Event-source23-Devices-empty',initial=True);ctl.create()","cleanup=ctl.cleanup()","co.cleanup_used<=90","after_checked(ref,O)"):
            self.assertIn(text,body)
        self.assertIn("C.load(owned)['physical']is None",body)
    def test_exact_new_review_no_old_approval(self):
        expected=O.review_contract();self.assertEqual(expected['decision'],'PENDING_MAIN')
        self.assertEqual(expected['resources']['guest_bytes'],8*2**30)
        self.assertEqual(expected['resources']['phase_seconds'],600)
        self.assertEqual(expected['resources']['cleanup_seconds'],90)
        self.assertEqual(expected['readonly_inputs'],W.selected(json.loads(O.checked(W.PLAN).read_bytes())))
        class P:
            def __init__(self,x):self.x=x
            def read_bytes(self):return json.dumps(self.x).encode()
        approved=dict(expected,decision='approve')
        with patch.object(O,'checked',return_value=P(approved)),patch.object(O.time,'time',return_value=O.START+1):
            self.assertEqual(O.require_review({'explicit':'synthetic in-memory fixture'}),approved)
        for k,v in [('schema','old-review'),('output_root','/wrong'),('resources',dict(O.BUDGET,Devices=[6]))]:
            bad=dict(approved);bad[k]=v
            with patch.object(O,'checked',return_value=P(bad)),patch.object(O.time,'time',return_value=O.START+1):
                with self.assertRaises(ValueError):O.require_review({'explicit':'synthetic fixture'})
    def test_real_cli_default_off_missing_review_and_unknown(self):
        for args,want in [([],0),(['--execute'],1),(['--bad-mode'],2)]:
            p=subprocess.run([sys.executable,'-I','-B',str(HERE/'owner.py'),*args],capture_output=True,text=True,timeout=5)
            self.assertEqual(p.returncode,want,p.stderr)
    def test_analyzer_bytes_unchanged_and_output_only_plan_delta(self):
        self.assertEqual(O.ref(HERE/'analyze_bridge.py'),W.ANALYSIS)
        plan=json.loads(O.checked(W.PLAN).read_bytes())
        self.assertEqual(plan['output'],str(W.OUT/'cpu/BRIDGE.json'))
        self.assertFalse(plan['qualification']);self.assertFalse(plan['new_NPU_execution'])
        self.assertNotIn('torch',sys.modules);self.assertNotIn('torch_npu',sys.modules)
if __name__=='__main__':unittest.main(verbosity=2)
