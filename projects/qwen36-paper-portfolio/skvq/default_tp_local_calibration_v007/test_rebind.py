"""Cross-stage rebind regressions. Fixtures are SOFTWARE_ONLY, never data authority."""
import ast,copy,hashlib,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path,PurePosixPath
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C
import whole_precheck as P
import cpu_host as H
import calibration_inputs as I
def sample():
    return dict(schema="skvq.capture014.offline.whole/v1",
      status="RELEASED014_ALL256_RAW_DERIVED_CPU_WHOLE_CONSUMED_NOT_CALIBRATED",
      source_ref=C.DERIVED,producer_source_ref=C.CAPTURE,original_failed_whole_ref=C.FAILED_ORIGINAL,
      original_failed_whole_preserved=True,original_failed_whole_succeeded=False,
      whole_operation_consumed=True,Devices_empty=True,CPU_QUEUE_no_peer_admission=True,
      events=16384,qkv_bytes=256*2**30,preprojection_K_raw_bytes=32*2**30,clock=C.CLOCK,
      portfolio_cutoff_epoch=C.CUT,author_calibration_pending=True,author_global_grouping_equivalent=False,
      native_ready=False,model_ready=False,performance_ready=False,task_ready=False)
def original_failure():
    path=Path(C.FAILED_ORIGINAL["path"])
    if not path.is_file():
        path=Path("C:/Users/Huawei/AppData/Local/Temp/skvq014-actual-metadata-main-20261011-001/MAIN_SKVQ014_05A7_FAILED_ORIGINAL_20261011.json")
    if not path.is_file():
        mirror=Path("C:/Users/Huawei/AppData/Local/Temp/skvq014-actual-metadata-main-20261011-001/MIRROR_MANIFEST.json")
        m=json.loads(mirror.read_bytes())
        # Locate only by this exact whole SHA, never by arbitrary basename.
        rows=m.get("files",m.get("mirrors",[]))
        for r in rows:
            if r.get("sha256")==C.FAILED_ORIGINAL["sha256"]:path=Path(r.get("local_path",r.get("local")))
    raw=path.read_bytes()
    C.need(len(raw)==C.FAILED_ORIGINAL["bytes"]and hashlib.sha256(raw).hexdigest()==C.FAILED_ORIGINAL["sha256"],
      "actual failed05a7 original mirror, not fixture")
    return json.loads(raw)
