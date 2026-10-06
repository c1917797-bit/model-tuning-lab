"""Producer-shaped SYNTHETIC authority tests; no Torch/device/load/subprocess launches."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import validator as v

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "SOURCE_MANIFEST.json"
NATIVE_SNAPSHOT = "/cache/cch/qwen36-damp-20261006/runtime-native-library-snapshot-v1/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"

class Fixture:
    def __init__(self):
        self.files = {}
        self.serial = 0
        self.manifest = v.clean_json(MANIFEST.read_bytes())
        self.sources = {p:Path(p).read_bytes() for p in self.manifest["frozen_dependencies"]}
        self.sources.update({str(HERE/name):(HERE/name).read_bytes() for name in self.manifest["files"]})
        self.sources[str(MANIFEST)] = MANIFEST.read_bytes()
        for value in self.manifest["artifacts"].values():
            self.sources[value["path"]] = Path(value["path"]).read_bytes()
        # This is an actual stopped-image byte snapshot, not a mapped NPU result.
        self.sources[NATIVE_SNAPSHOT] = Path(NATIVE_SNAPSHOT).read_bytes()
        self.native = dict(path=NATIVE_SNAPSHOT,sha256=v.NATIVE_SHA)
        self.producer_path = "/synthetic/software-only/producer.py"
        self.files[self.producer_path] = b"# explicitly synthetic source, never actual launch\n"
        self.producer = {self.producer_path:v.digest(self.files[self.producer_path])}
        self.b1 = self.make(1,5,"a"*64,"exec-synthetic-b1")
        self.b16 = self.make(16,6,"b"*64,"exec-synthetic-b16")
        self.source_manifest = dict(path=str(MANIFEST),sha256=v.digest(MANIFEST.read_bytes()))

    def read(self,path):
        return self.files[path] if path in self.files else self.sources[path]

    def put(self,value,name=None):
        self.serial += 1
        path = "/synthetic/software-only/" + (name or "blob%d"%self.serial)
        data = value if isinstance(value,bytes) else v.canonical(value)+b"\n"
        self.files[path] = data
        return dict(path=path,sha256=v.digest(data))

    def decoded(self,r):
        return v.clean_json(self.read(r["path"]))

    def protocol(self,b,card):
        return dict(batch=b,physical_device=card,logical_device=0,slots=b+3,eager_trials=1,graph_trials=3,
                    steps_per_case=160,feedback=True,output_limit=.00303,complete_and_per_head_l2_limit=2e-6,
                    graph_active_schedule=[0,1,3,7,12,15,16,16] if b==16 else [1],
                    reset_steps=[64,112],required_flushes=True,retry="none",
                    scope="kernel-only-not-model-E2E-or-task-accuracy")

    def cases(self,b):
        result = []
        for mode,trial in v.MODES:
            lengths=[0]*(b+3)
            c=dict(batch=b,mode=mode,trial=trial,status="passed",steps=[],merges=0,resets=2,
                   max_output_error=0.,max_state_l2=0.,max_head_l2=0.)
            for i in range(160):
                active=(0,1,3,7,12,15,16,16)[i%8] if b==16 and mode=="graph" else b
                reset=(i//16)%(b+3) if i in (64,112) else None
                if reset is not None:
                    lengths[reset]=0
                for token in range(active):
                    slot=(token+i)%(b+3)
                    if lengths[slot]==15:
                        lengths[slot]=0;c["merges"]+=1
                    else:
                        lengths[slot]+=1
                row=dict(step=i+1,active=active,reset_slot=reset,output_error=0.,complete_state_l2=0.,
                         max_per_head_l2=0.,all_logs_bitwise_outside_new_U=dict.fromkeys(v.LOGS,True),
                         raw_step=dict(file="raw-step-b%d-%s-t%d-step%d.pt"%(b,mode,trial,i+1),
                                       step=i+1,retained=False,bytes=4096,
                                       sha256=v.digest(("synthetic raw checkpoint %d/%s/%d/%d"%(b,mode,trial,i)).encode())),
                         passed=True,**dict.fromkeys(v.GUARDS,True))
                c["steps"].append(row)
            result.append(c)
        return result

    def make(self,b,card,cid,opid):
        deps=self.manifest["frozen_dependencies"]
        prefix=v.PROJECT+"/tools/split_gate_v1/"
        drivers={k[len(prefix):]:s for k,s in deps.items() if k.startswith(prefix)}
        inspect=self.put([dict(Id=cid,Image=v.IMAGE,HostConfig=dict(Privileged=False,Memory=v.CGROUP,
                         MemorySwap=v.CGROUP,Devices=[dict(PathOnHost="/dev/davinci%d"%card,
                         PathInContainer="/dev/davinci%d"%card,CgroupPermissions="rwm")]))])
        proof=self.put(dict(schema="kvbp.split-main-device-binding/v1",container_id=cid,image_id=v.IMAGE,
                       physical_devices=[card],logical_to_physical={"0":card},same_process_pid=777,
                       preflight_utc="2026-10-06T19:00:00Z",evidence_kind="synthetic-software-contract",
                       raw_refs={k:self.put(("SYNTHETIC "+k).encode()) for k in
                                 ("canary","mapping","host_processes","cgroup")}))
        ident=self.put(dict(schema="kvbp.split-launch-identity/v1",image_id=v.IMAGE,physical_devices=[card],
                       logical_to_physical={"0":card},fresh_idle_verified=True,nonprivileged=True,
                       source_canary_passed=True,memory_cgroup_bytes=v.CGROUP,protocol=self.protocol(b,card),
                       library_sha256=v.LIBRARY,build_receipt_sha256=v.BUILD,meta_receipt_sha256=v.META,
                       repo_sources=self.manifest["repo_pins"],native_sources=self.manifest["native_pins"],
                       driver_sources=drivers,preflight_utc="2026-10-06T19:00:00Z",
                       evidence=dict(device_proof=proof,container_inspect=inspect)))
        meta=v.clean_json(self.read(self.manifest["artifacts"]["meta"]["path"]))
        native_schema="_C_ascend::npu_recurrent_gated_delta_rule(Tensor query, Tensor key, Tensor value, Tensor state, *, Tensor beta, float scale, Tensor actual_seq_lengths, Tensor ssm_state_indices, Tensor? g=None) -> Tensor"
        r=dict(schema="kvbp.split-native-gate/v1",status="single_batch_kernel_native_eager_graph_pass",
               claim="kernel-only",created_ns=1791313210000000000,completed_ns=1791313220000000000,
               script_sha256=drivers["run.py"],driver_sources=drivers,launch_identity=self.decoded(ident),
               launch_identity_sha256=ident["sha256"],protocol=self.protocol(b,card),
               frozen_receipts=dict(build_receipt_sha256=v.BUILD,meta_receipt_sha256=v.META,
                                    library_sha256=v.LIBRARY,repo_sources=self.manifest["repo_pins"],
                                    meta_is_not_npu_proof=True),
               native_sources=self.manifest["native_pins"],cgroup=dict(path="/sys/fs/cgroup/memory.max",bytes=v.CGROUP),
               cases=self.cases(b),candidate_schema=meta["schema"],native_schema=native_schema,
               candidate_schema_sha256=v.digest(meta["schema"].encode()),native_schema_sha256=v.digest(native_schema.encode()),
               loaded_libraries={"/kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so":v.LIBRARY,
                                 v.NATIVE_PATH:v.NATIVE_SHA},
               runtime=dict(torch="2.10.0+cpu",torch_npu="2.10.0.post4",logical_device_count=1,
                            logical_device=0,device_name="SYNTHETIC_NOT_DEVICE_PROOF"))
        report=self.put(r)
        c=self.put(dict(schema="kvbp.split-child-execution/v1",evidence_kind="synthetic-software-contract",
                   report=report,identity=ident,image_identity_path="/kvbuffer-results/b%d.identity.json"%b,
                   image_output_dir="/kvbuffer-results/b%d"%b,producer_sources=self.producer,
                   container_inspect=inspect,device_proof=proof,native_library=self.native,
                   execution=dict(command="/usr/bin/docker",cwd=v.ROOT,exit_code=0,error=None,
                                  cancelled=False,timed_out=False,
                                  args=["exec","-e","ASCEND_RT_VISIBLE_DEVICES=0",cid,v.IMAGE_PYTHON,"-B",v.RUNNER,
                                        "--batch",str(b),"--physical-device",str(card),"--identity",
                                        "/kvbuffer-results/b%d.identity.json"%b,"--output-dir","/kvbuffer-results/b%d"%b],
                                  stdout=self.put(b"SYNTHETIC child stdout\n"),stderr=self.put(b""))))
        stdout=v.PREFIX+json.dumps(dict(report=report,identity=ident,child=c))+"\n"
        record=dict(id=opid,state="completed",command="/usr/bin/python3",args=["-B",self.producer_path],
                    cwd=v.ROOT,exitCode=0,error=None,cancelled=False,timedOut=False,stdout=stdout,stderr="")
        terminal=self.put(dict(operationId=opid,ok=True,routeDecision="peer_direct",targetPeerId="SYNTHETIC-peer",
                              result=dict(record=record,ok=True,state="completed")))
        return dict(report=report,identity=ident,operation=terminal,stdout=self.put(stdout.encode()),stderr=self.put(b""),
                    child=c,peer_id="SYNTHETIC-peer",operation_id=opid,command=record["command"],
                    args=record["args"],cwd=v.ROOT,producer_sources=self.producer)

    def refresh(self,a,kind,value):
        a[kind]=self.put(value)
        c=self.decoded(a["child"]);c.update(report=a["report"],identity=a["identity"])
        a["child"]=self.put(c)
        d=self.decoded(a["operation"])
        record=(d.get("operation",d).get("result",{}))["record"]
        stdout=v.PREFIX+json.dumps({k:a[k] for k in ("report","identity","child")})+"\n"
        record["stdout"]=stdout
        a["operation"]=self.put(d);a["stdout"]=self.put(stdout.encode())

    def result(self,**kw):
        return v.validate_complete(self.b1,self.b16,self.source_manifest,self.read,enabled=True,testing=True,**kw)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=Fixture()
    def setUp(self):
        self.f=copy.deepcopy(self.original)
    def reject_report(self,mutate):
        a=self.f.b1;r=self.f.decoded(a["report"]);mutate(r);self.f.refresh(a,"report",r)
        with self.assertRaises((ValueError,KeyError)):
            self.f.result()
    def test_producer_shaped_positive_is_software_only(self):
        result=self.f.result()
        self.assertEqual((result["unique_cases"],result["changing_feedback_steps"]),(8,1280))
        self.assertEqual(result["status"],"synthetic_contract_pass")
        self.assertFalse(result["npu_verified"]);self.assertFalse(result["service_ready"])
        self.assertFalse(result["matched_e2e_verified"])
        self.assertEqual(result["runs"][0]["raw_authority"],self.f.b1)
    def test_default_off_and_no_synthetic_actual_promotion(self):
        with self.assertRaises(ValueError):
            v.validate_complete(self.f.b1,self.f.b16,self.f.source_manifest,self.f.read)
        with self.assertRaises(ValueError):
            v.validate_complete(self.f.b1,self.f.b16,self.f.source_manifest,self.f.read,enabled=True)
    def test_old_consumer_rejects_new_descriptor(self):
        src=self.f.sources[v.PROJECT+"/tools/service/contract.py"]
        namespace={"__name__":"_source_checked_old_service"}
        exec(compile(src,"old-service-contract","exec"),namespace)
        with self.assertRaises(ValueError):
            namespace["validate_native_gate"](self.f.result())
    def test_partial_duplicate_mode_and_step(self):
        self.reject_report(lambda r:r["cases"].pop())
        self.setUp();self.reject_report(lambda r:r["cases"].__setitem__(1,copy.deepcopy(r["cases"][0])))
        self.setUp();self.reject_report(lambda r:r["cases"][0]["steps"][3].__setitem__("step",3))
    def test_failure_or_pending_raw_never_promoted(self):
        self.reject_report(lambda r:r.__setitem__("status","failed"))
        self.setUp();self.reject_report(lambda r:r["cases"][0].__setitem__("pending_raw_step",{}))
        self.setUp();self.reject_report(lambda r:r["cases"][0]["steps"][1]["raw_step"].__setitem__("retained",True))
    def test_numeric_finite_and_every_guard(self):
        for field in ("output_error","complete_state_l2","max_per_head_l2"):
            self.setUp();self.reject_report(lambda r:r["cases"][0]["steps"][7].__setitem__(field,1.))
        for field in v.GUARDS:
            self.setUp();self.reject_report(lambda r:r["cases"][0]["steps"][5].__setitem__(field,False))
        self.setUp();self.reject_report(lambda r:r["cases"][0]["steps"][5].__setitem__("max_per_head_l2",None))
        with self.assertRaises(ValueError):v.clean_json(b'{"metric":NaN}')
    def test_reset_flush_active_and_log(self):
        self.reject_report(lambda r:r["cases"][0].__setitem__("merges",0))
        self.setUp();self.reject_report(lambda r:r["cases"][0]["steps"][64].__setitem__("reset_slot",None))
        self.setUp();self.reject_report(lambda r:r["cases"][0]["steps"][0].__setitem__("active",0))
        self.setUp();self.reject_report(lambda r:r["cases"][0]["steps"][3]["all_logs_bitwise_outside_new_U"].__setitem__("u_log",False))
    def test_original_byte_source_and_schema_drift(self):
        path=self.f.b1["report"]["path"];self.f.files[path]+=b" "
        with self.assertRaises(ValueError):self.f.result()
        self.setUp();path=v.PROJECT+"/tools/service/contract.py";self.f.sources[path]+=b"\n"
        with self.assertRaises(ValueError):self.f.result()
        self.setUp();self.reject_report(lambda r:r.__setitem__("candidate_schema","fake"))
    def test_missing_new_metadata_explicitly_rejected(self):
        a=self.f.b1;c=self.f.decoded(a["child"]);c.pop("device_proof")
        self.f.refresh(a,"child",c)
        with self.assertRaises((ValueError,KeyError)):self.f.result()
    def test_terminal_original_record_not_outer_ok(self):
        for patch in (dict(state="running"),dict(exitCode=1,error="exit code"),dict(timedOut=True),dict(cancelled=True)):
            self.setUp();a=self.f.b1;d=self.f.decoded(a["operation"]);d["result"]["record"].update(patch)
            a["operation"]=self.f.put(d)
            with self.assertRaises(ValueError):self.f.result()
    def test_operation_get_shape_and_peer_argv_raw_io(self):
        a=self.f.b1;d=self.f.decoded(a["operation"])
        projected=dict(terminal=True,succeeded=True,operation=dict(routeDecision=d["routeDecision"],
                        targetPeerId=d["targetPeerId"],result=d["result"]))
        a["operation"]=self.f.put(projected)
        self.assertEqual(self.f.result()["changing_feedback_steps"],1280)
        self.setUp();self.f.b1["peer_id"]="other"
        with self.assertRaises(ValueError):self.f.result()
        self.setUp();self.f.b1["args"]=["invented"]
        with self.assertRaises(ValueError):self.f.result()
        self.setUp();self.f.b1["stderr"]=self.f.put(b"not original")
        with self.assertRaises(ValueError):self.f.result()
    def test_native_loaded_binding_and_two_distinct_jobs(self):
        self.reject_report(lambda r:r["loaded_libraries"].pop(v.NATIVE_PATH))
        self.setUp();self.f.b16=copy.deepcopy(self.f.b1)
        with self.assertRaises(ValueError):self.f.result()
    def test_container_overlap_and_exact_original_inner_cli(self):
        a=self.f.b1;c=self.f.decoded(a["child"]);ins=self.f.decoded(c["container_inspect"])
        ins[0]["HostConfig"]["Devices"].append(dict(PathOnHost="/dev/davinci0"))
        c["container_inspect"]=self.f.put(ins);self.f.refresh(a,"child",c)
        with self.assertRaises(ValueError):self.f.result()
        self.setUp();a=self.f.b1;c=self.f.decoded(a["child"]);c["execution"]["args"][-1]="../override"
        self.f.refresh(a,"child",c)
        with self.assertRaises(ValueError):self.f.result()
    def test_old_split_reports_identity_preserved_without_rewrite(self):
        original=copy.deepcopy(self.f.files)
        self.f.result()
        self.assertEqual(self.f.files,original)
if __name__=="__main__":
    unittest.main()
