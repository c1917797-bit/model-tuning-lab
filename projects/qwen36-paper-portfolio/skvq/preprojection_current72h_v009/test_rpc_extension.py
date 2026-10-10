"""Twelve source-bound stdlib regressions. Surrogates are NOT native worker PASS.
Same-image inside_cpu additionally executes the real installed encoder/decoder.
"""
import argparse,ast,copy,hashlib,inspect,json,os,sys,tempfile,types,unittest
from functools import partial
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import rpc_extension as E
import current_contract as C
REVIEW=None
def raw(name):
    manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
    pin=next(x for x in manifest["rpc_runtime_sources"]if Path(x["snapshot"]["path"]).name==name)
    path=(REVIEW/name)if REVIEW else Path(pin["snapshot"]["path"])
    value=path.read_bytes()
    C.require(len(value)==pin["snapshot"]["bytes"] and hashlib.sha256(value).hexdigest()==pin["snapshot"]["sha256"],
        "whole original RPC source bytes")
    return value.decode()
def node(text,name):
    return next(x for x in ast.walk(ast.parse(text))if isinstance(x,(ast.FunctionDef,ast.ClassDef))and x.name==name)
def source(name):return (HERE/name).read_text()
def original_run_method():
    namespace={"partial":partial,"cloudpickle":types.SimpleNamespace(loads=lambda x:(_ for _ in()).throw(AssertionError("no pickle"))),
        "Any":object,"Callable":object}
    value=node(raw("v1__serial_utils.py"),"run_method")
    text="from __future__ import annotations\n"+ast.unparse(value)
    exec(compile(text,"actual-original-run_method","exec"),namespace)
    return namespace["run_method"]
def native_extension_block(worker,extension):
    value=node(raw("v1__worker__worker_base.py"),"init_worker")
    block=next(x for x in value.body if isinstance(x,ast.If)and
        ast.unparse(x.test)=="parallel_config.worker_extension_cls")
    namespace={"parallel_config":types.SimpleNamespace(worker_extension_cls=E.QUALNAME),
        "resolve_obj_by_qualname":lambda name:extension,"worker_class":worker,
        "logger":types.SimpleNamespace(info=lambda *a:None)}
    exec(compile(ast.Module(body=[block],type_ignores=[]),"original-extension-injection","exec"),namespace)
    return namespace
def fixture(tmp):
    root=Path(tmp).absolute();rows=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())["rpc_runtime_sources"]
    if REVIEW:
        rows=[dict(r,snapshot=C.reference(REVIEW/Path(r["snapshot"]["path"]).name))for r in rows]
    path=root/"source.json";path.write_text(json.dumps({"rpc_runtime_sources":rows}))
    src=C.reference(path)
    value={"schema":"skvq.capture.safe-named-rpc-preflight/v1","source_ref":src,"extension_ref":C.reference(E.__file__),
        "qualified_name":E.QUALNAME,"runtime_origins":{x["module"]:{"path":x["runtime_path"],
            "bytes":x["snapshot"]["bytes"],"sha256":x["snapshot"]["sha256"]}for x in rows},
        "methods":[{"method":n,"timeout":t,"args":list(a),"kwargs":k,
            "request_and_reply_roundtrip":True,"wrapper_method_resolution":True}for n,t,a,k in E.call_cases(src)],
        "actual_function_serialization_rejected":True,"safe_serialization":True,"NPU_initialized":False,
        "surrogate_receiver_only":True,"actual_worker_installed":False,"model_ready":False,"native_ready":False}
    return src,value
