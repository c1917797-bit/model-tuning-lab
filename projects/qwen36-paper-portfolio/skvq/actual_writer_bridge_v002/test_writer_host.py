"""Actual donor Control AST and producer->whole boundaries, software fixture scope only.
No Docker/Torch/NPU invocation; these tests grant no runtime authority.
"""
import ast,copy,hashlib,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
import writer_host as H
import writer_resources as R
import writer_whole as W
DONOR=Path("C:/Users/Huawei/AppData/Local/Temp/skvq-preprojection-current72h-20261010-014/MAIN_HOST.py")
def control():
    row=C.HOST_BINDINGS["MAIN_HOST.py"]
    p=Path(row["path"])if Path(row["path"]).is_file()else DONOR
    raw=p.read_bytes()
    if len(raw)!=row["bytes"]or hashlib.sha256(raw).hexdigest()!=row["sha256"]:raise ValueError("actual donor whole bytes")
    with patch.object(C,"checked",return_value=raw),patch.object(C,"module",return_value=types.SimpleNamespace(actual_hbm=lambda t,c:[])):
        return H.control_class({"sha256":"a"*64},{"/results":("/results",True)},types.SimpleNamespace())
def inspected(cls,owned):
    return dict(Id=owned["cid"],Name="/"+owned["name"],Image=C.IMAGE,Config=dict(Image=C.IMAGE,
      Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],
      Labels={"model-tuning-lab.owner":H.OWNER,"model-tuning-lab.source":owned["source"]},
      Env=[k+"="+v for k,v in owned["env"].items()]),HostConfig=dict(Privileged=False,Memory=owned["mem"],
      MemorySwap=owned["mem"],NanoCpus=10**9,CpusetCpus=owned["cpuset"],CgroupnsMode="host",NetworkMode="none",
      IpcMode="private",ShmSize=2*H.GIB,PidsLimit=1024,CapDrop=["ALL"],SecurityOpt=["no-new-privileges"],
      DeviceRequests=[],DeviceCgroupRules=[],Devices=[dict(PathOnHost=k,PathInContainer=v,CgroupPermissions="rwm")
      for k,v in owned["devices"].items()]),Mounts=[dict(Type="bind",Destination=k,Source=v[0],RW=v[1])
      for k,v in owned["mounts"].items()])
def owned(npu=True):
    return dict(cid="a"*64,name="actual-test",source="b"*64,mem=8*H.GIB,cpuset="5",devices=
      {"/dev/davinci4":"/dev/davinci0",**{"/dev/"+k:"/dev/"+k for k in("davinci_manager","devmm_svm","hisi_hdc")}}if npu else {},
      mounts={"/actual":("/actual",False),"/results":("/results",True)},env=H.environment(npu))
def terminal(argv):
    return dict(schema="agentweb.operation/v1",terminal=True,status="completed",succeeded=True,error=None,
      operation=dict(ok=True,routeDecision="peer_direct",targetPeerId="lgw_a6109c51076a4a2c9d2674ca5a8704a0",
        result=dict(state="completed",record=dict(command=argv[0],args=argv[1:],exitCode=0,error=None,timedOut=False,cancelled=False))))
