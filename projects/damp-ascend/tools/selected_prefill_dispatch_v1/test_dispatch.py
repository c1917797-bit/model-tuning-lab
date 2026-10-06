"""Stdlib synthetic contracts ONLY; no Docker/Torch/NPU or real authority."""
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import controller as c
import child_shim as shim

def fixture_entry(stage="isolated",card=4):
    return c.plan("software",stage,card,{"actual_snapshot_manifests":[]},
                  "synthetic-bootstrap-no-execution")

def actual(entry):
    argv=entry["docker_create_argv"];idx=argv.index("--entrypoint")
    labels={argv[i+1].split("=",1)[0]:argv[i+1].split("=",1)[1]
            for i,x in enumerate(argv) if x=="--label"}
    env=[argv[i+1] for i,x in enumerate(argv) if x=="-e"]
    return {"Id":"a"*64,"Name":"/"+entry["container_name"],"Image":c.IMAGE,
      "HostConfig":{"Privileged":False,"NetworkMode":"none","IpcMode":"private",
        "DeviceRequests":[],"Memory":c.MEMORY,"MemorySwap":c.MEMORY,"NanoCpus":10**9,
        "CapDrop":["ALL"],"SecurityOpt":["no-new-privileges"],
        "Devices":[{"PathOnHost":"/dev/davinci%d"%entry["physical_card"],"PathInContainer":"/dev/davinci0"}]+
                  [{"PathOnHost":"/dev/"+n,"PathInContainer":"/dev/"+n}
                   for n in ("davinci_manager","devmm_svm","hisi_hdc")]},
      "Config":{"Labels":labels,"Env":env,"Entrypoint":["/bin/bash"],
                "Cmd":argv[idx+3:],"WorkingDir":str(c.REPO)},
      "Mounts":[{"Type":"bind","Source":p,"Destination":p,"RW":rw}
                for p,rw in entry["mounts"].items()]}

class FakeProcess:
    def __init__(self,done=False):
        self.returncode=0 if done else None
        self.calls=0;self.terminated=False;self.killed=False
    def poll(self):
        self.calls+=1
        if self.returncode is None and self.calls>=2:self.returncode=0
        return self.returncode
    def terminate(self):self.terminated=True;self.returncode=-15
    def kill(self):self.killed=True;self.returncode=-9
    def wait(self,timeout=None):return self.returncode

class InfiniteProcess(FakeProcess):
    def poll(self):return self.returncode

