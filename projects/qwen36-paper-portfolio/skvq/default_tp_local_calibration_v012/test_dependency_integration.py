"""Actual new library/binder/three-child source bodies with inert filesystem fixtures.
No package wheel, Torch, fitted author result, target ABI or calibration PASS.
"""
import ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from contextlib import contextmanager,ExitStack
from pathlib import Path,PurePosixPath
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C,dependency_overlay as D,library_probe as L,cpu_entry as E,cpu_host as H,consume_cpu_whole as W
from test_dependency_overlay import Bundle
@contextmanager
def actual_file_fixture():
    with tempfile.TemporaryDirectory(prefix="actual-binding-",dir=HERE)as td:
        base=Path(td).resolve();b=Bundle(base)
        for name in("torch","numpy","scipy"):
            f=base/"native"/name/"__init__.py";f.parent.mkdir(parents=True)
            f.write_text("__version__='inventory-fixture'\n",encoding="utf-8")
            b.baseline[name]["origin_ref"]=D.reference(f)
        b.members["scikit-learn"]["sklearn/__init__.py"]=b"__version__='1.0.0'\n"
        b.members["scikit-learn"]["sklearn/cluster/__init__.py"]=b"class KMeans:\n    pass\n"
        b.members["joblib"]["joblib/__init__.py"]=b"__version__='1.0.0'\n"
        b.members["threadpoolctl"]["threadpoolctl.py"]=b"__version__='1.0.0'\ndef threadpool_info():return []\n"
        for name in D.PACKAGES:b.rebuild(name)
        # Fixture uses exact reviewed topology, not the actual Linux deployment path.
        (base/"wheels").mkdir();(base/"metadata").mkdir()
        for row in b.rows:
            old=Path(row["wheel_ref"]["path"]);new=base/"wheels"/old.name;new.write_bytes(old.read_bytes());row["wheel_ref"]=D.reference(new)
            old=Path(row["pypi_metadata_ref"]["path"]);new=base/"metadata"/old.name;new.write_bytes(old.read_bytes());row["pypi_metadata_ref"]=D.reference(new)
        b.manifest["root"]=str(b.root);mf=base/"BUNDLE.json";mf.write_text(json.dumps(b.manifest),encoding="utf-8");ref=D.reference(mf)
        lock=dict(packages=[dict(name=r["name"],version=r["version"],bytes=r["wheel_ref"]["bytes"],
            sha256=r["wheel_ref"]["sha256"],url=r["download_url"],filename=Path(r["wheel_ref"]["path"]).name)for r in b.rows],
            total_wheel_bytes=11827308,native_baseline={n:v["version"]for n,v in b.baseline.items()},
            native_origin_refs={n:v["origin_ref"]for n,v in b.baseline.items()})
        lk=base/"LOCK.json";lk.write_text(json.dumps(lock),encoding="utf-8")
        # reviewed() uses site by this exact name; static tree verifier remains real.
        site=base/"site";b.root.rename(site);b.root=site;b.manifest["root"]=str(site);mf.write_text(json.dumps(b.manifest),encoding="utf-8");ref=D.reference(mf)
        with ExitStack()as s:
            s.enter_context(patch.object(D,"LOCK",lk));s.enter_context(patch.object(D,"BUNDLE_ROOT",base))
            s.enter_context(patch.object(D,"NATIVE_SITE",base/"native"));s.enter_context(patch.object(D,"BOUND",None))
            prior=list(sys.path);s.callback(lambda:sys.path.__setitem__(slice(None),prior))
            s.enter_context(patch.dict(sys.modules))
            for name in("torch","numpy"):
                f=base/"native"/name/"__init__.py";sp=importlib.util.spec_from_file_location(name,f)
                m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);sys.modules[name]=m
            yield b,ref,base
