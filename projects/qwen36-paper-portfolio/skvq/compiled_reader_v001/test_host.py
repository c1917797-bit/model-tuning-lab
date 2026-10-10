"""Actual source-qualified host factory/CLI/restoration tests; no hardware or data PASS.
This module is intentionally run by deployed software_check, after actual complete
remote source closure. Local stdlib21 tests do not substitute for these8.
"""
import argparse,ast,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import contract as C
import reader_host as H
import reader_whole as W
import numeric as N
import native_binding as B
import worker_patch as P
class HostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=C.ref(C.HERE/"SOURCE_MANIFEST.json");C.source(cls.source["sha256"])
        H.components();cls.controller=H.control_class(cls.source,{},H.preflight_module())
    def test01_original_control_ast_pins_and_exact5_literal_delta(self):
        rows=C.host_bindings();self.assertEqual(self.controller.donor_source,rows["MAIN_HOST.py"])
        self.assertEqual(len(self.controller.literal_delta),5)
        self.assertNotEqual(self.controller.original_ast_sha256,self.controller.adapted_ast_sha256)
        self.assertEqual(self.controller.__mro__[1].__name__,"Control")
    def test02_actual_control_devices_and_cpu_not_idle_gated(self):
        ctl=self.controller(C.ROOT.parent/"run-skvq-compiled-reader-001-source-only-test")
        self.assertEqual(ctl.devices(False),{})
        self.assertEqual(ctl.devices(True)["/dev/davinci4"],"/dev/davinci0")
        self.assertFalse(any(x in ctl.devices(True)for x in("/dev/davinci0","/dev/davinci5","/dev/davinci6","/dev/davinci7")))
        raw=C.read(C.host_bindings()["MAIN_HOST.py"]);tree=ast.parse(raw)
        control=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=="Control")
        execute=next(x for x in control.body if isinstance(x,ast.FunctionDef)and x.name=="exec")
        self.assertIn("if npu:",ast.unparse(execute));self.assertEqual(ctl.env(False)["ASCEND_RT_VISIBLE_DEVICES"],"")
        self.assertEqual(ctl.env(True)["QWEN36_SKVQ_COMPILED_READER_ENABLE"],"1")
    def test03_actual_all4stage_argv_and_absent_numeric_child(self):
        root=C.ROOT.parent/"run-skvq-compiled-reader-001-source-only-test";file=root/"WRITER_REF.json"
        for stage in("cpu","canary","numeric","independent"):
            value=H.args(stage,self.source,root,file);self.assertEqual(value[1],"--execute")
            self.assertEqual(value[value.index("--source-manifest-sha256")+1],self.source["sha256"])
        value=H.args("numeric",self.source,root,file)
        self.assertEqual(value[value.index("--output")+1],str(root/"candidate/work/numeric"))
        self.assertNotEqual(Path(value[-1]),root/"candidate/work")
        with self.assertRaises(ValueError):H.args("legacy",self.source,root,file)
    def test04_actual_numeric_cli_parses_exact_host_arguments(self):
        root=C.ROOT.parent/"run-skvq-compiled-reader-001-source-only-test";file=root/"WRITER_REF.json"
        value=H.args("numeric",self.source,root,file);ref=dict(path="descriptor",bytes=1,sha256="0"*64)
        with patch.object(Path,"read_bytes",return_value=json.dumps(ref).encode()),patch.object(N,"run",return_value=ref)as run:
            with patch.object(sys,"argv",value):N.main()
            run.assert_called_once_with(self.source["sha256"],ref,ref,str(root/"candidate/work/numeric"))
    def test05_actual_same_owner_bound_restoration_and_foreign_negative(self):
        class Object:
            def forward(self):return "original"
        for foreign in(False,True):
            obj=Object();old=obj.forward;fn=types.MethodType(lambda self:"own",obj);obj.__dict__["forward"]=fn
            s=P.Session.__new__(P.Session);s.patches=[(obj,"forward",fn,old)];s.gdn=();s.closed=False
            if foreign:
                obj.__dict__["forward"]=types.MethodType(lambda self:"foreign",obj)
                with self.assertRaises(ValueError):s.restore()
                self.assertIn("forward",obj.__dict__)
            else:
                s.restore();self.assertNotIn("forward",obj.__dict__)
                self.assertIs(obj.forward.__func__,old.__func__);self.assertTrue(s.closed)
    def test06_actual_source_cached_module_foreign_ref_rejected(self):
        row=next(r for r in C.obj(self.source)["files"]if r["path"].endswith("/layout.py"))
        fake=types.ModuleType("_skvq_reader_wrong_cached");fake.__file__=str(C.HERE/"reference.py")
        with patch.dict(sys.modules,{"_skvq_reader_wrong_cached":fake}):
            with self.assertRaises(ValueError):C.load("_skvq_reader_wrong_cached",row)
    def test07_actual_cached_request_class_fields_are_real_not_guess(self):
        body=C.obj(self.source);row=next(r for r in body["dependencies"]if r["sha256"]==B.INPUT_BATCH_SHA)
        tree=ast.parse(C.read(row));node=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="CachedRequestState")
        fields={n.target.id for n in node.body if isinstance(n,ast.AnnAssign)}
        self.assertTrue({"req_id","prompt_token_ids","mm_features","prompt_embeds","num_computed_tokens","output_token_ids"}<=fields)
        self.assertIn("self.num_prompt_tokens",ast.unparse(node))
        self.assertEqual(B.INPUT_BATCH,"vllm.v1.worker.gpu_input_batch")
    def test08_original_failed_terminal_cannot_borrow_any_permission(self):
        for value in({},dict(schema="agentweb.operation/v1",terminal=True,status="failed",succeeded=False,
          operation=dict(result=dict(record={})),error="exit code")):
            with self.assertRaises((ValueError,KeyError)):W.original(value,[])
if __name__=="__main__":unittest.main()