class Tests(unittest.TestCase):
    def test01_actual_safe_encoder_body_retains_function_refusal(self):
        fn=node(raw("v1__serial_utils.py"),"enc_hook")
        empty=type("NotAFunction",(),{})
        namespace={"torch":types.SimpleNamespace(Tensor=empty),"np":types.SimpleNamespace(ndarray=empty),
            "MultiModalKwargsItem":empty,"MultiModalKwargsItems":empty,"UtilityResult":empty,
            "envs":types.SimpleNamespace(VLLM_ALLOW_INSECURE_SERIALIZATION=False),"Any":object}
        exec(compile("from __future__ import annotations\n"+ast.unparse(fn),"original-enc_hook","exec"),namespace)
        with self.assertRaisesRegex(TypeError,"not serializable"):namespace["enc_hook"](object(),lambda:None)
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test02_actual_string_run_method_and_wrapper_getattr_all_four(self):
        original=node(raw("v1__worker__worker_base.py"),"__getattr__")
        namespace={};exec(compile(ast.Module(body=[original],type_ignores=[]),"original-wrapper-getattr","exec"),namespace)
        wrapper_cls=type("Wrapper",(),{"__getattr__":namespace["__getattr__"]})
        methods={}
        for name in E.METHODS:
            def make(n):
                def f(self,*args,**kwargs):return {"method":n,"args":list(args),"kwargs":kwargs}
                return f
            methods[name]=make(name)
        wrapper=wrapper_cls();wrapper.worker=type("Carrier",(),methods)()
        invoke=original_run_method()
        for n,t,args,kw in E.call_cases({"path":"/actual/SOURCE.json","sha256":"a"*64}):
            self.assertEqual(invoke(wrapper,n,args,kw),{"method":n,"args":list(args),"kwargs":kw})
        with self.assertRaises(NotImplementedError):invoke(wrapper,"foreign_rpc",(),{})
    def test03_actual_native_factory_injects_same_original_class(self):
        class NativeBase:pass
        class NPUWorker(NativeBase):pass
        before=(NPUWorker.__name__,NPUWorker.__module__,inspect.getsourcefile(NPUWorker))
        native_extension_block(NPUWorker,E.SKVQCaptureExtension)
        self.assertEqual(before,(NPUWorker.__name__,NPUWorker.__module__,inspect.getsourcefile(NPUWorker)))
        self.assertEqual(NPUWorker.__bases__,(NativeBase,E.SKVQCaptureExtension))
        for name in E.METHODS:self.assertIs(getattr(NPUWorker,name),getattr(E.SKVQCaptureExtension,name))
        native_extension_block(NPUWorker,E.SKVQCaptureExtension)
        self.assertEqual(NPUWorker.__bases__,(NativeBase,E.SKVQCaptureExtension))
    def test04_original_factory_conflict_is_not_bypassed(self):
        class NativeBase:pass
        class NPUWorker(NativeBase):
            def skvq_capture_arm(self):pass
        with self.assertRaises(AssertionError):native_extension_block(NPUWorker,E.SKVQCaptureExtension)
        self.assertEqual(NPUWorker.__bases__,(NativeBase,))
    def test05_real_extension_delegates_all_four_and_restore_no_admission(self):
        calls=[]
        projection=types.SimpleNamespace(install_rpc=lambda *a:calls.append(("install",a))or {"rank":0})
        runtime=types.SimpleNamespace(arm_rpc=lambda *a:calls.append(("arm",a))or {"sample_id":a[-1]},
            finish_rpc=lambda *a:calls.append(("finish",a))or {"finished":True},
            restore_rpc=lambda *a:calls.append(("restore",a))or {"no_session":True,"secondary":[]})
        worker=E.SKVQCaptureExtension()
        with patch.object(E,"installed_worker",return_value={"actual-software-only":True})as checked,patch.dict(sys.modules,
            {"projection_tap_current":projection,"runtime_capture_current":runtime}):
            result=worker.skvq_capture_install("actual-input","actual-out","a"*64)
            self.assertEqual(result["named_rpc_extension"],{"actual-software-only":True})
            worker.skvq_capture_arm(7);worker.skvq_capture_finish();worker.skvq_capture_restore()
            self.assertEqual(checked.call_count,3)
        self.assertEqual(calls,[("install",(worker,"actual-input","actual-out","a"*64)),
            ("arm",(worker,7)),("finish",(worker,)),("restore",(worker,))])
        with patch.object(E,"installed_worker",side_effect=ValueError("failed source")),patch.dict(sys.modules,{"runtime_capture_current":runtime}):
            self.assertTrue(worker.skvq_capture_restore()["no_session"])
    def test06_actual_capture_uses_four_string_method_names_and_native_kwargs(self):
        run=node(source("capture_current.py"),"run")
        calls=[n for n in ast.walk(run)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=="collective_rpc"]
        self.assertEqual(sorted(ast.unparse(n.args[0])for n in calls),sorted("rpc.METHODS[%d]"%i for i in range(4)))
        from model_kwargs import kwargs
        self.assertEqual(kwargs()["worker_extension_cls"],E.QUALNAME)
        self.assertIn('VLLM_ALLOW_INSECURE_SERIALIZATION="0"',source("MAIN_HOST.py"))
        self.assertNotIn("cloudpickle",source("capture_current.py"))
    def test07_whole_roundtrip_preflight_and_missing_method_refused(self):
        with tempfile.TemporaryDirectory()as tmp:
            src,value=fixture(tmp)
            self.assertEqual(E.consume_preflight(json.loads(json.dumps(value,sort_keys=True)),src),value)
            for changed in ("methods","safe_serialization","surrogate_receiver_only","NPU_initialized","actual_worker_installed"):
                bad=copy.deepcopy(value)
                if changed=="methods":bad[changed]=bad[changed][:-1]
                else:bad[changed]=not bad[changed]
                with self.assertRaises(ValueError):E.consume_preflight(bad,src)
    def test08_preflight_actual_origin_sha_or_qualified_name_tamper_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            src,value=fixture(tmp)
            for field in ("sha256","path"):
                bad=copy.deepcopy(value);name=next(iter(bad["runtime_origins"]))
                bad["runtime_origins"][name][field]="foreign"
                with self.assertRaises(ValueError):E.consume_preflight(bad,src)
            bad=copy.deepcopy(value);bad["qualified_name"]="foreign.Extension"
            with self.assertRaises(ValueError):E.consume_preflight(bad,src)
    def test09_safe_default_no_insecure_env_or_hardware_import(self):
        with patch.dict(os.environ,{},clear=True):E.secure()
        for bad in ("1","true",""):
            with patch.dict(os.environ,{"VLLM_ALLOW_INSECURE_SERIALIZATION":bad},clear=True):
                with self.assertRaises(ValueError):E.secure()
        self.assertEqual(set(E.SKVQCaptureExtension.__dict__)-{"__module__","__dict__","__weakref__","__doc__"},set(E.METHODS))
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test10_every_real_CPU_N1_install_and_consumer_edge_is_present(self):
        cpu=source("inside_cpu.py");engine=source("engine_config.py");whole=source("consume_host.py");stage=source("consume_stage.py")
        self.assertLess(cpu.index("engine_config.construct()"),cpu.index("rpc.preflight(source)"))
        self.assertIn('actual_named_rpc_preflight_ref=rpc_ref',cpu)
        self.assertIn('rpc_extension.before_weights(configuration,source)',engine)
        self.assertIn('rpc.consume_preflight(read(complete["actual_named_rpc_preflight_ref"]),source)',whole)
        self.assertIn('rpc.consume_install(result,source)',stage)
        self.assertIn('original exact NPUWorker receiver source retained',source("rpc_extension.py"))
        self.assertNotIn("worker_extension_cls",source("runtime_capture_current.py"))
    def test11_real_encoder_precheck_uses_both_original_request_and_reply(self):
        p=node(source("rpc_extension.py"),"preflight")
        text=ast.unparse(p)
        for expected in ("serial.MsgpackEncoder()","serial.MsgpackDecoder()","serial.run_method(wrapper, name, actual_args, actual_kw)",
            "decoder.decode(encoder.encode(message))","decoder.decode(encoder.encode(result))"):
            self.assertIn(expected,text)
        self.assertIn("surrogate_receiver_only",text)
        sync=node(raw("v1__engine__core_client.py"),"SyncMPClient")
        original=next(n for n in sync.body if isinstance(n,ast.FunctionDef)and n.name=="collective_rpc")
        self.assertIn("self.call_utility('collective_rpc', method, timeout, args, kwargs)",ast.unparse(original))
        self.assertIn('worker_class.__bases__ = worker_class.__bases__ + (worker_extension_cls,)',ast.unparse(node(raw("v1__worker__worker_base.py"),"init_worker")))
    def test12_full_compile_and_original_session_guard_bytes_unchanged(self):
        for path in HERE.glob("*.py"):compile(path.read_bytes(),str(path),"exec")
        prior=HERE.parent/"skvq-preprojection-current72h-20261010-008/runtime_capture_current.py"
        if prior.is_file():self.assertEqual((HERE/"runtime_capture_current.py").read_bytes(),prior.read_bytes())
        original=node(source("runtime_capture_current.py"),"actual_worker")
        self.assertIn('c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3',ast.unparse(original))
        self.assertNotIn("issubclass",ast.unparse(original))
def main():
    global REVIEW
    parser=argparse.ArgumentParser();parser.add_argument("--rpc-review-root",type=Path)
    args=parser.parse_args();REVIEW=args.rpc_review_root
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
