"""Producer-shaped SYNTHETIC stdlib regressions; no real operation/NPU/service authority."""
from __future__ import annotations
import ast,copy,io,json,sys,unittest
from contextlib import redirect_stdout
from datetime import datetime,timezone
from pathlib import Path
import binding as b
import consumer as c
SYNTHETIC=True
def case_rows(bridge,t,finite):
    path=b.PROJECT/"tools/split_service_authority_v1/test_validator.py"
    data=b.read_file(str(path))
    b.require(b.digest(data)=="6e4518ee4ccf6d478c718b775099360805f0300f3691e63d25221ff687a33ed6","old software fixture body")
    tree=ast.parse(data);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=="Fixture")
    fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=="cases")
    env={"v":bridge};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),"exec"),env)
    rows=env["cases"](None,t)
    finite_names=("state.base","state.k_log","state.u_log","state.lambda_log","state.decay","state.length",
                  "actual_all","expected_active","logical_complete","native_state_all")
    for case in rows:
        for row in case["steps"]:
            row.update(finite_scope=finite.FINITE_SCOPE,finite_buffer_checks=dict.fromkeys(finite_names,True),
                native_expected_defined_rows=row["active"],native_expected_undefined_padding_rows=t-row["active"],
                native_padding_values_rewritten=False)
    return rows
