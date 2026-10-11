"""Real source-derived CPU-only Control and cross-stage regressions.
All container/fit fixtures here are SOFTWARE_ONLY, never runtime authority.
"""
import ast,copy,hashlib,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C
import cpu_host as H
import consume_cpu_whole as W
import calibration_inputs as I
REMOTE="/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/MAIN_HOST.py"
LOCAL=Path("C:/Users/Huawei/AppData/Local/Temp/skvq-preprojection-current72h-20261010-014/MAIN_HOST.py")
def real_donor():
    path=Path(REMOTE)
    if not path.is_file():path=LOCAL
    ref=C.reference(path)
    if ref["sha256"]!=C.CAPTURE_BINDINGS["MAIN_HOST.py"]["sha256"]or ref["bytes"]!=C.CAPTURE_BINDINGS["MAIN_HOST.py"]["bytes"]:
        raise ValueError("source-exact Control donor")
    return ref
def cls(mounts=None):
    row=real_donor();bindings=dict(C.CAPTURE_BINDINGS,**{"MAIN_HOST.py":row})
    r=types.SimpleNamespace(HOST=512*2**20,RESERVE=8*2**30,rss=lambda:dict(live_sum_bytes=1,conservative_cumulative_peak_sum_bytes=1))
    pre=types.SimpleNamespace(observe=lambda m,p,s:dict(passed=True,errors=[],mounts=m,phase=p))
    with patch.object(C,"CAPTURE_BINDINGS",bindings):
        return H.control_class(dict(sha256="a"*64),r,mounts or{},pre)
def inspected():
    e=dict(cid="b"*64,name="skvq-software-fixture",source="a"*64,cpuset="1,2,3,4",mem=8*2**30,
      phase="calibration",npu=False,devices={},env=H.environment(),mounts={"/fixture/ro":["/fixture/ro",False],"/fixture/rw":["/fixture/rw",True]},
      released=True,release_ref={})
    x=dict(Id=e["cid"],Name="/"+e["name"],Image=H.IMAGE,
      Config=dict(Image=H.IMAGE,Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],
        Labels={"model-tuning-lab.owner":H.OWNER,"model-tuning-lab.source":e["source"]},
        Env=[k+"="+v for k,v in e["env"].items()]),
      HostConfig=dict(Privileged=False,Memory=e["mem"],MemorySwap=e["mem"],NanoCpus=4*10**9,CpusetCpus=e["cpuset"],
        CgroupnsMode="host",NetworkMode="none",IpcMode="private",ShmSize=2*2**30,PidsLimit=1024,
        CapDrop=["ALL"],SecurityOpt=["no-new-privileges"],DeviceRequests=[],DeviceCgroupRules=[],Devices=[]),
      Mounts=[dict(Type="bind",Destination=d,Source=s,RW=rw)for d,(s,rw)in e["mounts"].items()],
      State=dict(Running=False,Pid=0,OOMKilled=False),ExecIDs=[])
    return e,x
def operation(argv):
    return dict(schema="agentweb.operation/v1",terminal=True,status="completed",succeeded=True,error=None,
      operation=dict(ok=True,routeDecision="peer_direct",targetPeerId="lgw_a6109c51076a4a2c9d2674ca5a8704a0",
        result=dict(state="completed",record=dict(command=argv[0],args=argv[1:],exitCode=0,error=None,timedOut=False,cancelled=False))))
