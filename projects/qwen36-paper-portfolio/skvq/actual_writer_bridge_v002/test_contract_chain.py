"""Real source metadata/CLI/mount boundary tests. Fixtures grant no data/device authority."""
import copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
import writer_host as H
import writer_whole as W
class Chain(unittest.TestCase):
    def test01_actual_frozen_manifest_current_binding_and_six_format_refs(self):
        m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
        self.assertEqual(m["capture_source"],C.CAPTURE);self.assertEqual(m["calibration_source"],C.CALIBRATION)
        rows=m["files"]+m["dependencies"];refs={r["path"]:r for r in rows}
        self.assertEqual(len(rows),len(refs));self.assertEqual(len(rows),m["source_count"])
        for ref in [C.CAPTURE,C.CALIBRATION,C.WRITER,C.LAYOUT,C.IO,C.BUDGET,C.CLOCK,*C.HOST_BINDINGS.values(),*m["native_format_patch_chain"].values()]:
            self.assertEqual(ref,refs[ref["path"]])
        self.assertEqual(set(m["native_format_patch_chain"]),{"root","loader","exports","format","patch_manager","npu_patches"})
        self.assertFalse(any("/skvq-preprojection-current72h-v1-013/"in p and not p.endswith("/SOURCE_MANIFEST.json")for p in refs))
        entry=json.loads((HERE/"ENTRY.json").read_bytes())
        self.assertEqual(entry["source"]["sha256"],hashlib.sha256((HERE/"SOURCE_MANIFEST.json").read_bytes()).hexdigest())
        self.assertEqual(entry["host"]["argv"],[str(x).replace(chr(92),"/")for x in W.host_argv(Path(entry["host"]["output"]),entry["source"],Path(entry["prerequisite"]["calibration_whole_ref_json"]))])
    def test02_actual_fresh_isolated_cli_all_four_stages_default_OFF(self):
        out=C.ROOT.parent/"run-skvq-actual-writer-bridge-002-software-negative";source={"sha256":"a"*64}
        self.assertFalse(out.exists())
        for stage in ("input-plan","canary","numeric","independent"):
            argv=H.args(stage,source,out,C.ROOT.parent/"DATA_PENDING.json")
            argv.remove("--execute")
            # Windows local preparation uses only the exact declared byte mirror.
            if HERE!=C.ROOT:
                local=HERE/Path(argv[0]).name
                row=next(r for r in json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())["files"]if Path(r["path"]).name==local.name)
                raw=local.read_bytes();self.assertEqual(len(raw),row["bytes"]);self.assertEqual(hashlib.sha256(raw).hexdigest(),row["sha256"])
                argv[0]=str(local)
            r=subprocess.run([sys.executable,"-I","-B",*argv],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0,r.stderr);self.assertIs(json.loads(r.stdout)["default_enabled"],False)
        self.assertFalse(out.exists());self.assertNotIn("torch",sys.modules);self.assertNotIn("numpy",sys.modules)
    def test03_actual_mount_root_distinct_absent_numeric_and_plan_child(self):
        with tempfile.TemporaryDirectory()as tmp:
            mount=Path(tmp).absolute()
            for name in ("plan","numeric"):
                leaf=C.new_output(mount/name);self.assertTrue(leaf.is_dir())
                with self.assertRaises(ValueError):C.new_output(leaf)
            for name in ("work","source","other"):
                with self.assertRaises(ValueError):C.new_output(mount/name)
    def test04_actual_mount_factory_cal006_capture014_no_broad_cache_or_alias(self):
        m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes());out=C.ROOT.parent/"run-skvq-actual-writer-bridge-002-fixture"
        calroot=C.ROOT.parent/"run-skvq-default-tp-local-006-fixture"
        caproot=C.ROOT.parent/"run-skvq-current72h-projection-014-fixture"
        whole={"host_result_ref":{"path":str(calroot/"HOST_RESULT.json")},"capture_whole_ref":{"path":"actual-capture"}}
        capture={"host_result_ref":{"path":str(caproot/"HOST_RESULT.json")}}
        def obj(ref):
            if ref["path"].endswith("SOURCE_MANIFEST.json"):return m
            if ref["path"]=="actual-calibration":return whole
            if ref["path"]=="actual-capture":return capture
            raise AssertionError(ref)
        def ref(path):return {"path":str(path),"bytes":1,"sha256":"f"*64}
        with patch.object(C,"obj",side_effect=obj),patch.object(C,"ref",side_effect=ref):
            mounts=H.mount_set(out,C.ROOT.parent/"WHOLE_REF.json",{"path":"actual-calibration"})
            self.assertEqual([k for k,(_,rw)in mounts.items()if rw],[str(out)])
            for r in m["dependencies"]:
                p=Path(r["path"]);self.assertTrue(any((p==Path(dst)or Path(dst)in p.parents)and src==dst and rw is False for dst,(src,rw)in mounts.items()))
            self.assertNotIn("/cache",mounts);self.assertNotIn(str(C.ROOT.parent),mounts)
            for invalid in ("run-skvq-default-tp-local-005-fixture","run-skvq-default-tp-local-007-fixture"):
                bad=copy.deepcopy(whole);bad["host_result_ref"]["path"]=str(C.ROOT.parent/invalid/"HOST_RESULT.json")
                with patch.object(C,"obj",side_effect=lambda r:bad if r["path"]=="actual-calibration"else obj(r)):
                    with self.assertRaises(ValueError):H.mount_set(out,C.ROOT.parent/"WHOLE_REF.json",{"path":"actual-calibration"})
def main():
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Chain))
    return 0 if r.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
