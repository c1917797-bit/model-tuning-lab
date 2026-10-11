"""Source/CLI/registry/factory/consumer regressions, never numerical/model authority.
Local mode explicitly uses source-qualified AST and transport fixtures, no native
module imports. Installed software_check first verifies the real full closure.
"""
import argparse,ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bridge_contract as B
import model_options as O
import model_extension as E
import model_factory as F
import actual_config as A
CTX={}
def raw(ref):
    p=Path(CTX["mirrors"].get(ref["path"],ref["path"]));data=p.read_bytes()
    B.need(len(data)==ref["bytes"]and hashlib.sha256(data).hexdigest()==ref["sha256"],"whole actual test source mirror")
    return data
def module(name,path,drop_resource=False):
    tree=ast.parse(Path(path).read_bytes(),str(path))
    if drop_resource:
        for node in tree.body:
            if isinstance(node,ast.Import):node.names=[n for n in node.names if n.name!="resource"]
        tree.body=[n for n in tree.body if not isinstance(n,ast.Import)or n.names]
    value=types.ModuleType(name);value.__file__=str(path);sys.modules[name]=value
    exec(compile(tree,str(path),"exec"),value.__dict__);return value
def setup(local=False,mirrors=None):
    CTX.update(local=local,mirrors=mirrors or {})
    CTX["manifest"]=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
    CTX["reader"]=json.loads(raw(B.READER))
    CTX["capture_ref"]=CTX["reader"]["capture_source_ref"]
    CTX["capture"]=json.loads(raw(CTX["capture_ref"]))
    H=module("model_host",HERE/"model_host.py",local and os.name=="nt")
    W=module("model_whole",HERE/"model_whole.py")
    CTX.update(H=H,W=W)
def donor(name):
    if name in CTX["reader"]["host_bindings"]:return CTX["reader"]["host_bindings"][name]
    rows=CTX["reader"]["files"]+CTX["reader"]["dependencies"]
    matches=[r for r in rows if r["path"].endswith("/"+name)]
    B.need(len(matches)==1,"one exact donor in reader closure");return matches[0]
def registry_C(body=None):
    value=body or CTX["capture"];seen=[]
    class Contract:
        def writer_modules(self):return types.SimpleNamespace(CAPTURE=CTX["capture_ref"]),None
        def obj(self,r):return value
        def load(self,name,r):raw(r);seen.append((name,r));return types.SimpleNamespace(name=name)
    return Contract(),seen
