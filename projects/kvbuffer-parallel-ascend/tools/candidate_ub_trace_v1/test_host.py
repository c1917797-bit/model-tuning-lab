#!/usr/bin/env python3
"""Stdlib prerequisite tests only; no Docker, Torch or device execution."""
import contextlib,importlib.util,io,json,unittest
from pathlib import Path
from unittest.mock import patch
sp=importlib.util.spec_from_file_location("_trace_host_test",Path(__file__).with_name("host.py"))
h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
class HostContract(unittest.TestCase):
    def fixtures(self):
        manifest={"operator_sources":{"kernel.asc":"a"*64}}
        sources={"/immutable/source":"b"*64}
        refs={"library":{"path":str(h.LIB),"sha256":"c"*64},
              "build":{"path":str(h.BUILD/"build-receipt.json"),"sha256":"d"*64},
              "meta":{"path":str(h.BUILD/"meta-receipt.json"),"sha256":"e"*64}}
        build={"schema":"kvbp.candidate-ub-trace-build/v1","status":"compiled_no_device","npu_executed":False,
          "image_id":"sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1",
          "namespace":"qwen36_kvbuffer_native_order_trace_v1","npu_arch":"dav-2201","sources":manifest["operator_sources"],
          "sources_before":sources,"sources_after":sources,"library_sha256":"c"*64,
          "commands":[{"exit_code":0},{"exit_code":0}],
          "exported_kernel":{"name":"qwen36_gdn_kvbuffer_native_order_trace_v1_kernel","defined":True,"type":"T"}}
        meta={"schema":"kvbp.candidate-ub-trace-meta/v1","status":"actual-load-schema-meta-only","library":refs["library"],
          "positive_cases":2,"negative_cases":[{}]*12,"npu_executed":False,"numeric_verified":False,"serving_ready":False,
          "source_manifest_sha256":"e970dca058a7e7d01e964c85b9580a5dde00b5929e5ae16ea064f34b07557cdf",
          "mapped_library_lines":["valid "+str(h.LIB)]}
        return manifest,sources,refs,build,meta
    def check(self,vals):
        manifest,sources,refs,build,meta=vals
        def read(p):return json.dumps(build if str(p)==refs["build"]["path"] else meta).encode()
        with patch.object(h,"sha",side_effect=lambda p:next(r["sha256"] for r in refs.values() if r["path"]==str(p))),patch.object(Path,"read_bytes",read):
            return h.check_receipts(refs,manifest,sources)
    def test_default_off(self):
        out=io.StringIO()
        with patch.object(h,"configured",side_effect=AssertionError("must not load lease")),contextlib.redirect_stdout(out):h.main([])
        d=json.loads(out.getvalue());self.assertFalse(d["default_enabled"]);self.assertFalse(d["npu_executed"]);self.assertEqual(d["physical"],6)
    def test_missing_source_ref_rejected_before_configure(self):
        with patch.object(h,"configured",side_effect=AssertionError("too early")),self.assertRaises(ValueError):h.main(["--execute"])
    def test_receipt_contract_accepts_only_prerequisite(self):self.check(self.fixtures())
    def test_failed_build_retained_not_admitted(self):
        v=self.fixtures();v[3]["commands"][1]["exit_code"]=1
        with self.assertRaises(ValueError):self.check(v)
    def test_source_drift_not_admitted(self):
        v=self.fixtures();v[3]["sources_after"]={}
        with self.assertRaises(ValueError):self.check(v)
    def test_meta_not_npu_authority(self):
        v=self.fixtures();v[4]["numeric_verified"]=True
        with self.assertRaises(ValueError):self.check(v)
    def test_deleted_mapping_rejected(self):
        v=self.fixtures();v[4]["mapped_library_lines"]=["file (deleted)"]
        with self.assertRaises(ValueError):self.check(v)
    def test_unique_output_unchanged_lease(self):
        l=h.configured();self.assertEqual(l.OUT,h.OUT);self.assertEqual(l.MEM,8*1024**3)
        self.assertEqual(l.CAP,600);self.assertEqual(l.CLEANUP,90)
        self.assertEqual(l.devices()["/dev/davinci6"],"/dev/davinci0")
        self.assertNotIn("/dev/davinci0",l.devices());self.assertEqual(l.mounts()[str(h.BUILD)],(str(h.BUILD),False))
        self.assertIn('protected0-3 PID/starttime change',Path(h.LEASE).read_text())
if __name__=="__main__":unittest.main()