class Fixture:
    """All tool/child/report bytes here are synthetic shape tests, never usable real receipts."""
    def __init__(self):
        self.files={};self.serial=0
        memory=globals().get("_MEMORY_SOURCES")
        for name in b.OWN:
            self.files[str(b.BASE/name)]=(memory[name].encode() if memory is not None else b.read_file(str(b.BASE/name)))
        gr=b.actual_ref(b.GATE/"SOURCE_MANIFEST.json")
        packet=dict(schema="kvbp.native-order-followup-sources/v2",default_enabled=False,
            files={n:b.digest(self.files[str(b.BASE/n)]) for n in b.OWN},v2_gate_manifest=gr,
            old_consumer_packet=b.actual_ref(b.PROJECT/"tools/middle_service_bridge_v1/PACKET.json"))
        self.pr=self.put(packet,str(b.BASE/"SOURCE_MANIFEST.json"))
        self.packet,self.gm,self.pins,self.own,self.finite,self.bridge,self.legacy=b.sources(self.pr,self.read)
        self.gm["_followup_ref"]=self.pr
        lib=self.put(b"SYNTHETIC candidate library bytes, not dlopen proof","/synthetic/NOT_AUTHORITY/v2.so")
        build=self.put(dict(status="compiled_no_device",npu_executed=False,image_id=b.IMAGE,namespace=b.NS,
            sources=self.gm["operator_sources"],npu_arch="dav-2201",library_sha256=lib["sha256"],
            commands=[dict(exit_code=0)],exported_kernel=dict(name="qwen36_gdn_kvbuffer_native_order_v2_kernel",
                                                            defined=True,type="T")))
        self.schema=b.NS+"::decode(Tensor query, Tensor(a!) base_state) -> Tensor"
        self.native_schema="npu_recurrent_gated_delta_rule beta scale actual_seq_lengths ssm_state_indices"
        meta=self.put(dict(status="pass",namespace=b.NS,npu_executed=False,source_manifest=gr,
            sources_before=self.pins,sources_after=self.pins,library_sha256=lib["sha256"],
            build_receipt_sha256=build["sha256"],loaded_libraries={lib["path"]:lib["sha256"]},
            loaded_candidate_sha256=lib["sha256"],no_davinci_devices_observed=True,native_bootstrap_verified=False,
            schema=self.schema,prepare_schema=b.NS+"::prepare(Tensor query, Tensor base_state) -> ()",
            meta=[dict(T=t,shape=[t,12,128],dtype="torch.bfloat16",device="meta",nonalias=True,
                       prepare_return_none=True) for t in (1,16)],runtime=dict(torch="SYNTHETIC",torch_npu="SYNTHETIC")))
        self.ar=dict(library=lib,build=build,meta=meta)
        self.mm=self.put(dict(status="actual_v2_14_positive_Meta_pass",namespace=b.NS,
            source_manifest=gr,followup_manifest=self.pr,sources_before={**self.pins,**self.own},
            sources_after={**self.pins,**self.own},artifact_refs=self.ar,library_sha256=lib["sha256"],
            loaded_libraries={lib["path"]:lib["sha256"]},schema=self.schema,
            prepare_schema=b.NS+"::prepare(Tensor query, Tensor base_state) -> ()",
            npu_executed=False,no_davinci_devices_observed=True,native_bootstrap_verified=False,
            serving_ready=False,graph_proven=False,physical_nd_proven=False,
            meta=[dict(T=t,shape=[t,12,128],dtype="torch.bfloat16",device="meta",nonalias=True,
                       prepare_return_none=True) for t in range(2,16)]))
        self.producer=self.put(b"# SYNTHETIC actual-producer-shape-only; never executed\n")
        self.producer_sources={self.producer["path"]:self.producer["sha256"]}
        snapshot="/cache/cch/qwen36-damp-20261006/runtime-native-library-snapshot-v1/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
        self.native=dict(path=snapshot,sha256=b.NATIVE_SHA)
        self.inputs=dict(b1=self.make([1],5,1),b16=self.make([16],6,2),
                         middle=[self.make(list(ts),card,card) for card,ts in b.GROUPS.items()])
    def read(self,path):return self.files[path] if path in self.files else b.read_file(path)
    def put(self,x,path=None):
        self.serial+=1;path=path or "/synthetic/NOT_AUTHORITY/blob%d"%self.serial
        data=x if type(x) is bytes else b.canonical(x)+b"\n";self.files[path]=data
        return dict(path=path,sha256=b.digest(data))
    def obj(self,r):return b.obj(r,self.read)
    @staticmethod
    def smi(card=None,pid=None):
        lines=["Process id","+----+"]
        for x in range(8):
            lines.append("| %d 0 | %d | SYNTHETIC_PROCESS | 1 |"%(x,pid) if x==card
                         else "| No running processes found in NPU %d |"%x)
        return "\n".join(lines)+"\n"
    def make(self,batches,card,serial):
        middle=batches not in ([1],[16]);before={**self.pins,**self.own} if middle else self.pins
        pp=b.protocol(batches,card) if middle else b.split_protocol(batches[0],card,self.finite,self.legacy)
        cid=("%064x"%serial);owner="kvbuffer-SYNTHETIC";run="synthetic-%d"%serial
        devices=[dict(PathOnHost=x,PathInContainer=y,CgroupPermissions="rwm") for x,y in
                 {"/dev/davinci"+str(card):"/dev/davinci0","/dev/davinci_manager":"/dev/davinci_manager",
                  "/dev/devmm_svm":"/dev/devmm_svm","/dev/hisi_hdc":"/dev/hisi_hdc"}.items()]
        entry=dict(Id=cid,Image=b.IMAGE,HostConfig=dict(Privileged=False,Memory=8*b.GIB,MemorySwap=8*b.GIB,
            Devices=devices,DeviceRequests=[]),Config=dict(Labels={"model-tuning-lab.owner":owner,
            "model-tuning-lab.run":run}),State=dict(Running=True,Pid=700+serial))
        ins=self.put([entry]);stopped=copy.deepcopy(entry);stopped["State"]=dict(Running=False,Pid=0)
        si=self.put([stopped]);ts="2026-10-07T10:00:00Z";created=int(datetime.fromisoformat(ts.replace("Z","+00:00")).timestamp()*1e9)+10**9
        proof=self.put(dict(schema="kvbp.native-order-device-binding/v2",container_id=cid,image_id=b.IMAGE,
            physical_devices=[card],logical_to_physical={"0":card},preflight_utc=ts,separate_canary_not_gate=True,
            raw_refs=dict(canary=self.put(b"SYNTHETIC canary"),mapping=ins,
                          host_processes=self.put(b"SYNTHETIC host evidence"),cgroup=self.put(b"SYNTHETIC cgroup"))))
        ident=dict(schema="kvbp.native-order-middle-launch/v2" if middle else "kvbp.split-launch-identity/v2",
            image_id=b.IMAGE,protocol=pp,physical_devices=[card],logical_to_physical={"0":card},
            fresh_idle_verified=True,nonprivileged=True,source_canary_passed=True,memory_cgroup_bytes=8*b.GIB,
            sources=before,source_manifest=self.packet["v2_gate_manifest"],artifact_refs=self.ar,
            preflight_utc=ts,evidence=dict(device_proof=proof,container_inspect=ins))
        if middle:ident.update(followup_manifest=self.pr,middle_meta=self.mm)
        ir=self.put(ident)
        image_identity="/kvbuffer-launch/identity.json";image_out="/kvbuffer-results/gate"
        script=b.BASE/"middle_run.py" if middle else b.GATE/"run.py"
        args=[c.PYTHON,"-B",str(script),"--execute"]
        args+=["--batches",*map(str,batches)] if middle else ["--batch",str(batches[0])]
        args+=["--physical-device",str(card),"--identity",image_identity,"--output-dir",image_out]
        for key,r in self.ar.items():
            flag={"build":"build-receipt","meta":"meta-receipt","library":"library"}[key]
            args+=["--"+flag,r["path"],"--"+flag+"-sha256",r["sha256"]]
        if middle:
            args+=["--followup-manifest",self.pr["path"],"--followup-manifest-sha256",self.pr["sha256"],
                   "--middle-meta",self.mm["path"],"--middle-meta-sha256",self.mm["sha256"]]
        else:
            r=self.packet["v2_gate_manifest"];args+=["--source-manifest",r["path"],"--source-manifest-sha256",r["sha256"]]
        report=dict(schema="kvbp.intermediate-native-gate/v2" if middle else "kvbp.split-native-gate/v2",
            status="intermediate_batches_kernel_native_eager_graph_pass" if middle else "single_batch_kernel_native_eager_graph_pass",
            claim="kernel-only",candidate_namespace=b.NS,finite_scope=self.finite.FINITE_SCOPE,
            created_ns=created,completed_ns=created+100*10**9,source_manifest=self.packet["v2_gate_manifest"],
            artifact_refs=self.ar,sources_before=before,sources_after=before,launch_identity=ident,
            launch_identity_sha256=ir["sha256"],protocol=pp,native_sources=self.legacy.NATIVE_PINS,
            frozen_receipts=dict(artifacts=self.ar,meta_schema=self.schema,meta_is_not_npu_proof=True),
            candidate_schema=self.schema,native_schema=self.native_schema,
            script_sha256=before[str(script)],cgroup=dict(bytes=8*b.GIB),
            loaded_libraries={self.ar["library"]["path"]:self.ar["library"]["sha256"],b.NATIVE_SO:b.NATIVE_SHA},
            runtime=dict(logical_device_count=1,logical_device=0,device_name="SYNTHETIC_NOT_DEVICE_PROOF",
                         torch="SYNTHETIC",torch_npu="SYNTHETIC"),
            cases=[row for t in batches for row in case_rows(self.bridge,t,self.finite)])
        if middle:report.update(driver_sources=self.own,followup_manifest=self.pr,middle_meta=self.mm,
                                npu_executed=True,serving_ready=False,performance_measurement_admitted=False)
        rr=self.put(report);pid=800+serial;wait=dict(pid=pid,start_ticks=100+serial,cgroup="0::/docker/"+cid)
        wr=self.put(wait);obs=self.put(dict(physical_card=card,separate_canary_not_gate=True,
            process=dict(**wait,namespace_pids=[pid,23],argv=args),npu_smi=self.smi(card,pid)))
        protected={str(x):[] for x in range(4)}
        pb=self.put(dict(schema="kvbp.native-order-protected-processes/v2",observed_ns=created-1,processes=protected))
        pa=self.put(dict(schema="kvbp.native-order-protected-processes/v2",observed_ns=report["completed_ns"]+1,processes=protected))
        cr=self.put(dict(schema="kvbp.native-order-child/v2",evidence_kind="actual-main-execution",
            report=rr,identity=ir,image_identity_path=image_identity,image_output_dir=image_out,
            producer_sources=self.producer_sources,source_before=before,source_after=before,
            service_ready=False,performance=False,container_inspect=ins,stopped_inspect=si,device_proof=proof,
            actual_gate_process=obs,waiting_process=wr,release_processes=self.put(self.smi().encode()),
            protected0_3=protected,protected_processes_before=pb,protected_processes_after=pa,
            resource_refs=[self.put(b"SYNTHETIC sampled resource bytes")],native_library=self.native,
            cleanup=dict(container_id=cid,stopped=True,retained=True,deleted=False),
            execution=dict(command="/usr/bin/docker",args=["exec",cid,*args],cwd=str(b.ROOT),exit_code=0,error=None,
                           cancelled=False,timed_out=False,stdout=self.put(b"SYNTHETIC child stdout"),stderr=self.put(b""))))
        a=dict(report=rr,identity=ir,child=cr,peer_id=b.PEER,operation_id="exec-%032x"%serial,
            command="/usr/bin/python3",args=["-B",self.producer["path"]],cwd=str(b.ROOT),
            producer_sources=self.producer_sources,expected=dict(container_id=cid,owner=owner,run_id=run,
            physical_device=card,batches=batches,runner_argv=args))
        self.outer(a);return a
    def outer(self,a):
        stdout=b.PREFIX+json.dumps({k:a[k] for k in ("report","identity","child")})+"\n"
        record=dict(id=a["operation_id"],state="completed",command=a["command"],args=a["args"],cwd=a["cwd"],
                    exitCode=0,error=None,cancelled=False,timedOut=False,stdout=stdout,stderr="")
        a.update(operation=self.put(dict(schema="agentweb.operation/v1",kind="exec",operationId=a["operation_id"],
            terminal=True,status="completed",succeeded=True,error=None,operation=dict(routeDecision="peer_direct",
            targetPeerId=b.PEER,fallbackUsed=False,result=dict(record=record)))),stdout=self.put(stdout.encode()),stderr=self.put(b""))
    def change(self,a,kind,modify):
        value=self.obj(a[kind]);modify(value);a[kind]=self.put(value)
        if kind=="report":
            child=self.obj(a["child"]);child["report"]=a["report"];a["child"]=self.put(child)
        self.outer(a)
    def result(self):return c.validate_complete(self.inputs,self.pr,enabled=True,read=self.read)
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.original=Fixture()
    def setUp(self):
        self.f=copy.copy(self.original)
        self.f.files=copy.deepcopy(self.original.files)
        self.f.inputs=copy.deepcopy(self.original.inputs)
    def reject(self,kind,fn):
        self.f.change(self.f.inputs["b1"],kind,fn)
        with self.assertRaises((ValueError,KeyError)):self.f.result()
    def test_full_actual_shape_is_explicitly_only_software(self):
        r=self.f.result();self.assertEqual((r["unique_cases"],r["changing_feedback_steps"]),(64,10240))
        self.assertEqual(r["namespace"],b.NS);self.assertFalse(r["legacy_pass_fabricated"])
        for key in b.FALSE_SCOPE:self.assertFalse(r[key])
        self.assertFalse(r["service_launcher_admitted"]);self.assertFalse(r["resource_telemetry_semantics_validated"])
    def test_default_off(self):
        with self.assertRaises(ValueError):c.validate_complete(self.f.inputs,self.f.pr,read=self.f.read)
        out=io.StringIO()
        with redirect_stdout(out):c.main([])
        self.assertEqual(json.loads(out.getvalue())["status"],"OFF")
    def test_no_v1_pass_conversion(self):self.reject("report",lambda r:r.__setitem__("schema","kvbp.split-native-gate/v1"))
    def test_failed_report_pending_raw_or_missing_step(self):
        for fn in (lambda r:r.__setitem__("status","failed"),lambda r:r["cases"][0]["steps"].pop(),
                   lambda r:r["cases"][0].__setitem__("pending_raw_step",{})):
            self.setUp();self.reject("report",fn)
    def test_original_frozen_thresholds_and_fullfinite(self):
        for field,number in (("output_error",.00303001),("complete_state_l2",.000002001),("max_per_head_l2",.000002001)):
            self.setUp();self.reject("report",lambda r:r["cases"][0]["steps"][0].__setitem__(field,number))
        self.setUp();self.reject("report",lambda r:r["cases"][0]["steps"][0]["finite_buffer_checks"].__setitem__("actual_all",False))
        self.setUp();self.reject("report",lambda r:r["cases"][0]["steps"][0].__setitem__("native_padding_values_rewritten",True))
    def test_every_original_guard_log_flush(self):
        for field in self.f.bridge.GUARDS:
            self.setUp();self.reject("report",lambda r:r["cases"][0]["steps"][2].__setitem__(field,False))
        self.setUp();self.reject("report",lambda r:r["cases"][0]["steps"][2]["all_logs_bitwise_outside_new_U"].__setitem__("u_log",False))
        self.setUp();self.reject("report",lambda r:r["cases"][0].__setitem__("merges",0))
    def test_terminal_nonzero_timeout_cancel_and_raw_streams(self):
        for patch in (dict(exitCode=1,error="exit code"),dict(timedOut=True),dict(cancelled=True)):
            self.setUp();a=self.f.inputs["b1"];v=self.f.obj(a["operation"]);v["operation"]["result"]["record"].update(patch)
            a["operation"]=self.f.put(v)
            with self.assertRaises(ValueError):self.f.result()
        self.setUp();self.f.inputs["b1"]["stderr"]=self.f.put(b"not original")
        with self.assertRaises(ValueError):self.f.result()
    def test_producer_and_gate_source_drift(self):
        path=self.f.producer["path"];self.f.files[path]+=b"\n"
        with self.assertRaises(ValueError):self.f.result()
        self.setUp();p=str(b.GATE/"oracle.py");self.f.files[p]=b.read_file(p)+b"\n"
        with self.assertRaises(ValueError):self.f.result()
    def test_loaded_candidate_native_and_artifact_identity(self):
        self.reject("report",lambda r:r["loaded_libraries"].pop(b.NATIVE_SO))
        self.setUp();self.reject("report",lambda r:r.__setitem__("candidate_schema","unknown namespace"))
        self.setUp();self.reject("report",lambda r:r["sources_after"].pop(next(iter(r["sources_after"]))))
    def test_real_middle_groups_no_padding_or_missing_shard(self):
        self.f.inputs["middle"].pop()
        with self.assertRaises(ValueError):self.f.result()
        self.setUp();a=self.f.inputs["middle"][0];a["expected"]["batches"]=[2,3,4]
        with self.assertRaises(ValueError):self.f.result()
        with self.assertRaises(ValueError):b.protocol([2,3,4],4)
    def test_original_pid_cgroup_and_protected_history(self):
        self.reject("child",lambda r:r.__setitem__("waiting_process",self.f.put(dict(pid=999,start_ticks=123,cgroup="unknown"))))
        self.setUp();self.reject("child",lambda r:r.__setitem__("protected_processes_after",
            self.f.put(dict(schema="kvbp.native-order-protected-processes/v2",observed_ns=10**19,
                           processes={"0":[dict(pid=1,start_ticks=1)],"1":[],"2":[],"3":[]}))))
    def test_stopped_scope_no_privileged_or_card0(self):
        a=self.f.inputs["b1"];v=self.f.obj(self.f.obj(a["child"])["stopped_inspect"]);v[0]["State"]["Running"]=True
        self.reject("child",lambda r:r.__setitem__("stopped_inspect",self.f.put(v)))
        self.setUp();a=self.f.inputs["b1"];v=self.f.obj(self.f.obj(a["child"])["container_inspect"])
        v[0]["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci0"
        self.reject("child",lambda r:r.__setitem__("container_inspect",self.f.put(v)))
    def test_meta14_no_old_namespace_or_missingT(self):
        value=self.f.obj(self.f.mm);value["meta"].pop();self.f.files[self.f.mm["path"]]=b.canonical(value)+b"\n"
        with self.assertRaises(ValueError):self.f.result()
    def test_no_rewrite_and_no_unknown_flags(self):
        before=copy.deepcopy(self.f.files);self.f.result();self.assertEqual(before,self.f.files)
        with self.assertRaises(ValueError):c.flags(["--execute","--execute"])
        self.reject("child",lambda r:r["execution"]["args"].append("--unknown"))
    def test_existing_runtime_does_not_break_after_source_closure(self):
        keys=("torch","torch_npu","torch.audit_sentinel","torch_npu.audit_sentinel")
        saved={key:sys.modules[key] for key in keys if key in sys.modules}
        sentinels={key:type(sys)(key) for key in keys}
        try:
            sys.modules.update(sentinels)
            _,_,pins,own,_,_,_=b.sources(self.f.pr,self.f.read)
            self.assertEqual(pins,self.f.pins);self.assertEqual(own,self.f.own)
            for key,value in sentinels.items():self.assertIs(sys.modules[key],value)
        finally:
            for key in keys:
                if key in saved:sys.modules[key]=saved[key]
                else:sys.modules.pop(key,None)
    def test_source_loader_rejects_new_or_replaced_runtime(self):
        keys=("torch","torch_npu","torch.audit_new","torch_npu.audit_new")
        saved={key:sys.modules[key] for key in keys if key in sys.modules}
        try:
            for existing in (False,True):
                for name in keys:
                    for key in keys:sys.modules.pop(key,None)
                    if existing:
                        sys.modules["torch"]=type(sys)("torch")
                        sys.modules["torch_npu"]=type(sys)("torch_npu")
                    data=("import sys\nsys.modules["+repr(name)+"]=type(sys)("+repr(name)+")\n").encode()
                    path=Path("/synthetic/NOT_AUTHORITY/source-runtime-loader.py")
                    with self.assertRaises(ValueError):
                        b.module(path,b.digest(data),"_synthetic_new_runtime_source",lambda _:data)
                    self.assertIn(name,sys.modules)
            for key in keys:sys.modules.pop(key,None)
            bad=b"import sys\nsys.modules.pop('torch')\n"
            sys.modules["torch"]=type(sys)("torch")
            with self.assertRaises(ValueError):
                b.module(Path("/synthetic/NOT_AUTHORITY/remove-runtime.py"),b.digest(bad),
                         "_synthetic_remove_runtime_source",lambda _:bad)
        finally:
            for key in keys:
                if key in saved:sys.modules[key]=saved[key]
                else:sys.modules.pop(key,None)
    def test_source_ast_reuse_and_entrypoint_defaultoff(self):
        tree=ast.parse(b.read_file(str(b.GATE/"meta_probe.py")))
        original=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="meta_inputs")
        new=next(x for x in ast.parse(self.f.read(str(b.BASE/"binding.py"))) .body
                 if isinstance(x,ast.FunctionDef) and x.name=="meta_inputs")
        self.assertEqual(ast.dump(original,include_attributes=False),ast.dump(new,include_attributes=False))
        tree=ast.parse(self.f.read(str(b.BASE/"middle_run.py")))
        self.assertTrue(any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)
                            and x.func.attr=="run_case" for x in ast.walk(tree)))
if __name__=="__main__":unittest.main()