class BridgeTests(unittest.TestCase):
    def test01_all_own_compile_and_exact_metadata_closure(self):
        m=CTX["manifest"];rows=m["files"]+m["dependencies"]
        self.assertEqual(len(rows),m["source_count"]);self.assertEqual(len({r["path"]for r in rows}),len(rows))
        for r in m["files"]:
            p=HERE/Path(r["path"]).name;data=p.read_bytes()
            self.assertEqual((len(data),hashlib.sha256(data).hexdigest()),(r["bytes"],r["sha256"]))
            if p.suffix==".py":compile(data,str(p),"exec");ast.parse(data)
        for key in("runtime_configuration_sources","multiprocessing_runtime_sources","rpc_runtime_sources"):
            self.assertTrue(all(p["snapshot"]in rows for p in m[key]))
        self.assertIn(B.READER,rows);self.assertIn(B.ORIGINAL_PROMPT,rows)
        self.assertEqual(m["portfolio_cutoff_epoch"],1791788425)
    def test02_6g_common_options_fullcapacity_and_no_false_permissions(self):
        k=O.kwargs()
        self.assertEqual(k["kv_cache_memory_bytes"],6*2**30)
        self.assertEqual((k["max_model_len"],k["max_num_batched_tokens"],k["max_num_seqs"]),(33792,33792,1))
        self.assertIs(k["enable_chunked_prefill"],True);self.assertIs(k["enable_prefix_caching"],False)
        self.assertIs(k["async_scheduling"],False);self.assertEqual(k["compilation_config"],{"mode":0})
        self.assertEqual(k["worker_extension_cls"],E.QUALNAME)
        self.assertTrue(all(v is False for v in B.false_scopes().values()))
    def test03_exact_registry_own_dependency_real_manifest_positive(self):
        c,seen=registry_C()
        self.assertFalse(any(r["path"].endswith("/raw_sink.py")for r in CTX["capture"]["files"]))
        self.assertEqual(sum(r["path"].endswith("/raw_sink.py")for r in CTX["capture"]["dependencies"]),1)
        with patch.object(B,"bootstrap",return_value=c):value=F.capture_registry()
        self.assertEqual(value.name,"runtime_capture_current")
        self.assertEqual([n for n,r in seen],["io_contract","current_contract","tp_provider_current","post_rope_current",
          "raw_sink","text_input_current","runtime_capture_current"])
        self.assertEqual(seen[-1][1]["path"],CTX["capture"]["root"]+"/runtime_capture_current.py")
    def test04_registry_missing_dependency_fails_not_union(self):
        body=copy.deepcopy(CTX["capture"]);body["dependencies"]=[r for r in body["dependencies"]if not r["path"].endswith("/raw_sink.py")]
        c,_=registry_C(body)
        with patch.object(B,"bootstrap",return_value=c),self.assertRaisesRegex(ValueError,"raw_sink"):
            F.capture_registry()
    def test05_registry_wrong_sha_refused(self):
        body=copy.deepcopy(CTX["capture"])
        r=next(r for r in body["dependencies"]if r["path"].endswith("/raw_sink.py"));r["sha256"]="0"*64
        c,_=registry_C(body)
        with patch.object(B,"bootstrap",return_value=c),self.assertRaisesRegex(ValueError,"whole actual"):
            F.capture_registry()
    def test06_actual_fresh_factory_helper_and_one_policy_delta(self):
        row=donor("model_runtime.py");tree=ast.parse(raw(row))
        def ast_module(c,name,r):
            if name=="model_runtime":
                v=types.ModuleType(name);v.__file__=r["path"]
                # Actual donor needs only the original contract on module load.
                v.__dict__.update(C=types.SimpleNamespace());return v
        old=types.ModuleType("model_runtime");old.__file__=row["path"]
        class Contract:
            def obj(self,r):return CTX["reader"]
            def ref(self,p):return row if str(p)==row["path"]else dict(path=str(p),bytes=1,sha256="f"*64)
            def read(self,r):return raw(r)
        c=Contract();old_contract=types.ModuleType("contract")
        with patch.dict(sys.modules,{"model_runtime":old,"contract":old_contract}):
            cls,delta=F.factory_type(c)
            self.assertIs(cls.__init__.__globals__["capture_registry"],F.capture_registry)
            self.assertNotEqual(delta["original_ast_sha256"],delta["adapted_ast_sha256"])
            self.assertIs(delta["math_changed"],False)
            self.assertNotIn("capture_registry",old.__dict__)
            before=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="policy")
            after=ast.parse(raw(row));policy=next(n for n in after.body if isinstance(n,ast.FunctionDef)and n.name=="policy")
            self.assertEqual(ast.dump(before,include_attributes=False),ast.dump(policy,include_attributes=False))
    def test07_actual_all_stage_argv_parser_contract_and_absent_child(self):
        H=CTX["H"];source=dict(path="actual-mf",bytes=1,sha256="a"*64);root=B.ROOT.parent/"run-skvq-model-reader-002-software-only"
        for stage,file in(("cpu","model_cpu.py"),("n1","model_n1.py"),("model","model_launch.py"),("independent","model_consume.py")):
            argv=H.args(stage,source,root);self.assertEqual(Path(argv[0]).name,file)
            tree=ast.parse((HERE/file).read_bytes())if stage!="independent"else ast.parse(raw(donor(file)))
            names={n.args[0].value for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and
              n.func.attr=="add_argument"and n.args and isinstance(n.args[0],ast.Constant)}
            for arg in argv[1:]:
                if arg.startswith("--"):self.assertIn(arg,names)
            self.assertEqual(argv[argv.index("--source-manifest-sha256")+1],B.READER["sha256"]if stage=="independent"else source["sha256"])
        self.assertEqual(H.args("model",source,root)[-1],str(root/"candidate/model"))
        self.assertNotEqual(H.args("model",source,root)[-1],str(root/"candidate"))
        with self.assertRaises(ValueError):H.args("legacy",source,root)
    def test08_actual_control_only_disk_delta_no_cpu_npu_idle(self):
        H=CTX["H"];row=donor("MAIN_HOST.py")
        tree=ast.parse(raw(row));control=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Control")
        create=next(n for n in control.body if isinstance(n,ast.FunctionDef)and n.name=="create")
        cleanup=next(n for n in control.body if isinstance(n,ast.FunctionDef)and n.name=="cleanup")
        self.assertIn("if npu:",ast.unparse(create));self.assertIn("if self.current['npu']:",ast.unparse(cleanup))
        class C:
            def host_bindings(self):return CTX["reader"]["host_bindings"]
            def load(self,*args):return types.SimpleNamespace(actual_hbm=lambda text,card:None)
            def read(self,r):return raw(r)
            def ref(self,p):return {}
            def publish(self,*a):raise AssertionError("tests must not write production output")
        with patch.object(H,"mount_preflight",return_value=None):cls=H.control_class(C(),{}, {"exact":("exact",False)},5400)
        self.assertEqual(cls.literal_delta,["disk320->24GiB"])
        ctl=cls(B.ROOT.parent/"run-skvq-model-reader-002-software-only")
        self.assertEqual(ctl.devices(False),{});self.assertEqual(set(ctl.devices(True))&{"/dev/davinci%d"%i for i in range(8)},
          {"/dev/davinci4","/dev/davinci5","/dev/davinci6","/dev/davinci7"})
        self.assertEqual(ctl.env(False)["TMPDIR"],"/tmp")
        self.assertEqual(ctl.env(True)["VLLM_ALLOW_INSECURE_SERIALIZATION"],"0")
    def test09_actual_native_finish_uses_original_before_zero_token_return(self):
        gpu=ast.parse(raw(next(r for r in CTX["reader"]["dependencies"]if r["sha256"]==
          "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666")))
        cls=next(n for n in gpu.body if isinstance(n,ast.ClassDef)and n.name=="GPUModelRunner")
        update=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="_update_states")
        first=ast.unparse(update.body[1]);self.assertIn("scheduler_output.finished_req_ids",first);self.assertIn("self.requests.pop",first)
        native=ast.parse(raw(next(r for r in CTX["reader"]["dependencies"]if r["sha256"]==
          "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968")))
        cls=next(n for n in native.body if isinstance(n,ast.ClassDef)and n.name=="NPUModelRunner")
        native_update=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="_update_states")
        self.assertIn("return super()._update_states(scheduler_output)",ast.unparse(native_update))
        execute=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="execute_model")
        code=ast.unparse(execute);self.assertLess(code.index("self._update_states("),code.index("if not num_scheduled_tokens:"))
        finish=ast.parse(raw(donor("native_finish.py")));code=ast.unparse(finish)
        self.assertIn("result = owner.original(scheduler_output)",code);self.assertIn("return result",code)
        launch=ast.parse((HERE/"model_launch.py").read_bytes());code=ast.unparse(launch)
        self.assertNotIn("dummy",code);self.assertIn("native_finished_ref",code)
        whole=ast.unparse(ast.parse((HERE/"model_whole.py").read_bytes()))
        self.assertIn(".consume_identity(identity, rank)",whole)
        self.assertIn("factory_type(C)",whole);self.assertIn("installed['factory_delta_ref']",whole)
    def test10_complete_terminal_rejects_failed_original_and_partial_rows(self):
        W=CTX["W"];row=donor("reader_whole.py");tree=ast.parse(raw(row))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="original")
        ns={"C":types.SimpleNamespace(need=B.need)};exec(compile(ast.Module(body=[fn],type_ignores=[]),row["path"],"exec"),ns)
        with self.assertRaises((ValueError,KeyError)):
            ns["original"](dict(schema="agentweb.operation/v1",terminal=True,status="failed",succeeded=False,
              operation=dict(result=dict(record={})),error="real exit1"),[])
        value=dict(schema="skvq.compiled-reader.model-independent/v1",status="ALL4_ALL16_TWO_DECODE_NUMERIC_SMOKE_CONSUMED",
          source_ref=B.READER,cohort_ref={},actual_frames=128,actual_output_elements=196608,threshold_relative_rms=.005,
          actual_prompt_tokens=32768,actual_native_decode_steps=2,checked=[],**B.false_scopes())
        with self.assertRaisesRegex(ValueError,"missing"):
            W.math_rows(value,types.SimpleNamespace(),{},{})

    def test11_actual_n1_qualify_reads_same_six_refs_and_full_metadata_access_closure(self):
        m=CTX["manifest"];reader=CTX["reader"]
        refs=B.runtime_metadata(m,reader);self.assertEqual(m["native_format_patch_chain"],reader["native_format_patch_chain"])
        self.assertTrue(all(r in m["files"]+m["dependencies"]for r in refs))
        bad=copy.deepcopy(m);del bad["native_format_patch_chain"]
        with self.assertRaises(KeyError):B.runtime_metadata(bad,reader)
        bad=copy.deepcopy(m);bad["native_format_patch_chain"]["format"]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"six-source"):B.runtime_metadata(bad,reader)
        bad=copy.deepcopy(m);drop=bad["native_format_patch_chain"]["format"]
        bad["dependencies"]=[r for r in bad["dependencies"]if r!=drop]
        with self.assertRaisesRegex(ValueError,"metadata Ref"):B.runtime_metadata(bad,reader)
        n1tree=ast.parse(raw(reader["host_bindings"]["n1_format.py"]))
        qualify=next(n for n in n1tree.body if isinstance(n,ast.FunctionDef)and n.name=="qualify")
        policy_ref=next(r for r in reader["dependencies"]if r["sha256"]==
          "f3003c9c5eb67e7fd3cb10b9cefe0322431db21eae163ab0b2a13a02ab077b7a")
        policy=types.ModuleType("_actual_source_only_format_policy");exec(compile(raw(policy_ref),policy_ref["path"],"exec"),policy.__dict__)
        seen=[]
        class OriginalPolicyConsumer:
            def bind_getter(self,npu,binding,adapter,packet):
                policy.validate_chain(binding,adapter.bound)
                return None,None,{"source_metadata_only_not_runtime_getter":True}
        def bound(r):
            self.assertIn(r,refs);seen.append(r)
            # Windows regression checks actual archived manifest's exact six Refs.
            # Installed full-source gate has already read all six original bodies.
            if not CTX["local"]:raw(r)
            return r
        def dummy_getter():raise AssertionError("source metadata test never calls a device getter")
        ns={"json":json,"Path":Path,"inspect":__import__("inspect"),"SimpleNamespace":types.SimpleNamespace,
          "C":types.SimpleNamespace(checked=bound,reference=lambda p:None),"policy":lambda:OriginalPolicyConsumer(),"POLICY":policy_ref}
        exec(compile(ast.Module(body=[qualify],type_ignores=[]),reader["host_bindings"]["n1_format.py"]["path"],"exec"),ns)
        npu=types.SimpleNamespace(get_npu_format=dummy_getter)
        torch=types.SimpleNamespace(ops=types.SimpleNamespace(npu=types.SimpleNamespace(get_npu_format=object())))
        result=ns["qualify"](torch,npu,{"path":str(HERE/"SOURCE_MANIFEST.json")})
        self.assertCountEqual(seen,list(m["native_format_patch_chain"].values()))
        self.assertEqual(result[2]["binding"]["patch_chain"],m["native_format_patch_chain"])
        self.assertTrue(result[2]["observation"]["source_metadata_only_not_runtime_getter"])

def run():
    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BridgeTests))
def main():
    p=argparse.ArgumentParser();p.add_argument("--local-mirrors-json");a=p.parse_args()
    if a.local_mirrors_json:
        setup(True,json.loads(Path(a.local_mirrors_json).read_bytes()))
    else:
        C,source,m=B.source(__import__("hashlib").sha256((HERE/"SOURCE_MANIFEST.json").read_bytes()).hexdigest())
        setup(False)
    result=run()
    if not result.wasSuccessful():raise SystemExit(1)
if __name__=="__main__":main()

