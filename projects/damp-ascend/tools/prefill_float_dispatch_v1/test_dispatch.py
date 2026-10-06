"""Stdlib source/scheduling contracts only. No Docker, Torch or NPU execution."""
import ast
import contextlib
import copy
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("prefill_dispatch_contract", BASE / "dispatch.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

def parent(exit_code=0):
    h = SimpleNamespace(PARENT_OPERATION="exec-0000000000000455",
        PARENT_PEER="lgw_a6109c51076a4a2c9d2674ca5a8704a0")
    record = dict(id=h.PARENT_OPERATION, lane="job", state="completed", exitCode=exit_code,
        cancelled=False, timedOut=False, error=None, command="/usr/bin/python3", cwd=str(d.REPO))
    raw = dict(operationId=h.PARENT_OPERATION, terminal=True, operation=dict(
        routeDecision="peer_direct", targetPeerId=h.PARENT_PEER, result=dict(found=True, ok=True,
        lane="job", state="completed", record=record)))
    return h, raw

def actual(entry, cid="a"*64, running=True):
    argv = entry["docker_create_argv"]
    mounts = []
    for i, item in enumerate(argv):
        if item == "--mount":
            fields = dict(x.split("=",1) for x in argv[i+1].split(",") if "=" in x)
            mounts.append(dict(Destination=fields["target"], Source=fields["source"], Type="bind",
                               RW=not argv[i+1].endswith(",readonly")))
    after = argv[argv.index("--entrypoint")+2:]
    return dict(Id=cid, Name="/"+entry["container_name"], Image=d.IMAGE,
        Config=dict(Labels={"model-tuning-lab.owner":d.OWNER, "model-tuning-lab.run":entry["run_id"]},
            Env=[argv[i+1] for i,x in enumerate(argv) if x == "-e"],
            Entrypoint=["/bin/bash"], Cmd=after[1:], WorkingDir=str(d.REPO)),
        HostConfig=dict(Privileged=False, NetworkMode="none", IpcMode="private", DeviceRequests=None,
            Memory=d.MEMORY, MemorySwap=d.MEMORY, NanoCpus=10**9, CapDrop=["ALL"],
            SecurityOpt=["no-new-privileges"], Devices=[
                dict(PathOnHost="/dev/davinci"+str(entry["physical_card"]), PathInContainer="/dev/davinci0")]+[
                dict(PathOnHost="/dev/"+x, PathInContainer="/dev/"+x) for x in
                ("davinci_manager","devmm_svm","hisi_hdc")]),
        Mounts=mounts, State=dict(Running=running, Status="running" if running else "exited", Pid=123))

class DispatchContracts(unittest.TestCase):
    def test_real_terminal_not_outer_ok(self):
        for exit_code in (0, 1, 9):
            helper, raw = parent(exit_code)
            result = d.terminal(raw, helper)
            self.assertEqual(result["exit_code"], exit_code)
            self.assertEqual(result["capture_success"], exit_code == 0)
        h, raw = parent()
        for target, key, value in (("outer","terminal",False), ("route","targetPeerId","bad"),
                                  ("route","routeDecision","upstream_local_peer"),
                                  ("record","state","running"), ("record","timedOut",True),
                                  ("record","cancelled",True), ("record","exitCode",None),
                                  ("record","exitCode",True), ("record","command","bash"),
                                  ("record","cwd","/tmp")):
            bad = copy.deepcopy(raw)
            obj = bad if target == "outer" else bad["operation"] if target == "route" else bad["operation"]["result"]["record"]
            obj[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                d.terminal(bad,h)
        self.assertEqual(d.terminal({"structuredContent":raw},h)["operation_id"],h.PARENT_OPERATION)

    def test_exact_singlecard_create_scope(self):
        for physical in (4,5,6,7):
            entry = d.plan("contract",physical)
            row = actual(entry)
            self.assertEqual(d.inspect_owned(row,entry,"a"*64)["Id"],"a"*64)
            self.assertFalse(entry["launchable"])
            self.assertEqual(entry["logical_card"],0)
            self.assertIn("/dev/davinci%d:/dev/davinci0"%physical,entry["docker_create_argv"])
            self.assertNotIn("--privileged",entry["docker_create_argv"])
            launch = [m for m in row["Mounts"] if m["Destination"] == str(Path(entry["root"])/"launch")]
            self.assertEqual(len(launch),1)
            self.assertFalse(launch[0]["RW"])
        entry = d.plan("contract",4)
        for mode in range(11):
            bad = actual(entry)
            if mode == 0: bad["Id"]="b"*64
            elif mode == 1: bad["HostConfig"]["Privileged"]=True
            elif mode == 2: bad["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci0"
            elif mode == 3: bad["HostConfig"]["NetworkMode"]="host"
            elif mode == 4: bad["Mounts"][0]["RW"]=True
            elif mode == 5: bad["Config"]["Labels"]["model-tuning-lab.owner"]="foreign"
            elif mode == 6: bad["HostConfig"]["MemorySwap"]=9*d.GIB
            elif mode == 7: bad["HostConfig"]["NanoCpus"]=2*10**9
            elif mode == 8: bad["Config"]["Env"]=[]
            elif mode == 9: bad["Config"]["Cmd"]=["bad"]
            else: bad["HostConfig"]["Devices"].append(dict(PathOnHost="/dev/davinci7",PathInContainer="/dev/davinci7"))
            with self.subTest(mode=mode),self.assertRaises(RuntimeError):
                d.inspect_owned(bad,entry,"a"*64)
        for card in (0,3,8,True):
            with self.assertRaises(RuntimeError):d.plan("v1",card)
        for name in ("../escape","UPPER","x"*33,""):
            with self.assertRaises(RuntimeError):d.plan(name,4)

    def test_deadline_and_fixed_phase_budget(self):
        self.assertGreater(d.deadline(7200,datetime(2026,10,6,tzinfo=timezone.utc)),7200)
        with self.assertRaises(RuntimeError):
            d.deadline(now=datetime(2026,10,7,8,48,3,tzinfo=timezone.utc))
        with self.assertRaises(RuntimeError):
            d.deadline(3600,datetime(2026,10,7,8,tzinfo=timezone.utc))

    def test_no_overwrite_finite_json(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/"row.json"
            d.write(p,dict(raw_error=None,proof=False))
            self.assertFalse(d.read(p)["proof"])
            with self.assertRaises(FileExistsError):d.write(p,{})
            p = Path(temp)/"invalid.json"
            p.write_text('{"bad":NaN}')
            with self.assertRaises(ValueError):d.read(p)

    def test_source_admission_actual_host_no_torch(self):
        with patch.object(d.subprocess,"run",side_effect=AssertionError("no command")),\
                patch.object(d.subprocess,"Popen",side_effect=AssertionError("no process")):
            evidence,_,_,_,_ = d.closure()
        self.assertEqual((evidence["compiled_sources"],evidence["runtime_sources"],evidence["fixed_source_files"]),(9,15,4))
        self.assertIn("pending",evidence["image_local_OPP_admission"])
        self.assertNotIn("torch",sys.modules)
        self.assertNotIn("torch_npu",sys.modules)

    def test_actual_original_source_binding_called(self):
        original = SimpleNamespace(source_bindings=unittest.mock.Mock(return_value={"actual":1}),
                                   OPP_PATH=Path("/actual-image/OPP"))
        fixed = SimpleNamespace(source_snapshot=lambda args:{"all_match":True},
                                bind_sources=unittest.mock.Mock(return_value={"actual":1}))
        with patch.object(d,"closure",return_value=({},original,fixed,None,None)),\
                patch.object(d,"sha",return_value="a"*64):
            result = d.source_check()
        self.assertEqual(result["status"],"actual_source_bindings_pass")
        original.source_bindings.assert_called_once()
        fixed.bind_sources.assert_called_once()
        self.assertFalse(result["torch_imported"])
        self.assertFalse(result["npu_executed"])

    def test_source_binding_disagreement_rejects(self):
        original = SimpleNamespace(source_bindings=lambda a:{"original":1})
        fixed = SimpleNamespace(source_snapshot=lambda a:{"all_match":True},bind_sources=lambda *a:{"fixed":1})
        with patch.object(d,"closure",return_value=({},original,fixed,None,None)),self.assertRaises(RuntimeError):
            d.source_check()

    def test_default_dry_no_output_or_execution(self):
        out = io.StringIO()
        with patch.object(d,"closure",return_value=({},None,None,None,None)),\
                patch.object(d,"execute",side_effect=AssertionError("NO execute")),contextlib.redirect_stdout(out):
            self.assertEqual(d.main([]),0)
        row = json.loads(out.getvalue())
        self.assertFalse(row["launchable"])
        self.assertTrue(row["no_docker_or_npu"])
        self.assertFalse(row["scope"]["performance"])
        self.assertEqual(row["sequence"][2],"old full eager matrix")
        self.assertEqual(row["sequence"][4],"fixed-buffer eager matrix")

    def test_optin_before_any_preparation(self):
        with patch.dict(os.environ,{},clear=True),\
                patch.object(d,"closure",side_effect=AssertionError("must reject first")),self.assertRaises(RuntimeError):
            d.main(["--execute"])

    def test_wrong_report_or_artifact_rejects(self):
        with self.assertRaises(RuntimeError):d.report_identity({"status":"passed"})
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/"raw.pt"
            p.write_bytes(b"software fixture only")
            self.assertEqual(d.artifact(p,d.sha(p),Path(temp)),p)
            with self.assertRaises(RuntimeError):d.artifact(p,d.sha(p),Path(temp)/"wrong")
            with self.assertRaises(RuntimeError):d.artifact(p,"0"*64,Path(temp))

    def test_secondary_cleanup_cannot_replace_first_failure(self):
        process = SimpleNamespace(returncode=None, poll=lambda: None,
            terminate=unittest.mock.Mock(side_effect=ValueError("secondary-cleanup")),
            wait=unittest.mock.Mock(), kill=unittest.mock.Mock())
        entry = d.plan("contract",4)
        cmd = SimpleNamespace()
        with tempfile.TemporaryDirectory() as tmp, patch.object(d.subprocess,"Popen",return_value=process),\
                patch.object(d,"deadline",side_effect=[7200,RuntimeError("primary-deadline")]),\
                self.assertRaisesRegex(RuntimeError,"primary-deadline"):
            d.phase_run(cmd,None,["software-only-client"],entry,"a"*64,{},"old-matrix",Path(tmp))
            self.fail("must not continue")
        # A separate context verifies the persisted receipt before tempdir cleanup.
        with tempfile.TemporaryDirectory() as tmp, patch.object(d.subprocess,"Popen",return_value=process),\
                patch.object(d,"deadline",side_effect=[7200,RuntimeError("primary-deadline")]):
            with self.assertRaisesRegex(RuntimeError,"primary-deadline"):
                d.phase_run(cmd,None,["software-only-client"],entry,"a"*64,{},"old-matrix",Path(tmp))
            row=d.read(Path(tmp)/"old-matrix-command.json")
            self.assertIn("primary-deadline",row["error"])
            self.assertIn("secondary-cleanup",row["cleanup_errors"][0])
            self.assertFalse(row["automatic_retry"])

    def test_runner_before_mkdir_and_secondary_write_preserve_original_exception(self):
        for missing_output in (True, False):
            with self.subTest(missing_output=missing_output), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "prefill-float-dispatch-contract"
                (root / "launch").mkdir(parents=True)
                output = root / "old-matrix"
                if not missing_output:
                    output.mkdir()
                original = RuntimeError("primary-frozen-runner-before-mkdir")
                runner = SimpleNamespace(parse=lambda argv:SimpleNamespace(
                    execute=True, mode="npu", output_dir=str(output)),
                    main=unittest.mock.Mock(side_effect=original))
                stderr = io.StringIO()
                maps = "0 software " + str(d.SO.resolve()) + "\n0 software /software/libtorch_npu.so\n"
                with contextlib.ExitStack() as stack:
                    stack.enter_context(patch.object(d,"ROOT",Path(temp)))
                    stack.enter_context(patch.object(d,"closure",return_value=({},runner,None,None,None)))
                    stack.enter_context(patch.object(d,"source_check",return_value={}))
                    stack.enter_context(patch.object(d.Path,"read_text",return_value=maps))
                    stack.enter_context(patch.object(d,"sha",return_value=d.SO_SHA))
                    stack.enter_context(contextlib.redirect_stderr(stderr))
                    if not missing_output:
                        stack.enter_context(patch.object(d,"write",side_effect=OSError("secondary-evidence-write")))
                    with self.assertRaises(RuntimeError) as failure:
                        d.run_frozen_gate("old-matrix",[])
                self.assertIs(failure.exception,original)
                self.assertFalse((output/"LOADED_LIBRARIES.json").exists())
                if missing_output:
                    self.assertFalse(output.exists())
                row=json.loads(stderr.getvalue())
                self.assertEqual(row["status"],"failed")
                self.assertIn("primary-frozen-runner-before-mkdir",row["original_error"])
                self.assertIn("write failed",row["secondary_errors"][-1])
                self.assertFalse(row["evidence_written"])
                self.assertFalse(row["performance_claim"])

    def test_successful_runner_cannot_pass_failed_library_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"prefill-float-dispatch-contract"
            (root/"launch").mkdir(parents=True)
            output=root/"old-matrix"
            runner=SimpleNamespace(parse=lambda argv:SimpleNamespace(
                execute=True, mode="npu", output_dir=str(output)),main=lambda argv:None)
            stderr=io.StringIO()
            maps="0 software "+str(d.SO.resolve())+"\n0 software /software/libtorch_npu.so\n"
            with patch.object(d,"ROOT",Path(temp)),\
                    patch.object(d,"closure",return_value=({},runner,None,None,None)),\
                    patch.object(d,"source_check",return_value={}),\
                    patch.object(d.Path,"read_text",return_value=maps),\
                    patch.object(d,"sha",return_value=d.SO_SHA),\
                    patch.object(d,"write",side_effect=OSError("secondary-evidence-write")),\
                    contextlib.redirect_stderr(stderr),\
                    self.assertRaisesRegex(RuntimeError,"child loaded-library evidence failed"):
                d.run_frozen_gate("old-matrix",[])
            row=json.loads(stderr.getvalue())
            self.assertIsNone(row["original_error"])
            self.assertIn("secondary-evidence-write",row["secondary_errors"][-1])
            self.assertFalse(row["evidence_written"])

    def test_parse_failure_has_no_fabricated_output_or_library_evidence(self):
        original=SystemExit(2)
        runner=SimpleNamespace(parse=unittest.mock.Mock(side_effect=original),
                               main=unittest.mock.Mock())
        with patch.object(d,"closure",return_value=({},runner,None,None,None)),\
                patch.object(d,"source_check") as check,patch.object(d,"write") as write,\
                self.assertRaises(SystemExit) as failure:
            d.run_frozen_gate("old-matrix",[])
        self.assertIs(failure.exception,original)
        check.assert_not_called()
        write.assert_not_called()
        runner.main.assert_not_called()

    def test_early_source_check_failure_keeps_original_without_loaded_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"prefill-float-dispatch-contract"
            (root/"launch").mkdir(parents=True)
            original=RuntimeError("primary-source-check-before-runner")
            runner=SimpleNamespace(parse=lambda argv:SimpleNamespace(
                execute=True,mode="npu",output_dir=str(root/"old-matrix")),main=unittest.mock.Mock())
            with patch.object(d,"ROOT",Path(temp)),\
                    patch.object(d,"closure",return_value=({},runner,None,None,None)),\
                    patch.object(d,"source_check",side_effect=original),\
                    patch.object(d,"write") as write,self.assertRaises(RuntimeError) as failure:
                d.run_frozen_gate("old-matrix",[])
            self.assertIs(failure.exception,original)
            write.assert_not_called()
            runner.main.assert_not_called()
            self.assertFalse((root/"old-matrix").exists())
    def test_scope_sequence_first_failure_and_idle_owner(self):
        text = (BASE/"dispatch.py").read_text()
        ast.parse(text)
        self.assertNotIn("shell=True",text)
        self.assertNotIn('"rm"',text)
        self.assertIn('["docker", "stop", "--time", "30", cid]',text)
        self.assertIn('write(audit / "FAILURE.json", dict(original_error=failed',text)
        self.assertLess(text.index('write(audit / "FAILURE.json"'),text.index('cmd.run("stop-owned"'))
        self.assertIn('source_lock_required=False',text)
        self.assertIn('before = resources(cmd, h, entry["physical_card"], protected, cid)',text)
        self.assertIn('record = resources(cmd, h, entry["physical_card"], protected, cid, idle=False)',text)
        self.assertIn('for kind in ("old-matrix", "fixed-buffers"):',text)
        self.assertIn('closure(); packet(args.packet_manifest, args.packet_sha256)',text)
        self.assertNotIn("operation_get",text)
        self.assertEqual(d.PHASE_TIMEOUT,3600)
        self.assertEqual(d.FIXED_SHA,"44b4bb5056c8fb6695725fcd6058a72e45d67023ebf0c206c3c106d9bdfd860d")

if __name__=="__main__":
    unittest.main()
