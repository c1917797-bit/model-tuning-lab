"""Actual helper/CLI boundary regressions. Temp fixtures do not prove PyArrow import, TRAIN or hardware."""
import ast,contextlib,copy,hashlib,importlib.machinery,importlib.util,io,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import input_dependency as D
import current_contract as C
def source(name):return(HERE/name).read_text()
def fn(name,file):
    return next(x for x in ast.parse(source(file)).body if isinstance(x,ast.FunctionDef)and x.name==name)
def fixture(root):
    root=Path(root).absolute();root.mkdir(exist_ok=True)
    paths={"pyarrow":"pyarrow/__init__.py","pyarrow.parquet":"pyarrow/parquet/__init__.py","pyarrow.lib":"pyarrow/lib.cpython-312-aarch64-linux-gnu.so"}
    for relative in(*paths.values(),"pyarrow/empty","pyarrow-19.0.1.dist-info/METADATA"):
        p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b"VERSION='fixture-only'\n"if relative.endswith(".py")else b"")
    files=[D.ref(p)for p in sorted(root.rglob("*"))if p.is_file()]
    return dict(schema="skvq.input-cpu-dependencies/v1",root=str(root),packages=["pyarrow","pyarrow-19.0.1.dist-info"],
      files=files,python_cache_tag="cpython-312",pyarrow_version="19.0.1",
      expected_origins={k:str(root/v)for k,v in paths.items()},read_only=True,source_owner="MAIN-frozen-offline-dependency")
