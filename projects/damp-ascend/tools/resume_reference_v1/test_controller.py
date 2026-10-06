"""Stdlib/read-only tests for new controller; no Docker, Torch or NPU."""
import ast
import contextlib
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("damp_on_recovery_under_test",HERE/"controller.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

def protocol():
    return dict(rows=[{} for _ in range(36)],layers=list(range(48)),
                anchors=[256,512,768,2304,2560,2816],horizon=256)

class RecoveryTests(unittest.TestCase):
    def test_memory_disk_not_ram(self):
        p=c.memory_plan(protocol())
        self.assertEqual(p["rows_per_rank"],2654208)
        self.assertEqual(p["primitive_python_bytes"],4501536768)
        self.assertEqual(p["binary_payload_disk_bytes"],33124515840)
        self.assertEqual(p["original_admission_gib"],64)
        self.assertFalse(p["model_loading_peak_measured"])
        self.assertFalse(p["allocator_overhead_upper_bound_proven"])
        self.assertEqual(p["timeline_planning_reserve_bytes"],6752305152)

    def test_current_same_image_sizes_are_parameters_not_measured_claim(self):
        p=c.memory_plan(protocol(),float_bytes=24,row_tuple_bytes=136)
        self.assertFalse(p["object_sizes_measured_in_this_image"])
        self.assertIn("model/load CPU private-memory peak",p["unknowns"])

    def test_new_identity_never_old_evidence(self):
        for run_id in ("v1","v42"):
            audit,on,name=c.new_identity(run_id)
            self.assertNotEqual(audit,c.OLD_LAUNCH); self.assertNotEqual(on,c.OFF)
            self.assertNotEqual(on,c.ROOT/"full-capture-v1-on")
            self.assertEqual(audit.parent,c.ROOT); self.assertEqual(on.parent,c.ROOT)
            self.assertNotEqual(name,"qwen36_damp_full_capture_tp4_20261006_v1")
        for run_id in (None,"","v0","../v1","v1/x","v01","full-v1"):
            with self.assertRaises(RuntimeError): c.new_identity(run_id)

    def test_default_off_does_not_execute(self):
        out=io.StringIO()
        with mock.patch.object(c,"frozen",return_value=object()), \
             mock.patch.object(c,"off_lock",return_value=({},protocol())), \
             mock.patch.object(c,"execute") as execute, \
             mock.patch("sys.argv",["controller"]),contextlib.redirect_stdout(out):
            c.main()
        execute.assert_not_called()
        self.assertIn('"no_docker_or_npu": true',out.getvalue())

    def test_no_ambiguous_both_modes(self):
        with mock.patch("sys.argv",["controller","--plan","--execute"]),self.assertRaises(RuntimeError):
            c.main()

    def test_explicit_original_ram_boundary_remains64(self):
        original=c.frozen()
        self.assertEqual(original.resources({"meminfo":"MemAvailable: 67108864 kB\n"},
            SimpleNamespace(free=40*c.GiB))["minimum_memory_gib"],64)
        for memory in (67108863,0):
            with self.assertRaises(RuntimeError):
                original.resources({"meminfo":f"MemAvailable: {memory} kB\n"},SimpleNamespace(free=40*c.GiB))

    def test_actual_off_source_lock_read_only(self):
        original=c.frozen(); lock,manifest=c.off_lock(original)
        self.assertEqual(len(lock["source"]["files"]),28)
        self.assertEqual(len(manifest["rows"]),36)
        self.assertEqual(len(lock["original_evidence"][str(c.OFF)]),4)
        c.assert_original_unchanged(lock["original_evidence"])

    def test_source_bound_smoke_actual_readonly_adapter(self):
        report,proof=c.source_bound_smoke()
        self.assertEqual(report["requests"],2)
        self.assertEqual(proof["sidecar"]["sha256"],"1f78093b451b2ad943fb3d7c7166fcdb12ee5a5caf320377d6891daadd43a37e")
        self.assertTrue(proof["read_only_validation_reproduced"])
        self.assertEqual(len(proof["original_failed_validator_preserved"]),3)
        self.assertIn("NOT a fresh compressed",proof["scope"])

    def test_source_bound_smoke_does_not_accept_old_failed_or_invented_report(self):
        for path,sha in ((c.ROOT/"smoke-hook-v4-on/VALIDATION.json",None),
            (c.ROOT/"legacy-v4-identity-audit-v1/VALIDATION.json","0"*64)):
            with self.assertRaises(RuntimeError): c.source_bound_smoke(path,sha)

    def test_source_contract_no_off_launch_or_threshold_override(self):
        source=(HERE/"controller.py").read_text()
        tree=ast.parse(source)
        self.assertNotIn("--min-memory",source)
        for call in (n for n in ast.walk(tree) if isinstance(n,ast.Call)):
            if isinstance(call.func,ast.Attribute) and call.func.attr == "python_in_container":
                self.assertFalse(any(isinstance(a,ast.Constant) and a.value=="off" for a in call.args))
        self.assertNotIn("docker\",\"rm",source)
        self.assertIn('original.stage(safety,"canary",argv)',source)
        self.assertIn('original.fresh(safety,"on")',source)
        self.assertIn('original.container_proof(entry,cid,owner)',source)
        self.assertIn('source_lock = finalize(',source)
        self.assertIn('lock_source(path, original.MANIFEST',source)
        self.assertIn('current_lock == lock',source)
        self.assertIn('require_deadline()',source)
        # No subprocess/filesystem action at module top level: guarded MAIN only.
        for node in tree.body:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
                self.fail("unexpected top-level call")
        self.assertTrue(c.sys.dont_write_bytecode)

if __name__=="__main__":
    unittest.main(verbosity=2)
