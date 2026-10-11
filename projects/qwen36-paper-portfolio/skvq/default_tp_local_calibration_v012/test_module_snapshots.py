"""Eight actual transport/plumbing regressions, stdlib-only.
Explicit local guest-path surrogates are not library/calibration/device authority.
"""
import ast,copy,hashlib,json,sys,tempfile,types,unittest
from contextlib import ExitStack,contextmanager
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C
import module_snapshots as M
import library_probe as L
import consume as R
import consume_cpu_whole as W
import cpu_entry as E
import cpu_host as H
import dependency_overlay as D
def publish_bytes(path,raw):
    path=Path(path)
    with path.open("xb")as f:f.write(raw)
    return C.reference(path)
def publish(path,value):return publish_bytes(path,json.dumps(value,sort_keys=True).encode()+b"\n")
@contextmanager
def fixture(tmp):
    root=Path(tmp).absolute();library=root/"library";library.mkdir()
    original={};origins={}
    for name in M.NAMES:
        actual=root/(name+".py");actual.write_bytes(("# real test-owned bytes "+name+"\n").encode())
        guest="/usr/local/python3.12.13/lib/python3.12/site-packages/"+name+".py"
        r=C.reference(actual);origins[name]=dict(r,path=guest);original[guest]=actual
    real_reference=C.reference
    def fake_path(value):
        return original.get(str(value),Path(value))
    def read_reference(value):
        requested=str(value);r=real_reference(fake_path(value))
        for guest,actual in original.items():
            if requested in(guest,str(actual)):return dict(r,path=guest)
        return r
    source_file=root/"SOURCE.json";source_file.write_text('{"software_fixture":true}')
    packet=real_reference(source_file)
    with patch.object(M,"Path",side_effect=fake_path),patch.object(C,"reference",side_effect=read_reference),\
         patch.object(C,"atomic",return_value=types.SimpleNamespace(publish_bytes=publish_bytes)),\
         patch.object(C,"publish",side_effect=publish),\
         patch.object(D,"verify_saved",return_value=({"software_fixture":True},{})):
        snapshot=M.capture(origins,library,packet)
        probe=dict(schema="skvq.default-tp-local.library-probe/v1",
          status="ACTUAL_CPU_FITTING_DEPENDENCIES_IMPORTED_ONLY",source_ref=packet,
          Devices_empty=True,torch_npu_imported=False,NPU_initialized=False,
          calibration_executed=False,native_ready=False,model_ready=False,
          actual_python=dict(major_minor=[3,12],machine="aarch64"),actual_modules=origins,
          actual_cpu_threads=dict(intra=1,interop=1),actual_threadpools=[dict(num_threads=1)],
          actual_module_snapshots_ref=snapshot,dependency_helper_ref=C.reference(D.__file__),
          dependency_supply={"software_fixture":True})
        ref=publish(library/"LIBRARY_PROBE.json",probe)
        yield root,packet,probe,ref,original,read_reference
def replaced_probe(root,probe,value):
    result=copy.deepcopy(probe)
    p=root/"library"/"module-bytes"/("CHANGED-"+str(len(list(root.iterdir())))+".json")
    p.write_bytes(json.dumps(value,sort_keys=True).encode()+b"\n")
    # descriptor path is intentionally strict: replacement itself must be rejected.
    result["actual_module_snapshots_ref"]=C.reference(p)
    return result
