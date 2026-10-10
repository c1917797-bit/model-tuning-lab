"""Real stdlib spawn/source/receipt regressions only; no native runtime authority.
Actual copied native function bodies are compiled unchanged. Native imports stay UNRUN.
"""
import argparse,ast,copy,hashlib,importlib.util,json,multiprocessing as mp,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import current_contract as C
import spawn_startup as S
REVIEW=None
def node(raw,name):
    return next(x for x in ast.parse(raw).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))and x.name==name)
def archive(module):
    row=next(x for x in json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())["multiprocessing_runtime_sources"]if x["module"]==module)
    p=Path(row["snapshot"]["path"])
    if REVIEW:p=REVIEW/p.name
    raw=p.read_bytes()
    C.require(len(raw)==row["snapshot"]["bytes"]and hashlib.sha256(raw).hexdigest()==row["snapshot"]["sha256"],
        "entire original native source bytes; no AST substitute source")
    return raw.decode(),row
def spawned_probe(pipe):
    pipe.send({"pid":os.getpid(),"method":mp.get_start_method(allow_none=True),
       "environment":S.policy(),"Torch_imported":"torch"in sys.modules,"NPU_imported":"torch_npu"in sys.modules})
    pipe.close()
def native_factory_namespace():
    raw,_=archive("vllm.utils.system_utils")
    class Env:
        @property
        def VLLM_WORKER_MULTIPROC_METHOD(self):return os.environ.get(S.ENV,"fork")
    called=[]
    ns=dict(multiprocessing=mp,envs=Env(),
       _maybe_force_spawn=lambda:called.append("native-maybe-force"),
       _sync_visible_devices_env_vars=lambda:called.append("native-visible-sync"))
    exec(compile(ast.Module(body=[node(raw,"get_mp_context")],type_ignores=[]),"original-get_mp_context","exec"),ns)
    return ns,called
def receipt_fixture(root):
    root=Path(root).absolute()
    snap=root/"native.py";snap.write_text("native source snapshot\n")
    archive_ref=C.reference(snap)
    row={"module":"vllm.utils.system_utils","runtime_path":"/exact/image/vllm/utils/system_utils.py","snapshot":archive_ref}
    manifest=root/"SOURCE.json";manifest.write_text(json.dumps({"multiprocessing_runtime_sources":[row]}))
    source=C.reference(manifest);env={S.ENV:"spawn",**{k:"1"for k in S.THREADS}}
    parent={"schema":"skvq.capture.spawn-parent/v1","source_ref":source,"identity":{"pid":100,"pid_start_ticks":101},
       "environment":env,"native_factory":{"module":row["module"],"origin":{"path":row["runtime_path"],"bytes":archive_ref["bytes"],"sha256":archive_ref["sha256"]},
       "function":"get_mp_context","method":"spawn"},"before_actual_LLM_constructor":True,"capture_ready":False,"model_ready":False}
    pp=root/"PARENT.json";pp.write_text(json.dumps(parent));pr=C.reference(pp)
    results=[]
    for rank in range(4):
        pid={"pid":200+rank,"pid_start_ticks":300+rank}
        before={"identity":pid,"environment":env,"start_method":"spawn","source_ref":source,"helper_ref":C.reference(S.__file__)}
        value={"schema":"skvq.capture.spawn-worker-install/v1","source_ref":source,"rank":rank,"before":before,
           "after_identity":pid,"start_method":"spawn","instance_hooks":{"cache":16,"projection":16,"model":1,"sink":1,"total":34},
           "GDN_untouched_layers":48,"installed_before_sample_zero":True,"capture_ready":False,"model_ready":False}
        file=root/("RANK%d.json"%rank);file.write_text(json.dumps(value))
        results.append({"rank":rank,"installed":True,"identity":dict(pid,public_TP_rank=rank),"spawn_install_ref":C.reference(file)})
    return source,pr,results
def mutate_result(results,index,root,mutate):
    value=json.loads(Path(results[index]["spawn_install_ref"]["path"]).read_bytes());mutate(value)
    p=Path(root)/("MUTATED%d.json"%index);p.write_text(json.dumps(value))
    out=copy.deepcopy(results);out[index]["spawn_install_ref"]=C.reference(p);return out
