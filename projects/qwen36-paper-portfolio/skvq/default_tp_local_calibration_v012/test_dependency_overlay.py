"""Stdlib source/file tests. Three fake wheels are NOT dependency or ABI proof."""
import ast,copy,hashlib,importlib.util,json,os,stat,subprocess,sys,tempfile,unittest,warnings,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("_reviewed_dependency_overlay",HERE/"dependency_overlay.py")
D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)

class Bundle:
    def __init__(self,base):
        self.base=base;self.root=base/"ro-tree";self.root.mkdir();self.rows=[];self.members={}
        for name,(module,stem)in D.PACKAGES.items():
            version="1.0.0";dist=stem+"-"+version+".dist-info"
            code=(module+".py")if name=="threadpoolctl"else(module+"/__init__.py")
            tags="cp312-cp312-manylinux_2_17_aarch64"if name=="scikit-learn"else"py3-none-any"
            members={code:b"# Explicit inert software fixture, not the package.\n",
                dist+"/METADATA":("Metadata-Version: 2.1\nName: "+name+"\nVersion: "+version+"\nRequires-Python: >=3.9\n").encode(),
                dist+"/WHEEL":("Wheel-Version: 1.0\nTag: "+tags+"\n").encode(),
                dist+"/RECORD":b"# synthetic full archive record fixture\n"}
            row=dict(name=name,version=version,wheel_ref=None,pypi_metadata_ref=None,download_url="")
            self.rows.append(row);self.members[name]=members;self.rebuild(name)
        self.baseline={}
        for name in("torch","numpy","scipy"):
            p=base/(name+"-native-origin.py");p.write_bytes(b"# unchanged native-origin fixture only\n")
            self.baseline[name]=dict(version="inventory-fixture",origin_ref=D.reference(p))
        self.manifest=dict(schema="skvq.calibration-ro-three-wheel-bundle/v1",root=str(self.root.resolve()),
            python=[3,12],machine="aarch64",glibc_min=[2,17],distributions=self.rows,baseline=self.baseline)
    def rebuild(self,name,extra=None):
        row=next(r for r in self.rows if r["name"]==name);stem=D.PACKAGES[name][1]
        p=self.base/(stem+"-"+row["version"]+"-fixture.whl")
        with zipfile.ZipFile(p,"w")as z:
            for member,raw in self.members[name].items():
                i=zipfile.ZipInfo(member);i.external_attr=(stat.S_IFREG|0o644)<<16;z.writestr(i,raw)
                if not(member.startswith("/")or".."in Path(member).parts or"\\"in member):
                    dst=self.root.joinpath(*member.split("/"));dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
            if extra:extra(z)
        row["wheel_ref"]=D.reference(p);row["download_url"]="https://files.pythonhosted.org/packages/source-bound-fixture/"+p.name
        meta=dict(info=dict(name=name,version=row["version"]),urls=[dict(filename=p.name,url=row["download_url"],
            digests=dict(sha256=row["wheel_ref"]["sha256"]),size=row["wheel_ref"]["bytes"],packagetype="bdist_wheel",yanked=False)])
        m=self.base/(stem+"-official-metadata-fixture.json");m.write_text(json.dumps(meta),encoding="utf-8")
        row["pypi_metadata_ref"]=D.reference(m)
    def ref(self):
        p=self.base/"reviewed-fixture-manifest.json";p.write_text(json.dumps(self.manifest),encoding="utf-8");return D.reference(p)
    def row(self,name="scikit-learn"):return next(r for r in self.rows if r["name"]==name)
    def metadata(self,mutation,name="scikit-learn"):
        row=self.row(name);p=Path(row["pypi_metadata_ref"]["path"]);m=json.loads(p.read_bytes());mutation(m)
        p.write_text(json.dumps(m),encoding="utf-8");row["pypi_metadata_ref"]=D.reference(p)

class SupplyTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix="skvq-ro-wheel-fixture-",dir=HERE);self.b=Bundle(Path(self.tmp.name))
    def tearDown(self):self.tmp.cleanup()
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,zipfile.BadZipFile)):D.qualify(self.b.ref())
    def test_complete_real_file_chain_static_not_abi(self):
        manifest,proof=D.qualify(self.b.ref());self.assertEqual(proof["files"],12)
        self.assertTrue(proof["full_wheel_and_extracted_bytes_checked"])
        self.assertFalse(proof["actual_sameimage_import_fit_checked"])
        self.assertFalse(proof["calibration_executed"]);self.assertFalse(proof["model_ready"])
    def test_default_off_actual_child_imports_no_framework(self):
        code="import runpy,sys;sys.argv=['dependency_overlay'];runpy.run_path(%r,run_name='__main__');assert not any(x in sys.modules for x in ('torch','numpy','sklearn','scipy','torch_npu'))"%str(HERE/"dependency_overlay.py")
        p=subprocess.run([sys.executable,"-I","-B","-c",code],capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(json.loads(p.stdout)["default_enabled"])
    def test_actual_isolated_child_ignores_pythonpath(self):
        env=dict(os.environ,PYTHONPATH=str(self.b.root));p=subprocess.run([sys.executable,"-I","-B","-c","import os,sys;assert sys.flags.isolated and sys.flags.ignore_environment;assert os.environ['PYTHONPATH'] not in sys.path"],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_exact_ref_size_nonbool(self):
        r=self.b.ref();r["bytes"]=True
        with self.assertRaises(ValueError):D.qualify(r)
    def test_ref_sha_mutation(self):
        r=self.b.ref();r["sha256"]="0"*64
        with self.assertRaises(ValueError):D.qualify(r)
    def test_missing_distribution(self):self.b.manifest["distributions"].pop();self.reject()
    def test_wrong_python_abi(self):self.b.manifest["python"]=[3,11];self.reject()
    def test_noninventoried_baseline_version(self):self.b.baseline["numpy"]["version"]="";self.reject()
    def test_overlay_cannot_replace_native_numpy(self):
        p=self.b.root/"numpy.py";p.write_bytes(b"shadow")
        self.b.baseline["numpy"]["origin_ref"]=D.reference(p);self.reject()
    def test_native_baseline_bytes_mutation(self):
        Path(self.b.baseline["torch"]["origin_ref"]["path"]).write_bytes(b"changed");self.reject()
    def test_extracted_bytes_mutation(self):(self.b.root/"sklearn/__init__.py").write_bytes(b"changed");self.reject()
    def test_no_ambient_extra_package(self):(self.b.root/"unexpected.py").write_bytes(b"extra");self.reject()
    def test_no_pycache(self):
        p=self.b.root/"sklearn/__pycache__/init.pyc";p.parent.mkdir();p.write_bytes(b"extra");self.reject()
    def test_official_url_exact_not_mirror(self):self.b.row()["download_url"]="https://mirror.invalid/file.whl";self.reject()
    def test_official_metadata_sha_must_equal_bytes(self):self.b.metadata(lambda m:m["urls"][0]["digests"].update(sha256="0"*64));self.reject()
    def test_version_must_match_official_metadata(self):self.b.metadata(lambda m:m["info"].update(version="2.0.0"));self.reject()
    def test_yanked_wheel_rejected(self):self.b.metadata(lambda m:m["urls"][0].update(yanked=True));self.reject()
    def test_wrong_arch_tag_rejected(self):
        self.b.members["scikit-learn"]["scikit_learn-1.0.0.dist-info/WHEEL"]=b"Wheel-Version: 1.0\nTag: cp312-cp312-manylinux_2_17_x86_64\n";self.b.rebuild("scikit-learn");self.reject()
    def test_pure_python_must_support_python3(self):
        self.b.members["joblib"]["joblib-1.0.0.dist-info/WHEEL"]=b"Wheel-Version: 1.0\nTag: py2-none-any\n";self.b.rebuild("joblib");self.reject()
    def test_no_pth_hook(self):self.b.members["scikit-learn"]["sklearn/evil.pth"]=b"import os";self.b.rebuild("scikit-learn");self.reject()
    def test_no_torch_member(self):self.b.members["scikit-learn"]["torch/__init__.py"]=b"shadow";self.b.rebuild("scikit-learn");self.reject()
    def test_no_traversal_member(self):self.b.members["scikit-learn"]["../outside.py"]=b"escape";self.b.rebuild("scikit-learn");self.reject()
    def test_record_required(self):
        del self.b.members["scikit-learn"]["scikit_learn-1.0.0.dist-info/RECORD"]
        (self.b.root/"scikit_learn-1.0.0.dist-info/RECORD").unlink();self.b.rebuild("scikit-learn");self.reject()
    def test_duplicate_archive_member(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore");self.b.rebuild("scikit-learn",lambda z:z.writestr("sklearn/__init__.py",b"duplicate"))
        self.reject()
    def test_bind_rejects_ambient_package(self):
        sentinel=object();prior=sys.modules.get("sklearn",sentinel);sys.modules["sklearn"]=object()
        try:
            with self.assertRaises(ValueError):D.bind(self.b.ref())
        finally:
            if prior is sentinel:del sys.modules["sklearn"]
            else:sys.modules["sklearn"]=prior
    def test_real_smoke_requires_target_before_import(self):
        # Windows fixture execution cannot claim target aarch64/HAL ABI validation.
        if sys.platform=="win32":
            with self.assertRaises(ValueError):D.smoke(self.b.ref())
        else:self.skipTest("target refusal branch specifically Windows")
    def test_archive_symlink_refused(self):
        def add(z):
            i=zipfile.ZipInfo("sklearn/link");i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(i,b"target")
        self.b.rebuild("scikit-learn",add);self.reject()
    @unittest.skipUnless(hasattr(os,"mkfifo"),"POSIX FIFO fixture; Windows skipped")
    def test_actual_fifo_tree_refused(self):os.mkfifo(self.b.root/"fifo");self.reject()
    def test_no_package_versions_selected_in_source(self):
        tree=ast.parse((HERE/"dependency_overlay.py").read_text());literals=[n.value for n in ast.walk(tree)if isinstance(n,ast.Constant)and isinstance(n.value,str)]
        for candidate in("1.4.2","1.13.1","1.4.2","3.5.0"):self.assertNotIn(candidate,literals)

def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SupplyTests);result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