def real_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m);return m
class Dependency(unittest.TestCase):
    def test01_complete_source_compile_and_original_math_unchanged(self):
        for p in HERE.glob("*.py"):compile(p.read_bytes(),str(p),"exec")
        self.assertNotIn("__name__"+"for",source("input_dependency.py"))
        original=Path("C:/Users/Huawei/AppData/Local/Temp/c150-independent-backup/skvq-calibration-capture-chain-v1-001/build_inputs.py")
        if original.exists():
            raw=original.read_bytes()
            if hashlib.sha256(raw).hexdigest()!="8bf7eea24c3d13f6cb60d632a4852bcfa8f2d67de4b0f83d9489ecb33afd34c3"and raw.endswith(b"\n\n"):raw=raw[:-1]
            self.assertEqual(hashlib.sha256(raw).hexdigest(),"8bf7eea24c3d13f6cb60d632a4852bcfa8f2d67de4b0f83d9489ecb33afd34c3")
        self.assertIn('runpy.run_path(str(D.BASE/"build_inputs.py"),run_name="__main__")',source("input_entry.py"))
    def test02_actual_complete_tree_including_zero_bytes_and_stable_hash(self):
        with tempfile.TemporaryDirectory()as tmp:
            value=fixture(Path(tmp)/"site");self.assertEqual(D.validate_lock(value),value)
            self.assertEqual(sorted(D.verify_files(value),key=lambda x:x["path"]),sorted(value["files"],key=lambda x:x["path"]))
            empty=Path(value["root"])/"pyarrow/empty";self.assertEqual(D.ref(empty)["bytes"],0)
            self.assertEqual(D.ref(empty),D.ref(empty))
    def test03_extra_missing_and_changed_dependency_files_rejected(self):
        for mode in("extra","missing","changed"):
            with tempfile.TemporaryDirectory()as tmp:
                value=fixture(Path(tmp)/"site");p=Path(value["root"])/"pyarrow/empty"
                if mode=="extra":(p.parent/"extra.py").write_bytes(b"extra")
                elif mode=="missing":p.unlink()
                else:p.write_bytes(b"changed")
                with self.assertRaises(ValueError):D.verify_files(value)
    def test04_strict_lock_bool_extra_root_escape_and_missing_origin_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            value=fixture(Path(tmp)/"site")
            wrong=[]
            x=copy.deepcopy(value);x["files"][0]["bytes"]=True;wrong.append(x)
            x=copy.deepcopy(value);x["files"][0]["origin"]="guess";wrong.append(x)
            x=copy.deepcopy(value);x["files"][0]["path"]=str(Path(tmp)/"outside.py");wrong.append(x)
            x=copy.deepcopy(value);x["expected_origins"]["fake"]="guess";wrong.append(x)
            x=copy.deepcopy(value);x["python_cache_tag"]="cpython-39";wrong.append(x)
            x=copy.deepcopy(value);x["packages"].append("other-package");wrong.append(x)
            for x in wrong:
                with self.assertRaises(ValueError):D.validate_lock(x)
    def test05_real_source_loader_origin_and_foreign_cache_refused(self):
        with tempfile.TemporaryDirectory()as tmp:
            value=fixture(Path(tmp)/"site");p=Path(value["expected_origins"]["pyarrow"])
            m=real_module("pyarrow",p);self.assertEqual(D.module_ref(m,value),D.ref(p))
            other=Path(tmp)/"foreign.py";other.write_bytes(b"foreign=True\n")
            m=real_module("pyarrow",other)
            with self.assertRaises(ValueError):D.module_ref(m,value)
    def test06_lib_python_stub_and_forged_spec_origin_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            value=fixture(Path(tmp)/"site");m=real_module("pyarrow.lib",Path(value["expected_origins"]["pyarrow"]))
            with self.assertRaisesRegex(ValueError,"real PyArrow native extension"):D.module_ref(m,value)
            m=real_module("pyarrow",Path(value["expected_origins"]["pyarrow"]));m.__spec__.origin="/not-actual"
            with self.assertRaises(ValueError):D.module_ref(m,value)
    def test07_actual_interpreter_ABI_fails_before_any_pyarrow_import(self):
        with tempfile.TemporaryDirectory()as tmp:
            value=fixture(Path(tmp)/"site")
            with patch.object(D.sys,"implementation",types.SimpleNamespace(cache_tag="cpython-39")):
                with patch.object(D.importlib,"import_module",side_effect=AssertionError("must not import")):
                    with self.assertRaisesRegex(ValueError,"actual interpreter ABI"):D.install(value)
    def test08_manifest_tree_lock_actual_canonical_bytes_and_reduced_lock_refused(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);value=fixture(root/"site")
            tree=dict(schema="skvq.isolated.pyarrow-files/v1",root=value["root"],files=[
              dict(relative=Path(r["path"]).relative_to(value["root"]).as_posix(),bytes=r["bytes"],sha256=r["sha256"])for r in value["files"]])
            inventory=root/"ACTUAL_TREE.json";inventory.write_bytes(json.dumps(tree,sort_keys=True).encode()+b"\n")
            lock=root/"LOCK.json";lock.write_bytes(json.dumps(value,sort_keys=True).encode()+b"\n")
            manifest=root/"SOURCE_MANIFEST.json"
            m=dict(cpu_input_dependency_root=value["root"],cpu_input_dependency_lock_ref=C.reference(lock),
              cpu_input_dependency_inventory_ref=C.reference(inventory))
            manifest.write_bytes(json.dumps(m,sort_keys=True).encode()+b"\n");sr=C.reference(manifest)
            with patch.object(C,"source",return_value=sr):
                self.assertEqual(D.lock(),(value,m["cpu_input_dependency_lock_ref"],sr))
                changed=copy.deepcopy(value);changed["files"]=[r for r in value["files"]if Path(r["path"]).name!="empty"]
                lock.write_bytes(json.dumps(changed,sort_keys=True).encode()+b"\n");m["cpu_input_dependency_lock_ref"]=C.reference(lock)
                manifest.write_bytes(json.dumps(m,sort_keys=True).encode()+b"\n")
                with self.assertRaisesRegex(ValueError,"complete MAIN actual extracted tree"):D.lock()
    def test09_real_fresh_isolated_default_OFF_and_help_need_no_package_or_input(self):
        for script in("input_dependency.py","input_entry.py"):
            p=subprocess.run([sys.executable,"-I","-B",str(HERE/script)],capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,0,p.stderr);v=json.loads(p.stdout)
            self.assertIs(v["default_enabled"],False);self.assertIs(v["NPU_access"],False);self.assertIs(v["model_ready"],False)
            p=subprocess.run([sys.executable,"-I","-B",str(HERE/script),"--help"],capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,0,p.stderr)
    def test10_unmodified_execute_CPU_only_never_calls_payload_or_NPU_and_keeps_cleanup(self):
        import os,time
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);events=[];sr=dict(path="/fixture/SOURCE_MANIFEST.json",bytes=1,sha256="a"*64)
            def pub(p,v):
                p.write_bytes(json.dumps(v,sort_keys=True).encode()+b"\n");return C.reference(p)
            class LocalControl:
                def __init__(self,out,limit=7200):
                    self.limit=limit;self.out=out;self.start=time.monotonic();self.primary=None;self.secondary=[];self.owned=[];self.spend=[];self.cleanup_spent=0.;self.protected=None;self.observations=[]
                def create(self,phase,npu,mem,*args):
                    events.append((phase,npu,mem));self.owned.append(dict(phase=phase));self.spend.append(phase)
                def exec(self,label,args,**kwargs):
                    cpu=self.out/"cpu"
                    for name,value in(("CPU_COMPLETE.json",dict(status="ACTUAL23_AND_REAL_TRAIN_INPUTS_CONSUMED")),
                      ("ACTUAL_ENGINE_CONFIG.json",{}),("INPUT_DEPENDENCY.json",{}),("INPUTS_CONSUMED.json",{})):
                        pub(cpu/name,value)
                    d=cpu/"run-skvq-train-inputs-001-main";d.mkdir();pub(d/"INPUTS.json",{})
                def cleanup(self):events.append("cleanup")
            helper=types.SimpleNamespace(cpu_view=lambda pid:dict(effective_cpus=[0]))
            namespace=dict(os=os,time=time,TOTAL=7200,CLEANUP=180,DEADLINE=C.CUT,GIB=2**30,HERE=HERE,
              require=C.require,C=types.SimpleNamespace(configure=lambda expected:sr,CUT=C.CUT,clock=lambda:{}),
              closure=lambda:sr,R=types.SimpleNamespace(helper=lambda:helper,HOST=512*2**20),
              resource=types.SimpleNamespace(RLIMIT_AS=1,RLIM_INFINITY=-1,getrlimit=lambda x:(-1,-1),setrlimit=lambda *x:None),
              newroot=lambda output:root,Control=LocalControl,payload=lambda *a:(_ for _ in()).throw(AssertionError("NPU/payload forbidden")),
              reference=C.reference,publish_json=pub,json=json,sys=sys,traceback=__import__("traceback"))
            exec(compile(ast.Module(body=[fn("execute","MAIN_HOST.py")],type_ignores=[]),"actual-execute","exec"),namespace)
            a=types.SimpleNamespace(cpu_inputs_only=True,output=root,source_manifest_sha256=sr["sha256"])
            with patch.dict(os.environ,{"MAIN_SKVQ_HOST_ENABLE":"1"}),patch.object(os,"sched_setaffinity",create=True),contextlib.redirect_stdout(io.StringIO()):
                namespace["execute"](a)
            result=json.loads((root/"HOST_RESULT.json").read_bytes())
            self.assertEqual(result["status"],"REAL_CPU_INPUTS_CONSUMED_NO_NPU")
            self.assertIs(result["cpu_input_only"],True);self.assertIs(result["native_ready"],False)
            self.assertEqual([e for e in events if type(e)is tuple],[("preflight",False,8*2**30)])
            self.assertGreaterEqual(events.count("cleanup"),2)
    def test11_full_capture_consumer_refuses_successful_CPU_only_terminal(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);m=root/"SOURCE_MANIFEST.json";m.write_bytes(json.dumps(dict(schema="skvq.current72h.preprojection.sources/v1",files=[],dependencies=[])).encode())
            sr=C.reference(m)
            v=dict(schema="SKVQ_HOST_CAPTURE_RESULT_V1",max_total_seconds=7200,cleanup_included_seconds=180,
              actual_cleanup_spent_seconds=1,elapsed_seconds=2,source_lock=sr,status="REAL_CPU_INPUTS_CONSUMED_NO_NPU",
              current_clock=dict(protocol_ref=C.CLOCK,portfolio_cutoff_epoch=C.CUT),portfolio_deadline_utc="2026-10-12T07:00:25Z",primary=None,secondary=[])
            (root/"HOST_RESULT.json").write_bytes(json.dumps(v).encode())
            ns=dict(Path=Path,reference=C.reference,json=json,require=C.require,C=types.SimpleNamespace(source=lambda:sr,CLOCK=C.CLOCK,CUT=C.CUT,checked=C.checked),
              read=lambda ref:json.loads(Path(ref["path"]).read_bytes()))
            exec(compile(ast.Module(body=[fn("consume","consume_host.py")],type_ignores=[]),"actual-whole-consumer","exec"),ns)
            with self.assertRaisesRegex(ValueError,"actual host completed"):ns["consume"](root)
    def test12_real_production_parent_fresh_child_and_consumer_bind_the_same_dependency(self):
        body=source("inside_cpu.py")
        self.assertLess(body.index('depchild=subprocess.run'),body.index('for root,name,want'))
        self.assertLess(body.index('INPUT_DEPENDENCY_REF.json'),body.index('str(HERE/"input_entry.py")'))
        self.assertEqual(body.count("C.configure("),1)
        entry=source("input_entry.py")
        self.assertLess(entry.index("D.consume("),entry.index("D.install("));self.assertLess(entry.index("D.install("),entry.index("runpy.run_path("))
        self.assertIn('dependency_source==source',source("consume_host.py"))
        self.assertIn('str(C.ROOT/"input_entry.py")',source("consume_host.py"))
        self.assertIn('D.mounts().items()',source("MAIN_HOST.py"))
        self.assertIn('module_refs(dependency)',source("input_dependency.py"))
        for core in("fill_pool","select_windows","record_text","records"):
            self.assertNotIn("def "+core+"(",entry)
def main():
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Dependency));return 0 if r.wasSuccessful()else 1
if __name__=="__main__":sys.exit(main())
