"""Delivery subprocess controls; enabled path uses an explicit fake loader."""
import copy,hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def fixture(self,root,*,runtime_name="LIFECYCLE_COMPACT_MANIFEST_R16.json"):
        base=Path(root);package=base/"delivery_runtime";package.mkdir()
        for name in ("patch.py","sitecustomize.py","run_with_patch.sh"):shutil.copyfile(HERE/"delivery_runtime"/name,package/name)
        loader=base/"independent_compact_loader.py"
        loader.write_text("from pathlib import Path\ndef enable():Path(__file__).with_name('enabled.marker').write_text('stub-enabled')\n")
        runtime={"source_sha256":{"independent_compact_loader.py":hashlib.sha256(loader.read_bytes()).hexdigest()}}
        rp=base/runtime_name;rp.write_text(json.dumps(runtime))
        m=json.loads((HERE/"delivery_runtime"/"MANIFEST.json").read_text())
        m["runtime_manifest_file"]=runtime_name
        m["runtime_manifest_sha256"]=hashlib.sha256(rp.read_bytes()).hexdigest()
        (package/"MANIFEST.json").write_text(json.dumps(m))
        return base,package,rp
    def run_case(self,flag,mutate=lambda b,p,r:None,*,launcher=True,args=True,
                 runtime_name="LIFECYCLE_COMPACT_MANIFEST_R16.json"):
        with tempfile.TemporaryDirectory()as td:
            base,package,rp=self.fixture(td,runtime_name=runtime_name);mutate(base,package,rp)
            env={"PATH":os.environ["PATH"],"PYTHONPATH":str(package)+":"+str(base),"INDEPENDENT_COMPACT_MANIFEST":str(rp),"PYTHONDONTWRITEBYTECODE":"1","TMPDIR":"/cache/cch"}
            if flag is not None:env["INDEPENDENT_COMPACT_HYPIC"]=flag
            body=[sys.executable,"-B","-c","import sys;assert 'torch_npu'not in sys.modules;print('SERVICE')"]
            cmd=(["bash",str(package/"run_with_patch.sh")]+(body if args else []))if launcher else body
            p=subprocess.run(cmd,env=env,cwd="/cache/cch",capture_output=True,text=True)
            return p,(base/"enabled.marker").exists()
    def test_default_disabled(self):
        p,enabled=self.run_case(None);self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(enabled);self.assertNotIn("HOOK_READY",p.stderr)
    def test_explicit_disabled(self):
        p,enabled=self.run_case("0");self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(enabled)
    def test_enabled_stub(self):
        p,enabled=self.run_case("1");self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(enabled);self.assertIn("IMPORT_HOOK_READY",p.stderr);self.assertIn("SERVICE",p.stdout)
    def test_runtime_source_drift(self):
        p,enabled=self.run_case("1",lambda b,p,r:(b/"independent_compact_loader.py").write_text("changed"))
        self.assertEqual(p.returncode,78,p.stderr);self.assertFalse(enabled);self.assertNotIn("SERVICE",p.stdout)
    def test_wrapper_patch_drift(self):
        def mutate(b,p,r):
            f=p/"patch.py";f.write_text(f.read_text()+"\n# drift\n")
        p,enabled=self.run_case("1",mutate);self.assertEqual(p.returncode,78,p.stderr);self.assertFalse(enabled)
    def test_runtime_manifest_drift(self):
        p,enabled=self.run_case("1",lambda b,p,r:r.write_text("{}"))
        self.assertEqual(p.returncode,78,p.stderr);self.assertFalse(enabled)
    def test_python_startup_fails_closed_without_launcher(self):
        p,enabled=self.run_case("1",lambda b,p,r:r.write_text("{}"),launcher=False)
        self.assertEqual(p.returncode,78,p.stderr);self.assertNotIn("SERVICE",p.stdout)
    def test_no_command(self):
        p,enabled=self.run_case("0",args=False);self.assertEqual(p.returncode,2);self.assertFalse(enabled)
    def test_r21_enabled_explicit_stub(self):
        p,enabled=self.run_case("1",runtime_name="LIFECYCLE_COMPACT_MANIFEST_R21.json")
        self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(enabled)
    def test_r21_source_drift_fails_closed(self):
        p,enabled=self.run_case("1",lambda b,p,r:(b/"independent_compact_loader.py").write_text("changed"),
            runtime_name="LIFECYCLE_COMPACT_MANIFEST_R21.json")
        self.assertEqual(p.returncode,78,p.stderr);self.assertFalse(enabled)
    def test_unapproved_runtime_names_rejected(self):
        for name in ("OTHER.json","../LIFECYCLE_COMPACT_MANIFEST_R21.json",
                     "/tmp/LIFECYCLE_COMPACT_MANIFEST_R21.json"):
            def mutate(b,p,r):
                f=p/"MANIFEST.json";m=json.loads(f.read_text());m["runtime_manifest_file"]=name
                f.write_text(json.dumps(m))
            p,enabled=self.run_case("1",mutate)
            self.assertEqual(p.returncode,78,p.stderr);self.assertFalse(enabled)
    def test_declared_r21_cannot_use_r16_environment(self):
        def mutate(b,p,r):
            f=p/"MANIFEST.json";m=json.loads(f.read_text())
            m["runtime_manifest_file"]="LIFECYCLE_COMPACT_MANIFEST_R21.json"
            (b/m["runtime_manifest_file"]).write_bytes(r.read_bytes())
            f.write_text(json.dumps(m))
        p,enabled=self.run_case("1",mutate)
        self.assertEqual(p.returncode,78,p.stderr);self.assertFalse(enabled)
if __name__=="__main__":unittest.main()
