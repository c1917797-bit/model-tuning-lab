"""SYNTHETIC producer-shaped software contracts; never original tool/device authority."""
from __future__ import annotations
import ast,copy,hashlib,io,json,sys,unittest
from contextlib import redirect_stdout
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import contract as c
import launch as l
import pair as pair

SYNTHETIC=True

def cases(bridge,b):
    # Original numerical fixture method/body, source-bound and not an alternative oracle.
    path=c.PROJECT/"tools/split_service_authority_v1/test_validator.py"
    wanted="6e4518ee4ccf6d478c718b775099360805f0300f3691e63d25221ff687a33ed6"
    data=c.read_file(str(path));c.require(c.digest(data)==wanted,"original software fixture drift")
    tree=ast.parse(data);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=="Fixture")
    fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=="cases")
    env={"v":bridge};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),"exec"),env)
    return env["cases"](None,b)

class Fixture:
    """Raw markers/receipts are deliberately SYNTHETIC, not AWMCP/NPU evidence."""
    def __init__(self):
        self.files={}
        def read(path):return self.files[path] if path in self.files else c.read_file(path)
        self.read=read
        self.put=lambda path,v:self._put(path,v)
        deps=json.loads(self.source("PACKET.json"))["dependencies"]
        self.packet=dict(dependencies=deps)
        self.old=c.load_pinned(c.SPLIT/"consumer.py",deps[str(c.SPLIT/"consumer.py")],"_software_middle_actual_old")
        manifest=dict(schema="kvbp.split-service-consumer-sources/v1",enabled=False,
                      files={n:c.digest(c.read_file(str(c.SPLIT/n))) for n in self.old.OWN},
                      dispatcher_packet={"path":str(self.old.PACKET),"sha256":self.old.PACKET_SHA})
        self.manifest=self.put("/synthetic/consumer-manifest.json",manifest)
        self.runtime=self.old.sources(self.manifest,self.read)
        self.sp,self.pins49,self.producer,self.bridge,self.d,self.realhost,self.helper=self.runtime
        self.m=c.load_pinned(c.PROGRAM,c.PROGRAM_SHA,"_software_middle_real_program")
        self.runner=c.load_pinned(c.RUNNER,c.RUNNER_SHA,"_software_middle_real_runner")
        path=c.PROJECT/"tools/split_gate_v1/contract.py"
        self.split=c.load_pinned(path,self.pins49[str(path)],"_software_middle_gate")
        self.pins54={**self.pins49,str(c.PROJECT/"tools/split_dispatch_v1/PACKET.json"):self.old.PACKET_SHA,
                     str(c.RUNNER):c.RUNNER_SHA,**self.m.RELEASE_PINS}
        config=dict(main_approved=True,main_program_sha256=c.PROGRAM_SHA,middle_meta14=c.META14,
                    release_authority_kind="host_job_cleanup_observed",release_helper_sources=self.m.RELEASE_PINS,
                    formal_start_utc="2026-10-07T08:00:00Z",deadline_utc="2026-10-08T08:00:00Z",
                    phase_seconds=dict.fromkeys(map(str,c.GROUPS),3600),run_slug="synthetic-contract-only",
                    release_host_job_refs=c.HOST_RELEASE_REFS)
        self.root=c.RESULT/("middle-main-"+config["run_slug"]);self.audit=self.root/"audit"
        self.config_ref=self.put("/synthetic/middle-inputs.json",config)
        self.joint_ref=self.put("/synthetic/split-joint.json",dict(inputs=dict(
            formal_start_utc=config["formal_start_utc"],deadline_utc=config["deadline_utc"])))
        self.checked=dict(source_manifest=self.manifest,joint=self.joint_ref)
        program=c.read_file(str(c.PROGRAM)).decode()
        self.authority=dict(operation_id="exec-abcdef012345",peer_id=c.PEER,command="/usr/bin/python3",
            args=["-B","-c",program,"--execute","--inputs",self.config_ref["path"],
                  "--inputs-sha256",self.config_ref["sha256"]],cwd=str(c.ROOT),inputs=self.config_ref,
            program={"path":str(c.PROGRAM),"sha256":c.PROGRAM_SHA})
        prereq=dict(report=c.META14,status="actual_14_positive_Meta_pass",positive_batches=list(range(2,16)),
                    npu_executed=False,scope="positive Meta prerequisite only; actual device identity/terminal still required")
        self.put(self.audit/"PROGRAM.json",dict(source=program,sha256=c.PROGRAM_SHA,
            actual_process_argv=[self.authority["command"]]+self.authority["args"],
            source_dependencies=self.pins54,inputs=self.config_ref,middle_meta14=prereq))
        self.release=self.put(self.audit/"PARENT_RELEASE.json",dict(rpc_terminal_reconstructed=False,
            scope="release only, not numerical PASS",source_helpers=self.m.RELEASE_PINS,
            authority=dict(authority_kind="host_job_cleanup_observed",awmcp_terminal_reconstructed=False,
                           numerical_pass_claimed=False,original_failure_retained=True,references=c.HOST_RELEASE_REFS),
            stopped=[dict(state=dict(Running=False,Pid=0)) for _ in range(4)]))
        self.markers=[]
        for card,batches in c.GROUPS.items():
            job=self.m.spec(card,config["run_slug"]);ca=Path(job["job_root"])/"audit";cid=str(card)*64
            create=job["create_argv"];env=[create[i+1] for i,x in enumerate(create) if x=="-e"]
            labels=dict(create[i+1].split("=",1) for i,x in enumerate(create) if x=="--label")
            devices=[dict(PathOnHost=create[i+1].split(":")[0],PathInContainer=create[i+1].split(":")[1],
                          CgroupPermissions="rwm") for i,x in enumerate(create) if x=="--device"]
            mounts=[]
            for i,x in enumerate(create):
                if x=="--mount":
                    items=create[i+1].split(",");d=dict(v.split("=",1) for v in items if "=" in v)
                    mounts.append(dict(Type="bind",Source=d["source"],Destination=d["target"],RW="readonly" not in items))
            entry=dict(Id=cid,Image=self.d.IMAGE,Name="/"+job["container_name"],
                HostConfig=dict(Privileged=False,Memory=8*c.GIB,MemorySwap=8*c.GIB,NanoCpus=10**9,
                    NetworkMode="none",IpcMode="private",DeviceRequests=[],CapDrop=["ALL"],
                    SecurityOpt=["no-new-privileges"],Devices=devices),Mounts=mounts,
                Config=dict(Labels=labels,Env=env,WorkingDir=str(c.ROOT),Entrypoint=["/bin/bash"],
                            Cmd=["-c","exec sleep infinity"]),State=dict(Running=True,Pid=700+card))
            mapping=self.put(ca/"mapping.json",[entry])
            fresh=self.put(ca/"FRESH_PRELAUNCH.json",dict(protected="SYNTHETIC-protected",
                docker_info=dict(NCPU=8),available=48*c.GIB,joint_ram_required=40*c.GIB,
                free_disk_bytes=100*c.GIB,disk_required=12*c.GIB))
            cv=self.put(ca/"canary.json",dict(status="actual_canary_pass",expected_physical_card=card,
                create_argv_sha256=c.digest(c.canonical(create)),canary_program_sha256=self.helper.CANARY_SHA,
                synthetic=True))
            wait=dict(pid=800+card,start_ticks=100+card,cgroup="0::/docker/"+cid)
            waitref=self.put(ca/"WAIT_PID.json",wait)
            gate=self.m.gate_argv(job,cid,self.d);proc=dict(**wait,namespace_pids=[800+card,23],
                                                          argv=gate[gate.index(self.d.PYTHON):])
            rows={str(i):[] for i in range(8)};rows[str(card)]=[dict(pid=800+card)]
            obs=self.put(ca/"ACTUAL_GATE_NPU_PID.json",dict(process=proc,npu_smi=json.dumps(rows),
                physical_card=card,separate_canary_not_gate=True))
            image=self.put(ca/"image.json",dict(synthetic=True))
            ident=dict(schema="kvbp.middle-batch-launch-identity/v1",image_id=self.d.IMAGE,
                physical_devices=[card],logical_to_physical={"0":card},fresh_idle_verified=True,
                nonprivileged=True,source_canary_passed=True,memory_cgroup_bytes=8*c.GIB,
                protocol=self.runner.protocol(batches,card),library_sha256=self.split.LIBRARY_SHA,
                build_receipt_sha256=self.split.BUILD_SHA,meta_receipt_sha256=self.split.META_SHA,
                repo_sources=self.split.REPO_PINS,native_sources=self.split.NATIVE_PINS,
                driver_sources={"run.py":c.RUNNER_SHA},native_library_sha256=self.runner.NATIVE_SO_SHA,
                preflight_utc="2026-10-07T08:00:00+00:00",
                evidence=dict(mapping=mapping,host_processes=fresh,separate_canary=cv,image_sources=image,
                              parent_release=self.release,middle_meta14=c.META14,waiting_bash=waitref))
            ir=self.put(Path(job["launch_root"])/"identity.json",ident)
            meta=self.old.obj(self.sp["artifacts"]["meta"],self.read)
            report=dict(schema="kvbp.intermediate-native-gate/v1",
                status="intermediate_batches_kernel_native_eager_graph_pass",claim="kernel-only",
                npu_executed=True,serving_ready=False,performance_measurement_admitted=False,
                script_sha256=c.RUNNER_SHA,driver_sources={"run.py":c.RUNNER_SHA},launch_identity=ident,
                launch_identity_sha256=ir["sha256"],protocol=ident["protocol"],native_sources=self.split.NATIVE_PINS,
                cgroup=dict(bytes=8*c.GIB),runtime=dict(logical_device_count=1,logical_device=0,device_name="SYNTHETIC910B4",
                    torch=meta["torch"],torch_npu=meta["torch_npu"]),
                candidate_schema=meta["schema"],
                native_schema="npu_recurrent_gated_delta_rule beta scale actual_seq_lengths ssm_state_indices",
                frozen_receipts=dict(build_receipt_sha256=self.split.BUILD_SHA,meta_receipt_sha256=self.split.META_SHA,
                    library_sha256=self.split.LIBRARY_SHA,repo_sources=self.split.REPO_PINS,meta_is_not_npu_proof=True),
                loaded_libraries={"/kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so":self.split.LIBRARY_SHA,
                    self.runner.NATIVE_SO:self.runner.NATIVE_SO_SHA},created_ns=1791350401000000000,
                completed_ns=1791350501000000000,cases=[x for t in batches for x in cases(self.bridge,t)])
            # Bind timestamps to the actual synthetic preflight rather than a magic epoch.
            report["created_ns"]=int(datetime.fromisoformat(ident["preflight_utc"]).timestamp()*1e9)+1000000000
            report["completed_ns"]=report["created_ns"]+100000000000
            for k in ("native_schema","candidate_schema"):report[k+"_sha256"]=c.digest(report[k].encode())
            rr=self.put(Path(job["output_root"])/"gate/report.json",report)
            out=self.put(ca/"gate.stdout",b"SYNTHETIC gate output\n");err=self.put(ca/"gate.stderr",b"")
            entry["State"]=dict(Running=False,Pid=0)
            sr=self.put(ca/"cleanup/0001-stopped-inspect.stdout",[entry]);er=self.put(ca/"cleanup/0001-stopped-inspect.stderr",b"")
            self.put(ca/"cleanup/0001-stopped-inspect.receipt.json",dict(
                argv=["/usr/bin/docker","inspect",cid],command="/usr/bin/docker",cwd=str(c.ROOT),
                exit_code=0,error=None,automatic_retry=False,stdout=sr["path"],stderr=er["path"],
                stdout_sha256=sr["sha256"],stderr_sha256=er["sha256"]))
            child=self.put(ca/"CHILD.json",dict(argv=gate,cwd=str(c.ROOT),exit_code=0,stdout=out,stderr=err,
                report=rr,identity=ir,actual_gate_pid=obs,cleanup=dict(container_id=cid,stopped=True,retained=True,deleted=False),
                source_after=self.pins54,main_program_sha256=c.PROGRAM_SHA,middle_meta14=prereq,
                service_ready=False,performance=False))
            self.markers.append(dict(physical_card=card,batches=batches,child=child,report=rr))
        self.finish()
    @staticmethod
    def source(name):
        override=globals().get("NEW_SOURCE",{})
        return override[name] if name in override else (c.BASE/name).read_text()
    def _put(self,path,value):
        data=value if isinstance(value,bytes) else c.canonical(value)+b"\n"
        self.files[str(path)]=data;return dict(path=str(path),sha256=c.digest(data))
    def finish(self):
        self.authority["shards"]=self.markers
        complete=dict(cases=56,feedback_steps=8960,source_after=self.pins54,service_ready=False,performance=False)
        stdout="".join("MAIN_KVBUFFER_MIDDLE_SHARD "+json.dumps(x)+"\n" for x in self.markers)
        stdout+="MAIN_KVBUFFER_MIDDLE_COMPLETE "+json.dumps(complete)+"\n"
        self.authority["stdout"]=self.put("/synthetic/outer.stdout",stdout.encode())
        self.authority["stderr"]=self.put("/synthetic/outer.stderr",b"")
        r=dict(id=self.authority["operation_id"],state="completed",exitCode=0,error=None,cancelled=False,timedOut=False,
               command=self.authority["command"],args=self.authority["args"],cwd=self.authority["cwd"],stdout=stdout,stderr="")
        terminal=dict(schema="agentweb.operation/v1",kind="exec",operationId=r["id"],terminal=True,status="completed",
            succeeded=True,error=None,operation=dict(routeDecision="peer_direct",targetPeerId=c.PEER,fallbackUsed=False,
                                                     result=dict(record=r)),synthetic=True)
        self.authority["operation"]=self.put("/synthetic/original-terminal.json",terminal)
    def invoke(self):
        # Only the raw PID text decoder is a declared software stand-in. Actual schema,
        # immutable source, create geometry, numerical validator and command receipts execute.
        host=SimpleNamespace(parse_processes=lambda raw:{int(k):v for k,v in json.loads(raw).items()},
                             protected_fingerprint=lambda rows:"SYNTHETIC-protected")
        runtime=list(self.runtime);runtime[5]=host
        with patch.object(self.old,"sources",return_value=tuple(runtime)):
            return c.middle(self.authority,self.checked,self.packet,self.old,self.read,
                            lambda audit:[p for p in self.files if Path(p).parent==Path(audit) and p.endswith(".receipt.json")])