class Tests(unittest.TestCase):
    def test01_exact_native_factory_and_official_cli_spawn_body(self):
        raw,_=archive("vllm.entrypoints.serve.utils.api_utils")
        fn=node(raw,"cli_env_setup");ns={"os":os,"logger":types.SimpleNamespace(debug=lambda *a:None)}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),"actual-cli-env-setup","exec"),ns)
        with patch.dict(os.environ,{},clear=True):
            ns["cli_env_setup"]();self.assertEqual(os.environ[S.ENV],"spawn")
            os.environ[S.ENV]="fork";ns["cli_env_setup"]();self.assertEqual(os.environ[S.ENV],"fork")
        raw,_=archive("vllm.utils.system_utils")
        forcing=ast.unparse(node(raw,"_maybe_force_spawn"))
        self.assertIn("os.environ.get('VLLM_WORKER_MULTIPROC_METHOD') == 'spawn'",forcing)
        self.assertIn("return",forcing)
        raw,_=archive("vllm.v1.executor.multiproc_executor")
        worker=node(raw,"WorkerProc")
        make=next(x for x in worker.body if isinstance(x,ast.FunctionDef)and x.name=="make_worker_process")
        self.assertIn("context = get_mp_context()",ast.unparse(make))
        self.assertIn("context.Process(",ast.unparse(make))
        self.assertIn("target=WorkerProc.worker_main",ast.unparse(make))
    def test02_policy_rejects_fork_absent_and_thread_growth(self):
        good={S.ENV:"spawn",**{k:"1"for k in S.THREADS}}
        with patch.dict(os.environ,good,clear=True):self.assertEqual(S.policy(),good)
        for key,bad in [(S.ENV,"fork"),(S.ENV,""),*[(k,"2")for k in S.THREADS]]:
            with patch.dict(os.environ,dict(good,**{key:bad}),clear=True):
                with self.assertRaises(ValueError):S.policy()
    def test03_actual_stdlib_spawn_child_preserves_explicit_environment(self):
        ns,called=native_factory_namespace()
        with patch.dict(os.environ,{S.ENV:"spawn",**{k:"1"for k in S.THREADS}},clear=False):
            context=ns["get_mp_context"]();self.assertEqual(context.get_start_method(),"spawn")
            receive,send=context.Pipe(duplex=False);process=context.Process(target=spawned_probe,args=(send,))
            process.start();send.close()
            try:
                self.assertTrue(receive.poll(20),"actual bounded stdlib child result")
                value=receive.recv();process.join(20)
                self.assertEqual(process.exitcode,0);self.assertNotEqual(value["pid"],os.getpid())
                self.assertEqual(value["method"],"spawn");self.assertEqual(value["environment"],S.policy())
                self.assertFalse(value["Torch_imported"]);self.assertFalse(value["NPU_imported"])
            finally:
                receive.close()
                if process.is_alive():process.terminate();process.join(5)
        self.assertEqual(called,["native-maybe-force","native-visible-sync"])
    def test04_native_context_checks_actual_cached_module_and_unwrapped_owner(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).absolute();p=root/"system_utils.py"
            p.write_text("import multiprocessing\ndef get_mp_context():\n    return multiprocessing.get_context('spawn')\n")
            spec=importlib.util.spec_from_file_location("vllm.utils.system_utils",p)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            row={"module":module.__name__,"runtime_path":str(p),"snapshot":C.reference(p)}
            m=root/"SOURCE.json";m.write_text(json.dumps({"multiprocessing_runtime_sources":[row]}));source=C.reference(m)
            with patch.object(S.importlib,"import_module",return_value=module):
                self.assertEqual(S.native_context(source)["method"],"spawn")
                original=module.get_mp_context
                module.get_mp_context=lambda:mp.get_context("spawn")
                with self.assertRaisesRegex(ValueError,"no wrapper or substitute"):S.native_context(source)
                module.get_mp_context=original
                module.__spec__=types.SimpleNamespace(name=module.__name__,origin=str(root/"foreign.py"))
                with self.assertRaisesRegex(ValueError,"module origin"):S.native_context(source)
    def test05_worker_guard_rejects_fork_and_bad_current_environment(self):
        with patch.dict(os.environ,{S.ENV:"spawn",**{k:"1"for k in S.THREADS}},clear=False),patch.object(S.mp,"get_start_method",return_value="fork"):
            with self.assertRaisesRegex(ValueError,"actual worker process is spawn"):S.before_worker({"source":"software"})
    def test06_complete_persisted_four_rank_receipts_and_host_does_not_open_image_source(self):
        with tempfile.TemporaryDirectory()as tmp:
            source,parent,results=receipt_fixture(tmp)
            refs=S.consume_installs(results,parent,source)
            self.assertEqual(refs,[r["spawn_install_ref"]for r in results])
            producer={"worker_install_results":results,"spawn_parent_ref":parent,"worker_spawn_install_refs":refs}
            self.assertEqual(S.consume_producer(producer,source),refs)
            producer["worker_spawn_install_refs"]=refs[:-1]
            with self.assertRaisesRegex(ValueError,"exact complete original RPC receipt list"):S.consume_producer(producer,source)
    def test07_receipts_reject_wrong_source_fork_hook_and_GDN_omission(self):
        with tempfile.TemporaryDirectory()as tmp:
            source,parent,results=receipt_fixture(tmp)
            mutations=(lambda v:v.update(source_ref={"wrong":True}),
               lambda v:v.update(start_method="fork"),
               lambda v:v["instance_hooks"].update(projection=15),
               lambda v:v.update(GDN_untouched_layers=47),
               lambda v:v.update(capture_ready=True),
               lambda v:v.update(installed_before_sample_zero=False))
            for modify in mutations:
                with self.assertRaises(ValueError):S.consume_installs(mutate_result(results,0,tmp,modify),parent,source)
    def test08_receipts_reject_duplicate_PID_parent_PID_and_missing_rank(self):
        with tempfile.TemporaryDirectory()as tmp:
            source,parent,results=receipt_fixture(tmp)
            with self.assertRaises(ValueError):S.consume_installs(results[:-1],parent,source)
            bad=copy.deepcopy(results);bad[1]["identity"]=copy.deepcopy(bad[0]["identity"]);bad[1]["identity"]["public_TP_rank"]=1
            def duplicate(v):
                v["before"]["identity"]={"pid":200,"pid_start_ticks":300};v["after_identity"]={"pid":200,"pid_start_ticks":300}
            bad=mutate_result(bad,1,tmp,duplicate)
            with self.assertRaisesRegex(ValueError,"distinct actual workers"):S.consume_installs(bad,parent,source)
            def parentpid(v):
                v["before"]["identity"]={"pid":100,"pid_start_ticks":101};v["after_identity"]={"pid":100,"pid_start_ticks":101}
            bad=mutate_result(results,0,tmp,parentpid);bad[0]["identity"].update(pid=100,pid_start_ticks=101)
            with self.assertRaisesRegex(ValueError,"actual distinct worker"):S.consume_installs(bad,parent,source)
    def test09_actual_child_hook_completion_gate_rejects_missing_bound_hook(self):
        with patch.dict(os.environ,{S.ENV:"spawn",**{k:"1"for k in S.THREADS}},clear=False),patch.object(S.mp,"get_start_method",return_value="spawn"),patch.object(S,"identity",return_value={"pid":os.getpid(),"pid_start_ticks":456}):
            source={"software":True};before=S.before_worker(source);worker=types.SimpleNamespace(rank=0)
            patches=[]
            for name in ["reshape_and_cache"]*16+["forward"]*17+["capture"]:
                obj=types.SimpleNamespace();bound=object();obj.__dict__[name]=bound;patches.append((obj,name,bound,object()))
            session=types.SimpleNamespace(w=worker,rank=lambda:{"pid":os.getpid()},patches=patches,linear=[None]*48,
              active=None,next_id=0,closed=False,poisoned=False,sink=types.SimpleNamespace(path=Path("/software-only")))
            worker._skvq_capture_session=session
            with patch.object(S,"publish",side_effect=lambda path,value:value):
                value=S.installed(worker,session,source,before);self.assertEqual(value["instance_hooks"]["total"],34)
                patches[0][0].__dict__.pop("reshape_and_cache")
                with self.assertRaisesRegex(ValueError,"all34"):S.installed(worker,session,source,before)
    def test10_real_entry_spawn_before_LLM_and_RPC_child_source_and_whole_consumer(self):
        host=(HERE/"MAIN_HOST.py").read_text()
        self.assertIn('VLLM_WORKER_MULTIPROC_METHOD="spawn"',host)
        run=ast.unparse(node((HERE/"capture_current.py").read_text(),"run"))
        self.assertLess(run.index("startup.parent("),run.index("llm = LLM("))
        self.assertIn("startup.consume_installs(install, startup_ref, C.source())",run)
        install=ast.unparse(node((HERE/"projection_tap_current.py").read_text(),"install_rpc"))
        self.assertLess(install.index("C.configure("),install.index("startup.before_worker("))
        self.assertLess(install.index("startup.before_worker("),install.index("loader_bridge.install_rpc("))
        self.assertIn("startup.installed(w, s, source, spawn_before)",install)
        cohort=ast.unparse(node((HERE/"consume_stage.py").read_text(),"cohort"))
        self.assertIn("startup.consume_producer(producer, source)",cohort)
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
def main():
    global REVIEW
    parser=argparse.ArgumentParser();parser.add_argument("--review-root",type=Path);args=parser.parse_args();REVIEW=args.review_root
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