class CPUHost(unittest.TestCase):
    def test01_exact_original_Control_ast_not_donor_mutation(self):
        control=cls();raw=Path(real_donor()["path"]).read_bytes();node=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef)and n.name=="Control")
        self.assertEqual(control.donor_class_ast_sha256,__import__("control_ast").control_digest(raw))
        self.assertEqual(control.__mro__[1].validate.__code__.co_filename,real_donor()["path"])
        self.assertNotIn("current_contract",sys.modules)
    def test02_actual_constructor600_cleanup90_and_NPU_hard_rejection(self):
        v=cls()(Path("/fixture/output"));self.assertEqual(v.limit,600);self.assertLessEqual(v.end-v.start,600)
        for action in(lambda:v.observe(),lambda:v.devices(True),lambda:v.env(True),
          lambda:v.create("tp4",True,64*2**30),lambda:v.exec("calibration128",[],True)):
            with self.assertRaises(ValueError):action()
        self.assertEqual(v.devices(False),{});self.assertEqual(v.env(False),H.environment())
        with self.assertRaises(ValueError):cls()(Path("/fixture/output"),1200)
    def test03_replayed_json_mount_tuples_and_exact_cpu_isolation(self):
        control=cls();e,x=inspected();e=json.loads(json.dumps(e,sort_keys=True))
        normalized=copy.deepcopy(e);normalized["mounts"]={d:(s,rw)for d,(s,rw)in e["mounts"].items()}
        self.assertEqual(control.validate(None,x,normalized),x)
        for mutate in("device","owner","source","swap","CPU","privileged","RW"):
            y=copy.deepcopy(x)
            if mutate=="device":y["HostConfig"]["Devices"]=[dict(PathOnHost="/dev/davinci4",PathInContainer="/dev/davinci0",CgroupPermissions="rwm")]
            elif mutate=="owner":y["Config"]["Labels"]["model-tuning-lab.owner"]="capture-old"
            elif mutate=="source":y["Config"]["Labels"]["model-tuning-lab.source"]="0"*64
            elif mutate=="swap":y["HostConfig"]["MemorySwap"]+=1
            elif mutate=="CPU":y["HostConfig"]["NanoCpus"]=5*10**9
            elif mutate=="privileged":y["HostConfig"]["Privileged"]=True
            else:y["Mounts"][0]["RW"]=True
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):control.validate(None,y,normalized)
    def test04_exact_owned_terminal_source_and_no_borrowed_original(self):
        argv=W.host_argv(Path("/fixture/output"),"a"*64,Path("/fixture/WHOLE_REF.json"),"bf16-exact-cpu32")
        self.assertEqual(W.original(operation(argv),argv)["exitCode"],0)
        for mode in("failed","running","timeout","cancel","source","peer"):
            v=operation(argv)
            if mode=="failed":v["succeeded"]=False;v["operation"]["result"]["record"]["exitCode"]=1;v["error"]="exit code"
            elif mode=="running":v["terminal"]=False
            elif mode=="timeout":v["operation"]["result"]["record"]["timedOut"]=True
            elif mode=="cancel":v["operation"]["result"]["record"]["cancelled"]=True
            elif mode=="source":v["operation"]["result"]["record"]["args"][-1]="other"
            else:v["operation"]["targetPeerId"]="other"
            with self.subTest(mode=mode),self.assertRaises(ValueError):W.original(v,argv)
    def test05_entry_host_and_aggregate_real_exact_argv(self):
        entry=json.loads((HERE/"ENTRY.json").read_bytes());source=entry["source"];root=Path(entry["host"]["output"])
        wf=Path(entry["prerequisite"]["actual_successful_capture_whole_ref_json"])
        posix=lambda argv:[v.replace(chr(92),chr(47))for v in argv]
        df=Path(entry["prerequisite"]["dependency_ref_json"])
        self.assertEqual(entry["host"]["argv"],posix(W.host_argv(root,source["sha256"],wf,"bf16-exact-cpu32",df)))
        self.assertEqual(entry["cpu_workload"]["output"],(root/"work").as_posix())
        self.assertEqual(entry["cpu_workload"]["argv"][3:],posix(H.guest_args(source,wf,root,"bf16-exact-cpu32",df)))
        self.assertEqual(entry["resource"]["total_seconds"],600);self.assertEqual(entry["resource"]["cleanup_included_seconds"],90)
        self.assertTrue(entry["resource"]["CPU_QUEUE_no_peer_admission"])
    def test06_default_OFF_whole_host_real_clean_process(self):
        for name in("cpu_host.py","consume_cpu_whole.py"):
            r=subprocess.run([sys.executable,"-I","-B",str(HERE/name)],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)["default_enabled"])
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test07_successful_source_boolean_without_full_capture_never_creates(self):
        a=types.SimpleNamespace(source_manifest_sha256="a"*64,whole_ref_json=None,output="/fixture/no-create",feature_mode="bf16-exact-cpu32")
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/"failed.json";p.write_text("{}");a.whole_ref_json=str(p)
            with patch.dict(os.environ,MAIN_SKVQ_CALIBRATION_CPU_ENABLE="1"),patch.object(C,"source",return_value={}),\
              patch.object(I,"inputs",side_effect=ValueError("actual whole capture missing")),patch.object(H,"newroot",side_effect=AssertionError("must not create")):
                with self.assertRaisesRegex(ValueError,"actual whole capture missing"):H.execute(a)
    def test08_outputcap_actual_walk_regular_no_peak_claim(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp);(p/"a").write_bytes(b"123");(p/"b").mkdir();(p/"b"/"c").write_bytes(b"45")
            self.assertEqual(H.output_bytes(p),5)
            with patch.object(H,"OUTCAP",4),self.assertRaises(ValueError):H.output_bytes(p)
    def test09_readonly_independent_artifact_replay_remains_full_math(self):
        import consume as R
        tree=ast.parse((HERE/"consume.py").read_bytes());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="consume")
        self.assertEqual(node.args.kwonlyargs[0].arg,"write_artifacts")
        text=ast.get_source_segment((HERE/"consume.py").read_text(),node)
        self.assertIn("checked[rank][layer][side]=validate(expected_features,row,4)",text)
        self.assertIn("saved=decode(pt",text);self.assertIn("bound(ar)==value",text)
        self.assertIn("consume_writer_artifact(ar",text)
        self.assertIn("write_artifacts=False",(HERE/"consume_cpu_whole.py").read_text())
    def test10_full_fixed_source_closure_current014_not_failed009_union(self):
        m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes());deps={r["path"]:r for r in m["dependencies"]}
        self.assertEqual(m["capture_source_ref"],C.CAPTURE)
        self.assertEqual(deps[C.CAPTURE["path"]],C.CAPTURE)
        for r in C.CAPTURE_BINDINGS.values():self.assertEqual(deps[r["path"]],r)
        self.assertFalse(any("skvq-preprojection-current72h-v1-009/"in p or "skvq-preprojection-current72h-v1-008/"in p for p in deps))
        self.assertEqual(m["resource_protocol"]["output_bytes_cap"],32*2**20)
    def test11_cpu_only_control_no_native_observe_path(self):
        original=cls().__mro__[1]
        for method in("create","exec","cleanup"):
            source=Path(real_donor()["path"]).read_text();tree=ast.parse(source)
            c=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Control")
            node=next(n for n in c.body if isinstance(n,ast.FunctionDef)and n.name==method)
            gates=[n.test for n in ast.walk(node)if isinstance(n,ast.If)and any(isinstance(x,ast.Call)and
              isinstance(x.func,ast.Attribute)and x.func.attr=="observe"for x in ast.walk(n))]
            self.assertTrue(gates)
        code=(HERE/"cpu_host.py").read_text()
        self.assertIn('phase=="calibration"and npu is False',code)
        self.assertNotIn("create_model_config(",code);self.assertNotIn("create_engine_config(",code)
    def test12_same_CPU_RW_work_directory_actual_nonoverwriting_path(self):
        with tempfile.TemporaryDirectory()as tmp:
            parent=Path(tmp).resolve();declared=parent/"source";declared.mkdir()
            out=parent/"run-skvq-default-tp-local-012-software"
            with patch.object(C,"ROOT",declared):
                self.assertEqual(H.newroot(out),out)
                with self.assertRaises(ValueError):H.newroot(out)
                work=out/"work";work.mkdir();self.assertEqual(C.stage_root(work),work)
                library=C.output_root(work/"library");self.assertTrue(library.is_dir())
                with self.assertRaises(ValueError):C.output_root(library)
                with self.assertRaises(ValueError):C.stage_root(out)
                with self.assertRaises(ValueError):H.newroot(parent/"run-skvq-default-tp-local-002-wrong")
def main():
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CPUHost))
    return 0 if r.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