class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=Fixture()
    def fresh(self):return Fixture()
    def test_off_no_acquisition(self):
        with self.assertRaisesRegex(ValueError,"default OFF"):c.validate_complete({}, {},enabled=False)
        for m in (c,l,pair):
            out=io.StringIO()
            with redirect_stdout(out):self.assertEqual(m.main([]),0)
            self.assertIn("OFF",out.getvalue())
    def test_producer_shaped_full_middle_and_real_original_numerics(self):
        f=self.fresh();r=f.invoke()
        self.assertEqual((r["cases"],r["steps"]),(56,8960));self.assertEqual(len(r["details"]),4)
    def test_missing_source_raw_drift(self):
        f=self.fresh();f.files[f.authority["stdout"]["path"]]=b"drift"
        with self.assertRaisesRegex(ValueError,"byte drift"):f.invoke()
    def test_terminal_primary_flags_and_argv_rejected(self):
        for key,value in (("exitCode",1),("cancelled",True),("timedOut",True),("command","python"),("args",[])):
            f=self.fresh();t=c.obj(f.authority["operation"],f.read);t["operation"]["result"]["record"][key]=value
            f.authority["operation"]=f.put(f.authority["operation"]["path"],t)
            with self.subTest(key=key),self.assertRaises(ValueError):f.invoke()
    def test_duplicate_marker_and_group_cannot_fake_endpoints(self):
        for mutate in ("duplicate","fakegroup"):
            f=self.fresh()
            if mutate=="duplicate":f.markers[-1]=copy.deepcopy(f.markers[0])
            else:f.markers[0]["batches"]=[2,15]
            f.finish()
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):f.invoke()
    def test_numeric_original_threshold_and_raw_retained(self):
        for kind in ("state","raw","steps","logs"):
            f=self.fresh();mark=f.markers[0];r=c.obj(mark["report"],f.read)
            row=r["cases"][0]["steps"][0]
            if kind=="state":row["complete_state_l2"]=2.00001e-6
            if kind=="raw":row["raw_step"]["retained"]=True
            if kind=="steps":r["cases"][0]["steps"].pop()
            if kind=="logs":row["all_logs_bitwise_outside_new_U"]["k_log"]=False
            mark["report"]=f.put(mark["report"]["path"],r)
            child=c.obj(mark["child"],f.read);child["report"]=mark["report"]
            mark["child"]=f.put(mark["child"]["path"],child);f.finish()
            with self.subTest(kind=kind),self.assertRaises(ValueError):f.invoke()
    def test_source_after_alias_and_scope_rejected(self):
        for kind in ("source","scope","alias","argv"):
            f=self.fresh();mark=f.markers[0];child=c.obj(mark["child"],f.read)
            if kind=="source":child["source_after"].pop(next(iter(child["source_after"])))
            if kind=="scope":child["service_ready"]=True
            if kind=="alias":child["identity"]=f.markers[1]["report"]
            if kind=="argv":child["argv"][0]="docker"
            mark["child"]=f.put(mark["child"]["path"],child);f.finish()
            with self.subTest(kind=kind),self.assertRaises(ValueError):f.invoke()
    def test_fullT_original_validator_14_positive_and84_negative(self):
        v=self.base.bridge
        for b in range(2,16):
            r=dict(cases=cases(v,b));self.assertEqual(v.validate_cases(r,b),640)
            for kind in ("duplicate","step","state","untouched","PAD","raw"):
                q=copy.deepcopy(r)
                if kind=="duplicate":q["cases"][-1]=copy.deepcopy(q["cases"][0])
                if kind=="step":q["cases"][0]["steps"].pop()
                if kind=="state":q["cases"][0]["steps"][0]["complete_state_l2"]=2.0001e-6
                if kind=="untouched":q["cases"][0]["steps"][0]["untouched_slots_bitwise"]=False
                if kind=="PAD":q["cases"][0]["steps"][0]["active"]=0
                if kind=="raw":q["cases"][0]["steps"][0]["raw_step"]["retained"]=True
                with self.subTest(batch=b,kind=kind),self.assertRaises(ValueError):v.validate_cases(q,b)
    def test_launch_exact_refs_no_hidden_flag(self):
        f=self.base;pr={"path":"/synthetic/checked.json","sha256":"a"*64}
        inputs=dict(split_manifest=f.manifest,split_checked=dict(input_ref=f.config_ref,checked=f.joint_ref))
        ir={"path":"/synthetic/freshTP4.json","sha256":"b"*64}
        ident=dict(evidence=dict(all_T_kernel_prerequisite=pr),native_gate_kind="split-kernel-prerequisite",
                   formal_performance_authorized=False,diagnostic_scope="same-eager-P1-lifecycle-screen")
        argv=[]
        for n,r in (("manifest",f.manifest),("inputs",f.config_ref),("checked",f.joint_ref),("identity",ir)):
            argv+=["--"+n,r["path"],"--"+n+"-sha256",r["sha256"]]
        argv+=["--arm","candidate","--port","8231","--output-dir","/kvbuffer-results/new","--prepare-only"]
        self.assertEqual(l.binding(argv,inputs,pr,ident,ir,f.packet)["--arm"],"candidate")
        for tail in (["--prepare-only"],["--enforce-eager"],["--identity","x"]):
            with self.subTest(tail=tail),self.assertRaises(ValueError):l.flags(argv+tail)
        ident["evidence"]["all_T_kernel_prerequisite"]={"path":"/wrong","sha256":"a"*64}
        with self.assertRaises(ValueError):l.binding(argv,inputs,pr,ident,ir,f.packet)
    def test_pair_preserves_original_scopes(self):
        checked={"path":"/synthetic/allT.json","sha256":"a"*64}
        split={"path":"/synthetic/split.json","sha256":"b"*64}
        manifest={"path":"/synthetic/manifest.json","sha256":"c"*64}
        inputs=dict(split_checked=dict(checked=split),split_manifest=manifest)
        ids={k:dict(ref={"path":"/synthetic/"+k,"sha256":str(i)*64},
                    value=dict(evidence=dict(all_T_kernel_prerequisite=checked))) for i,k in enumerate(("dense","candidate"),1)}
        arms={k:dict(schema="kvbp.service-arm/v1",arm=k,prepare_only=False,identity_sha256=ids[k]["ref"]["sha256"],
              checked_split_prerequisite=split,consumer_source_manifest=manifest,native_gate_kind="split-kernel-prerequisite",
              formal_performance_authorized=False,task_accuracy_verified=False) for k in ids}
        pair.check_bindings(arms,ids,checked,inputs)
        arms["candidate"]["formal_performance_authorized"]=True
        with self.assertRaises(ValueError):pair.check_bindings(arms,ids,checked,inputs)
    def test_nonfinite_and_scope_flags_no_expansion(self):
        with self.assertRaises(ValueError):c.clean(b'{"metric":1e309}')
        with self.assertRaises(ValueError):c.false_scope(dict.fromkeys(c.FALSE_SCOPE,True))
        c.false_scope(dict.fromkeys(c.FALSE_SCOPE,False))
    def test_byte_exact_legacy_mount_helpers_private_globals(self):
        f=self.base;helpers=l.mounts(f.packet,f.old)
        entry=dict(Mounts=[dict(Type="bind",Source=str(c.ROOT),Destination=str(c.ROOT),RW=False)])
        helpers.mount_binding(entry,str(c.PROGRAM))
        with self.assertRaises(ValueError):helpers.mount_binding(entry,"/cache/unmounted")
    def test_delegate_is_actual_old_strict_validator_not_testing(self):
        source=Fixture.source("contract.py");tree=ast.parse(source)
        fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="validate_complete")
        calls=[x for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=="validate"]
        self.assertEqual(len(calls),1)
        self.assertEqual({k.arg:ast.literal_eval(k.value) for k in calls[0].keywords if k.arg=="enabled"},{"enabled":True})
        self.assertNotIn("testing", {k.arg for k in calls[0].keywords})
    def test_no_device_acquisition_in_new_sources(self):
        for name in ("contract.py","launch.py","pair.py"):
            s=Fixture.source(name)
            self.assertNotIn("import torch",s);self.assertNotIn("torch.ops",s.replace("# No torch.ops reassignment",""))
            self.assertNotIn("docker create",s)
            tree=ast.parse(s)
            imports={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
            self.assertNotIn("runpy",imports)
if __name__=="__main__":unittest.main()