class Rebind(unittest.TestCase):
    def test01_typed_new_contract_and_actual_failed_original_never_upgrade(self):
        self.assertEqual(P.envelope(sample()),sample())
        old=original_failure();self.assertEqual(old["operation"]["result"]["record"]["exitCode"],1)
        with self.assertRaises(ValueError):P.envelope(old)
        for v in (dict(schema="skvq.current72h.preprojection.whole/v1",
          status="FULL_CAPTURE_PREPROJECTION_ORIGINAL_CONSUMED_NOT_CALIBRATED"),dict(sample(),status="FAILED")):
            with self.assertRaises(ValueError):P.envelope(v)
    def test02_source_coverage_clock_and_authority_negatives(self):
        for key,value in (("source_ref",C.CAPTURE),("producer_source_ref",C.DERIVED),
          ("original_failed_whole_succeeded",True),("original_failed_whole_preserved",False),
          ("events",16383),("events",True),("qkv_bytes",float(256*2**30)),
          ("preprojection_K_raw_bytes",0),("whole_operation_consumed",False),("Devices_empty",False),
          ("clock",{}),("portfolio_cutoff_epoch",C.CUT+1),("native_ready",True),("model_ready",True),
          ("performance_ready",True),("task_ready",True),("author_calibration_pending",False)):
            with self.subTest(key=key),self.assertRaises(ValueError):P.envelope(dict(sample(),**{key:value}))
    def test03_real_clean_default_OFF_and_parent_basename_unchanged(self):
        before=sys.modules["cpu_host"]
        r=subprocess.run([sys.executable,"-I","-B",str(HERE/"whole_precheck.py")],capture_output=True,text=True,timeout=5)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIs(json.loads(r.stdout)["default_enabled"],False)
        self.assertIs(sys.modules["cpu_host"],before)
        self.assertNotIn("offline_contract",sys.modules);self.assertNotIn("torch",sys.modules)
    def test04_fresh_child_argv_preserves_isolation_and_no_shell(self):
        ref=dict(path="/actual/DERIVED_WHOLE.json",bytes=100,sha256="a"*64)
        argv=P.command(ref,"b"*64)
        self.assertEqual(argv[:3],[sys.executable,"-I","-B"])
        self.assertEqual(Path(argv[3]),HERE/"whole_precheck.py")
        self.assertEqual(json.loads(argv[-1]),ref);self.assertNotIn("-c",argv)
        body=(HERE/"whole_precheck.py").read_text()
        self.assertNotIn("sys.modules.pop",body);self.assertNotIn("del sys.modules",body)
        self.assertIn('reader.consume(',body);self.assertNotIn("D.publish(",body)
    def test05_replay_rejects_loaded_foreign_namespace_before_donor(self):
        value=sample();manifest=dict(schema="skvq.capture014.offline.sources/v1",producer_source_ref=C.CAPTURE,
          default_enabled=False,files=[])
        def bound(r):return manifest if r==C.DERIVED else value
        with patch.object(C,"source"),patch.object(C,"bound",side_effect=bound),\
          patch.object(C,"donor",side_effect=AssertionError("no donor before namespace check")):
            with self.assertRaisesRegex(ValueError,"fresh isolated"):P.replay({},"a"*64)
    def test06_actual_precheck_child_failure_and_wrong_stdout_refused(self):
        source=C.reference(HERE/"SOURCE_MANIFEST.json");mf=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
        mf["files"]=[C.reference(HERE/"whole_precheck.py")if Path(r["path"]).name=="whole_precheck.py"else r for r in mf["files"]]
        value=sample()
        def bound(r):return mf if r==source else value
        for result in (types.SimpleNamespace(returncode=1,stdout=b"",stderr=b"real fixture exit"),
          types.SimpleNamespace(returncode=0,stdout=b"{}",stderr=b"")):
            with patch.object(C,"bound",side_effect=bound),patch.object(P.subprocess,"run",return_value=result)as run:
                with self.assertRaises(ValueError):P.precheck({})
                self.assertEqual(run.call_args.kwargs["timeout"],120)
                self.assertTrue(run.call_args.kwargs["capture_output"])
    def test07_actual_mount_constructor_both_ro_trees_exact_alias_and_only_new_rw(self):
        value=sample();base=PurePosixPath(C.ROOT.as_posix()).parent
        old=base/"run-skvq-current72h-projection-014-main-20261010-001"
        derived=base/"run-skvq-capture014-offline-001-main-20261011-001"
        value.update(original_capture_host_result_ref=dict(path=str(old/"HOST_RESULT.json")),
          host_result_ref=dict(path=str(derived/"HOST_RESULT.json")),
          original_ref=dict(path=str(derived/"WHOLE_ORIGINAL.json"),bytes=100,sha256="c"*64))
        whole_ref=dict(path=str(derived/"DERIVED_WHOLE.json"),bytes=100,sha256="d"*64)
        whole_descriptor=dict(path="/actual/WHOLE_REF.json",bytes=100,sha256="e"*64)
        alias="/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v1"
        source="/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v2"
        prior=dict(owned=[dict(npu=False,released=True,mounts={str(derived):[str(derived),True],alias:[source,False]})])
        manifest=dict(dependencies=[C.DERIVED])
        def bound(r,limit=8*2**20):
            if r==whole_ref:return value
            if r==value["host_result_ref"]:return prior
            return manifest
        out=base/"run-skvq-default-tp-local-007-software"
        with patch.object(C,"bound",side_effect=bound),patch.object(C,"reference",return_value=whole_descriptor),\
          patch.object(H,"Path",PurePosixPath),patch.object(C,"ROOT",PurePosixPath(C.ROOT.as_posix())):
            mounts=H.mount_set(out,PurePosixPath("/actual/WHOLE_REF.json"),whole_ref)
        self.assertEqual(mounts[str(old)],(str(old),False));self.assertEqual(mounts[str(derived)],(str(derived),False))
        self.assertEqual(mounts[alias],(source,False))
        self.assertEqual([d for d,(_,rw)in mounts.items()if rw],[str(out)])
        bad=dict(prior,owned=[dict(npu=True,released=True,mounts={})])
        prior.clear();prior.update(bad)
        with patch.object(C,"bound",side_effect=bound),patch.object(C,"reference",return_value=whole_descriptor),\
          patch.object(H,"Path",PurePosixPath),patch.object(C,"ROOT",PurePosixPath(C.ROOT.as_posix())),self.assertRaises(ValueError):
            H.mount_set(out,PurePosixPath("/actual/WHOLE_REF.json"),whole_ref)
    def test08_all_unchanged_algorithm_and_module_snapshot_bytes(self):
        m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
        for row in m["unchanged_math_and_library_files"]:
            p=HERE/Path(row["path"]).name
            self.assertEqual(p.stat().st_size,row["bytes"]);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row["sha256"])
        body=(HERE/"calibration_inputs.py").read_text()
        self.assertIn("precheck(whole_ref)",body);self.assertNotIn('loader.original(',body)
        self.assertIn('for eref in rr["events"]',body);self.assertIn("all16384 original event identities",body)
    def test09_complete_derived_manifest_closure_not_cli_only_repin(self):
        m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes());deps={r["path"]:r for r in m["dependencies"]}
        path=Path(C.DERIVED["path"])
        if not path.is_file():path=Path("C:/Users/Huawei/AppData/Local/Temp/skvq-capture014-offline-consumer-20261011-001/SOURCE_MANIFEST.json")
        raw=path.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),C.DERIVED["sha256"])
        prior=json.loads(raw)
        for row in [C.DERIVED,*prior["files"],*prior["dependencies"]]:self.assertEqual(deps[row["path"]],row)
        self.assertEqual(m["derived_capture_consumer_source_ref"],C.DERIVED)
        self.assertEqual(len(m["files"])+len(m["dependencies"]),m["source_count"])
        e=json.loads((HERE/"ENTRY.json").read_bytes())
        self.assertEqual(e["prerequisite"]["derived_consumer_source"],C.DERIVED)
        self.assertIn("DERIVED_WHOLE_REF.json",e["prerequisite"]["actual_successful_capture_whole_ref_json"])
    def test10_600_window_accounts_for_precheck_before_controller(self):
        node=next(n for n in ast.parse((HERE/"cpu_host.py").read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=="execute")
        body=ast.get_source_segment((HERE/"cpu_host.py").read_text(),node)
        self.assertLess(body.index("stage_start=time.monotonic()"),body.index("inputs(whole_ref)"))
        self.assertIn("ctl.start=stage_start;ctl.end=min(ctl.end,stage_start+TOTAL)",body)
        self.assertEqual(H.TOTAL,600);self.assertEqual(H.CLEANUP,90)
def main():
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Rebind))
    return 0 if r.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