class Contracts(unittest.TestCase):
    def test_01_all_single_card_stages(self):
        for stage in ("isolated","native_feedback"):
            for card in range(4,8):
                e=fixture_entry(stage,card)
                self.assertFalse(e["launchable"])
                self.assertEqual(e["batches"],[1,16]);self.assertEqual(e["steps"],160)
                devices=[e["docker_create_argv"][i+1] for i,x in enumerate(e["docker_create_argv"]) if x=="--device"]
                self.assertEqual(devices[0],"/dev/davinci%d:/dev/davinci0"%card)
                self.assertEqual(len(devices),4)
                self.assertEqual([p for p,rw in e["mounts"].items() if rw],[e["stage_output"]])
                self.assertFalse(e["mounts"][e["audit"]])
                self.assertNotIn(e["root"],e["mounts"])
    def test_02_reject_bad_card_stage_id(self):
        for stage,card,rid in (("isolated",3,"v1"),("isolated",8,"v1"),("meta",4,"v1"),
                               ("isolated",True,"v1"),("isolated",4,"../x"),("isolated",4,"bad space")):
            with self.assertRaises(RuntimeError):c.plan(rid,stage,card,{"actual_snapshot_manifests":[]},"x")
    def test_03_exact_inspect_positive(self):
        for stage in ("isolated","native_feedback"):
            e=fixture_entry(stage);a=actual(e)
            self.assertIs(c.inspect_owned(a,e,"a"*64),a)
    def test_04_inspect_rejects_each_mismatch(self):
        e=fixture_entry()
        mutations=[
            lambda a:a.update(Id="b"*64),lambda a:a.update(Name="/foreign"),
            lambda a:a.update(Image="sha256:"+"b"*64),
            lambda a:a["HostConfig"].update(Privileged=True),
            lambda a:a["HostConfig"].update(NetworkMode="host"),
            lambda a:a["HostConfig"].update(IpcMode="host"),
            lambda a:a["HostConfig"].update(MemorySwap=2*c.MEMORY),
            lambda a:a["HostConfig"].update(NanoCpus=2*10**9),
            lambda a:a["HostConfig"].update(DeviceRequests=[{}]),
            lambda a:a["HostConfig"].update(CapDrop=[]),
            lambda a:a["HostConfig"].update(SecurityOpt=[]),
            lambda a:a["HostConfig"]["Devices"][0].update(PathOnHost="/dev/davinci0"),
            lambda a:a["HostConfig"]["Devices"].append({"PathOnHost":"/dev/davinci1","PathInContainer":"/dev/davinci1"}),
            lambda a:a["Config"]["Labels"].update({"model-tuning-lab.owner":"foreign"}),
            lambda a:a["Config"].update(WorkingDir="/tmp"),
            lambda a:a["Config"].update(Cmd=["sleep","infinity"]),
            lambda a:a["Config"].update(Env=[]),
            lambda a:a["Mounts"][0].update(RW=True),
            lambda a:a["Mounts"].append({"Type":"bind","Source":"/tmp","Destination":"/tmp","RW":True}),
            lambda a:a["Mounts"][0].update(Source="/other"),
            lambda a:a["Mounts"][0].update(Type="volume")]
        for change in mutations:
            a=actual(e);change(a)
            with self.assertRaises(RuntimeError):c.inspect_owned(a,e,"a"*64)
    def test_05_snapshot_only_ro(self):
        e=c.plan("v1","native_feedback",7,{"actual_snapshot_manifests":[
            {"path":"/cache/cch/a/MANIFEST.json","sha256":"a"*64}]},"x")
        self.assertFalse(e["mounts"]["/cache/cch/a"])
    def test_06_explicit_frozen_cli(self):
        for stage in ("isolated","native_feedback"):
            e=fixture_entry(stage);args=c.gate_args(e,Path(e["audit"])/"proof.json")
            self.assertEqual(args[0],str(c.GATE/"run.py"))
            self.assertEqual(args[args.index("--batches")+1:args.index("--batches")+3],["1","16"])
            self.assertEqual(args.count("--execute"),1)
            if stage=="native_feedback":
                self.assertIn("--reference-library",args);self.assertIn("--decode-library",args)
            else:self.assertNotIn("--decode-library",args)
    def test_07_child_actual_docker_command(self):
        e=fixture_entry("native_feedback",7)
        args=c.shim_argv(e,"a"*64,"bootstrap",Path(e["audit"])/"proof.json","b"*64)
        self.assertEqual(args[:4],["docker","exec","-e","DAMP_ENABLE_NATIVE_REFERENCE=1"])
        self.assertIn("a"*64,args);self.assertIn(str(c.GATE/"run.py"),args)
        self.assertEqual(args.count("--stage"),1);self.assertEqual(args.count("--"),1)
    def test_08_cutoff_unchanged(self):
        with self.assertRaises(RuntimeError):c.deadline(now=datetime(2026,10,7,8,48,3,tzinfo=timezone.utc))
        self.assertGreater(c.deadline(3600,datetime(2026,10,6,tzinfo=timezone.utc)),3600)
    def test_09_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"receipt.json";c.write(p,{"actual":"synthetic-fixture"})
            with self.assertRaises(FileExistsError):c.write(p,{"actual":"not-allowed"})
    def test_10_nonfinite_and_duplicate_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x"
            p.write_text('{"a":NaN}')
            with self.assertRaises(ValueError):c.read(p)
            p.write_text('{"a":1,"a":2}')
            with self.assertRaises(RuntimeError):c.read(p)
    def run_phase(self,proc,monitor=lambda:None,timeout=1):
        with tempfile.TemporaryDirectory() as d:
            def popen(argv,**kwargs):
                self.assertEqual(kwargs["cwd"],c.REPO)
                kwargs["stdout"].write(b"synthetic stdout\n")
                kwargs["stderr"].write(b"synthetic stderr\n")
                return proc
            with patch.object(c.subprocess,"Popen",side_effect=popen),patch.object(c.time,"sleep"),patch.object(c,"deadline"):
                row=c.phase(["synthetic-owned-exec-client"],Path(d),monitor,timeout)
            self.assertEqual(json.loads((Path(d)/"EXECUTION.json").read_text()),row)
            return row
    def test_11_real_completion_branch_fixture(self):
        p=FakeProcess()
        row=self.run_phase(p)
        self.assertEqual(row["state"],"completed");self.assertEqual(row["returncode"],0)
        self.assertFalse(row["timed_out"]);self.assertFalse(row["cancelled"])
        self.assertIsNone(row["error"]);self.assertIn("synthetic stdout",row["stdout"])
    def test_12_timeout_derives_flags(self):
        p=InfiniteProcess();row=self.run_phase(p,timeout=0)
        self.assertEqual(row["state"],"timeout");self.assertTrue(row["timed_out"])
        self.assertFalse(row["cancelled"]);self.assertTrue(p.terminated)
        self.assertIn("TimeoutError",row["error"])
    def test_13_cancel_derives_flags(self):
        p=InfiniteProcess()
        def cancel():raise c.CancelledRun("synthetic cancel branch")
        row=self.run_phase(p,cancel)
        self.assertEqual(row["state"],"cancelled");self.assertTrue(row["cancelled"])
        self.assertFalse(row["timed_out"]);self.assertTrue(p.terminated)
    def test_14_monitor_error_original_preserved(self):
        p=InfiniteProcess()
        def bad():raise ValueError("ORIGINAL monitor")
        row=self.run_phase(p,bad)
        self.assertEqual(row["state"],"failed");self.assertIn("ORIGINAL monitor",row["error"])
        self.assertFalse(row["cancelled"]);self.assertFalse(row["timed_out"])
    def test_15_popen_failure_preserved(self):
        with tempfile.TemporaryDirectory() as d,patch.object(c.subprocess,"Popen",side_effect=OSError("ORIGINAL Popen")):
            row=c.phase(["synthetic"],Path(d),lambda:None)
        self.assertIsNone(row["returncode"]);self.assertEqual(row["state"],"failed")
        self.assertIn("ORIGINAL Popen",row["error"])
    def test_16_negative_exit_not_success(self):
        p=FakeProcess(done=True);p.returncode=9
        row=self.run_phase(p)
        self.assertEqual(row["state"],"completed");self.assertEqual(row["returncode"],9)
        self.assertIsNone(row["error"])
    def test_17_parent_failed_capture_still_terminal_not_promoted(self):
        f=c.load("_selected_test_float",c.REPO/next(iter(c.REUSED)))
        h=SimpleNamespace(PARENT_OPERATION="exec-0000000000000455",PARENT_PEER="peer")
        r={"id":h.PARENT_OPERATION,"lane":"job","state":"completed","exitCode":7,"cancelled":False,
           "timedOut":False,"error":None,"command":"/usr/bin/python3","cwd":str(c.REPO)}
        raw={"operationId":h.PARENT_OPERATION,"terminal":True,"operation":{"routeDecision":"peer_direct",
             "targetPeerId":"peer","result":{"found":True,"ok":True,"lane":"job","state":"completed","record":r}}}
        row=f.terminal(raw,h);self.assertFalse(row["capture_success"]);self.assertEqual(row["exit_code"],7)
        raw["terminal"]=False
        with self.assertRaises(RuntimeError):f.terminal(raw,h)
    def test_18_maps_are_same_process_not_file_presence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"not_loaded.so";p.write_bytes(b"synthetic binary")
            with patch.object(c,"expected_libraries",return_value={str(p):c.sha(p)}):
                row=shim.observation("isolated",{})
            self.assertEqual(row["loaded_libraries"],{})
    def test_19_no_native_source_claim_for_isolated(self):
        row=shim.observation("isolated",{"actual_image_sources":{"/nonexistent":"a"*64}})
        self.assertEqual(row["runtime_image_sources"],{})
        self.assertIsNone(row["runtime"])
    def test_20_native_missing_bytes_is_secondary_not_PASS(self):
        with patch.object(c,"expected_libraries",return_value={}):
            row=shim.observation("native_feedback",{"actual_image_sources":{"/nonexistent":"a"*64}})
        self.assertEqual(row["runtime_image_sources"],{})
        self.assertTrue(row["secondary_errors"])
    def test_21_before_Torch_cli_unchanged_source_contract(self):
        source=(HERE/"child_shim.py").read_text()
        self.assertIn("runner.admission(args)",source)
        self.assertNotIn("MagicMock",source);self.assertNotIn("torch.ops",source)
        self.assertIn('runner=c.load("run"',source)
    def test_22_source_default_OFF_and_old_byte_closure(self):
        row=c.packet();prepared=c.closure()
        self.assertFalse(row["default_enabled"]);self.assertEqual(len(prepared[0]["actual_image_sources"]),23)
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test_23_main_default_plan_no_Docker_calls(self):
        with patch.object(c.subprocess,"Popen",side_effect=AssertionError("no Popen")),\
             patch.object(c.subprocess,"run",side_effect=AssertionError("no subprocess")):
            self.assertEqual(c.main(["--stage","native_feedback","--physical-card","7"]),0)
    def test_24_execute_requires_opt_in_before_helpers(self):
        with patch.dict(c.os.environ,{},clear=True),patch.object(c,"closure",side_effect=AssertionError("no closure")):
            with self.assertRaises(RuntimeError):c.main(["--execute"])
    def test_25_marker_single_in_controller_source(self):
        source=(HERE/"controller.py").read_text()
        self.assertEqual(source.count('print("MAIN_SELECTED_PREFILL_CHILD "'),1)
        self.assertNotIn("operation_cancel",source)
        self.assertNotIn('["docker","rm"',source)
        self.assertNotIn("killall",source)
    def test_26_kernel_oracle_not_rewritten(self):
        source=(HERE/"child_shim.py").read_text()
        self.assertNotIn("fraction_locator",source);self.assertNotIn("pack_value_major",source)
        self.assertIn("runner.main(argv[1:])",source)
        self.assertIn("gate_returncode=code",source)
    def test_27_nullable_child_not_promoted(self):
        e=fixture_entry()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);e["gate_out"]=str(root/"missing");e["observation"]=str(root/"missing.json")
            proof=root/"proof.json";c.write(proof,{"synthetic_fixture":True})
            row=c.child_receipt(e,"a"*64,{"state":"failed","returncode":None}, {},None,proof,
                                {"sources":{"controller.py":"b"*64}})
            self.assertIsNone(row["report"]);self.assertIsNone(row["runtime"])
            self.assertIsNone(row["same_process_observation"])
            self.assertFalse(row["serving_ready"]);self.assertFalse(row["performance_measurement_admitted"])
    def test_28_success_flags_not_override_false_scope(self):
        e=fixture_entry()
        for name in ("state","returncode","error","cancelled","timed_out","secondary_errors"):
            execution={"state":"completed","returncode":0,"error":None,"cancelled":False,
                       "timed_out":False,"secondary_errors":[]}
            execution[name]={"state":"failed","returncode":7,"error":"bad","cancelled":True,
                             "timed_out":True,"secondary_errors":["bad"]}[name]
            with self.assertRaises(RuntimeError):
                c.validate_stage({}, {},execution,e,{},None,None,1,2)
    def test_29_raw_after_error_does_not_replace_dispatch(self):
        p=InfiniteProcess()
        def bad():raise ValueError("dispatch-origin")
        row=self.run_phase(p,bad)
        self.assertIn("dispatch-origin",row["error"])
        self.assertIn("stderr",row)
        self.assertGreaterEqual(row["completed_ns"],row["started_ns"])
    def test_30_actual_reference_hash_and_unchanged_deadline(self):
        self.assertEqual(c.REFERENCE_SHA,"853f655c45c11cb5de5a1b0810c9a8850c0b66aea4c9aa049e01ac89f1aeccc8")
        self.assertEqual(c.DEADLINE,"2026-10-07T08:48:03Z")

    def shim_fixture(self,runner,observation_row=None):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);output=root/"selected-prefill-dispatch-software-isolated"/"stage-output"
            output.mkdir(parents=True)
            args=SimpleNamespace(out=output/"isolated",stage="isolated")
            runtime={"sources":{},"dependencies":{}}
            patches=[patch.object(c,"ROOT",root),patch.object(c,"packet",return_value={}),
                     patch.object(shim,"image_admission",return_value=(runner,args,runtime)),
                     patch.object(c,"expected_libraries",return_value={})]
            if observation_row is not None:
                patches.append(patch.object(shim,"observation",return_value=observation_row))
            from contextlib import ExitStack
            with ExitStack() as stack:
                for p in patches:stack.enter_context(p)
                code=shim.run([str(c.GATE/"run.py"),"--execute"],"b"*64,
                              output/"same-process-observation.json")
            return code,json.loads((output/"same-process-observation.json").read_text())
    def test_31_shim_original_exception_saved(self):
        def fail(argv):raise ValueError("ORIGINAL frozen gate exception")
        code,row=self.shim_fixture(SimpleNamespace(main=fail))
        self.assertEqual(code,1);self.assertIsNone(row["gate_returncode"])
        self.assertIn("ORIGINAL frozen gate exception",row["primary_error"]["error"])
        self.assertIn("ValueError",row["primary_error"]["traceback"])
    def test_32_shim_gate_failed_return_not_changed(self):
        code,row=self.shim_fixture(SimpleNamespace(main=lambda argv:9))
        self.assertEqual(code,9);self.assertEqual(row["gate_returncode"],9)
        self.assertIsNone(row["primary_error"])
    def test_33_shim_secondary_failure_cannot_become_complete0(self):
        code,row=self.shim_fixture(SimpleNamespace(main=lambda argv:0),
          {"secondary_errors":[{"stage":"maps","error":"synthetic maps-copy failure"}]})
        self.assertEqual(code,1);self.assertEqual(row["gate_returncode"],0)
        self.assertEqual(row["secondary_errors"][0]["stage"],"maps")

    def producer_bridge(self):
        """SYNTHETIC parser interoperability. Never issues actual NPU authority."""
        from contextlib import contextmanager
        from dataclasses import replace
        import time
        @contextmanager
        def fixture():
            runtime,_,a,_,_,_,_=c.closure()
            previous=sys.modules.get("contract")
            try:
                sys.modules["contract"]=a
                old=c.load("_selected_producer_frozen_fixture",c.ADMISSION/"tests/test_admission.py")
            finally:
                if previous is None:sys.modules.pop("contract",None)
                else:sys.modules["contract"]=previous
            f=old.Fixture()
            mp=c.ROOT/"runtime-native-library-snapshot-v1/MANIFEST.json"
            c.checked(mp,"7a6675fc13ad41dab32acbbdb40d78adb8345b43e0aaa61b8cdb0e804ff18c0b")
            snapshot=c.read(mp)
            self.assertEqual(snapshot["source_path"],str(c.NATIVE))
            self.assertEqual(snapshot["sha256"],c.NATIVE_SHA)
            self.assertFalse(snapshot["container_started"])
            self.assertFalse(snapshot["npu_executed"])
            native_bytes=c.checked(snapshot["host_snapshot_path"],c.NATIVE_SHA).read_bytes()
            def read_bytes(path):
                # Actual original immutable SO bytes only, NOT a real loaded map.
                if path==str(c.NATIVE):return native_bytes
                return Path(path).read_bytes()
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);runs=[];entries=[]
                for stage,card in (("isolated",4),("native_feedback",7)):
                    with patch.object(c,"ROOT",root):
                        e=c.plan("SYNTHETIC".lower(),stage,card,runtime,"SOFTWARE-no-container")
                    entries.append(e)
                    audit=Path(e["audit"]);audit.mkdir(parents=True)
                    out=Path(e["gate_out"]);out.mkdir(parents=True)
                    proof=Path(e["audit"])/"proof.json"
                    c.proof(proof,e,"a"*64,actual(e),{"SOFTWARE_ONLY_SYNTHETIC":True})
                    argv=c.shim_argv(e,"a"*64,"SOFTWARE-no-exec",proof,c.sha(c.BASE/"PACKET.json"))
                    proc=FakeProcess(done=True)
                    def popen(args,**kwargs):
                        kwargs["stdout"].write(b"SOFTWARE ONLY synthetic raw client stdout\n")
                        return proc
                    with patch.object(c.subprocess,"Popen",side_effect=popen):
                        ex=c.phase(argv,audit,lambda:None)
                    when=(ex["started_ns"]+ex["completed_ns"])//2
                    report=f.report(stage,c.read(proof),str(out),when)
                    for row in report.get("artifacts",[]):
                        Path(row["path"]).write_bytes(f.memory[row["path"]])
                    c.write(out/"report.json",report)
                    observation={"runtime":{"soc":"Ascend910B4","torch":"2.10.0+cpu",
                        "torch_npu":"2.10.0.post4","opp_version_info_sha256":c.OPP_SHA},
                        "runtime_image_sources":runtime["actual_image_sources"] if stage=="native_feedback" else {},
                        "loaded_libraries":c.expected_libraries(stage),"SOFTWARE_ONLY_SYNTHETIC":True}
                    c.write(e["observation"],observation)
                    child=c.child_receipt(e,"a"*64,ex,observation,report,proof,c.packet())
                    c.write(audit/"child.json",child)
                    childref=a.Ref(str(audit/"child.json"),c.sha(audit/"child.json"))
                    reportref=a.Ref(str(out/"report.json"),c.sha(out/"report.json"))
                    proofref=a.Ref(str(proof),c.sha(proof))
                    sources=tuple(a.Ref(str(c.BASE/name),pin) for name,pin in c.packet()["sources"].items())
                    opid="exec-SOFTWARE-ONLY-PRODUCER-"+stage
                    outerargs=("-B",str(c.BASE/"controller.py"),"--execute","--stage",stage,
                               "--physical-card",str(card),"--packet-sha256",c.sha(c.BASE/"PACKET.json"))
                    marker="MAIN_SELECTED_PREFILL_CHILD "+json.dumps({"child":a.ref_dict(childref),
                        "report":a.ref_dict(reportref),"stage":stage},sort_keys=True)
                    terminal={"schema":"agentweb.operation/v1","kind":"exec","operationId":opid,
                      "terminal":True,"status":"completed","succeeded":True,"error":None,
                      "SOFTWARE_ONLY_SYNTHETIC_NOT_ACTUAL_TOOL_EVIDENCE":True,
                      "operation":{"routeDecision":"peer_direct","targetPeerId":a.PEER,"result":{"record":{
                        "id":opid,"state":"completed","exitCode":0,"error":None,"cancelled":False,"timedOut":False,
                        "command":"/usr/bin/python3","args":list(outerargs),"cwd":str(c.REPO),
                        "stdout":marker,"stderr":"","durationMs":ex["duration_ms"]}}}}
                    c.write(audit/"terminal.json",terminal)
                    tref=a.Ref(str(audit/"terminal.json"),c.sha(audit/"terminal.json"))
                    t=a.TerminalAuthority(tref,a.PEER,opid,"/usr/bin/python3",outerargs,str(c.REPO))
                    runs.append(a.RunAuthority(stage,reportref,childref,t,argv[0],tuple(argv[1:]),str(c.REPO),
                                                "a"*64,card,proofref,sources))
                yield a,f,read_bytes,runs,entries
        return fixture()

    def test_34_original_full_admission_accepts_producer_shaped_software_fixture(self):
        with self.producer_bridge() as (a,f,reader,runs,entries):
            result=a.validate_complete(*runs,reader,source_manifest=f.manifest,enabled=True)
            self.assertEqual(result.batches,(1,16));self.assertEqual(result.native_case_count,8)
            self.assertEqual(result.isolated_case_count,134);self.assertEqual(len(result.libraries),4)
            self.assertFalse(result.serving_ready);self.assertFalse(result.performance_measurement_admitted)
            self.assertFalse(result.graph_supported);self.assertFalse(result.all_prefill_batches_supported)
            self.assertEqual(len(result.controller_sources),4)
            for run,e in zip(runs,entries):
                self.assertEqual(run.child_command,"docker")
                self.assertIn(str(c.BASE/"child_shim.py"),run.child_args)
                self.assertIn(str(c.GATE/"run.py"),run.child_args)
                self.assertEqual(run.child_args[run.child_args.index("--preflight")+1],run.owner_proof.path)
                self.assertEqual([p for p,rw in e["mounts"].items() if rw],[e["stage_output"]])
                i=run.child_args.index("--batches");self.assertEqual(run.child_args[i+1:i+3],("1","16"))
                if run.stage=="native_feedback":
                    for flag,value in (("--decode-library",str(c.DECODE)),("--decode-library-sha256",c.DECODE_SHA),
                                       ("--reference-library",str(c.REFERENCE)),("--reference-library-sha256",c.REFERENCE_SHA),
                                       ("--native-anchor-report",str(c.ANCHOR))):
                        self.assertEqual(run.child_args[run.child_args.index(flag)+1],value)
                    self.assertIn("DAMP_ENABLE_NATIVE_REFERENCE=1",run.child_args)

    def test_35_original_admission_rejects_duplicate_producer_marker(self):
        from dataclasses import replace
        with self.producer_bridge() as (a,f,reader,runs,entries):
            r=runs[0];terminal=c.read(r.terminal.receipt.path)
            terminal["operation"]["result"]["record"]["stdout"] += "\n"+terminal["operation"]["result"]["record"]["stdout"]
            p=Path(r.terminal.receipt.path).with_name("duplicate.json");c.write(p,terminal)
            bad=replace(r,terminal=replace(r.terminal,receipt=a.Ref(str(p),c.sha(p))))
            with self.assertRaises(a.Pending) as caught:
                a.validate_complete(bad,runs[1],reader,source_manifest=f.manifest,enabled=True)
            self.assertIn("raw stdout",str(caught.exception))

    def test_36_source_drift_before_mkdir_no_observation_or_fake_report(self):
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/"observation.json"
            with patch.object(shim,"image_admission",side_effect=RuntimeError("ORIGINAL SOURCE DRIFT")):
                with self.assertRaises(RuntimeError) as caught:
                    shim.run([str(c.GATE/"run.py"),"--execute"],"b"*64,output)
            self.assertIn("ORIGINAL SOURCE DRIFT",str(caught.exception))
            self.assertFalse(output.exists());self.assertFalse((Path(d)/"report.json").exists())

    def test_37_failure_record_keeps_dispatch_before_copy_or_gate_error(self):
        row=c.failure_record(RuntimeError("secondary copy"),{"error":"ORIGINAL DISPATCH"},
          {"error":"later gate"},{"primary_error":{"error":"later shim"}},[{"copy":"report","error":"missing"}])
        self.assertEqual(row["original_error"],"ORIGINAL DISPATCH")
        self.assertIn("secondary copy",row["controller_error"])
        self.assertEqual(row["secondary_errors"][0]["copy"],"report")
        row=c.failure_record(RuntimeError("copy"),{"error":None},None,
                             {"primary_error":{"error":"ORIGINAL BEFORE MKDIR"}},[])
        self.assertEqual(row["original_error"],"ORIGINAL BEFORE MKDIR")

    def test_38_host_failure_and_cleanup_fail_do_not_overwrite_dispatch_or_emit_marker(self):
        from contextlib import redirect_stdout
        import io
        with tempfile.TemporaryDirectory() as d,patch.object(c,"ROOT",Path(d)),patch.object(c,"deadline"),\
             patch.dict(c.os.environ,{"DAMP_SELECTED_PREFILL_DISPATCH_EXECUTE":"1"}):
            runtime={"actual_snapshot_manifests":[]};e=c.plan("synthetic","isolated",4,runtime,"software")
            parent=Path(d)/"original-parent-software.json";c.write(parent,{"SOFTWARE_ONLY":True})
            args=SimpleNamespace(run_id="synthetic",stage="isolated",physical_card=4,
                packet_sha256="b"*64,parent_operation_receipt=parent,parent_operation_sha256=c.sha(parent))
            class Commands:
                def __init__(self,audit):self.audit=audit
                def json(self,label,argv):
                    return [{"Id":c.IMAGE,"Architecture":"arm64"}]
                def run(self,label,argv,**kwargs):
                    if label=="stop-owned":raise RuntimeError("SECONDARY CLEANUP FAILURE")
                    return ("a"*64,"")
            h=SimpleNamespace(Commands=Commands,absent_names=lambda *a:None,
              inspect=lambda *a:dict(actual(e),State={"Running":True,"Status":"running","OOMKilled":False}),
              cgroup_record=lambda *a:{"memory_current_bytes":1})
            f=SimpleNamespace(BOOTSTRAP="software",terminal=lambda *a:None,parent_stopped=lambda *a:{"SOFTWARE_ONLY":True},
                             resources=lambda *a,**k:{"protected":{}})
            def canary(cmd,h,f,e,cid,protected,audit):
                p=audit/"actual-canary-software.json";c.write(p,{"SOFTWARE_ONLY":True});return p
            execution={"state":"failed","returncode":7,"error":"ORIGINAL DISPATCH FAILURE","stdout":"software",
                       "stderr":"software","cancelled":False,"timed_out":False}
            with patch.object(c,"closure"),patch.object(c,"packet",return_value={}),\
                 patch.object(c,"canary",side_effect=canary),patch.object(c,"phase",return_value=execution):
                captured=io.StringIO()
                with redirect_stdout(captured),self.assertRaises(RuntimeError):
                    c.execute(args,(runtime,None,None,f,h,None,{}),{"sources":{}})
            audit=Path(e["audit"]);failure=c.read(audit/"FAILURE.json");cleanup=c.read(audit/"CLEANUP_FAILURE.json")
            self.assertEqual(failure["original_error"],"ORIGINAL DISPATCH FAILURE")
            self.assertEqual(cleanup["original_error"],"ORIGINAL DISPATCH FAILURE")
            self.assertIn("SECONDARY CLEANUP FAILURE",cleanup["records"][0]["cleanup_error"])
            self.assertTrue(failure["secondary_errors"])
            self.assertNotIn("MAIN_SELECTED_PREFILL_CHILD",captured.getvalue())
            child=c.read(audit/"child-receipt.json")
            self.assertIsNone(child["report"]);self.assertIsNone(child["runtime"])

    def test_39_original_runner_before_mkdir_no_report_or_marker(self):
        from contextlib import redirect_stdout
        import io
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/"selected-prefill-dispatch-software-isolated"/"stage-output"
            out.mkdir(parents=True)
            args=SimpleNamespace(out=out/"isolated",stage="isolated")
            def fail(argv):raise RuntimeError("ORIGINAL RUNNER BEFORE MKDIR")
            runtime={"sources":{},"dependencies":{}}
            captured=io.StringIO()
            with patch.object(c,"ROOT",root),patch.object(c,"packet",return_value={}),\
                 patch.object(shim,"image_admission",return_value=(SimpleNamespace(main=fail),args,runtime)),\
                 patch.object(c,"expected_libraries",return_value={}),redirect_stdout(captured):
                code=shim.run([str(c.GATE/"run.py"),"--execute"],"b"*64,out/"same-process-observation.json")
            row=c.read(out/"same-process-observation.json")
            self.assertEqual(code,1);self.assertIsNone(row["gate_returncode"])
            self.assertIn("ORIGINAL RUNNER BEFORE MKDIR",row["primary_error"]["error"])
            self.assertIsNone(row["runtime"])
            self.assertFalse((out/"isolated").exists())
            self.assertNotIn("MAIN_SELECTED_PREFILL_CHILD",captured.getvalue())

if __name__=="__main__":unittest.main()