class Integration(unittest.TestCase):
    def test01_real_current_modules_then_five_real_match_loaded_calls(self):
        with actual_file_fixture()as(b,ref,base):
            values=L.current_modules(ref)
            origins={n:C.reference(__import__("inspect").getfile(m))for n,m in values.items()}
            probe=dict(dependency_supply=dict(manifest_ref=ref),actual_modules=origins)
            for _ in range(5):
                again=L.match_loaded(probe)
                self.assertTrue(all(again[n]is values[n]for n in values))
            self.assertEqual(sys.path[0],str(b.root));self.assertNotIn("torch_npu",sys.modules)
    def test02_different_manifest_identity_rejected_after_import(self):
        with actual_file_fixture()as(b,ref,base):
            L.current_modules(ref)
            with self.assertRaises(ValueError):D.bind(dict(ref,sha256="0"*64))
    def test03_real_cached_package_origin_substitution_rejected(self):
        with actual_file_fixture()as(b,ref,base):
            L.current_modules(ref);sys.modules["sklearn"].__file__=str(base/"foreign.py")
            with self.assertRaises(ValueError):D.bind(ref)
    def test04_real_cached_spec_origin_substitution_rejected(self):
        with actual_file_fixture()as(b,ref,base):
            L.current_modules(ref);sys.modules["joblib"]=types.SimpleNamespace(__file__=str(b.root/"joblib/__init__.py"),__spec__=None)
            with self.assertRaises(ValueError):D.bind(ref)
    def test05_entire_tree_rechecked_after_first_import(self):
        with actual_file_fixture()as(b,ref,base):
            L.current_modules(ref);(b.root/"sklearn/__init__.py").write_bytes(b"changed")
            with self.assertRaises(ValueError):D.bind(ref)
    def test06_process_identity_change_refused(self):
        with actual_file_fixture()as(b,ref,base):
            L.current_modules(ref);D.BOUND=dict(D.BOUND,pid=os.getpid()+1)
            with self.assertRaises(ValueError):D.bind(ref)
    def test07_existing_path_injection_refused_before_import(self):
        with actual_file_fixture()as(b,ref,base):
            sys.path.insert(0,str(b.root))
            with self.assertRaises(ValueError):D.bind(ref)
    def test08_ambient_sklearn_cold_substitution_refused(self):
        with actual_file_fixture()as(b,ref,base):
            sys.modules["sklearn"]=types.SimpleNamespace()
            with self.assertRaises(ValueError):D.bind(ref)
    def test09_actual_three_fresh_child_plans_only_library_receives_bundle(self):
        df=Path("/reviewed/BUNDLE_REF.json");rows=E.plans(dict(sha256="a"*64),Path("/WHOLE"),Path("/work"),"bf16-exact-cpu32",df)
        self.assertEqual([x[0]for x in rows],["LIBRARY","PRODUCER","INDEPENDENT"])
        for _,argv,_ in rows:self.assertEqual(argv[1:3],["-I","-B"])
        self.assertEqual(rows[0][1][-2:],["--dependency-ref-json",str(df)])
        self.assertNotIn("--dependency-ref-json",rows[1][1]);self.assertNotIn("--dependency-ref-json",rows[2][1])
        self.assertIn("--library-ref-json",rows[1][1])
    def test10_library_sets_threads_once_then_smoke(self):
        source=(HERE/"library_probe.py").read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=="main")
        calls=[n for n in ast.walk(node)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
        setters=[n for n in calls if n.func.attr=="set_num_interop_threads"];smoke=[n for n in calls if n.func.attr=="smoke_loaded"]
        self.assertEqual(len(setters),1);self.assertEqual(len(smoke),1);self.assertLess(setters[0].lineno,smoke[0].lineno)
        helper=ast.parse((HERE/"dependency_overlay.py").read_text());sm=next(n for n in helper.body if isinstance(n,ast.FunctionDef)and n.name=="smoke_loaded")
        self.assertFalse(any(isinstance(n,ast.Attribute)and n.attr=="set_num_interop_threads"for n in ast.walk(sm)))
    def test11_independent_consume_stays_stdlib_live_and_snapshot(self):
        source=(HERE/"consume.py").read_text()
        self.assertNotIn("match_loaded(",source);self.assertNotIn("current_modules(",source)
        self.assertNotIn("import sklearn",source);self.assertNotIn("import torch",source)
        self.assertIn('captured=module_namespace=="captured"',source)
        self.assertIn("128",source);self.assertIn("==64",source)
    def test12_immutable_real_author_and_producer_bytes(self):
        mf=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
        for r in mf["unchanged_math_and_library_files"]:
            p=HERE/Path(r["path"]).name
            self.assertEqual(p.stat().st_size,r["bytes"]);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r["sha256"])
        lock=json.loads(D.LOCK.read_bytes())
        self.assertEqual(set(lock["native_origin_refs"]),{"torch","numpy","scipy"})
        self.assertEqual(lock["total_wheel_bytes"],sum(r["bytes"]for r in lock["packages"]))
        for n,r in lock["native_origin_refs"].items():
            if os.name!="nt":self.assertEqual(D.ref_shape(r,2**20),r)
            self.assertEqual(set(r),{"path","bytes","sha256"})
            self.assertIs(type(r["bytes"]),int);self.assertGreater(r["bytes"],0)
            self.assertEqual(PurePosixPath(r["path"]),PurePosixPath("/usr/local/python3.12.13/lib/python3.12/site-packages")/n/"__init__.py")
        for row in lock["packages"]:
            meta=json.loads((HERE/(row["name"]+"-"+row["version"]+"-PYPI.json")).read_bytes())
            selected=[f for f in meta["urls"]if f["filename"]==row["filename"]]
            self.assertEqual(len(selected),1);f=selected[0]
            self.assertEqual((f["url"],f["size"],f["digests"]["sha256"]),(row["url"],row["bytes"],row["sha256"]))
        body=(HERE/"cluster_producer.py").read_text()
        self.assertIn('kw=={"n_init":10}',body);self.assertIn('np.random.get_state()',body)
        self.assertNotIn("np.random.seed(",body)
    def test13_actual_host_and_whole_bundle_parameter(self):
        df=Path("/reviewed/BUNDLE_REF.json");sha="a"*64;wf=Path("/WHOLE");out=Path("/output")
        self.assertEqual(H.guest_args(dict(sha256=sha),wf,out,"bf16-exact-cpu32",df)[-2:],["--dependency-ref-json",str(df)])
        self.assertEqual(W.host_argv(out,sha,wf,"bf16-exact-cpu32",df)[-2:],["--dependency-ref-json",str(df)])
        host=(HERE/"cpu_host.py").read_text();whole=(HERE/"consume_cpu_whole.py").read_text()
        self.assertIn('mounts[str(D.BUNDLE_ROOT)]=(str(D.BUNDLE_ROOT),False)',host)
        self.assertIn('H.dependency_input(dependency_file)',whole)
        self.assertEqual(H.TOTAL,600);self.assertEqual(H.CLEANUP,90);self.assertEqual(H.OUTCAP,32*2**20)
    def test14_wrong_reviewed_version_rejected_before_bind(self):
        with actual_file_fixture()as(b,ref,base):
            lock=json.loads(D.LOCK.read_bytes());lock["packages"][0]["version"]="2.0.0";D.LOCK.write_text(json.dumps(lock))
            with self.assertRaises(ValueError):D.bind(ref)
    def test15_reviewed_tree_no_native_replacement(self):
        with actual_file_fixture()as(b,ref,base):
            D.reviewed(ref,native=False)
            manifest=json.loads(Path(ref["path"]).read_bytes());manifest["baseline"]["numpy"]["origin_ref"]["path"]=str(b.root/"numpy/__init__.py")
            Path(ref["path"]).write_text(json.dumps(manifest));ref=D.reference(ref["path"])
            with self.assertRaises(ValueError):D.reviewed(ref,native=False)
    def test16_no_actual_dependency_or_calibration_claim_in_fixture(self):
        with actual_file_fixture()as(b,ref,base):
            _,proof=D.reviewed(ref,native=False)
            self.assertFalse(proof["actual_sameimage_import_fit_checked"]);self.assertFalse(proof["calibration_executed"])
            self.assertFalse(proof["native_ready"]);self.assertFalse(proof["model_ready"])
def main():
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Integration))
    return 0 if r.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