class SnapshotTests(unittest.TestCase):
    def test01_complete_six_raw_snapshots_and_original_path_identity(self):
        with tempfile.TemporaryDirectory()as tmp,fixture(tmp)as(root,packet,probe,ref,paths,reader):
            value=M.verify(probe,ref,packet)
            self.assertEqual(set(value["modules"]),set(M.NAMES))
            self.assertEqual(value["total_snapshot_bytes"],sum(x["bytes"]for x in probe["actual_modules"].values()))
            self.assertEqual(L.verify(ref,packet),probe)
            self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test02_host_does_not_open_guest_origins_but_runtime_still_does(self):
        with tempfile.TemporaryDirectory()as tmp,fixture(tmp)as(root,packet,probe,ref,paths,reader):
            def host_reference(value):
                if str(value)in paths:raise AssertionError("host must not open guest origin")
                return reader(value)
            with patch.object(C,"reference",side_effect=host_reference):
                self.assertEqual(L.verify(ref,packet,captured=True),probe)
                with self.assertRaisesRegex(AssertionError,"guest origin"):L.verify(ref,packet)
                with self.assertRaises(ValueError):L.verify(ref,packet,captured=1)
    def test03_original_refs_reject_bool_extra_relative_and_tampered_bytes(self):
        for bad in(dict(path="/real.py",bytes=True,sha256="a"*64),
          dict(path="/real.py",bytes=1,sha256="a"*64,origin="discard-me"),
          dict(path="relative.py",bytes=1,sha256="a"*64),
          dict(path="/a/../b.py",bytes=1,sha256="a"*64)):
            with self.assertRaises(ValueError):M.original_ref(bad)
        with tempfile.TemporaryDirectory()as tmp,fixture(tmp)as(root,packet,probe,ref,paths,reader):
            saved=C.bound(probe["actual_module_snapshots_ref"])["modules"]["torch"]["snapshot_ref"]
            Path(saved["path"]).write_bytes(b"changed")
            with self.assertRaises(ValueError):L.verify(ref,packet,captured=True)
    def test04_missing_wrong_source_alias_snapshot_and_extra_keys_failclosed(self):
        for mutation in("missing","source","helper","extra","alias","bool"):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory()as tmp,fixture(tmp)as(root,packet,probe,ref,paths,reader):
                bad=copy.deepcopy(probe);value=C.bound(probe["actual_module_snapshots_ref"])
                if mutation=="missing":bad["actual_modules"].pop("numpy")
                elif mutation=="source":packet=dict(packet,sha256="f"*64)
                elif mutation=="helper":value["helper_ref"]=dict(value["helper_ref"],sha256="e"*64)
                elif mutation=="extra":value["modules"]["torch"]["origin"]="foreign"
                elif mutation=="alias":value["modules"]["torch"]["original_ref"]["path"]="/foreign/torch.py"
                else:value["total_snapshot_bytes"]=True
                if mutation not in("missing","source"):
                    descriptor=Path(probe["actual_module_snapshots_ref"]["path"])
                    descriptor.write_bytes(json.dumps(value,sort_keys=True).encode()+b"\n")
                    bad["actual_module_snapshots_ref"]=C.reference(descriptor)
                with self.assertRaises(ValueError):M.verify(bad,ref,packet)
    def test05_snapshot_capture_is_exclusive_and_checks_live_origin_before_read(self):
        with tempfile.TemporaryDirectory()as tmp,fixture(tmp)as(root,packet,probe,ref,paths,reader):
            with self.assertRaises(ValueError):M.capture(probe["actual_modules"],root/"library",packet)
            fresh=root/"fresh";fresh.mkdir();bad=copy.deepcopy(probe["actual_modules"])
            bad["torch"]["sha256"]="a"*64
            with self.assertRaises(ValueError):M.capture(bad,fresh,packet)
            self.assertFalse((fresh/"module-bytes"/"torch.bin").exists())
    def test06_real_whole_workload_calls_captured_readonly_consumer(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).absolute();(root/"work").mkdir();whole_file=root/"WHOLE_REF.json";whole_file.write_text("{}")
            source=dict(path="/actual/SOURCE.json",bytes=1,sha256="a"*64);whole=dict(path="/actual/WHOLE.json",bytes=1,sha256="b"*64)
            independent=dict(actual_rank_fits=128,calibration_refs=list(range(64)),writer_handoffs=list(range(64)),fixture_only=True)
            completed=[]
            for label,argv,result in E.plans(source,whole_file,root/"work","bf16-exact-cpu32"):
                result.parent.mkdir(parents=True,exist_ok=True)
                rr=publish(result,independent if label=="INDEPENDENT"else dict(fixture_only=True))
                so=publish(root/"work"/(label+".stdout.json"),rr);se=publish_bytes(root/"work"/(label+".stderr"),b"")
                argv[0]=H.PY
                cli=publish(root/"work"/(label+"-CLI.json"),dict(argv=argv,exit_code=0,timed_out=False,actual_child_completed=True,source_ref=source,stdout=so,stderr=se))
                completed.append(dict(stage=label,result_ref=rr,original_cli_ref=cli))
            value=dict(schema="skvq.default-tp-local.cpu-workload/v1",status="CALIBRATION_CPU_WORKLOAD_CONSUMED_HOST_AUTHORITY_PENDING",
              source_ref=source,capture_whole_ref=whole,primary=None,total_seconds=600,cleanup_reserved_seconds=90,
              host_owned_terminal_consumer_required=True,native_ready=False,model_ready=False,performance_ready=False,task_ready=False,completed=completed)
            with patch.object(R,"consume",return_value=independent)as call:
                self.assertEqual(W.workload(value,source,whole,root,whole_file,"bf16-exact-cpu32")[1],independent)
                call.assert_called_once_with(root/"work"/"producer",whole,source,write_artifacts=False,module_namespace="captured")
    def test07_fresh_runtime_children_keep_default_live_and_full_capture_gate(self):
        code=(HERE/"consume.py").read_text();fn=next(x for x in ast.parse(code).body if isinstance(x,ast.FunctionDef)and x.name=="consume")
        self.assertEqual(fn.args.kwonlyargs[1].arg,"module_namespace")
        self.assertEqual(fn.args.kw_defaults[1].value,"live")
        self.assertIn('library=verify(p["actual_library_probe_ref"],packet,captured=module_namespace=="captured")',code)
        self.assertIn('for actual in e["actual_modules"].values():need(reference(actual["path"])==actual',code)
        self.assertEqual([x[0]for x in E.plans(dict(sha256="a"*64),Path("/WHOLE"),Path("/work"),"original")],["LIBRARY","PRODUCER","INDEPENDENT"])
        self.assertEqual(C.CAPTURE["sha256"],"9c7b1118b1cd1f2a20ab7fde0ecb98031bf14289c9c795c18f48de9cdb805acd")
    def test08_all_source_compile_and_no_framework_import(self):
        for path in HERE.glob("*.py"):compile(path.read_bytes(),str(path),"exec")
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SnapshotTests))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