class Tests(unittest.TestCase):
    def test01_actual_Control_unchanged_bodies_except_five_literals(self):
        cls=control();self.assertEqual(len(cls.literal_delta),5)
        self.assertIn(["cpu=4, started_elapsed=","cpu=1, started_elapsed="],cls.literal_delta)
        self.assertNotEqual(cls.original_ast_sha256,cls.adapted_ast_sha256)
        value=cls(Path("/unused"));self.assertEqual(value.limit,1800)
        self.assertEqual(value.devices(True)["/dev/davinci4"],"/dev/davinci0")
        self.assertNotIn("/dev/davinci5",value.devices(True))
        self.assertEqual(value.devices(False),{})
    def test02_actual_original_validate_physical4_CPU1_and_CPU_Devices_empty(self):
        cls=control()
        for npu in(True,False):
            e=owned(npu);x=inspected(cls,e)
            self.assertIs(cls.validate(None,x,e),x)
            for mutate in("owner","cpu","device","mount","memory"):
                bad=copy.deepcopy(x)
                if mutate=="owner":bad["Config"]["Labels"]["model-tuning-lab.owner"]="borrowed"
                elif mutate=="cpu":bad["HostConfig"]["NanoCpus"]=4*10**9
                elif mutate=="device":bad["HostConfig"]["Devices"].append(dict(PathOnHost="/dev/davinci0",PathInContainer="/dev/davinci4",CgroupPermissions="rwm"))
                elif mutate=="mount":bad["Mounts"][0]["RW"]=True
                else:bad["HostConfig"]["Memory"]=64*H.GIB
                with self.assertRaises(ValueError):cls.validate(None,bad,e)
    def test03_CPU_original_branch_does_not_observe_NPU(self):
        raw=DONOR.read_bytes()if DONOR.is_file()else C.checked(C.HOST_BINDINGS["MAIN_HOST.py"])
        cls=next(x for x in ast.parse(raw).body if isinstance(x,ast.ClassDef)and x.name=="Control")
        for name in("create","exec","cleanup"):
            f=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name==name)
            calls=[x for x in ast.walk(f)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and
              isinstance(x.func.value,ast.Name)and x.func.value.id=="self"and x.func.attr=="observe"]
            self.assertTrue(calls)
            for call in calls:
                guards=[x for x in ast.walk(f)if isinstance(x,ast.If)and call in list(ast.walk(x))]
                self.assertTrue(any(("npu" in ast.unparse(x.test))for x in guards))
    def test04_four_real_argv_existing_mount_absent_children(self):
        out=Path("/cache/owned");source={"sha256":"c"*64};whole=Path("/cache/cal.json")
        for stage,file in(("input-plan","writer_cpu.py"),("canary","writer_canary.py"),("numeric","writer_numeric.py"),("independent","writer_consume.py")):
            args=H.args(stage,source,out,whole)
            self.assertEqual(args[0],str(C.ROOT/file));self.assertEqual(args[1:4],["--execute","--source-manifest-sha256","c"*64])
            self.assertEqual(args.count("--output"),1)
        self.assertEqual(H.args("numeric",source,out,whole)[-1],str(out/"candidate/work/numeric"))
        self.assertEqual(H.args("input-plan",source,out,whole)[-1],str(out/"input-plan/work"))
        self.assertEqual(H.args("independent",source,out,whole)[-1],str(out/"candidate/work/numeric/WRITER_INDEPENDENT.json"))
        self.assertIn("p.name in", (HERE/"writer_contract.py").read_text())
    def test05_original_whole_actual_exact_entry_and_failed_negatives(self):
        argv=W.host_argv(Path("/out"),{"sha256":"a"*64},Path("/cal-ref.json"))
        value=terminal(argv);W.original(value,argv)
        for mutate in("exit","timeout","cancel","route","args","running","error"):
            bad=copy.deepcopy(value);record=bad["operation"]["result"]["record"]
            if mutate=="exit":record["exitCode"]=1
            elif mutate=="timeout":record["timedOut"]=True
            elif mutate=="cancel":record["cancelled"]=True
            elif mutate=="route":bad["operation"]["targetPeerId"]="foreign"
            elif mutate=="args":record["args"][-1]="/other"
            elif mutate=="running":bad["terminal"]=False
            else:bad["error"]="Transport closed"
            with self.assertRaises(ValueError):W.original(bad,argv)
    def test06_actual_CPU4_ancestor_budget_and_negatives(self):
        host=dict(effective_capacity=1,effective_cpus=[4],quota_ancestors=[dict(key="common",capacity=4)])
        daemon=dict(effective_capacity=3,effective_cpus=[4,5,6,7],quota_ancestors=[dict(key="common",capacity=4)])
        self.assertEqual(R.allocate(host,daemon)["guest_cpus"],[5])
        self.assertEqual(R.allocate(host,daemon)["reserve_cpus"],[6,7])
        bad=copy.deepcopy(daemon);bad["quota_ancestors"][0]["capacity"]=3
        with self.assertRaises(ValueError):R.allocate(host,bad)
    def test07_actual_CLI_source_constructor_and_negative_npu_env(self):
        argv=H.args("numeric",{"sha256":"a"*64},Path("/out"),Path("/cal.json"));cid="b"*64
        actual=[H.DOCKER,"exec","--env","MAIN_OWNED_CID="+cid,cid,"/bin/bash","-c",
          'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"skvq-owned",H.PY,"-B",*argv]
        row=dict(argv=actual,actual_wrapped_argv=[H.PRLIMIT,"--as=unlimited","--",*actual],exit_code=0,
          terminated=True,primary=None,stdout={"path":"stdout"},stderr={"path":"stderr"})
        with patch.object(C,"obj",return_value=row),patch.object(C,"checked"):
            self.assertIs(W.child_cli({},cid,argv,npu=True),row)
            with self.assertRaises(ValueError):W.child_cli({},cid,argv,npu=False)
            row["exit_code"]=1
            with self.assertRaises(ValueError):W.child_cli({},cid,argv,npu=True)
    def test08_guest_identity_requires_host_exact_raw_proof(self):
        who=dict(pid=8,start_ticks=123,cgroup="0::/docker/"+"a"*64,argv=["python","worker.py"],cmdline_sha256="c"*64)
        proof=dict(who,physical=4,chip=0,pid=999,namespace_pids=[999,8])
        W.identity_proved(who,[proof],"a"*64,who["argv"])
        for key,value in(("start_ticks",124),("cmdline_sha256","d"*64),("argv",["python","other"])):
            bad=dict(proof,**{key:value})
            with self.assertRaises(ValueError):W.identity_proved(who,[bad],"a"*64,who["argv"])
    def test09_actual_byte_oracle_result_fields_whole_interface(self):
        from test_writer_bridge import axis_fixture
        import writer_byte_oracle as O
        l,raw,row,store=axis_fixture();fields=O.check_axis(row,raw,l,2,"float16",store.__getitem__)
        self.assertTrue(fields["full_input_unchanged"]);self.assertTrue(fields["full_sink_recent_guard_unchanged"])
        self.assertTrue(fields["independent_candidate_math_not_called"])
        text=(HERE/"writer_whole.py").read_text()
        for key in fields:
            if type(fields[key])is bool:self.assertIn('result["'+key+'"]',text)
    def test10_source14_current_contract_cmdline_helper_and_chain_are_bound(self):
        self.assertEqual(C.CAPTURE["sha256"],"9c7b1118b1cd1f2a20ab7fde0ecb98031bf14289c9c795c18f48de9cdb805acd")
        self.assertEqual(C.CALIBRATION["sha256"],"07b526100b7184b4555138a7318c5f4a7c45ac451207ea96f656173cba1366c1")
        text=(HERE/"writer_host.py").read_text()
        self.assertIn('C.module("process_cmdline",C.HOST_BINDINGS["process_cmdline.py"])',text)
        self.assertIn('PC.consume(C.obj(proof["actual_cmdline_raw_ref"]),proof,source)',(HERE/"writer_whole.py").read_text())
    def test11_all_actual_source_compile_and_default_OFF_no_native_import(self):
        for path in HERE.glob("*.py"):compile(path.read_bytes(),str(path),"exec")
        for module in(H,W,R):self.assertIsNotNone(module.__file__)
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules);self.assertNotIn("numpy",sys.modules)
    def test12_owned_independent_CPU_cleanup_contract_rejects_NPU_scope(self):
        tree=ast.parse((HERE/"writer_whole.py").read_bytes())
        f=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="inspect_cleanup")
        text=ast.unparse(f)
        self.assertIn("'release_smi' in release",text)
        self.assertIn("== npu",text)
        self.assertIn("Controller.validate(None, rows[0], normalized)",text)
        self.assertTrue(all(x is False for x in C.scopes().values()))
def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())

